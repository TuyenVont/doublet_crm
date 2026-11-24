<template>
  <div class="flex h-full min-w-0 flex-col bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <div class="flex min-w-0 items-center gap-2">
          <RouterLink
            :to="REPORTS_HOME_ROUTE"
            class="shrink-0 text-lg-medium text-ink-gray-5 hover:text-ink-gray-7"
          >
            {{ __('Reports') }}
          </RouterLink>
          <template v-if="report">
            <span class="text-ink-gray-4" aria-hidden="true">/</span>
            <span class="truncate text-lg-medium text-ink-gray-9">
              {{ __(report.title) }}
            </span>
          </template>
        </div>
      </template>
    </LayoutHeader>

    <main class="min-h-0 flex-1 overflow-auto">
      <div class="mx-auto w-full max-w-6xl space-y-5 p-4 sm:p-6">
        <header class="space-y-1">
          <h1 class="text-2xl font-semibold text-ink-gray-9">
            {{ report ? __(report.title) : __('Reports') }}
          </h1>
          <p class="max-w-2xl text-sm text-ink-gray-5">
            {{ report ? __(report.description) : __('Choose an analytical section to continue.') }}
          </p>
        </header>

        <nav
          v-if="report"
          class="-mx-1 flex gap-1 overflow-x-auto px-1 pb-1"
          :aria-label="__('Report sections')"
        >
          <RouterLink
            v-for="section in REPORT_SECTIONS"
            :key="section.key"
            :to="{ name: section.name }"
            class="shrink-0 rounded-md px-3 py-2 text-sm font-medium transition-colors"
            :class="section.key === report.key
              ? 'bg-surface-gray-3 text-ink-gray-9'
              : 'text-ink-gray-6 hover:bg-surface-gray-1 hover:text-ink-gray-9'"
            :aria-current="section.key === report.key ? 'page' : undefined"
          >
            {{ __(section.title) }}
          </RouterLink>
        </nav>

        <SalesPerformanceReport v-if="report?.key === 'sales-performance'" />

        <PipelineAnalyticsReport v-else-if="report?.key === 'pipeline-analytics'" />

        <CustomerJourneyReport v-else-if="report?.key === 'customer-journey'" />

        <QuotationOrderReport v-else-if="report?.key === 'quotation-order'" />

        <ActivityContactCenterReport v-else-if="report?.key === 'activity-contact-center'" />

        <section
          v-else-if="report"
          class="flex min-h-72 flex-col items-center justify-center rounded-xl border border-dashed border-outline-gray-3 bg-surface-gray-1 px-5 py-12 text-center"
          aria-labelledby="report-placeholder-title"
        >
          <div class="mb-4 flex size-12 items-center justify-center rounded-full bg-surface-gray-3 text-ink-gray-7">
            <Icon :icon="report.icon" class="size-5" />
          </div>
          <h2 id="report-placeholder-title" class="text-lg font-semibold text-ink-gray-9">
            {{ __('Analytics not yet implemented') }}
          </h2>
          <p class="mt-2 max-w-lg text-sm text-ink-gray-5">
            {{ __('This section is ready for future analytics. No report data or metrics are available in REP-04.') }}
          </p>
        </section>

        <section v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-label="Report sections">
          <RouterLink
            v-for="section in REPORT_SECTIONS"
            :key="section.key"
            :to="{ name: section.name }"
            class="group flex min-h-44 flex-col rounded-xl border border-outline-gray-2 bg-surface-white p-5 transition hover:border-outline-gray-4 hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
          >
            <div class="flex size-10 items-center justify-center rounded-lg bg-surface-gray-2 text-ink-gray-7">
              <Icon :icon="section.icon" class="size-5" />
            </div>
            <h2 class="mt-4 font-semibold text-ink-gray-9 group-hover:text-ink-gray-8">
              {{ __(section.title) }}
            </h2>
            <p class="mt-1 flex-1 text-sm text-ink-gray-5">
              {{ __(section.description) }}
            </p>
            <p class="mt-4 text-xs font-medium text-ink-gray-5">
              {{ isLiveReport(section.key) ? __('Live analytics') : __('Analytics not yet implemented') }}
            </p>
          </RouterLink>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PipelineAnalyticsReport from '@/components/Reports/PipelineAnalyticsReport.vue'
import SalesPerformanceReport from '@/components/Reports/SalesPerformanceReport.vue'
import CustomerJourneyReport from '@/components/Reports/CustomerJourneyReport.vue'
import QuotationOrderReport from '@/components/Reports/QuotationOrderReport.vue'
import ActivityContactCenterReport from '@/components/Reports/ActivityContactCenterReport.vue'
import { getReportSection, REPORT_SECTIONS, REPORTS_HOME_ROUTE } from '@/utils/reports'

const props = defineProps({
  reportKey: { type: String, default: '' },
})

const report = computed(() => getReportSection(props.reportKey))
const liveReportKeys = new Set(['sales-performance', 'pipeline-analytics', 'customer-journey', 'quotation-order', 'activity-contact-center'])

function isLiveReport(key) {
  return liveReportKeys.has(key)
}
</script>
