<template>
  <Teleport to="body">
    <Transition name="call-log-drawer">
      <div
        v-if="show"
        class="fixed inset-0 z-[90] flex justify-end bg-black/25"
        @click.self="show = false"
      >
        <section
          ref="panel"
          class="flex h-full w-full min-w-0 flex-col bg-white shadow-2xl outline-none sm:max-w-[34rem]"
          role="dialog"
          aria-modal="true"
          :aria-label="__('Call details')"
          tabindex="-1"
          @keydown="handleKey"
        >
          <header class="shrink-0 border-b border-outline-gray-2 px-4 pb-3 pt-4 sm:px-6">
            <div class="flex items-start gap-3">
              <span class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-surface-gray-2 text-ink-gray-7">
                <FeatherIcon :name="callDirectionIcon" class="size-5" aria-hidden="true" />
              </span>
              <div class="min-w-0 flex-1">
                <h2 class="break-words text-lg font-semibold leading-6 text-ink-gray-9">
                  {{ callLog.customer?.label || callLog.customer_number || __(callLog.call_type || 'Call') }}
                </h2>
                <div class="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-ink-gray-6">
                  <Badge :label="__(callLog.status || 'Unknown')" :theme="callOutcomeTheme(callLog.status)" />
                  <span>{{ __(callLog.call_type || 'Call') }}</span>
                  <span>{{ formatCallTime(callLog.start_time) }}</span>
                </div>
              </div>
              <Button
                variant="ghost"
                icon="x"
                :label="__('Close call details')"
                class="shrink-0"
                @click="show = false"
              />
            </div>

            <nav v-if="sections.length > 1" :aria-label="__('Call detail sections')" class="mt-4 flex flex-wrap gap-1.5">
              <Button
                v-for="item in sections"
                :key="item.value"
                :label="__(item.label)"
                :variant="activeSection === item.value ? 'subtle' : 'ghost'"
                :aria-pressed="activeSection === item.value"
                @click="section = item.value"
              />
            </nav>
          </header>

          <slot name="feedback" />

          <div ref="body" class="min-h-0 flex-1 overflow-y-auto overscroll-contain bg-surface-gray-1 px-3 py-3 sm:px-5 sm:py-4">
            <div v-if="activeSection === 'overview'" class="space-y-3 sm:space-y-4">
              <section class="rounded-xl border border-outline-gray-2 bg-white p-3.5 sm:p-4">
                <h3 class="text-sm font-semibold text-ink-gray-9">{{ __('Call information') }}</h3>
                <dl class="mt-3 grid grid-cols-2 gap-x-3 gap-y-3.5 text-sm">
                  <div class="min-w-0">
                    <dt class="text-xs text-ink-gray-5">{{ __('From') }}</dt>
                    <dd class="mt-0.5 break-words font-medium tabular-nums text-ink-gray-9">{{ callLog.from_number || '—' }}</dd>
                  </div>
                  <div class="min-w-0">
                    <dt class="text-xs text-ink-gray-5">{{ __('To') }}</dt>
                    <dd class="mt-0.5 break-words font-medium tabular-nums text-ink-gray-9">{{ callLog.to_number || '—' }}</dd>
                  </div>
                  <div>
                    <dt class="text-xs text-ink-gray-5">{{ __('Duration') }}</dt>
                    <dd class="mt-0.5 font-medium tabular-nums text-ink-gray-9">{{ duration }}</dd>
                  </div>
                  <div class="min-w-0">
                    <dt class="text-xs text-ink-gray-5">{{ __('Agent') }}</dt>
                    <dd class="mt-0.5 break-words text-ink-gray-8">{{ callLog.agent || '—' }}</dd>
                  </div>
                  <div v-if="callLog.line_number" class="col-span-2 min-w-0">
                    <dt class="text-xs text-ink-gray-5">{{ __('Line') }}</dt>
                    <dd class="mt-0.5 break-words text-ink-gray-8">{{ callLog.line_number }}</dd>
                  </div>
                </dl>
              </section>

              <section class="rounded-xl border border-outline-gray-2 bg-white p-3.5 sm:p-4">
                <h3 class="flex items-center gap-2 text-sm font-semibold text-ink-gray-9">
                  <FeatherIcon name="headphones" class="size-4 text-ink-gray-5" aria-hidden="true" />
                  {{ __('Recording') }}
                </h3>
                <div v-if="callLog.recording?.state === 'Available' && !recordingFailed" class="mt-2 space-y-2">
                  <a
                    :href="callLog.recording.url"
                    :aria-label="__('Open recording')"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="flex items-start gap-1.5 break-all text-sm font-medium text-ink-blue-6 hover:underline"
                  >
                    {{ callLog.recording.label }}
                    <FeatherIcon name="arrow-up-right" class="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
                  </a>
                  <audio
                    class="block h-9 w-full min-w-0"
                    controls
                    preload="none"
                    :src="callLog.recording.url"
                    :aria-label="__('Call recording')"
                    @error="recordingFailed = true"
                  />
                </div>
                <div v-else class="mt-2 rounded-md bg-surface-gray-1 p-2.5 text-sm leading-5 text-ink-gray-7">
                  <p role="status">{{ __(recordingMessage) }}</p>
                  <Button
                    v-if="recordingFailed"
                    class="mt-2"
                    variant="subtle"
                    :label="__('Retry playback')"
                    @click="recordingFailed = false"
                  />
                </div>
              </section>

              <section id="call-customer-details" class="rounded-xl border border-outline-gray-2 bg-white p-3.5 sm:p-4">
                <h3 class="text-sm font-semibold text-ink-gray-9">{{ __('Related customer') }}</h3>
                <RouterLink
                  v-if="customerRoute"
                  :to="customerRoute"
                  class="mt-2 inline-flex max-w-full items-start gap-1.5 break-words text-sm font-medium text-ink-blue-6 hover:underline"
                >
                  <span class="min-w-0">{{ callLog.customer.label }}</span>
                  <FeatherIcon name="arrow-up-right" class="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
                </RouterLink>
                <p v-else class="mt-1.5 text-sm text-ink-gray-6">{{ __(linkMessages[callLog.link_state]) }}</p>
                <slot name="customer-actions" />
              </section>

              <section v-if="callLog.note" class="rounded-xl border border-outline-gray-2 bg-white p-3.5 sm:p-4">
                <h3 class="text-sm font-semibold text-ink-gray-9">{{ __('Original note') }}</h3>
                <p class="mt-1.5 whitespace-pre-wrap break-words text-sm leading-5 text-ink-gray-7">{{ callLog.note }}</p>
              </section>

              <details class="rounded-xl border border-outline-gray-2 bg-white px-3.5 py-3 sm:px-4">
                <summary class="cursor-pointer text-sm font-medium text-ink-gray-8">{{ __('Technical details') }}</summary>
                <dl class="mt-3 space-y-2 text-sm">
                  <div class="flex justify-between gap-3">
                    <dt class="text-ink-gray-5">{{ __('Log ID') }}</dt>
                    <dd class="break-all text-right font-mono text-xs text-ink-gray-8">{{ callLog.name }}</dd>
                  </div>
                  <div class="flex justify-between gap-3">
                    <dt class="shrink-0 text-ink-gray-5">{{ __('External Call ID') }}</dt>
                    <dd class="min-w-0 break-all text-right font-mono text-xs text-ink-gray-8">{{ callLog.external_call_id || '—' }}</dd>
                  </div>
                  <div class="flex justify-between gap-3">
                    <dt class="text-ink-gray-5">{{ __('Ended') }}</dt>
                    <dd class="text-right text-ink-gray-8">{{ formatCallTime(callLog.end_time) }}</dd>
                  </div>
                </dl>
              </details>
            </div>
            <CallLogAISummary
              v-else-if="activeSection === 'ai'"
              :call-log-name="callLog.name"
              :recording-url="callLog.recording?.url || ''"
            />
            <slot v-else-if="activeSection === 'handling'" name="handling" />
            <slot v-else name="history" />
          </div>

          <slot v-if="activeSection === 'handling'" name="footer" />
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { Badge, Button, FeatherIcon } from 'frappe-ui'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import CallLogAISummary from '@/components/Modals/CallLogAISummary.vue'
import { callCustomerRoute, callOutcomeTheme, formatCallTime } from '@/utils/contactCenterCalls'

const show = defineModel({ type: Boolean })
const section = defineModel('section', { type: String, default: 'overview' })
const props = defineProps({ callLog: { type: Object, required: true } })
const panel = ref(null)
const body = ref(null)
const recordingFailed = ref(false)
const customerRoute = computed(() => callCustomerRoute(props.callLog.customer))
const activeSection = computed(() =>
  sections.value.some((item) => item.value === section.value) ? section.value : 'overview',
)
const callDirectionIcon = computed(() =>
  props.callLog.call_type?.startsWith('Incoming') ? 'phone-incoming' : 'phone-outgoing',
)
const duration = computed(() => {
  const seconds = Math.max(0, Math.floor(Number(props.callLog.duration) || 0))
  const minutes = Math.floor(seconds / 60)
  const pad = (part) => String(part).padStart(2, '0')
  const time = pad(minutes % 60) + ':' + pad(seconds % 60)
  return minutes >= 60 ? Math.floor(minutes / 60) + ':' + time : time
})
const sections = computed(() => {
  const items = [{ value: 'overview', label: 'Overview' }]
  if (props.callLog.can_handle) {
    items.push({ value: 'handling', label: 'Handling' }, { value: 'history', label: 'History' })
  }
  if (props.callLog.can_use_ai_summary) items.push({ value: 'ai', label: 'AI Summary' })
  return items
})
const recordingMessages = {
  None: 'No recording attached.',
  Legacy: 'Attach a private audio file to play this legacy recording.',
  Ambiguous: 'Multiple audio files are attached. Set the recording link on the Call Log to enable playback.',
  Missing: 'Recording unavailable. The private audio file may be missing.',
}
const recordingMessage = computed(() =>
  recordingFailed.value
    ? 'Playback failed. Retry or check the private audio file.'
    : recordingMessages[props.callLog.recording?.state] || recordingMessages.Missing,
)
const linkMessages = {
  Unmatched: 'No customer is linked. Select a Lead or Contact.',
  Ambiguous: 'Several customers match this number. Select the correct record.',
  Restricted: 'The linked customer is outside your access.',
}

let returnFocus = null
onMounted(async () => {
  returnFocus = document.activeElement
  await nextTick()
  panel.value?.focus({ preventScroll: true })
})
onUnmounted(() => {
  if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true })
})
watch(activeSection, () => {
  if (body.value) body.value.scrollTop = 0
})
watch(() => props.callLog.recording?.url, () => { recordingFailed.value = false })

function handleKey(event) {
  if (event.key === 'Escape') {
    event.stopPropagation()
    show.value = false
  }
  if (event.key !== 'Tab') return
  const controls = [...panel.value.querySelectorAll('a[href], button, input, select, textarea, summary, audio[controls], [tabindex="0"]')]
    .filter((element) => element.tabIndex >= 0 && !element.disabled && element.getClientRects().length)
  const first = controls[0]
  const last = controls.at(-1)
  if (event.shiftKey && [first, panel.value].includes(document.activeElement)) {
    event.preventDefault()
    last?.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first?.focus()
  }
}
</script>

<style scoped>
.call-log-drawer-enter-active,
.call-log-drawer-leave-active {
  transition: opacity 0.18s ease;
}

.call-log-drawer-enter-active > section,
.call-log-drawer-leave-active > section {
  transition: transform 0.2s ease;
}

.call-log-drawer-enter-from,
.call-log-drawer-leave-to {
  opacity: 0;
}

.call-log-drawer-enter-from > section,
.call-log-drawer-leave-to > section {
  transform: translateX(28px);
}

@media (prefers-reduced-motion: reduce) {
  .call-log-drawer-enter-active,
  .call-log-drawer-leave-active,
  .call-log-drawer-enter-active > section,
  .call-log-drawer-leave-active > section {
    transition: none;
  }
}
</style>
