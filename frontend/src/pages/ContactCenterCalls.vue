<template>
  <div class="flex h-full min-h-0 min-w-0 flex-col bg-surface-gray-1">
    <LayoutHeader>
      <template #left-header>
        <span class="hidden text-sm text-ink-gray-5 sm:inline">{{ __('Contact Center') }}</span>
        <FeatherIcon name="chevron-right" class="hidden size-4 text-ink-gray-4 sm:inline" />
        <h1 class="text-lg-medium text-ink-gray-9">{{ __('Calls') }}</h1>
      </template>
      <template #right-header>
        <Button icon="refresh-cw" :label="__('Refresh calls')" :loading="loading" @click="load()" />
      </template>
    </LayoutHeader>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto max-w-[1460px] space-y-4 px-3 py-4 sm:px-5 sm:py-5 lg:px-7">
        <div class="grid grid-cols-3 gap-2 sm:gap-3" role="group" :aria-label="__('Queue status totals')">
          <button
            v-for="metric in metrics"
            :key="metric.status"
            type="button"
            class="min-w-0 rounded-xl border bg-white px-2.5 py-3 text-left sm:px-4"
            :class="handlingStatus === metric.status
              ? 'border-outline-gray-4 ring-1 ring-outline-gray-4'
              : 'border-outline-gray-2 hover:border-outline-gray-4'"
            :aria-pressed="handlingStatus === metric.status"
            :disabled="!counts"
            @click="toggleStatus(metric.status)"
          >
            <span class="flex items-center gap-1.5 text-xs leading-4 text-ink-gray-6 sm:text-sm">
              <span class="size-1.5 shrink-0 rounded-full" :class="metric.dot" aria-hidden="true" />
              {{ __(metric.status) }}
            </span>
            <span class="mt-1.5 block text-xl font-semibold tabular-nums leading-none text-ink-gray-9 sm:text-2xl">
              {{ counts ? (counts[metric.status] || 0) : '—' }}
            </span>
          </button>
        </div>

        <section class="min-w-0 rounded-xl border border-outline-gray-2 bg-white" aria-labelledby="calls-queue-title">
          <div class="border-b border-outline-gray-2 px-3 py-3 sm:px-4 sm:py-4">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-1">
                <h2 id="calls-queue-title" class="text-base font-semibold text-ink-gray-9">{{ __('Call queue') }}</h2>
                <span v-if="rows.length" class="text-xs tabular-nums text-ink-gray-5">
                  {{ __('{0} loaded', [rows.length]) }}
                </span>
              </div>
              <RouterLink
                :to="{ name: 'Call Logs' }"
                class="inline-flex shrink-0 items-center gap-1 text-sm text-ink-gray-6 hover:text-ink-gray-9 hover:underline"
              >
                {{ __('Call logs') }}
                <FeatherIcon name="arrow-up-right" class="size-3.5" aria-hidden="true" />
              </RouterLink>
            </div>

            <div class="mt-3 flex flex-wrap items-center gap-2">
              <FormControl
                v-model="search"
                type="search"
                :aria-label="__('Search calls')"
                :placeholder="__('Search by customer, number or call ID')"
                maxlength="100"
                class="w-full sm:w-64"
              />
              <FormControl
                v-if="canManage"
                v-model="scope"
                type="select"
                :aria-label="__('Assignment scope')"
                :options="scopeOptions"
                class="!w-auto max-w-full"
              />
              <span v-else-if="canManage === false" class="text-sm font-medium text-ink-gray-7">{{ __('Assigned to Me') }}</span>
              <FormControl
                v-model="handlingStatus"
                type="select"
                :aria-label="__('Handling status')"
                :options="handlingOptions"
                class="!w-auto max-w-full"
              />
              <FormControl
                v-model="callType"
                type="select"
                :aria-label="__('Call type')"
                :options="typeOptions"
                class="!w-auto max-w-full"
              />
              <Button v-if="filtered" variant="ghost" :label="__('Clear filters')" @click="clearFilters" />
            </div>
          </div>

          <div :aria-busy="loading">
            <div v-if="error" class="m-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 sm:m-4" role="alert">
              <span>{{ error }}</span>
              <Button variant="subtle" :label="__('Retry')" @click="load(Boolean(rows.length && nextStart !== null))" />
            </div>

            <div v-if="loading && !rows.length" class="space-y-2 px-3 py-4 sm:px-4" role="status">
              <span class="sr-only">{{ __('Loading calls…') }}</span>
              <div v-for="line in 3" :key="line" class="h-9 animate-pulse rounded-md bg-surface-gray-2 motion-reduce:animate-none" />
            </div>

            <div v-else-if="!rows.length && !error" class="flex flex-col items-center gap-2 px-4 py-10 text-center" role="status">
              <div class="rounded-lg bg-surface-gray-2 p-2.5 text-ink-gray-5">
                <FeatherIcon name="phone" class="size-5" aria-hidden="true" />
              </div>
              <p class="text-sm font-semibold text-ink-gray-9">
                {{ __(nextStart !== null ? 'No matches in this batch' : 'No calls match these filters.') }}
              </p>
              <p v-if="nextStart !== null" class="max-w-xs text-sm text-ink-gray-6">
                {{ __('Continue to search older calls in this view.') }}
              </p>
            </div>

            <div v-if="rows.length" role="table" :aria-label="__('Call queue')" class="min-w-0">
              <div role="row" class="queue-layout sr-only items-center gap-3 border-b border-outline-gray-2 bg-surface-gray-1 text-xs font-medium text-ink-gray-6 lg:not-sr-only lg:grid lg:px-4 lg:py-2.5">
                <span v-for="heading in headings" :key="heading" role="columnheader">{{ __(heading) }}</span>
              </div>
              <div role="rowgroup" class="grid gap-2.5 p-2.5 sm:grid-cols-2 sm:p-3 lg:block lg:divide-y lg:divide-outline-gray-1 lg:p-0">
                <div
                  v-for="row in rows"
                  :key="row.name"
                  role="row"
                  class="queue-layout grid min-w-0 grid-cols-2 items-start gap-x-2 gap-y-2.5 rounded-lg border border-outline-gray-2 px-3 py-3 text-sm hover:bg-surface-gray-1 lg:items-center lg:gap-3 lg:rounded-none lg:border-0 lg:px-4"
                >
                  <div role="cell" class="col-span-2 flex min-w-0 items-center gap-2.5 lg:col-auto">
                    <span class="flex size-8 shrink-0 items-center justify-center rounded-lg bg-surface-gray-2 text-ink-gray-6" aria-hidden="true">
                      <FeatherIcon :name="row.call_type?.startsWith('Incoming') ? 'phone-incoming' : 'phone-outgoing'" class="size-4" />
                    </span>
                    <div class="min-w-0 flex-1">
                      <RouterLink
                        :to="{ name: 'CallDetail', params: { callId: row.name } }"
                        class="block break-words font-semibold text-ink-gray-9 hover:underline lg:truncate"
                      >
                        {{ row.customer?.label || row.customer_number || row.name }}
                      </RouterLink>
                      <span v-if="row.customer && row.customer_number" class="block break-all text-xs tabular-nums text-ink-gray-5">{{ row.customer_number }}</span>
                    </div>
                  </div>
                  <div role="cell" class="min-w-0 text-xs leading-4 text-ink-gray-7 lg:text-sm">
                    <span class="block text-ink-gray-5 lg:hidden">{{ __('Call type') }}</span>
                    {{ __(row.call_type) }}
                  </div>
                  <div role="cell" class="min-w-0 space-y-0.5">
                    <span class="block text-xs text-ink-gray-5 lg:hidden">{{ __('Call outcome') }}</span>
                    <Badge :label="__(row.status)" :theme="callOutcomeTheme(row.status)" />
                  </div>
                  <div role="cell" class="min-w-0 space-y-0.5">
                    <span class="block text-xs text-ink-gray-5 lg:hidden">{{ __('Handling status') }}</span>
                    <Badge :label="__(row.handling_status)" :theme="caseStatusTheme[row.handling_status]" />
                  </div>
                  <div role="cell" class="min-w-0 text-xs leading-4 text-ink-gray-7 lg:text-sm">
                    <span class="block text-ink-gray-5 lg:hidden">{{ __('Assignee') }}</span>
                    <span class="block break-words lg:truncate">{{ row.assignee_label || __('Unassigned') }}</span>
                  </div>
                  <div role="cell" class="col-span-2 text-xs tabular-nums text-ink-gray-5 lg:col-auto lg:text-sm">
                    {{ formatCallTime(row.start_time) }}
                  </div>
                </div>
              </div>
            </div>

            <div v-if="nextStart !== null && !error" class="flex justify-center border-t border-outline-gray-2 p-3">
              <Button :loading="loading" :label="__(rows.length ? 'Load more' : 'Continue search')" @click="load(true)" />
            </div>
          </div>
        </section>
      </div>
    </div>
    <RouterView @changed="refreshQueue" />
  </div>
</template>

<script setup>
import { Badge, Button, FeatherIcon, FormControl, call } from 'frappe-ui'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { globalStore } from '@/stores/global'
import { caseStatusTheme, callOutcomeTheme, formatCallTime } from '@/utils/contactCenterCalls'

const { $socket } = globalStore()
const search = ref('')
const scope = ref('')
const handlingStatus = ref('')
const callType = ref('')
const rows = ref([])
const counts = ref(null)
const canManage = ref(null)
const nextStart = ref(null)
const loading = ref(true)
const error = ref('')
const filtered = computed(() => Boolean(search.value || scope.value || handlingStatus.value || callType.value))
const headings = ['Customer', 'Call type', 'Call outcome', 'Handling status', 'Assignee', 'Started']
const metrics = [
  { status: 'Waiting', dot: 'bg-amber-500' },
  { status: 'In Progress', dot: 'bg-blue-500' },
  { status: 'Resolved', dot: 'bg-green-500' },
]
const scopeOptions = [
  { value: '', label: __('All cases') },
  { value: 'mine', label: __('Assigned to Me') },
  { value: 'unassigned', label: __('Unassigned') },
]
const handlingOptions = [
  { value: '', label: __('Open cases') },
  ...metrics.map(({ status }) => ({ value: status, label: __(status) })),
]
const typeOptions = [
  { value: '', label: __('All call types') },
  ...['Incoming', 'Outgoing', 'Incoming Forwarded', 'Callback'].map((value) => ({ value, label: __(value) })),
]
let requestId = 0

async function load(append = false) {
  if (append && (loading.value || nextStart.value === null)) return
  const id = ++requestId
  loading.value = true
  error.value = ''
  try {
    const result = await call('doublet_crm.contact_center_calls.get_calls', {
      scope: scope.value,
      handling_status: handlingStatus.value,
      call_type: callType.value,
      search: search.value,
      start: append ? nextStart.value : 0,
    })
    if (id !== requestId) return
    if (append) {
      const current = new Map(rows.value.map((row) => [row.name, row]))
      for (const row of result.rows) current.set(row.name, row)
      rows.value = [...current.values()]
    } else {
      rows.value = result.rows
      counts.value = result.counts
    }
    canManage.value = result.can_manage
    nextStart.value = result.next_start
  } catch (e) {
    if (id === requestId) error.value = e.messages?.[0] || __('Unable to load the call queue.')
  } finally {
    if (id === requestId) loading.value = false
  }
}

function toggleStatus(status) {
  handlingStatus.value = handlingStatus.value === status ? '' : status
}

function clearFilters() {
  search.value = ''
  scope.value = ''
  handlingStatus.value = ''
  callType.value = ''
}

const fetchSearch = useDebounceFn((id) => {
  if (id === requestId) load()
}, 260)
const refreshQueue = useDebounceFn(() => load(), 80)

watch([search, scope, handlingStatus, callType], ([term, ...filters], [oldTerm, ...oldFilters]) => {
  const id = ++requestId
  rows.value = []
  nextStart.value = null
  error.value = ''
  loading.value = true
  if (term && term !== oldTerm && filters.every((value, index) => value === oldFilters[index])) fetchSearch(id)
  else load()
})
onMounted(() => {
  load()
  $socket?.on('doublet_calls_changed', refreshQueue)
})
onUnmounted(() => {
  $socket?.off('doublet_calls_changed', refreshQueue)
  requestId++
})
</script>

<style scoped>
@media (min-width: 1024px) {
  .queue-layout {
    grid-template-columns: minmax(8rem, 1.65fr) minmax(5rem, 0.85fr) minmax(5rem, 0.8fr)
      minmax(6rem, 0.95fr) minmax(5rem, 1fr) minmax(7rem, 1fr);
  }
}
</style>
