<template>
  <section class="space-y-3 rounded-xl border border-outline-gray-2 bg-white p-3.5 sm:p-4" :aria-busy="initialLoading || running">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 class="flex items-center gap-2 text-sm font-semibold text-ink-gray-9">
        <FeatherIcon name="zap" class="size-4 text-ink-gray-6" aria-hidden="true" />
        {{ __('AI Call Summary') }}
      </h3>
      <Button
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
      <p>{{ requestError || view.error }}</p>
      <Button v-if="requestError" variant="subtle" class="mt-2" :label="__('Refresh summary')" @click="refresh" />
    </div>
    <p v-if="notice && !running" class="text-sm leading-5 text-ink-gray-6">{{ notice }}</p>

    <div v-if="view?.result" class="space-y-3 border-t border-outline-gray-2 pt-3">
      <div class="flex flex-wrap items-center gap-2">
        <Badge :label="__('Summary saved')" theme="green" />
        <time class="text-xs text-ink-gray-5">{{ formatCallTime(view.result.generated_at) }}</time>
      </div>
      <div>
        <h4 class="text-sm font-semibold text-ink-gray-9">{{ __('Summary') }}</h4>
        <p class="mt-1 whitespace-pre-wrap break-words text-sm leading-5 text-ink-gray-7">{{ view.result.summary }}</p>
      </div>
      <div v-for="group in resultGroups" :key="group.label">
        <h4 class="text-sm font-semibold text-ink-gray-9">{{ __(group.label) }}</h4>
        <ul v-if="group.items.length" class="mt-1 list-disc space-y-1 pl-5 text-sm leading-5 text-ink-gray-7">
          <li v-for="(item, index) in group.items" :key="index" class="break-words">{{ item }}</li>
        </ul>
        <p v-else class="mt-1 text-sm text-ink-gray-6">{{ __('None identified in the call.') }}</p>
      </div>
      <details class="rounded-md bg-surface-gray-1 p-2.5">
        <summary class="cursor-pointer text-sm font-medium text-ink-gray-9">{{ __('Transcript') }}</summary>
        <p class="mt-2 whitespace-pre-wrap break-words text-sm leading-5 text-ink-gray-7">{{ view.result.transcript }}</p>
      </details>
    </div>

    <details v-if="view?.legacy_note" :open="!view.result" class="rounded-md bg-surface-gray-1 p-2.5">
      <summary class="cursor-pointer text-sm font-medium text-ink-gray-9">{{ __('Legacy AI summary') }}</summary>
      <p class="mt-2 text-xs text-ink-gray-6">{{ __('The earlier workflow saved these notes without a transcript.') }}</p>
      <p class="mt-2 whitespace-pre-wrap break-words text-sm leading-5 text-ink-gray-7">{{ view.legacy_note }}</p>
    </details>
  </section>
</template>

<script setup>
import { Badge, Button, FeatherIcon, call } from 'frappe-ui'
import { computed, onUnmounted, ref, watch } from 'vue'
import { formatCallTime } from '@/utils/contactCenterCalls'

const props = defineProps({
  callLogName: { type: String, required: true },
  recordingUrl: { type: String, default: '' },
})
const view = ref(null)
const initialLoading = ref(true)
const submitting = ref(false)
const requestError = ref('')
const running = computed(() => submitting.value || ['Queued', 'Processing'].includes(view.value?.status))
const canGenerate = computed(() =>
  !running.value && !requestError.value && !view.value?.retry_after &&
  view.value?.configured && view.value.recording_state === 'Available',
)
const resultGroups = computed(() => [
  { label: 'Customer needs', items: view.value.result.customer_needs },
  { label: 'Next steps', items: view.value.result.next_steps },
])
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
  if (recordingMessages[view.value.recording_state]) return __(recordingMessages[view.value.recording_state])
  if (!view.value.configured) return __('BeeKnoee is not configured for Call Summary.')
  if (view.value.retry_after) return __('The call can be summarized again shortly.')
  if (view.value.recording_changed) return __('The recording changed. Generate a summary from the selected recording.')
  return __('Generating a summary sends the private recording to BeeKnoee.')
})

let requestId = 0
let pollTimer = null

async function load(method, values = {}) {
  clearTimeout(pollTimer)
  const id = ++requestId
  requestError.value = ''
  try {
    const result = await call('doublet_crm.call_log.ai_summary.' + method, {
      call_log_name: props.callLogName,
      ...values,
    })
    if (id === requestId) view.value = result
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
  return load('get_call_summary')
}

function generate() {
  if (!canGenerate.value) return
  submitting.value = true
  return load('summarize_call', { regenerate: Boolean(view.value?.result || view.value?.legacy_note) })
}

watch(() => [props.callLogName, props.recordingUrl], () => {
  view.value = null
  initialLoading.value = true
  submitting.value = false
  refresh()
}, { immediate: true })

onUnmounted(() => {
  requestId++
  clearTimeout(pollTimer)
})
</script>
