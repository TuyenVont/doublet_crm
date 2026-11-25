<template>
  <div class="space-y-5">
    <section class="rounded-xl border border-outline-gray-2 bg-surface-white p-4">
      <div class="grid gap-4 sm:grid-cols-3 lg:items-end">
        <label><span class="mb-1.5 block text-sm font-medium">{{ __('As-of Date') }}</span><input v-model="filters.asOfDate" type="date" class="h-9 w-full rounded border border-outline-gray-2 px-3 text-sm" :max="today" /></label>
        <label><span class="mb-1.5 block text-sm font-medium">{{ __('Deal Owner') }}</span><select v-model="filters.salesperson" class="h-9 w-full rounded border border-outline-gray-2 px-3 text-sm"><option value="">{{ __('All owners') }}</option><option v-for="item in salespeople" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
        <label><span class="mb-1.5 block text-sm font-medium">{{ __('Alert Type') }}</span><select v-model="filters.alertType" class="h-9 w-full rounded border border-outline-gray-2 px-3 text-sm"><option value="">{{ __('All alerts') }}</option><option value="stale_deal">{{ __('Stale Deal') }}</option><option value="prolonged_stage">{{ __('Prolonged Stage') }}</option><option value="past_expected_close">{{ __('Past Expected Close') }}</option><option value="quotation_expiry">{{ __('Quotation Expiry') }}</option><option value="overdue_task">{{ __('Overdue Task') }}</option></select></label>
      </div>
      <div class="mt-3 flex gap-2"><Button class="w-24 shrink-0" variant="solid" :label="__('Apply')" :aria-busy="loading" :aria-disabled="loading" @click="load" /><Button class="w-16 shrink-0" :label="__('Reset')" :aria-disabled="loading" @click="reset" /></div>
      <ReportActions class="mt-3" report-key="smart-insights" :filters="appliedFilters || {}" :enabled="Boolean(appliedFilters)" @restore="restoreFilters" />
    </section>

    <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700" role="alert">
      {{ error }} <Button class="ml-2" :label="__('Try again')" @click="load" />
    </div>
    <div v-else-if="loading && !data" class="grid gap-3 sm:grid-cols-4"><div v-for="index in 4" :key="index" class="h-24 animate-pulse rounded-xl bg-surface-gray-2" /></div>

    <template v-else-if="data">
      <p class="rounded-lg bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6">{{ data.semantics }} {{ __('Thresholds: {0} unchanged days; {1} days in current stage; {2} days until quotation expiry.'.replace('{0}', String(data.thresholds.deal_unchanged_days)).replace('{1}', String(data.thresholds.stage_aging_days)).replace('{2}', String(data.thresholds.quotation_expiry_days))) }}</p>
      <div v-if="data.capabilities?.stage_aging?.available === false" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6" role="status">{{ data.capabilities.stage_aging.reason || __('Prolonged-stage alerts are unavailable because readable Version history is unavailable.') }}</div>
      <div v-else-if="data.capabilities?.stage_aging?.unknown_count" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6" role="status">{{ __('Some Deals have incomplete stage history and remain Unknown; they do not generate prolonged-stage alerts.') }}</div>
      <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Alerts" :value="data.summary.total" /><Metric label="Critical" :value="data.summary.critical" /><Metric label="Warnings" :value="data.summary.warning" /><Metric label="Deals needing attention" :value="data.summary.needs_attention" />
      </section>

      <section class="overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white">
        <div class="p-4"><h2 class="font-semibold">{{ __('Current alerts') }}</h2><p class="mt-1 text-sm text-ink-gray-5">{{ __('Only readable source records are included. Reading this report never creates Tasks.') }}</p></div>
        <div v-if="!data.alerts.length" class="border-t p-8 text-center text-sm text-ink-gray-5">{{ __('No current alerts match these filters.') }}</div>
        <div v-else class="overflow-x-auto"><table class="min-w-full text-left text-sm"><thead class="border-y bg-surface-gray-1"><tr><th class="px-4 py-3">{{ __('Severity') }}</th><th>{{ __('Source') }}</th><th>{{ __('Reason') }}</th><th>{{ __('Owner') }}</th><th>{{ __('Action') }}</th></tr></thead><tbody><tr v-for="alert in data.alerts" :key="`${alert.type}-${alert.source_id}`" class="border-t"><td class="px-4 py-3"><span :class="severityClass(alert.severity)">{{ alert.severity }}</span></td><td><RouterLink :to="alert.route" class="font-medium text-[#1D4ED8] hover:underline">{{ alert.source_label }}</RouterLink></td><td class="max-w-md px-3 py-3">{{ alert.reason }}</td><td>{{ alert.owner || __('Unassigned') }}</td><td class="px-3"><Button :label="__('Create follow-up')" :disabled="!alert.follow_up?.available" :title="alert.follow_up?.reason || ''" :loading="creating === alert.source_id" @click="createFollowUp(alert)" /></td></tr></tbody></table></div>
        <p v-if="actionStatus" class="border-t px-4 py-3 text-sm text-ink-gray-6" role="status">{{ actionStatus }}</p>
      </section>

      <section class="overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white">
        <div class="p-4"><h2 class="font-semibold">{{ __('Deal Health Score') }}</h2><p class="mt-1 text-sm text-ink-gray-5">{{ data.health[0]?.definition || __('No readable open Deals.') }}</p></div>
        <div v-if="!data.health.length" class="border-t p-8 text-center text-sm text-ink-gray-5">{{ __('No readable open Deals.') }}</div>
        <div v-else class="overflow-x-auto"><table class="min-w-full text-left text-sm"><thead class="border-y bg-surface-gray-1"><tr><th class="px-4 py-3">{{ __('Deal') }}</th><th>{{ __('Score') }}</th><th>{{ __('Category') }}</th><th>{{ __('Coverage') }}</th><th>{{ __('Factors') }}</th></tr></thead><tbody><tr v-for="row in data.health" :key="row.deal" class="border-t align-top"><td class="px-4 py-3"><RouterLink :to="row.route" class="font-medium text-[#1D4ED8] hover:underline">{{ row.deal_title }}</RouterLink></td><td>{{ row.score ?? __('Unknown') }}</td><td>{{ row.category }}</td><td>{{ row.coverage.known_factors }}/{{ row.coverage.total_factors }}</td><td class="min-w-80 px-3 py-3"><details><summary class="cursor-pointer">{{ __('View explanation') }}</summary><ul class="mt-2 space-y-1 text-xs text-ink-gray-6"><li v-for="factor in row.factors" :key="factor.key"><strong>{{ factor.label }}:</strong> {{ factor.points == null ? __('Unknown') : `${factor.points}/${factor.weight}` }} — {{ factor.reason }}</li></ul></details></td></tr></tbody></table></div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { call } from 'frappe-ui'

import ReportActions from '@/components/Reports/ReportActions.vue'
import { message } from '@/utils/quotation'

const today = new Date().toISOString().slice(0, 10)
const filters = reactive({ asOfDate: today, salesperson: '', alertType: '' })
const data = ref(null), loading = ref(false), error = ref(''), creating = ref(''), actionStatus = ref('')
const appliedFilters = ref(null)
const salespeople = computed(() => data.value?.salespeople || [])
const actionFilters = computed(() => ({ as_of_date: filters.asOfDate, salesperson: filters.salesperson || null, alert_type: filters.alertType || null }))
const Metric = defineComponent({ props: { label: String, value: Number }, setup: props => () => h('article', { class: 'rounded-xl border border-outline-gray-2 p-4' }, [h('p', { class: 'text-sm text-ink-gray-5' }, props.label), h('p', { class: 'mt-1 text-2xl font-semibold' }, String(props.value ?? 0))]) })
const severityClass = value => ({ critical: 'rounded bg-red-100 px-2 py-1 text-xs text-red-700', warning: 'rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-700' }[value] || 'rounded bg-gray-100 px-2 py-1 text-xs')

async function load() {
  if (loading.value) return
  loading.value = true; error.value = ''
  try { const request = { ...actionFilters.value }; data.value = await call('doublet_crm.smart_insights.get_smart_insights', request); appliedFilters.value = request }
  catch (requestError) { data.value = null; error.value = message(requestError) }
  finally { loading.value = false }
}
function reset() { if (loading.value) return; Object.assign(filters, { asOfDate: today, salesperson: '', alertType: '' }); load() }
function restoreFilters(saved) { Object.assign(filters, { asOfDate: saved.as_of_date || today, salesperson: saved.salesperson || '', alertType: saved.alert_type || '' }); load() }
async function createFollowUp(alert) {
  if (!alert.follow_up?.available) return
  creating.value = alert.source_id; actionStatus.value = ''; error.value = ''
  try {
    const result = await call('doublet_crm.smart_insights.create_follow_up_task', { alert_type: alert.type, source_id: alert.source_id })
    actionStatus.value = result.duplicate ? __('An active follow-up Task already exists.') : __('Follow-up Task created.')
  } catch (requestError) { error.value = message(requestError) }
  finally { creating.value = '' }
}
onMounted(load)
</script>
