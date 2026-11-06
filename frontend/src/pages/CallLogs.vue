<template>
  <div class="flex h-full flex-col bg-gray-50/70">
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-3">
          <div
            class="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-100 text-sky-700"
          >
            <PhoneIcon class="h-5 w-5" />
          </div>

          <div>
            <div class="text-base font-semibold text-ink-gray-9">
              {{ __('Call Logs') }}
            </div>
            <div class="text-xs text-ink-gray-5">
              {{ __('Call history and customer conversations') }}
            </div>
          </div>
        </div>
      </template>

      <template #right-header>
        <Button
          variant="subtle"
          icon="refresh-cw"
          :loading="callLogs.loading"
          @click="callLogs.reload()"
        >
          {{ __('Refresh') }}
        </Button>
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
      <div class="mx-auto flex max-w-[1600px] flex-col gap-5">
        <!-- KPI -->
        <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <div class="rounded-2xl border bg-white p-4 shadow-sm">
            <div class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
              {{ __('Total calls') }}
            </div>
            <div class="mt-2 text-2xl font-semibold text-ink-gray-9">
              {{ summary.total }}
            </div>
          </div>

          <div class="rounded-2xl border bg-white p-4 shadow-sm">
            <div class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
              {{ __('Completed') }}
            </div>
            <div class="mt-2 flex items-center gap-2">
              <div class="text-2xl font-semibold text-ink-gray-9">
                {{ summary.completed }}
              </div>
              <span class="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
            </div>
          </div>

          <div class="rounded-2xl border bg-white p-4 shadow-sm">
            <div class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
              {{ __('Missed') }}
            </div>
            <div class="mt-2 flex items-center gap-2">
              <div class="text-2xl font-semibold text-ink-gray-9">
                {{ summary.missed }}
              </div>
              <span class="h-2.5 w-2.5 rounded-full bg-red-500"></span>
            </div>
          </div>

          <div class="rounded-2xl border bg-white p-4 shadow-sm">
            <div class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
              {{ __('Avg. duration') }}
            </div>
            <div class="mt-2 text-2xl font-semibold text-ink-gray-9">
              {{ formatDuration(summary.avgDuration) }}
            </div>
          </div>
        </div>

        <!-- Toolbar -->
        <div
          class="flex flex-col gap-3 rounded-2xl border bg-white p-3 shadow-sm lg:flex-row lg:items-center"
        >
          <div class="relative min-w-0 flex-1">
            <FeatherIcon
              name="search"
              class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-gray-5"
            />
            <input
              v-model="search"
              type="text"
              :placeholder="__('Search phone, agent, reference, external ID...')"
              class="h-10 w-full rounded-xl border border-gray-200 bg-gray-50 pl-9 pr-3 text-sm outline-none transition focus:border-sky-400 focus:bg-white focus:ring-2 focus:ring-sky-100"
            />
          </div>

          <select
            v-model="statusFilter"
            class="h-10 rounded-xl border border-gray-200 bg-white px-3 text-sm text-ink-gray-8 outline-none focus:border-sky-400"
          >
            <option value="">{{ __('All statuses') }}</option>
            <option
              v-for="status in statuses"
              :key="status"
              :value="status"
            >
              {{ __(status) }}
            </option>
          </select>

          <select
            v-model="typeFilter"
            class="h-10 rounded-xl border border-gray-200 bg-white px-3 text-sm text-ink-gray-8 outline-none focus:border-sky-400"
          >
            <option value="">{{ __('All call types') }}</option>
            <option
              v-for="type in callTypes"
              :key="type"
              :value="type"
            >
              {{ __(type) }}
            </option>
          </select>
        </div>

        <!-- Error -->
        <div
          v-if="callLogs.error"
          class="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700"
        >
          {{ __('Could not load Call Logs.') }}
          <Button class="ml-2" variant="subtle" @click="callLogs.reload()">
            {{ __('Retry') }}
          </Button>
        </div>

        <!-- Loading -->
        <div
          v-else-if="callLogs.loading && !logs.length"
          class="rounded-2xl border bg-white p-10 text-center text-sm text-ink-gray-5 shadow-sm"
        >
          {{ __('Loading call history...') }}
        </div>

        <!-- List -->
        <div
          v-else
          class="overflow-hidden rounded-2xl border bg-white shadow-sm"
        >
          <div class="overflow-x-auto">
            <table class="w-full min-w-[980px] border-collapse">
              <thead>
                <tr class="border-b bg-gray-50/80 text-left">
                  <th class="px-4 py-3 text-xs font-semibold text-ink-gray-5">
                    {{ __('Time') }}
                  </th>
                  <th class="px-4 py-3 text-xs font-semibold text-ink-gray-5">
                    {{ __('Call') }}
                  </th>
                  <th class="px-4 py-3 text-xs font-semibold text-ink-gray-5">
                    {{ __('Number') }}
                  </th>
                  <th class="px-4 py-3 text-xs font-semibold text-ink-gray-5">
                    {{ __('Related') }}
                  </th>
                  <th class="px-4 py-3 text-xs font-semibold text-ink-gray-5">
                    {{ __('Agent') }}
                  </th>
                  <th class="px-4 py-3 text-xs font-semibold text-ink-gray-5">
                    {{ __('Duration') }}
                  </th>
                  <th class="px-4 py-3 text-xs font-semibold text-ink-gray-5">
                    {{ __('Status') }}
                  </th>
                  <th class="w-12 px-3 py-3"></th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="log in filteredLogs"
                  :key="log.name"
                  class="group cursor-pointer border-b last:border-b-0 hover:bg-sky-50/50"
                  @click="openDetail(log)"
                >
                  <td class="px-4 py-3.5">
                    <div class="text-sm font-medium text-ink-gray-9">
                      {{ formatDateTime(log.start_time).date }}
                    </div>
                    <div class="mt-0.5 text-xs text-ink-gray-5">
                      {{ formatDateTime(log.start_time).time }}
                    </div>
                  </td>

                  <td class="px-4 py-3.5">
                    <div class="flex items-center gap-2">
                      <div
                        class="flex h-8 w-8 items-center justify-center rounded-full bg-sky-50 text-sky-700"
                      >
                        <FeatherIcon
                          :name="callTypeIcon(log.call_type)"
                          class="h-4 w-4"
                        />
                      </div>

                      <div>
                        <div class="text-sm font-medium text-ink-gray-9">
                          {{ __(log.call_type || 'Unknown') }}
                        </div>
                        <div
                          v-if="log.line_number"
                          class="text-xs text-ink-gray-5"
                        >
                          {{ log.line_number }}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td class="px-4 py-3.5">
                    <div class="text-sm font-medium text-ink-gray-9">
                      {{ primaryNumber(log) || '—' }}
                    </div>
                    <div class="mt-0.5 text-xs text-ink-gray-5">
                      {{ secondaryNumber(log) }}
                    </div>
                  </td>

                  <td class="px-4 py-3.5">
                    <div
                      v-if="log.reference_name"
                      class="inline-flex max-w-[220px] items-center gap-1.5 rounded-lg bg-gray-100 px-2 py-1 text-xs font-medium text-ink-gray-8"
                    >
                      <FeatherIcon
                        :name="log.reference_doctype === 'DoubleT Lead' ? 'user' : 'contact'"
                        class="h-3.5 w-3.5"
                      />
                      <span class="truncate">{{ log.reference_name }}</span>
                    </div>
                    <span v-else class="text-sm text-ink-gray-4">—</span>
                  </td>

                  <td class="px-4 py-3.5">
                    <div class="max-w-[180px] truncate text-sm text-ink-gray-8">
                      {{ log.agent || '—' }}
                    </div>
                  </td>

                  <td class="px-4 py-3.5">
                    <div class="font-mono text-sm text-ink-gray-8">
                      {{ formatDuration(log.duration) }}
                    </div>
                  </td>

                  <td class="px-4 py-3.5">
                    <span
                      class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold"
                      :class="statusClass(log.status)"
                    >
                      {{ __(log.status || 'Unknown') }}
                    </span>
                  </td>

                  <td class="px-3 py-3.5">
                    <FeatherIcon
                      name="chevron-right"
                      class="h-4 w-4 text-ink-gray-4 group-hover:text-sky-600"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div
            v-if="!filteredLogs.length"
            class="px-6 py-14 text-center"
          >
            <div
              class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-100"
            >
              <PhoneIcon class="h-5 w-5 text-ink-gray-5" />
            </div>
            <div class="mt-3 text-sm font-medium text-ink-gray-8">
              {{ __('No call logs found') }}
            </div>
            <div class="mt-1 text-xs text-ink-gray-5">
              {{ __('Try changing your filters or search terms.') }}
            </div>
          </div>

          <div
            v-if="logs.length"
            class="flex items-center justify-between border-t bg-gray-50/60 px-4 py-3"
          >
            <div class="text-xs text-ink-gray-5">
              {{ filteredLogs.length }} / {{ logs.length }} {{ __('calls') }}
            </div>

            <div class="text-xs text-ink-gray-5">
              {{ __('Showing latest 100 records') }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <CallLogDetailModal
      v-model="showCallLogDetailModal"
      v-model:callLog="selectedCallLog"
    />
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CallLogDetailModal from '@/components/Modals/CallLogDetailModal.vue'
import { Button, FeatherIcon, createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

const search = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

const statuses = [
  'Completed',
  'Missed',
  'Canceled',
  'Failed',
  'Busy',
  'No Answer',
]

const callTypes = [
  'Incoming',
  'Outgoing',
  'Incoming Forwarded',
  'Callback',
]

const callLogs = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'DoubleT Call Log',
    fields: [
      'name',
      'agent',
      'line_number',
      'call_type',
      'duration',
      'start_time',
      'end_time',
      'status',
      'from_number',
      'to_number',
      'recording_url',
      'reference_doctype',
      'reference_name',
      'note',
      'external_call_id',
      'creation',
      'modified',
    ],
    order_by: 'start_time desc',
    limit_page_length: 100,
  },
  auto: true,
})

const logs = computed(() =>
  Array.isArray(callLogs.data) ? callLogs.data : [],
)

const filteredLogs = computed(() => {
  const q = search.value.trim().toLowerCase()

  return logs.value.filter((log) => {
    if (statusFilter.value && log.status !== statusFilter.value) {
      return false
    }

    if (typeFilter.value && log.call_type !== typeFilter.value) {
      return false
    }

    if (!q) return true

    return [
      log.from_number,
      log.to_number,
      log.agent,
      log.reference_name,
      log.reference_doctype,
      log.external_call_id,
      log.line_number,
      log.status,
      log.call_type,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(q))
  })
})

const summary = computed(() => {
  const data = logs.value
  const completed = data.filter((d) => d.status === 'Completed').length
  const missed = data.filter((d) =>
    ['Missed', 'No Answer'].includes(d.status),
  ).length

  const durations = data
    .map((d) => Number(d.duration || 0))
    .filter((d) => Number.isFinite(d) && d >= 0)

  const avgDuration = durations.length
    ? Math.round(
        durations.reduce((sum, value) => sum + value, 0) /
          durations.length,
      )
    : 0

  return {
    total: data.length,
    completed,
    missed,
    avgDuration,
  }
})

const showCallLogDetailModal = ref(false)
const selectedCallLog = ref({})

function openDetail(log) {
  selectedCallLog.value = { ...log }
  showCallLogDetailModal.value = true
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
  if (!value) return { date: '—', time: '' }

  const parsed = new Date(String(value).replace(' ', 'T'))

  if (Number.isNaN(parsed.getTime())) {
    return { date: value, time: '' }
  }

  return {
    date: new Intl.DateTimeFormat('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(parsed),
    time: new Intl.DateTimeFormat('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(parsed),
  }
}

function callTypeIcon(type) {
  return ['Incoming', 'Incoming Forwarded'].includes(type)
    ? 'phone-incoming'
    : 'phone-outgoing'
}

function primaryNumber(log) {
  return ['Incoming', 'Incoming Forwarded'].includes(log.call_type)
    ? log.from_number
    : log.to_number
}

function secondaryNumber(log) {
  const value = ['Incoming', 'Incoming Forwarded'].includes(log.call_type)
    ? log.to_number
    : log.from_number

  return value ? `${__('via')} ${value}` : ''
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
</script>
