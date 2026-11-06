<template>
  <div class="flex flex-col overflow-y-auto">
    <details open class="border-b">
      <summary class="cursor-pointer px-5 py-4 text-sm font-semibold text-ink-gray-9">
        {{ __('Details') }}
      </summary>

      <div class="space-y-4 px-5 pb-5">
        <InfoRow :label="__('Email')" :value="contact.email" />
        <InfoRow :label="__('Phone')" :value="contact.phone" />
        <InfoRow :label="__('Birthday')" :value="contact.birthday" />
        <InfoRow :label="__('Job Title')" :value="contact.job_title" />
        <InfoRow :label="__('Source')" :value="contact.source" />
        <InfoRow :label="__('Primary Owner')" :value="labels.owner || contact.contact_owner" />
      </div>
    </details>

    <details open class="border-b">
      <summary class="cursor-pointer px-5 py-4 text-sm font-semibold text-ink-gray-9">
        {{ __('Organization') }}
      </summary>

      <div class="space-y-4 px-5 pb-5">
        <LinkedRow
          :label="__('Company')"
          :value="contact.company"
          :display-value="labels.company"
          @open="openCompany"
        />
        <InfoRow :label="__('Address')" :value="contact.address" />
      </div>
    </details>

    <details open class="border-b">
      <summary class="cursor-pointer px-5 py-4 text-sm font-semibold text-ink-gray-9">
        {{ __('Related') }}
      </summary>

      <div class="space-y-5 px-5 pb-5">
        <div>
          <div class="mb-2 text-xs text-ink-gray-5">{{ __('Source Lead') }}</div>
          <button
            v-if="sourceLead"
            type="button"
            class="text-left text-sm font-medium text-blue-600 hover:underline"
            @click="openLead(sourceLead.name)"
          >
            {{ sourceLead.label }}
          </button>
          <div v-else class="text-sm text-ink-gray-8">-</div>
        </div>

        <div>
          <div class="mb-2 flex items-center justify-between">
            <span class="text-xs text-ink-gray-5">{{ __('Deals') }}</span>
            <span class="rounded-full bg-surface-gray-2 px-2 py-0.5 text-xs text-ink-gray-6">{{ deals.length }}</span>
          </div>

          <div v-if="deals.length" class="space-y-2">
            <button
              v-for="deal in deals"
              :key="deal.name"
              type="button"
              class="block w-full rounded-lg border border-outline-gray-2 bg-white px-3 py-2 text-left hover:bg-surface-gray-1"
              @click="openDeal(deal.name)"
            >
              <div class="truncate text-sm font-medium text-blue-600">{{ deal.deal_title || deal.name }}</div>
              <div class="mt-1 flex flex-wrap items-center gap-2">
                <span
                  class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold"
                  :class="dealStageClass(deal)"
                >
                  <span class="size-1.5 rounded-full bg-current opacity-70" />
                  {{ dealStageLabel(deal) }}
                </span>

                <span
                  v-if="dealAmount(deal)"
                  class="text-xs font-medium text-ink-gray-6"
                >
                  {{ dealAmount(deal) }}
                </span>
              </div>
            </button>
          </div>

          <div v-else class="text-sm text-ink-gray-8">-</div>
        </div>
      </div>
    </details>

    <details v-if="contact.notes" open>
      <summary class="cursor-pointer px-5 py-4 text-sm font-semibold text-ink-gray-9">
        {{ __('Notes') }}
      </summary>
      <div class="whitespace-pre-wrap break-words px-5 pb-5 text-sm text-ink-gray-8">
        {{ contact.notes }}
      </div>
    </details>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { formatCurrency } from '@/utils'

const props = defineProps({
  contact: { type: Object, required: true },
})

const router = useRouter()
const labels = reactive({ company: '', owner: '' })
const deals = ref([])
const sourceLead = ref(null)
const dealStages = ref([])

const stageMap = computed(() => {
  const map = new Map()
  for (const stage of dealStages.value) map.set(stage.name, stage)
  return map
})

async function getDoc(doctype, name) {
  if (!name) return null
  try {
    return await call('frappe.client.get', { doctype, name })
  } catch {
    return null
  }
}

function dealStageLabel(deal) {
  const stage = stageMap.value.get(deal.stage)
  return stage?.stage_name || deal.stage || __('No Stage')
}

function dealStageType(deal) {
  return stageMap.value.get(deal.stage)?.stage_type || 'OPEN'
}

function dealStageClass(deal) {
  const type = dealStageType(deal)
  if (type === 'WON') return 'border-green-200 bg-green-50 text-green-700'
  if (type === 'LOST') return 'border-red-200 bg-red-50 text-red-700'
  return 'border-blue-200 bg-blue-50 text-blue-700'
}

function dealAmount(deal) {
  if (deal.amount === null || deal.amount === undefined || deal.amount === '') return ''
  try {
    return formatCurrency(deal.amount)
  } catch {
    return String(deal.amount)
  }
}

async function loadStages() {
  try {
    const rows = await call('frappe.client.get_list', {
      doctype: 'DoubleT Deal Stage',
      fields: ['name', 'stage_name', 'stage_type', 'sort_order', 'enabled'],
      filters: { enabled: 1 },
      order_by: 'sort_order asc',
      limit_page_length: 200,
    })
    dealStages.value = rows || []
  } catch {
    dealStages.value = []
  }
}

async function loadRelated() {
  labels.company = ''
  labels.owner = ''
  deals.value = []
  sourceLead.value = null

  const tasks = []

  if (props.contact.company) {
    tasks.push(
      getDoc('DoubleT Company', props.contact.company).then(doc => {
        labels.company = doc?.company_name || doc?.name || props.contact.company
      }),
    )
  }

  if (props.contact.contact_owner) {
    tasks.push(
      getDoc('User', props.contact.contact_owner).then(doc => {
        labels.owner = doc?.full_name || doc?.first_name || doc?.name || props.contact.contact_owner
      }),
    )
  }

  tasks.push(
    call('frappe.client.get_list', {
      doctype: 'DoubleT Deal',
      filters: { contact: props.contact.name },
      fields: ['name', 'deal_title', 'stage', 'amount', 'modified'],
      order_by: 'modified desc',
      limit_page_length: 50,
    })
      .then(rows => {
        deals.value = rows || []
      })
      .catch(() => {
        deals.value = []
      }),
  )

  tasks.push(
    call('frappe.client.get_list', {
      doctype: 'DoubleT Lead',
      filters: { converted_contact: props.contact.name },
      fields: ['name', 'first_name', 'last_name', 'modified'],
      order_by: 'modified desc',
      limit_page_length: 1,
    })
      .then(rows => {
        const lead = rows?.[0]
        if (!lead) return
        sourceLead.value = {
          name: lead.name,
          label: [lead.first_name, lead.last_name].filter(Boolean).join(' ') || lead.name,
        }
      })
      .catch(() => {
        sourceLead.value = null
      }),
  )

  await Promise.all(tasks)
}

function openCompany() {
  if (!props.contact.company) return
  router.push({ name: 'CompanyDetail', params: { companyId: props.contact.company } })
}

function openLead(name) {
  router.push({ name: 'LeadDetail', params: { leadId: name } })
}

function openDeal(name) {
  router.push({ name: 'DealDetail', params: { dealId: name } })
}

watch(
  () => props.contact,
  () => loadRelated(),
  { immediate: true, deep: true },
)

loadStages()

const InfoRow = defineComponent({
  props: { label: String, value: [String, Number] },
  setup(rowProps) {
    return () =>
      h('div', { class: 'grid grid-cols-[92px_minmax(0,1fr)] gap-3 text-sm' }, [
        h('div', { class: 'text-ink-gray-5' }, rowProps.label),
        h(
          'div',
          { class: 'min-w-0 whitespace-pre-wrap break-words text-ink-gray-9' },
          rowProps.value === null || rowProps.value === undefined || rowProps.value === ''
            ? '-'
            : String(rowProps.value),
        ),
      ])
  },
})

const LinkedRow = defineComponent({
  props: { label: String, value: String, displayValue: String },
  emits: ['open'],
  setup(rowProps, { emit }) {
    return () =>
      h('div', { class: 'grid grid-cols-[92px_minmax(0,1fr)] gap-3 text-sm' }, [
        h('div', { class: 'text-ink-gray-5' }, rowProps.label),
        rowProps.value
          ? h(
              'button',
              {
                type: 'button',
                class: 'min-w-0 truncate text-left text-blue-600 hover:underline',
                onClick: () => emit('open'),
              },
              rowProps.displayValue || rowProps.value,
            )
          : h('div', { class: 'text-ink-gray-9' }, '-'),
      ])
  },
})
</script>
