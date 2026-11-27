<template>
  <div class="flex h-full flex-col overflow-auto bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Dashboard" />
      </template>
      <template #right-header>
        <Button
          :label="__('Refresh')"
          :loading="loading"
          @click="load"
        />
      </template>
    </LayoutHeader>

    <div class="space-y-5 p-4 sm:p-5">
      <div
        v-if="error"
        class="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700"
      >
        {{ error }}
        <Button
          class="ml-2"
          :label="__('Try again')"
          @click="load"
        />
      </div>

      <div
        v-if="loading && !data"
        class="p-10 text-center text-ink-gray-5"
      >
        {{ __('Loading dashboard...') }}
      </div>

      <template v-else-if="data">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <button
            v-for="card in cards"
            :key="card.key"
            class="rounded-lg border p-4 text-left shadow-sm hover:border-outline-gray-4 disabled:cursor-not-allowed"
            :disabled="!canAccess(card)"
            @click="open(card.route, card.query)"
          >
            <div class="text-sm text-ink-gray-5">{{ __(card.label) }}</div>
            <div
              v-if="!canAccess(card)"
              class="mt-2 text-sm text-ink-gray-5"
            >
              {{ __('You do not have access to this data.') }}
            </div>
            <div
              v-else
              class="mt-1 text-2xl font-semibold"
            >
              {{ card.format === 'money' && data.kpis[card.key] != null ? money(data.kpis[card.key]) : (data.kpis[card.key] ?? '—') }}
            </div>
            <div class="mt-1 text-xs text-ink-gray-4">{{ __(card.scope) }}</div>
          </button>
        </div>

        <div class="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <section class="rounded-lg border p-4">
            <h2 class="mb-4 font-semibold">{{ __('Leads by source') }}</h2>
            <Restricted v-if="!data.permissions.leads" />
            <EmptyState
              v-else-if="!data.lead_sources.length"
              :title="__('No leads yet')"
            />
            <Bars
              v-else
              :items="data.lead_sources"
            />
          </section>

          <section class="rounded-lg border p-4">
            <h2 class="mb-4 font-semibold">{{ __('Deals by current stage') }}</h2>
            <Restricted v-if="!data.permissions.deals || !data.permissions.stages" />
            <EmptyState
              v-else-if="!data.deal_stages.length"
              :title="__('No deal stages configured')"
            />
            <Bars
              v-else
              :items="data.deal_stages"
            />
          </section>
        </div>

        <section class="rounded-lg border p-4" aria-labelledby="needs-attention-title">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div><h2 id="needs-attention-title" class="font-semibold">{{ __('Needs Attention') }}</h2><p class="mt-1 text-xs text-ink-gray-5">{{ data.needs_attention?.semantics || __('Current permission-scoped alerts.') }}</p></div>
            <Button :label="__('View All')" @click="router.push({ name: 'SmartInsightsReport' })" />
          </div>
          <p v-if="data.insights_error" class="mt-3 text-sm text-ink-gray-5" role="status">{{ __('Smart Insights is temporarily unavailable. Existing Dashboard metrics are still available.') }}</p>
          <Restricted v-else-if="!data.permissions.insights" />
          <EmptyState v-else-if="!data.needs_attention?.alerts?.length" class="mt-3" :title="__('No current alerts')" />
          <div v-else class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <button v-for="alert in data.needs_attention.alerts" :key="`${alert.type}-${alert.source_id}`" class="rounded-lg border border-outline-gray-2 p-3 text-left hover:bg-surface-gray-1" @click="router.push(alert.route)">
              <div class="flex items-center justify-between gap-2"><span class="truncate font-medium">{{ alert.source_label }}</span><span class="rounded px-2 py-0.5 text-xs font-medium" :class="severityClass(alert.severity)">{{ __(alert.severity) }}</span></div>
              <p class="mt-2 line-clamp-2 text-xs text-ink-gray-6">{{ alert.alert_count > 1 ? __('{0} alert reasons', [alert.alert_count]) : alert.reason }}</p>
            </button>
          </div>
        </section>

        <section class="rounded-lg border p-4">
          <div class="flex items-center justify-between gap-3"><div><h2 class="font-semibold">{{ __('Upcoming Activities') }}</h2><p class="mt-1 text-xs text-ink-gray-5">{{ __('Readable scheduled appointments and unfinished tasks, ordered by due time.') }}</p></div><Button :label="__('Appointments')" @click="open('Appointments', {})" /></div>
          <Restricted v-if="!data.permissions.appointments && !data.permissions.tasks" />
          <EmptyState v-else-if="!data.upcoming_activities.length" class="mt-3" :title="__('No upcoming activities')" />
          <div v-else class="mt-3 divide-y rounded border">
            <button v-for="item in data.upcoming_activities" :key="`${item.type}-${item.name}`" class="flex w-full flex-wrap items-center justify-between gap-3 p-3 text-left hover:bg-surface-gray-1" @click="router.push(item.route)">
              <div class="min-w-0"><div class="flex items-center gap-2"><span class="rounded bg-surface-gray-2 px-2 py-0.5 text-xs">{{ __(item.type) }}</span><span class="truncate font-medium">{{ item.title }}</span></div><div class="mt-1 text-xs text-ink-gray-5">{{ item.related || __('No related record') }} · {{ item.assigned_to || __('Unassigned') }}</div></div>
              <time class="text-sm text-ink-gray-6">{{ displayDateTime(item.due_at) }}</time>
            </button>
          </div>
        </section>

        <section class="rounded-lg border p-4">
          <h2 class="font-semibold">{{ __('Quotations to follow up') }}</h2>
          <p class="mb-3 text-xs text-ink-gray-5">
            {{ __('Sent means manually marked as sent and is included only while valid.') }}
          </p>
          <Restricted v-if="!data.permissions.quotations" />
          <EmptyState
            v-else-if="!data.quotations.length"
            :title="__('No quotations need follow-up')"
          />
          <div
            v-else
            class="overflow-x-auto"
          >
            <table class="w-full min-w-[700px] text-left text-sm">
              <thead>
                <tr>
                  <th class="p-2">{{ __('Quotation') }}</th>
                  <th>{{ __('Customer') }}</th>
                  <th>{{ __('Deal') }}</th>
                  <th>{{ __('Status') }}</th>
                  <th>{{ __('Valid until') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in data.quotations"
                  :key="row.name"
                  class="cursor-pointer border-t hover:bg-surface-gray-1"
                  @click="open('QuotationDetail', { quotationId: row.name })"
                >
                  <td class="p-2">{{ row.name }}</td>
                  <td>{{ linkedLabel(row.customer_label, row.customer_restricted) }}</td>
                  <td>
                    <button
                      v-if="row.deal"
                      class="hover:underline"
                      @click.stop="open('DealDetail', { dealId: row.deal })"
                    >
                      {{ row.deal_label }}
                    </button>
                    <span v-else>{{ linkedLabel(row.deal_label, row.deal_restricted) }}</span>
                  </td>
                  <td><span :class="quotationStatusClass(row.display_status)">{{ __(row.display_status) }}</span></td>
                  <td>{{ row.valid_until || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { h, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, call } from 'frappe-ui'

import EmptyState from '@/components/ListViews/EmptyState.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { money } from '@/utils/quotation'

const router = useRouter()
const data = ref(null)
const loading = ref(false)
const error = ref('')

const cards = [
  { key: 'leads', label: 'Total Leads', scope: 'Current total', permissions: ['leads'], route: 'Leads', query: {} },
  { key: 'open_deals', label: 'Open Deals', scope: 'Current total', permissions: ['deals', 'stages'], route: 'Deals', query: { lifecycle: 'OPEN' } },
  { key: 'won_deals', label: 'Won Deals', scope: 'Current total', permissions: ['deals', 'stages'], route: 'Deals', query: { lifecycle: 'WON' } },
  { key: 'draft_quotations', label: 'Draft Quotations', scope: 'Current total', permissions: ['quotations'], route: 'Quotations', query: { status: 'Draft' } },
  { key: 'booked_sales', label: 'Booked Sales', scope: 'All Confirmed / Completed Orders', format: 'money', permissions: ['orders'], route: 'Orders', query: {} },
  { key: 'booked_orders', label: 'Booked Orders', scope: 'All Confirmed / Completed Orders', permissions: ['orders'], route: 'Orders', query: { booked: '1' } },
  { key: 'critical_alerts', label: 'Critical Alerts', scope: 'Current alerts', permissions: ['insights'], route: 'SmartInsightsReport', query: { severity: 'critical' } },
  { key: 'upcoming_appointments', label: 'Upcoming Appointments', scope: 'Next 7 days', permissions: ['appointments'], route: 'Appointments', query: { time: 'upcoming' } },
]
const severityClass = value => value === 'critical' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
const quotationStatusClass = value => ({ Expired: 'rounded bg-red-100 px-2 py-1 text-xs text-red-700', Sent: 'rounded bg-blue-100 px-2 py-1 text-xs text-blue-700', Draft: 'rounded bg-gray-100 px-2 py-1 text-xs text-gray-700' }[value] || '')
const displayDateTime = value => value ? new Date(String(value).replace(' ', 'T')).toLocaleString() : '—'

const Bars = {
  props: ['items'],
  setup(props) {
    return () => h(
      'div',
      { class: 'space-y-3' },
      props.items.map((item) => h('div', { class: 'space-y-1' }, [
        h('div', { class: 'flex justify-between gap-3 text-sm' }, [
          h('span', { class: 'truncate' }, item.label || item.name),
          h('span', String(item.count)),
        ]),
        h('div', { class: 'h-2 rounded bg-surface-gray-2' }, [
          h('div', {
            class: 'h-2 rounded bg-blue-500',
            style: {
              width: `${Math.max(4, item.count / Math.max(...props.items.map((entry) => entry.count), 1) * 100)}%`,
            },
          }),
        ]),
      ])),
    )
  },
}

const Restricted = {
  setup() {
    return () => h(
      'div',
      { class: 'py-8 text-sm text-ink-gray-5' },
      __('You do not have permission to view this data.'),
    )
  },
}

function canAccess(card) {
  return card.permissions.every((permission) => data.value.permissions[permission])
}

function linkedLabel(label, restricted) {
  if (label) return label
  return restricted ? __('Restricted') : '—'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await call('doublet_crm.dashboard.get_overview')
  } catch (requestError) {
    error.value = requestError?.message || __('Could not load dashboard.')
  } finally {
    loading.value = false
  }
}

function open(name, query) {
  const isDetail = ['DealDetail', 'QuotationDetail'].includes(name)
  router.push({
    name,
    params: isDetail ? query : {},
    query: isDetail ? {} : query,
  })
}

onMounted(load)
</script>
