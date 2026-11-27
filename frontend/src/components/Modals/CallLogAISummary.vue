<template>
  <section class="space-y-4 rounded-xl border border-outline-gray-2 bg-white p-3.5 sm:p-5" :aria-busy="initialLoading || running">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 class="flex items-center gap-2 text-base font-semibold text-ink-gray-9">
        <FeatherIcon name="zap" class="size-4 text-ink-gray-6" aria-hidden="true" />
        {{ __('AI Call Assistant') }}
      </h3>
      <Badge v-if="view?.demo_only" :label="__('DEMO / MÔ PHỎNG')" theme="orange" />
      <Button
        v-else
        variant="solid"
        :label="__(view?.result || view?.legacy_note ? 'Regenerate' : 'Generate')"
        :loading="running"
        :disabled="!canGenerate"
        @click="generate"
      />
    </div>

    <p v-if="initialLoading" class="text-sm text-ink-gray-6" role="status">{{ __('Loading AI summary…') }}</p>
    <p v-if="running" class="text-sm text-ink-gray-7" role="status">
      {{ __(view?.status === 'Queued' ? 'Waiting for the AI worker…' : 'Processing the recording…') }}
    </p>
    <div v-if="requestError || view?.error" class="rounded-md bg-red-50 p-2.5 text-sm text-red-800" role="alert">
      <p class="font-medium">{{ __('AI summary unavailable') }}</p>
      <p class="mt-1">{{ requestError || view.error }}</p>
      <Button v-if="requestError" variant="subtle" class="mt-2" :label="__('Refresh summary')" @click="refresh" />
    </div>
    <p v-if="notice && !running" class="text-sm leading-5 text-ink-gray-6">{{ notice }}</p>

    <div v-if="result" class="space-y-4">
      <div v-if="view.demo_sample" class="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-950">
        {{ view.demo_sample.label }}
      </div>
      <div v-else class="flex flex-wrap items-center gap-2">
        <Badge :label="__('Summary saved')" theme="green" />
        <time class="text-xs text-ink-gray-5">{{ formatCallTime(result.generated_at) }}</time>
      </div>

      <div class="grid gap-3 sm:grid-cols-2">
        <section class="min-w-0 rounded-lg bg-surface-gray-1 p-3">
          <h4 class="text-sm font-semibold text-ink-gray-9">{{ __('Summary') }}</h4>
          <p class="mt-1.5 whitespace-pre-wrap break-words text-sm leading-5 text-ink-gray-7">{{ result.summary }}</p>
        </section>
        <section class="min-w-0 rounded-lg bg-surface-gray-1 p-3">
          <h4 class="text-sm font-semibold text-ink-gray-9">{{ __('Customer Needs') }}</h4>
          <ul v-if="result.customer_needs.length" class="mt-1.5 list-disc space-y-1 pl-5 text-sm leading-5 text-ink-gray-7">
            <li v-for="(item, index) in result.customer_needs" :key="index" class="break-words">{{ item }}</li>
          </ul>
          <p v-else class="mt-1.5 text-sm text-ink-gray-6">{{ __('None identified in the call.') }}</p>
        </section>
      </div>

      <details class="rounded-lg border border-outline-gray-2 p-3">
        <summary class="cursor-pointer text-sm font-semibold text-ink-gray-9">{{ __('Transcript') }}</summary>
        <p class="mt-2 whitespace-pre-wrap break-words text-sm leading-5 text-ink-gray-7">{{ result.transcript }}</p>
      </details>

      <section class="space-y-2 rounded-lg border border-outline-gray-2 p-3" :aria-label="__('Next Steps')">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h4 class="text-sm font-semibold text-ink-gray-9">{{ __('Next Steps') }}</h4>
          <Badge v-if="noteState?.version" :label="__('Saved in Notes')" theme="green" />
        </div>
        <form v-if="noteState?.can_save" class="space-y-2" @submit.prevent="saveNextSteps">
          <FormControl
            v-model="draft"
            type="textarea"
            :label="__('Edit next steps before saving')"
            :rows="4"
            :maxlength="12000"
            :disabled="saving"
            @update:model-value="saveFeedback = ''"
          />
          <p class="text-xs leading-5 text-ink-gray-6">{{ __('Use one step per line. The saved note appears in the linked customer’s Notes.') }}</p>
          <Button
            type="submit"
            variant="solid"
            :label="__('Save to Notes')"
            :loading="saving"
            :disabled="!draft.trim() || Boolean(noteState.version && !draftChanged)"
          />
          <p v-if="saveFeedback" class="text-sm text-green-700" role="status">{{ saveFeedback }}</p>
          <div v-if="saveError" class="space-y-2 text-sm text-red-700" role="alert">
            <p>{{ saveError }}</p>
            <Button variant="subtle" :label="__('Reload saved note')" @click="refresh" />
          </div>
        </form>
        <template v-else>
          <p v-if="noteState?.version" class="whitespace-pre-wrap break-words text-sm leading-5 text-ink-gray-7">{{ noteState.content }}</p>
          <ul v-else-if="result.next_steps.length" class="list-disc space-y-1 pl-5 text-sm leading-5 text-ink-gray-7">
            <li v-for="(item, index) in result.next_steps" :key="index" class="break-words">{{ item }}</li>
          </ul>
          <p v-else class="text-sm text-ink-gray-6">{{ __('None identified in the call.') }}</p>
          <p v-if="noteState?.reason" class="text-xs text-ink-gray-6">{{ noteState.reason }}</p>
        </template>
      </section>
    </div>

    <details v-if="view?.legacy_note" :open="!view.result" class="rounded-md bg-surface-gray-1 p-2.5">
      <summary class="cursor-pointer text-sm font-medium text-ink-gray-9">{{ __('Legacy AI summary') }}</summary>
      <p class="mt-2 text-xs text-ink-gray-6">{{ __('The earlier workflow saved these notes without a transcript.') }}</p>
      <p class="mt-2 whitespace-pre-wrap break-words text-sm leading-5 text-ink-gray-7">{{ view.legacy_note }}</p>
    </details>
  </section>
</template>

<script setup>
import { Badge, Button, FeatherIcon, FormControl, call } from 'frappe-ui'
import { computed, onUnmounted, ref, watch } from 'vue'
import { formatCallTime } from '@/utils/contactCenterCalls'

const props = defineProps({
  callLogName: { type: String, required: true },
  recordingUrl: { type: String, default: '' },
})
const api = 'doublet_crm.call_log.ai_summary.'
const view = ref(null)
const initialLoading = ref(true)
const submitting = ref(false)
const requestError = ref('')
const result = computed(() => view.value?.demo_sample || view.value?.result)
const running = computed(() => submitting.value || ['Queued', 'Processing'].includes(view.value?.status))
const canGenerate = computed(() =>
  !running.value && !requestError.value && !view.value?.retry_after &&
  view.value?.configured && view.value.recording_state === 'Available',
)
const noteState = ref(null)
const draft = ref('')
const loadedDraft = ref('')
const draftChanged = computed(() => draft.value !== loadedDraft.value)
const saving = ref(false)
const saveError = ref('')
const saveFeedback = ref('')
const recordingMessages = {
  None: 'Attach a private recording to this call.',
  Missing: 'The private recording could not be opened.',
  Legacy: 'Attach a private copy of the legacy recording to generate a summary.',
  Ambiguous: 'Select the call’s recording before generating a summary.',
  TooLarge: 'The recording exceeds the 25 MB limit.',
  Invalid: 'The private recording is empty or invalid.',
}
const notice = computed(() => {
  if (!view.value) return ''
  if (view.value.demo_only) {
    return view.value.demo_sample ? '' : __('The private demo WAV or manifest is unavailable.')
  }
  if (recordingMessages[view.value.recording_state]) return __(recordingMessages[view.value.recording_state])
  if (!view.value.configured) return __('BeeKnoee API key or valid HTTPS configuration is missing. Contact your administrator.')
  if (view.value.retry_after) return __('The call can be summarized again shortly.')
  if (view.value.recording_changed) return __('The recording changed. Generate a summary from the selected recording.')
  if (view.value.status === 'Error') return __('The previous AI request failed. Refresh the summary or try again later.')
  return __('Generating a summary sends the private recording to BeeKnoee.')
})

let requestId = 0
let saveId = 0
let pollTimer = null

async function load(method, values = {}) {
  clearTimeout(pollTimer)
  const id = ++requestId
  const noteRequest = saveId
  requestError.value = ''
  try {
    const response = await call(api + method, { call_log_name: props.callLogName, ...values })
    if (id !== requestId) return
    view.value = response
    if (response.next_steps_note && noteRequest === saveId && !saving.value) {
      const dirty = draftChanged.value
      noteState.value = response.next_steps_note
      loadedDraft.value = noteState.value.content ?? result.value.next_steps.join('\n')
      if (!dirty) draft.value = loadedDraft.value
    }
  } catch (e) {
    if (id === requestId) {
      view.value = null
      requestError.value = e.messages?.[0] || __('Unable to load the AI summary. Try again.')
    }
  } finally {
    if (id === requestId) {
      initialLoading.value = false
      submitting.value = false
      if (running.value) pollTimer = setTimeout(refresh, 2000)
      else if (view.value?.configured && view.value?.retry_after) {
        pollTimer = setTimeout(refresh, view.value.retry_after * 1000)
      }
    }
  }
}

function refresh() {
  saveError.value = ''
  return load('get_call_summary')
}

function generate() {
  if (!canGenerate.value) return
  submitting.value = true
  return load('summarize_call', { regenerate: Boolean(view.value?.result || view.value?.legacy_note) })
}

async function saveNextSteps() {
  if (!noteState.value?.can_save || saving.value || !draft.value.trim()) return
  const id = ++saveId
  saving.value = true
  saveError.value = ''
  saveFeedback.value = ''
  try {
    const saved = await call(api + 'save_next_steps', {
      call_log_name: props.callLogName,
      content: draft.value,
      version: noteState.value.version,
    })
    if (id !== saveId) return
    noteState.value = { ...noteState.value, ...saved }
    draft.value = loadedDraft.value = saved.content
    saveFeedback.value = __('Next steps saved to Notes.')
  } catch (e) {
    if (id === saveId) saveError.value = e.messages?.[0] || __('Unable to save the next steps. Your edits are still here.')
  } finally {
    if (id === saveId) saving.value = false
  }
}

watch(() => [props.callLogName, props.recordingUrl], () => {
  ++saveId
  view.value = null
  noteState.value = null
  draft.value = loadedDraft.value = ''
  saving.value = false
  saveFeedback.value = ''
  initialLoading.value = true
  submitting.value = false
  refresh()
}, { immediate: true })

onUnmounted(() => {
  requestId++
  saveId++
  clearTimeout(pollTimer)
})
</script>
