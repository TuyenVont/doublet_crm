export const REPORTS_HOME_ROUTE = Object.freeze({ name: 'Reports' })

export const REPORT_SECTIONS = Object.freeze([
  {
    key: 'sales-performance',
    name: 'SalesPerformanceReport',
    title: 'Sales Performance',
    description: 'Review sales outcomes and team performance over time.',
    icon: 'trending-up',
  },
  {
    key: 'pipeline-analytics',
    name: 'PipelineAnalyticsReport',
    title: 'Pipeline Analytics',
    description: 'Understand deal movement, stages, and pipeline health.',
    icon: 'filter',
  },
  {
    key: 'quotation-order',
    name: 'QuotationOrderReport',
    title: 'Quotation & Order',
    description: 'Analyze the flow from quotations to confirmed orders.',
    icon: 'file-text',
  },
  {
    key: 'customer-journey',
    name: 'CustomerJourneyReport',
    title: 'Customer Journey',
    description: 'Explore customer progression across the CRM lifecycle.',
    icon: 'map',
  },
  {
    key: 'activity-contact-center',
    name: 'ActivityContactCenterReport',
    title: 'Activity & Contact Center',
    description: 'Review CRM activity and contact center engagement.',
    icon: 'phone-call',
  },
  {
    key: 'smart-insights',
    name: 'SmartInsightsReport',
    title: 'Smart Insights',
    description: 'Act on current alerts and transparent Deal health factors.',
    icon: 'alert-triangle',
  },
])

export function getReportSection(key) {
  return REPORT_SECTIONS.find((section) => section.key === key)
}
