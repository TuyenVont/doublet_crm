<template>
  <div class="space-y-5">
    <ReportsFilters
      v-model:start-date="filters.startDate"
      v-model:end-date="filters.endDate"
      v-model:salesperson="filters.employee"
      :salesperson-options="employees"
      :salesperson-supported="employeeFilterSupported"
      person-label="Employee (Call Agent / Task Assignee)"
      all-people-label="All employees"
      person-unsupported-text="Employee filtering is unavailable because neither Calls nor Tasks is readable."
      :show-compare="false"
      :loading="loading"
      @apply="loadReport"
      @reset="resetFilters"
    />

    <div v-if="errorMessage" class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center" role="alert">
      <h2 class="font-semibold text-ink-gray-9">{{ __('Unable to load activity analytics') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ errorMessage }}</p>
      <Button class="mt-4" :label="__('Try again')" :loading="loading" @click="loadReport" />
    </div>

    <template v-else-if="data">
      <p class="rounded-lg bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6">{{ data.source_definitions }}</p>

      <section class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5" aria-labelledby="activity-trend-title">
        <h2 id="activity-trend-title" class="font-semibold text-ink-gray-9">{{ __('Daily activity') }}</h2>
        <p class="mt-1 text-sm text-ink-gray-5">{{ __('Each bar uses only readable records matching the applied source date and employee rules.') }}</p>
        <div class="mt-3 flex flex-wrap gap-3 text-xs text-ink-gray-6">
          <span v-for="item in legend" :key="item.key" class="inline-flex items-center gap-1"><span class="size-2.5 rounded-sm" :class="item.color" />{{ __(item.label) }}</span>
        </div>
        <div class="mt-4 overflow-x-auto pb-2">
          <div class="flex h-40 min-w-max items-end gap-2 border-b border-outline-gray-2 px-1">
            <div v-for="point in data.trend" :key="point.date" class="flex w-7 shrink-0 flex-col items-center justify-end gap-1" :title="trendTitle(point)">
              <div class="flex w-5 flex-col-reverse overflow-hidden rounded-t" :style="{ height: barHeight(point) }">
                <div v-for="item in legend" :key="item.key" v-show="point[item.key]" :class="item.color" :style="{ flex: point[item.key] }" />
              </div>
              <span class="text-[10px] text-ink-gray-4">{{ shortDate(point.date) }}</span>
            </div>
          </div>
        </div>
      </section>

      <SourceSection title="Call Logs" :available="sources.calls.available" date-note="Filtered by Start Time; employee means Call Agent.">
        <div class="grid gap-3 sm:grid-cols-3">
          <MetricCard label="Total calls" :value="metric(sources.calls.total)" />
          <MetricCard label="Missed calls" :value="metric(sources.calls.missed)" />
          <MetricCard label="Total duration" :value="duration(sources.calls.duration_seconds)" />
        </div>
        <ReportTable v-if="sources.calls.rows.length" :headers="['Call', 'Agent', 'Type', 'Status', 'Start Time', 'Duration']">
          <tr v-for="item in sources.calls.rows" :key="item.name" class="border-t border-outline-gray-1">
            <td class="px-4 py-3"><RouterLink class="font-medium text-ink-blue-3 hover:underline" :to="{ name: 'CallHistoryDetail', params: { callId: item.name } }">{{ item.name }}</RouterLink></td>
            <td class="px-4 py-3">{{ item.agent }}</td><td class="px-4 py-3">{{ item.call_type }}</td><td class="px-4 py-3">{{ item.status }}</td>
            <td class="px-4 py-3">{{ displayDateTime(item.start_time) }}</td><td class="px-4 py-3 text-right">{{ duration(item.duration) }}</td>
          </tr>
        </ReportTable>
      </SourceSection>

      <SourceSection title="Tasks" :available="sources.tasks.available" date-note="Filtered by Creation; employee means Task Assignee.">
        <p class="mb-3 text-xs text-ink-gray-5">{{ sources.tasks.overdue_definition }}</p>
        <div class="grid gap-3 sm:grid-cols-4">
          <MetricCard label="Total tasks" :value="metric(sources.tasks.total)" />
          <MetricCard label="Completed" :value="metric(sources.tasks.completed)" />
          <MetricCard label="Pending" :value="metric(sources.tasks.pending)" />
          <MetricCard label="Overdue" :value="metric(sources.tasks.overdue)" />
        </div>
        <ReportTable v-if="sources.tasks.rows.length" :headers="['Task', 'Assignee', 'Status', 'Created', 'Due Date']">
          <tr v-for="item in sources.tasks.rows" :key="item.name" class="border-t border-outline-gray-1">
            <td class="px-4 py-3"><RouterLink class="font-medium text-ink-blue-3 hover:underline" :to="{ name: 'Tasks', query: { task: item.name } }">{{ item.title || item.name }}</RouterLink></td>
            <td class="px-4 py-3">{{ item.assigned_to || __('Unassigned') }}</td><td class="px-4 py-3">{{ item.status }}</td>
            <td class="px-4 py-3">{{ displayDateTime(item.creation) }}</td><td class="px-4 py-3">{{ displayDateTime(item.due_date) || '—' }}</td>
          </tr>
        </ReportTable>
      </SourceSection>

      <SourceSection title="Email" :available="sources.email.available" date-note="Filtered by Communication Creation.">
        <UnsupportedEmployee v-if="filters.employee" :text="sources.email.unsupported_filter_reason" />
        <div class="grid gap-3 sm:grid-cols-2">
          <MetricCard label="Incoming" :value="metric(sources.email.incoming)" />
          <MetricCard label="Outgoing" :value="metric(sources.email.outgoing)" />
        </div>
        <ReportTable v-if="sources.email.rows.length" :headers="['Subject', 'Direction', 'Sender', 'Recipients', 'Created']">
          <tr v-for="item in sources.email.rows" :key="item.name" class="border-t border-outline-gray-1">
            <td class="px-4 py-3 font-medium">{{ item.subject || item.name }}</td><td class="px-4 py-3">{{ item.sent_or_received }}</td>
            <td class="px-4 py-3">{{ item.sender }}</td><td class="max-w-xs truncate px-4 py-3">{{ item.recipients }}</td><td class="px-4 py-3">{{ displayDateTime(item.creation) }}</td>
          </tr>
        </ReportTable>
      </SourceSection>

      <SourceSection title="Zalo OA" :available="sources.zalo.available" date-note="Conversations use Creation; messages use Sent At.">
        <UnsupportedEmployee v-if="filters.employee" :text="sources.zalo.unsupported_filter_reason" />
        <div class="grid gap-3 sm:grid-cols-4">
          <MetricCard label="Conversations" :value="metric(sources.zalo.conversation_count)" />
          <MetricCard label="Messages" :value="metric(sources.zalo.message_count)" />
          <MetricCard label="Real messages" :value="metric(sources.zalo.real_message_count)" />
          <MetricCard label="Mock / simulated" :value="metric(sources.zalo.simulated_message_count)" />
        </div>
        <p v-if="!sources.zalo.conversations_available || !sources.zalo.messages_available" class="mt-3 text-sm text-ink-gray-5">
          {{ __('Conversation and message permissions are checked independently; unavailable metrics are not shown as zero.') }}
        </p>
        <ReportTable v-if="sources.zalo.messages.length" :headers="['Message', 'Direction', 'Type', 'Sent At']">
          <tr v-for="item in sources.zalo.messages" :key="item.name" class="border-t border-outline-gray-1">
            <td class="max-w-md truncate px-4 py-3">
              <RouterLink v-if="item.conversation" class="font-medium text-ink-blue-3 hover:underline" :to="{ name: 'Inbox', query: { conversation: item.conversation } }">{{ item.content }}</RouterLink>
              <span v-else>{{ item.content }}</span>
            </td><td class="px-4 py-3">{{ item.direction }}</td>
            <td class="px-4 py-3"><span class="rounded bg-surface-gray-2 px-2 py-1 text-xs text-ink-gray-7">{{ item.is_simulated ? __('Mock / simulated') : __('Real') }}</span></td>
            <td class="px-4 py-3">{{ displayDateTime(item.sent_at) }}</td>
          </tr>
        </ReportTable>
      </SourceSection>
    </template>

    <div v-else class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-live="polite"><div v-for="index in 4" :key="index" class="h-28 animate-pulse rounded-xl bg-surface-gray-2" /></div>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { call } from 'frappe-ui'

import ReportsFilters from '@/components/Reports/ReportsFilters.vue'
import { reportDatePreset } from '@/utils/reportFilters'
import { message } from '@/utils/quotation'

const MetricCard = defineComponent({ props: { label: String, value: String }, setup: props => () => h('article', { class: 'rounded-lg bg-surface-gray-1 p-4' }, [h('p', { class: 'text-sm text-ink-gray-5' }, props.label), h('p', { class: 'mt-1 text-2xl font-semibold text-ink-gray-9' }, props.value)]) })
const SourceSection = defineComponent({ props: { title: String, available: Boolean, dateNote: String }, setup: (props, { slots }) => () => h('section', { class: 'space-y-4 rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5' }, [h('div', [h('h2', { class: 'font-semibold text-ink-gray-9' }, props.title), h('p', { class: 'mt-1 text-sm text-ink-gray-5' }, props.dateNote)]), props.available ? slots.default?.() : h('p', { class: 'rounded-lg bg-surface-gray-1 px-4 py-6 text-center text-sm text-ink-gray-5' }, 'Unavailable — you do not have read permission for this source.')]) })
const ReportTable = defineComponent({ props: { headers: Array }, setup: (props, { slots }) => () => h('div', { class: 'overflow-x-auto rounded-lg border border-outline-gray-2' }, [h('table', { class: 'min-w-full text-left text-sm text-ink-gray-7' }, [h('thead', { class: 'bg-surface-gray-1 text-ink-gray-5' }, h('tr', props.headers.map((label, index) => h('th', { class: ['whitespace-nowrap px-4 py-3', index === props.headers.length - 1 ? 'text-right' : ''] }, label)))), h('tbody', slots.default?.())])]) })
const UnsupportedEmployee = defineComponent({ props: { text: String }, setup: props => () => h('p', { class: 'rounded-md bg-surface-gray-1 px-3 py-2 text-xs text-ink-gray-7', role: 'status' }, props.text) })

const initialRange = reportDatePreset('30-days')
const filters = reactive({ ...initialRange, employee: '' })
const data = ref(null), loading = ref(false), errorMessage = ref('')
const sources = computed(() => data.value.sources)
const employees = computed(() => data.value?.employees || [])
const employeeFilterSupported = computed(() => Boolean(data.value?.permissions?.calls || data.value?.permissions?.tasks))
const legend = [
  { key: 'calls', label: 'Calls', color: 'bg-blue-500' }, { key: 'tasks', label: 'Tasks', color: 'bg-green-500' },
  { key: 'emails', label: 'Email', color: 'bg-violet-500' }, { key: 'zalo_messages', label: 'Zalo messages', color: 'bg-orange-500' },
]
const maxDaily = computed(() => Math.max(...(data.value?.trend || []).map(point => legend.reduce((sum, item) => sum + (Number(point[item.key]) || 0), 0)), 1))
const metric = value => value == null ? __('Unavailable') : new Intl.NumberFormat('en-US').format(value)
const duration = seconds => seconds == null ? __('Unavailable') : `${Math.floor(Number(seconds) / 60)}m ${Number(seconds) % 60}s`
const displayDateTime = value => value ? new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(String(value).replace(' ', 'T') + 'Z')) : ''
const shortDate = value => value.slice(5).replace('-', '/')
const pointTotal = point => legend.reduce((sum, item) => sum + (Number(point[item.key]) || 0), 0)
const barHeight = point => `${Math.max(pointTotal(point) / maxDaily.value * 112, pointTotal(point) ? 4 : 0)}px`
const trendTitle = point => `${point.date}: ${legend.map(item => `${item.label} ${point[item.key] == null ? __('Unavailable') : point[item.key]}`).join(', ')}`

async function loadReport() {
  loading.value = true; errorMessage.value = ''
  try { data.value = await call('doublet_crm.reports.get_activity_contact_center', { start_date: filters.startDate, end_date: filters.endDate, employee: filters.employee || null }) }
  catch (error) { data.value = null; errorMessage.value = message(error) }
  finally { loading.value = false }
}
function resetFilters() { Object.assign(filters, reportDatePreset('30-days'), { employee: '' }); loadReport() }
onMounted(loadReport)
</script>
