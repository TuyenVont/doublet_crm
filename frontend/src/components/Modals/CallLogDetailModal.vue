<template>
  <Teleport to="body">
    <Transition name="call-log-drawer">
      <div
        v-if="show"
        class="fixed inset-0 z-[100] flex justify-end bg-black/25 backdrop-blur-[1px]"
        @click.self="show = false"
      >
        <div
          class="flex h-full w-full flex-col bg-white shadow-2xl sm:max-w-xl"
        >
          <!-- Header -->
          <div class="border-b px-5 py-4 sm:px-6">
            <div class="flex items-start justify-between gap-4">
              <div class="flex min-w-0 items-center gap-3">
                <div
                  class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-sky-100 text-sky-700"
                >
                  <FeatherIcon
                    :name="callTypeIcon(callLog.call_type)"
                    class="h-5 w-5"
                  />
                </div>

                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2">
                    <h2 class="text-lg font-semibold text-ink-gray-9">
                      {{ __(callLog.call_type || 'Call') }}
                    </h2>

                    <span
                      class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold"
                      :class="statusClass(callLog.status)"
                    >
                      {{ __(callLog.status || 'Unknown') }}
                    </span>
                  </div>

                  <div class="mt-1 text-sm text-ink-gray-5">
                    {{ formatDateTime(callLog.start_time) }}
                  </div>
                </div>
              </div>

              <Button
                variant="ghost"
                icon="x"
                @click="show = false"
              />
            </div>
          </div>

          <!-- Body -->
          <div class="flex-1 overflow-y-auto px-5 py-5 sm:px-6">
            <div class="flex flex-col gap-5">
              <!-- Call summary -->
              <div class="grid grid-cols-2 gap-3">
                <InfoCard
                  :label="__('Duration')"
                  :value="formatDuration(callLog.duration)"
                  icon="clock"
                />
                <InfoCard
                  :label="__('Agent')"
                  :value="callLog.agent || '—'"
                  icon="user"
                />
              </div>

              <!-- Phone flow -->
              <section class="rounded-2xl border bg-gray-50/60 p-4">
                <div class="mb-4 text-xs font-semibold uppercase tracking-wide text-ink-gray-5">
                  {{ __('Call route') }}
                </div>

                <div class="flex items-center gap-3">
                  <div class="min-w-0 flex-1">
                    <div class="text-xs text-ink-gray-5">
                      {{ __('From') }}
                    </div>
                    <div class="mt-1 truncate text-base font-semibold text-ink-gray-9">
                      {{ callLog.from_number || '—' }}
                    </div>
                  </div>

                  <div
                    class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white text-sky-700 shadow-sm ring-1 ring-gray-200"
                  >
                    <FeatherIcon name="arrow-right" class="h-4 w-4" />
                  </div>

                  <div class="min-w-0 flex-1 text-right">
                    <div class="text-xs text-ink-gray-5">
                      {{ __('To') }}
                    </div>
                    <div class="mt-1 truncate text-base font-semibold text-ink-gray-9">
                      {{ callLog.to_number || '—' }}
                    </div>
                  </div>
                </div>

                <div
                  v-if="callLog.line_number"
                  class="mt-4 border-t pt-3 text-xs text-ink-gray-5"
                >
                  {{ __('Line') }}:
                  <span class="font-medium text-ink-gray-8">
                    {{ callLog.line_number }}
                  </span>
                </div>
              </section>

              <!-- Related customer -->
              <section
                v-if="callLog.reference_name"
                class="rounded-2xl border bg-white p-4"
              >
                <div class="text-xs font-semibold uppercase tracking-wide text-ink-gray-5">
                  {{ __('Related customer') }}
                </div>

                <div class="mt-3 flex items-center gap-3">
                  <div
                    class="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50 text-violet-700"
                  >
                    <FeatherIcon
                      :name="callLog.reference_doctype === 'DoubleT Lead' ? 'user' : 'contact'"
                      class="h-4 w-4"
                    />
                  </div>

                  <div class="min-w-0">
                    <div class="truncate text-sm font-semibold text-ink-gray-9">
                      {{ callLog.reference_name }}
                    </div>
                    <div class="text-xs text-ink-gray-5">
                      {{ callLog.reference_doctype }}
                    </div>
                  </div>
                </div>
              </section>

              <!-- Recording -->
              <section
                v-if="callLog.recording_url"
                class="rounded-2xl border bg-white p-4"
              >
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <div class="text-xs font-semibold uppercase tracking-wide text-ink-gray-5">
                      {{ __('Recording') }}
                    </div>
                    <div class="mt-1 text-sm text-ink-gray-7">
                      {{ __('Call recording URL') }}
                    </div>
                  </div>

                  <a
                    :href="callLog.recording_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-sm font-medium text-sky-700 hover:underline"
                  >
                    {{ __('Open') }}
                  </a>
                </div>

                <audio
                  class="mt-4 h-9 w-full"
                  controls
                  preload="none"
                  :src="callLog.recording_url"
                ></audio>
              </section>

              <!-- Note -->
              <section class="rounded-2xl border bg-white p-4">
                <div class="flex items-center gap-2">
                  <FeatherIcon
                    name="file-text"
                    class="h-4 w-4 text-ink-gray-5"
                  />
                  <div class="text-xs font-semibold uppercase tracking-wide text-ink-gray-5">
                    {{ __('Note') }}
                  </div>
                </div>

                <div
                  v-if="callLog.note"
                  class="mt-3 whitespace-pre-wrap text-sm leading-6 text-ink-gray-8"
                >
                  {{ callLog.note }}
                </div>

                <div
                  v-else
                  class="mt-3 text-sm italic text-ink-gray-4"
                >
                  {{ __('No note for this call.') }}
                </div>
              </section>

              <!-- Technical -->
              <section class="rounded-2xl border bg-gray-50/60 p-4">
                <div class="text-xs font-semibold uppercase tracking-wide text-ink-gray-5">
                  {{ __('Technical details') }}
                </div>

                <dl class="mt-3 space-y-3 text-sm">
                  <div class="flex items-start justify-between gap-4">
                    <dt class="text-ink-gray-5">
                      {{ __('Call ID') }}
                    </dt>
                    <dd class="max-w-[65%] break-all text-right font-mono text-xs text-ink-gray-8">
                      {{ callLog.external_call_id || '—' }}
                    </dd>
                  </div>

                  <div class="flex items-start justify-between gap-4">
                    <dt class="text-ink-gray-5">
                      {{ __('Started') }}
                    </dt>
                    <dd class="text-right text-ink-gray-8">
                      {{ formatDateTime(callLog.start_time) }}
                    </dd>
                  </div>

                  <div class="flex items-start justify-between gap-4">
                    <dt class="text-ink-gray-5">
                      {{ __('Ended') }}
                    </dt>
                    <dd class="text-right text-ink-gray-8">
                      {{ formatDateTime(callLog.end_time) }}
                    </dd>
                  </div>
                </dl>
              </section>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { Button, FeatherIcon } from 'frappe-ui'
import { defineComponent, h } from 'vue'

const show = defineModel({ type: Boolean })
const callLog = defineModel('callLog', {
  type: Object,
  default: () => ({}),
})

const InfoCard = defineComponent({
  props: {
    label: String,
    value: [String, Number],
    icon: String,
  },
  setup(props) {
    return () =>
      h(
        'div',
        {
          class:
            'rounded-2xl border bg-white p-4 shadow-sm',
        },
        [
          h(
            'div',
            {
              class:
                'flex items-center gap-2 text-xs font-medium text-ink-gray-5',
            },
            [
              h(FeatherIcon, {
                name: props.icon,
                class: 'h-3.5 w-3.5',
              }),
              props.label,
            ],
          ),
          h(
            'div',
            {
              class:
                'mt-2 truncate text-base font-semibold text-ink-gray-9',
            },
            props.value || '—',
          ),
        ],
      )
  },
})

function callTypeIcon(type) {
  return ['Incoming', 'Incoming Forwarded'].includes(type)
    ? 'phone-incoming'
    : 'phone-outgoing'
}

function statusClass(status) {
  const classes = {
    Completed: 'bg-emerald-50 text-emerald-700',
    Missed: 'bg-red-50 text-red-700',
    'No Answer': 'bg-red-50 text-red-700',
    Failed: 'bg-red-50 text-red-700',
    Busy: 'bg-amber-50 text-amber-700',
    Canceled: 'bg-gray-100 text-gray-600',
  }

  return classes[status] || 'bg-gray-100 text-gray-600'
}

function formatDuration(seconds) {
  const total = Math.max(0, Number(seconds || 0))

  if (!Number.isFinite(total)) return '00:00'

  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const secs = Math.floor(total % 60)

  if (hours) {
    return [
      hours,
      String(minutes).padStart(2, '0'),
      String(secs).padStart(2, '0'),
    ].join(':')
  }

  return [
    String(minutes).padStart(2, '0'),
    String(secs).padStart(2, '0'),
  ].join(':')
}

function formatDateTime(value) {
  if (!value) return '—'

  const parsed = new Date(String(value).replace(' ', 'T'))

  if (Number.isNaN(parsed.getTime())) return value

  return new Intl.DateTimeFormat('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(parsed)
}
</script>

<style scoped>
.call-log-drawer-enter-active,
.call-log-drawer-leave-active {
  transition: opacity 0.18s ease;
}

.call-log-drawer-enter-active > div,
.call-log-drawer-leave-active > div {
  transition: transform 0.2s ease;
}

.call-log-drawer-enter-from,
.call-log-drawer-leave-to {
  opacity: 0;
}

.call-log-drawer-enter-from > div,
.call-log-drawer-leave-to > div {
  transform: translateX(28px);
}
</style>
