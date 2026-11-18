<template>
  <section class="rounded-2xl border bg-white p-4">
    <div class="flex items-center justify-between gap-2">
      <div class="flex items-center gap-2">
        <FeatherIcon name="zap" class="h-4 w-4 text-violet-600" />
        <h3 class="text-sm font-semibold text-ink-gray-9">AI Call Assistant</h3>
      </div>

      <span
        v-if="recordingUrl"
        class="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700"
      >
        <FeatherIcon name="mic" class="h-3 w-3" />
        Sẵn sàng phân tích
      </span>
      <span
        v-else
        class="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500"
      >
        Chưa có file ghi âm
      </span>
    </div>

    <p class="mt-2 text-xs text-gray-500">
      {{
        recordingUrl
          ? "AI sẽ đọc dữ liệu ghi âm của cuộc gọi này để tóm tắt nội dung và đề xuất Next Step."
          : "Cuộc gọi này chưa có dữ liệu ghi âm từ tổng đài."
      }}
    </p>

    <div v-if="recordingUrl" class="mt-3 flex items-center justify-between gap-2">
      <label class="inline-flex cursor-pointer items-center gap-2 text-xs text-gray-600">
        <input
          v-model="autoSaveNextStep"
          type="checkbox"
          class="rounded border-gray-300 text-violet-600 focus:ring-violet-500"
        />
        <span>Tự động lưu Next Step vào Notes</span>
      </label>

      <Button
        label="AI Đọc & Tóm tắt"
        variant="solid"
        :loading="isAnalyzing"
        :disabled="!canAnalyze"
        @click="analyzeCall"
      />
    </div>

    <p v-if="error" class="mt-3 text-xs font-medium text-red-600">
      {{ error }}
    </p>

    <div v-if="summary || nextStep" class="mt-4 space-y-3 rounded-xl bg-violet-50/80 p-4">
      <div v-if="transcript">
        <div class="text-xs font-semibold uppercase tracking-wide text-violet-800">
          Nội dung ghi âm (Transcript)
        </div>
        <p class="mt-1 whitespace-pre-wrap text-xs leading-5 text-gray-700">
          {{ transcript }}
        </p>
      </div>

      <div v-if="summary" class="border-t border-violet-200/70 pt-3">
        <div class="text-xs font-semibold uppercase tracking-wide text-violet-800">
          Tóm tắt cuộc gọi
        </div>
        <p class="mt-1 whitespace-pre-wrap text-sm leading-6 text-gray-900">
          {{ summary }}
        </p>
      </div>

      <div class="border-t border-violet-200/70 pt-3">
        <label class="text-xs font-semibold uppercase tracking-wide text-violet-800">
          Next Step (có thể chỉnh sửa trước khi lưu)
        </label>
        <textarea
          v-model="nextStep"
          rows="3"
          class="mt-1.5 w-full rounded-xl border border-violet-200 bg-white p-2.5 text-sm text-gray-900 focus:border-violet-500 focus:outline-none"
          placeholder="Hành động tiếp theo sau cuộc gọi..."
        />

        <div class="mt-2.5 flex items-center justify-between gap-2">
          <span v-if="saveSuccess" class="text-xs font-medium text-emerald-700">
            {{ saveSuccess }}
          </span>
          <span v-else class="text-xs text-gray-500">
            Lưu trực tiếp vào phần Notes của cuộc gọi
          </span>

          <Button
            label="Lưu Next Step vào Notes"
            variant="solid"
            :loading="isSaving"
            :disabled="isSaving || (!nextStep.trim() && !summary.trim())"
            @click="saveToNotes"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from "vue"
import { Button, FeatherIcon } from "frappe-ui"

const props = defineProps({
  callLogName: { type: String, default: "" },
  recordingUrl: { type: String, default: "" },
})

const emit = defineEmits(["note-updated"])

const autoSaveNextStep = ref(true)
const isAnalyzing = ref(false)
const isSaving = ref(false)
const transcript = ref("")
const summary = ref("")
const nextStep = ref("")
const error = ref("")
const saveSuccess = ref("")

const canAnalyze = computed(() =>
  Boolean(props.callLogName) &&
  Boolean(props.recordingUrl) &&
  !isAnalyzing.value
)

function getCsrfToken() {
  return window.csrf_token || window.frappe?.csrf_token || ""
}

async function analyzeCall() {
  if (!canAnalyze.value) return
  isAnalyzing.value = true
  error.value = ""
  saveSuccess.value = ""
  transcript.value = ""
  summary.value = ""
  nextStep.value = ""

  try {
    const res = await fetch("/api/method/doublet_crm.call_log.ai_summary.summarize_call", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": getCsrfToken(),
      },
      body: JSON.stringify({
        call_log_name: props.callLogName,
      }),
    })

    const data = await res.json()
    if (!res.ok || data.exc) {
      let msg = "Không thể phân tích file ghi âm. Vui lòng thử lại."
      if (data._server_messages) {
        try {
          const parsed = JSON.parse(data._server_messages)
          const first = JSON.parse(parsed[0])
          if (first?.message) msg = first.message
        } catch (_) {}
      }
      throw new Error(msg)
    }

    const payload = data.message || {}
    transcript.value = payload.transcript || ""
    summary.value = payload.summary || ""
    nextStep.value = payload.next_step || ""

    if (autoSaveNextStep.value && (nextStep.value.trim() || summary.value.trim())) {
      await saveToNotes()
    }
  } catch (err) {
    error.value = err?.message || "Không thể phân tích file ghi âm. Vui lòng thử lại."
  } finally {
    isAnalyzing.value = false
  }
}

async function saveToNotes() {
  if (isSaving.value || (!nextStep.value.trim() && !summary.value.trim())) return
  isSaving.value = true
  error.value = ""
  saveSuccess.value = ""

  try {
    const res = await fetch("/api/method/doublet_crm.call_log.ai_summary.save_next_step_to_note", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": getCsrfToken(),
      },
      body: JSON.stringify({
        call_log_name: props.callLogName,
        next_step: nextStep.value.trim(),
        summary: summary.value.trim(),
        mode: "append",
      }),
    })

    const data = await res.json()
    if (!res.ok || data.exc) {
      throw new Error("Không thể lưu Next Step vào Notes.")
    }

    const updatedNote = data.message?.note
    if (typeof updatedNote === "string") {
      emit("note-updated", updatedNote)
    }
    saveSuccess.value = "Đã lưu vào Notes!"
  } catch (err) {
    error.value = err?.message || "Không thể lưu Next Step vào Notes."
  } finally {
    isSaving.value = false
  }
}
</script>