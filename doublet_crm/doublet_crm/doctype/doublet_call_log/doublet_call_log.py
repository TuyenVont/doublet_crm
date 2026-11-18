import random
import frappe
from frappe.model.document import Document
from frappe.utils.background_jobs import get_workers

MOCK_RECORDINGS = [
    "/files/mock-call-01.mp3",
    "/files/mock-call-02.mp3",
    "/files/mock-call-03.mp3",
]


class DoubleTCallLog(Document):
    def before_insert(self):
        # Tự động gán file ghi âm giả định nếu chưa có recording_url
        if not (self.recording_url or "").strip():
            self.recording_url = random.choice(MOCK_RECORDINGS)

    def after_insert(self):
        if not (self.recording_url or "").strip():
            return

        has_active_worker = bool(get_workers())
        frappe.enqueue(
            "doublet_crm.call_log.ai_summary.auto_process_call_log",
            queue="default",
            timeout=120,
            call_log_name=self.name,
            enqueue_after_commit=has_active_worker,
            now=not has_active_worker,
        )
