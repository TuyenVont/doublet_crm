import json
import mimetypes
import os
from urllib.parse import urlparse

import frappe
import requests
from frappe import _
from frappe.utils.file_manager import save_file

BEEKNOEE_BASE_URL = "https://platform.beeknoee.com/v1"
ALLOWED_AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".mp4", ".mpeg"}
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB


def _get_ai_config():
    api_key = os.environ.get("DOUBLET_BEEKNOEE_API_KEY")
    if not api_key:
        frappe.throw(_("AI service is not configured."))
    stt_model = os.environ.get("DOUBLET_BEEKNOEE_STT_MODEL", "whisper-large-v3-turbo")
    llm_model = os.environ.get("DOUBLET_BEEKNOEE_MODEL", "openai/gpt-oss-120b")
    return api_key, stt_model, llm_model


def _resolve_local_file_path(file_url: str) -> str | None:
    if not file_url:
        return None
    parsed = urlparse(file_url)
    path = parsed.path if parsed.scheme else file_url

    if path.startswith("/private/files/"):
        rel_path = path.lstrip("/")
    elif path.startswith("/files/"):
        rel_path = os.path.join("public", path.lstrip("/"))
    else:
        return None

    site_root = os.path.abspath(frappe.get_site_path())
    full_path = os.path.abspath(os.path.join(site_root, rel_path))
    if not full_path.startswith(site_root + os.sep):
        frappe.throw(_("Invalid file path."))
    if not os.path.isfile(full_path):
        frappe.throw(_("Recording file not found on server."))
    return full_path


def _load_audio_payload(call_log, uploaded_file=None):
    """Return (filename, audio_bytes, content_type, new_recording_url_or_None)."""
    if uploaded_file is not None:
        filename = os.path.basename(uploaded_file.filename or "recording.mp3")
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_AUDIO_EXTS:
            frappe.throw(_("Unsupported audio format. Use MP3, WAV, M4A, OGG, or WEBM."))

        audio_bytes = uploaded_file.read()
        if not audio_bytes:
            frappe.throw(_("Uploaded audio file is empty."))
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            frappe.throw(_("Audio file exceeds 25 MB limit."))

        content_type = uploaded_file.mimetype or mimetypes.guess_type(filename)[0] or "audio/mpeg"

        new_url = None
        if not call_log.recording_url:
            saved = save_file(
                fname=filename,
                content=audio_bytes,
                dt="DoubleT Call Log",
                dn=call_log.name,
                is_private=0,
            )
            new_url = saved.file_url
            call_log.db_set("recording_url", new_url, update_modified=True)

        return filename, audio_bytes, content_type, new_url

    recording_url = (call_log.recording_url or "").strip()
    if not recording_url:
        frappe.throw(_("No recording found. Please upload an audio file."))

    local_path = _resolve_local_file_path(recording_url)
    if local_path:
        filename = os.path.basename(local_path)
        with open(local_path, "rb") as f:
            audio_bytes = f.read()
        content_type = mimetypes.guess_type(filename)[0] or "audio/mpeg"
        return filename, audio_bytes, content_type, None

    if recording_url.startswith(("http://", "https://")):
        try:
            resp = requests.get(recording_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException:
            frappe.throw(_("Could not download recording from Recording URL."))
        audio_bytes = resp.content
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            frappe.throw(_("Remote audio file exceeds 25 MB limit."))
        filename = os.path.basename(urlparse(recording_url).path) or "recording.mp3"
        content_type = resp.headers.get("Content-Type") or "audio/mpeg"
        return filename, audio_bytes, content_type, None

    frappe.throw(_("Invalid Recording URL."))


def _transcribe_audio(api_key: str, stt_model: str, filename: str, audio_bytes: bytes, content_type: str) -> str:
    try:
        response = requests.post(
            f"{BEEKNOEE_BASE_URL}/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (filename, audio_bytes, content_type)},
            data={"model": stt_model, "language": "vi"},
            timeout=90,
        )
    except requests.RequestException:
        frappe.throw(_("Speech-to-Text service connection failed."))

    if not response.ok:
        frappe.throw(_("Speech-to-Text service could not transcribe the audio."))

    try:
        data = response.json()
        transcript = (data.get("text") or "").strip()
    except ValueError:
        transcript = response.text.strip()

    if not transcript:
        frappe.throw(_("No speech detected in the audio file."))

    return transcript


def _analyze_transcript(api_key: str, llm_model: str, transcript: str) -> dict:
    system_prompt = (
        "Bạn là trợ lý phân tích cuộc gọi CRM. Dựa trên transcript cuộc gọi tiếng Việt, "
        "hãy trả về DUY NHẤT một đối tượng JSON hợp lệ (không markdown, không giải thích thêm) "
        "với đúng 2 khóa:\n"
        '1. "summary": Tóm tắt ngắn gọn nội dung chính của cuộc gọi (2-4 câu, tiếng Việt).\n'
        '2. "next_step": Danh sách hành động tiếp theo (Next Steps) cụ thể, rõ người thực hiện/thời hạn nếu có, '
        "trình bày dạng gạch đầu dòng ngắn gọn bằng tiếng Việt.\n"
        "Chỉ dựa vào thông tin trong transcript, không bịa đặt."
    )

    try:
        response = requests.post(
            f"{BEEKNOEE_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": llm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcript[:12000]},
                ],
                "max_tokens": 1200,
                "temperature": 0.2,
                "stream": False,
            },
            timeout=90,
        )
    except requests.RequestException:
        frappe.throw(_("AI summary service connection failed."))

    if not response.ok:
        frappe.throw(_("AI summary service could not process the transcript."))

    try:
        raw_content = response.json()["choices"][0]["message"]["content"].strip()
    except (ValueError, KeyError, IndexError, TypeError):
        frappe.throw(_("Invalid AI summary response."))

    if raw_content.startswith("```"):
        lines = raw_content.splitlines()
        raw_content = "\n".join(line for line in lines if not line.strip().startswith("```")).strip()

    try:
        parsed = json.loads(raw_content)
        raw_summary = parsed.get("summary")
        summary = "\n".join(str(x).strip() for x in raw_summary if str(x).strip()) if isinstance(raw_summary, list) else str(raw_summary or "").strip()

        raw_next_step = parsed.get("next_step")
        if isinstance(raw_next_step, list):
            steps = []
            for item in raw_next_step:
                s = str(item or "").strip()
                if s:
                    steps.append(s if s.startswith("-") else f"- {s}")
            next_step = "\n".join(steps)
        else:
            next_step = str(raw_next_step or "").strip()
    except ValueError:
        summary = raw_content
        next_step = ""

    if not summary and not next_step:
        frappe.throw(_("AI returned an empty analysis."))

    return {"summary": summary, "next_step": next_step}


@frappe.whitelist()
def summarize_call(call_log_name: str, transcript: str | None = None):
    if not call_log_name:
        frappe.throw(_("Call Log ID is required."))

    call_log = frappe.get_doc("DoubleT Call Log", call_log_name)
    call_log.check_permission("read")

    api_key, stt_model, llm_model = _get_ai_config()

    uploaded_file = None
    if getattr(frappe, "request", None) and getattr(frappe.request, "files", None):
        uploaded_file = frappe.request.files.get("audio_file")

    new_recording_url = None
    if uploaded_file or not (transcript and transcript.strip()):
        filename, audio_bytes, content_type, new_recording_url = _load_audio_payload(
            call_log, uploaded_file=uploaded_file
        )
        transcript_text = _transcribe_audio(api_key, stt_model, filename, audio_bytes, content_type)
    else:
        transcript_text = transcript.strip()
        if len(transcript_text) < 10 or len(transcript_text) > 12000:
            frappe.throw(_("Transcript must contain 10 to 12000 characters."))

    analysis = _analyze_transcript(api_key, llm_model, transcript_text)

    return {
        "transcript": transcript_text,
        "summary": analysis["summary"],
        "next_step": analysis["next_step"],
        "recording_url": new_recording_url or call_log.recording_url or "",
    }


@frappe.whitelist()
def save_next_step_to_note(call_log_name: str, next_step: str, summary: str = "", mode: str = "append"):
    if not call_log_name:
        frappe.throw(_("Call Log ID is required."))

    next_step = (next_step or "").strip()
    summary = (summary or "").strip()
    if not next_step and not summary:
        frappe.throw(_("Nothing to save to Notes."))

    call_log = frappe.get_doc("DoubleT Call Log", call_log_name)
    call_log.check_permission("write")

    blocks = []
    if summary:
        blocks.append(f"[AI Tóm tắt]\n{summary}")
    if next_step:
        blocks.append(f"[Next Step]\n{next_step}")
    ai_block = "\n\n".join(blocks)

    existing_note = (call_log.note or "").strip()
    if mode == "replace" or not existing_note:
        updated_note = ai_block
    else:
        updated_note = f"{existing_note}\n\n---\n{ai_block}"

    call_log.db_set("note", updated_note, update_modified=True)

    return {
        "note": updated_note,
    }


def auto_process_call_log(call_log_name: str):
    """Background job: transcribe recording, extract summary + next_step, and append to note."""
    if not call_log_name or not frappe.db.exists("DoubleT Call Log", call_log_name):
        return

    call_log = frappe.get_doc("DoubleT Call Log", call_log_name)
    if not (call_log.recording_url or "").strip():
        return

    # Skip if AI summary/next step was already written
    existing_note = (call_log.note or "").strip()
    if "[Next Step]" in existing_note or "[AI Tóm tắt]" in existing_note:
        return

    try:
        api_key, stt_model, llm_model = _get_ai_config()
        filename, audio_bytes, content_type, _ = _load_audio_payload(call_log)
        transcript_text = _transcribe_audio(api_key, stt_model, filename, audio_bytes, content_type)
        analysis = _analyze_transcript(api_key, llm_model, transcript_text)

        blocks = []
        if analysis.get("summary"):
            blocks.append(f"[AI Tóm tắt]\n{analysis['summary']}")
        if analysis.get("next_step"):
            blocks.append(f"[Next Step]\n{analysis['next_step']}")
        if not blocks:
            return

        ai_block = "\n\n".join(blocks)
        updated_note = f"{existing_note}\n\n---\n{ai_block}" if existing_note else ai_block
        frappe.db.set_value("DoubleT Call Log", call_log_name, "note", updated_note, update_modified=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"DoubleT AI Call Summary Failed: {call_log_name}")
