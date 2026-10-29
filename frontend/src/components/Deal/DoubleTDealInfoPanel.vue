<template>
  <div class="flex flex-col overflow-y-auto">

    <!-- DEAL DETAILS -->
    <details open class="border-b">
      <summary
        class="flex cursor-pointer items-center justify-between px-5 py-4 text-sm font-semibold text-ink-gray-9"
      >
        <span>{{ __('Deal Details') }}</span>

        <button
          type="button"
          class="rounded-md px-2 py-1 text-xs font-normal text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9"
          @click.prevent.stop="startEdit('details')"
        >
          {{
            detailsEditing
              ? __('Editing')
              : __('Edit')
          }}
        </button>
      </summary>

      <!-- VIEW -->
      <div
        v-if="!detailsEditing"
        class="space-y-4 px-5 pb-5"
      >
        <InfoRow
          :label="__('Stage')"
          :value="deal.stage"
        />

        <InfoRow
          :label="__('Amount')"
          :value="displayAmount"
        />

        <InfoRow
          :label="__('Close Date')"
          :value="deal.expected_close_date"
        />

        <InfoRow
          :label="__('Primary Owner')"
          :value="labels.deal_owner || deal.deal_owner"
        />

        <InfoRow
          :label="__('Deal Type')"
          :value="deal.deal_type"
        />
      </div>

      <!-- EDIT -->
      <div
        v-else
        class="space-y-4 px-5 pb-5"
      >
        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Stage') }} *
          </span>

          <select
            v-model="detailsForm.stage"
            class="w-full rounded-lg border border-outline-gray-2 bg-white px-3 py-2 text-sm"
          >
            <option
              v-for="item in stages"
              :key="item.name"
              :value="item.name"
            >
              {{ item.stage_name || item.name }}
            </option>
          </select>
        </label>

        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Amount') }}
          </span>

          <input
            v-model="detailsForm.amount"
            type="number"
            min="0"
            step="0.01"
            class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
          />
        </label>

        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Expected Close Date') }}
          </span>

          <input
            v-model="detailsForm.expected_close_date"
            type="date"
            class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
          />
        </label>

        <div class="space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Primary Owner') }}
          </span>

          <Link
            :value="detailsForm.deal_owner"
            doctype="User"
            :hide-me="true"
            :placeholder="__('Select Primary Owner')"
            @change="
              value =>
                (detailsForm.deal_owner =
                  value || '')
            "
          />
        </div>

        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Deal Type') }}
          </span>

          <select
            v-model="detailsForm.deal_type"
            class="w-full rounded-lg border border-outline-gray-2 bg-white px-3 py-2 text-sm"
            @change="onDealTypeChange"
          >
            <option value="PERSONAL">
              {{ __('Personal') }}
            </option>

            <option value="COMPANY">
              {{ __('Company') }}
            </option>
          </select>
        </label>

        <label
          v-if="detailsStageType === 'LOST'"
          class="block space-y-1"
        >
          <span class="text-xs text-ink-gray-5">
            {{ __('Lost Reason') }} *
          </span>

          <textarea
            v-model="detailsForm.lost_reason"
            rows="3"
            class="w-full resize-y rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
          />
        </label>

        <p
          v-if="detailsError"
          class="rounded-md bg-red-50 px-3 py-2 text-xs text-red-600"
        >
          {{ detailsError }}
        </p>

        <div class="flex justify-end gap-2">
          <button
            type="button"
            class="rounded-lg border px-3 py-1.5 text-sm"
            :disabled="detailsSaving"
            @click="cancelEdit('details')"
          >
            {{ __('Cancel') }}
          </button>

          <button
            type="button"
            class="rounded-lg bg-gray-900 px-3 py-1.5 text-sm text-white disabled:opacity-50"
            :disabled="detailsSaving"
            @click="saveDetails"
          >
            {{
              detailsSaving
                ? __('Saving...')
                : __('Save')
            }}
          </button>
        </div>
      </div>
    </details>

    <!-- RELATED -->
    <details open class="border-b">
      <summary
        class="flex cursor-pointer items-center justify-between px-5 py-4 text-sm font-semibold text-ink-gray-9"
      >
        <span>{{ __('Related') }}</span>

        <button
          type="button"
          class="rounded-md px-2 py-1 text-xs font-normal text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9"
          @click.prevent.stop="startEdit('related')"
        >
          {{
            relatedEditing
              ? __('Editing')
              : __('Edit')
          }}
        </button>
      </summary>

      <!-- VIEW -->
      <div
        v-if="!relatedEditing"
        class="space-y-4 px-5 pb-5"
      >
        <LinkedRow
          :label="__('Contact')"
          :value="deal.contact"
          :display-value="labels.contact"
          @open="openContact"
        />

        <LinkedRow
          :label="__('Company')"
          :value="deal.company"
          :display-value="labels.company"
          @open="openCompany"
        />

        <LinkedRow
          :label="__('Source Lead')"
          :value="deal.source_lead"
          :display-value="labels.source_lead"
          @open="openSourceLead"
        />

        <InfoRow
          :label="__('Source')"
          :value="deal.source"
        />
      </div>

      <!-- EDIT -->
      <div
        v-else
        class="space-y-4 px-5 pb-5"
      >
        <div class="space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Contact') }}
          </span>

          <Link
            :value="relatedForm.contact"
            doctype="DoubleT Contact"
            :placeholder="__('Select Contact')"
            @change="onContactChange"
          />
        </div>

        <div class="space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Company') }}
          </span>

          <Link
            :value="relatedForm.company"
            doctype="DoubleT Company"
            :placeholder="__('Select Company')"
            :disabled="
              detailsForm.deal_type ===
              'PERSONAL'
            "
            @change="onCompanyChange"
          />
        </div>

        <div class="space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Source Lead') }}
          </span>

          <Link
            :value="relatedForm.source_lead"
            doctype="DoubleT Lead"
            :placeholder="__('Select Source Lead')"
            @change="onSourceLeadChange"
          />
        </div>

        <div class="space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Source') }}
          </span>

          <Link
            :value="relatedForm.source"
            doctype="DoubleT Lead Source"
            :placeholder="__('Select Source')"
            @change="
              value =>
                (relatedForm.source =
                  value || '')
            "
          />
        </div>

        <p
          v-if="relatedError"
          class="rounded-md bg-red-50 px-3 py-2 text-xs text-red-600"
        >
          {{ relatedError }}
        </p>

        <div class="flex justify-end gap-2">
          <button
            type="button"
            class="rounded-lg border px-3 py-1.5 text-sm"
            :disabled="relatedSaving"
            @click="cancelEdit('related')"
          >
            {{ __('Cancel') }}
          </button>

          <button
            type="button"
            class="rounded-lg bg-gray-900 px-3 py-1.5 text-sm text-white disabled:opacity-50"
            :disabled="relatedSaving"
            @click="saveRelated"
          >
            {{
              relatedSaving
                ? __('Saving...')
                : __('Save')
            }}
          </button>
        </div>
      </div>
    </details>

    <!-- OUTCOME -->
    <details open>
      <summary
        class="cursor-pointer px-5 py-4 text-sm font-semibold text-ink-gray-9"
      >
        {{ __('Outcome') }}
      </summary>

      <div class="space-y-4 px-5 pb-5">
        <InfoRow
          :label="__('Won On')"
          :value="deal.won_on"
        />

        <InfoRow
          :label="__('Lost On')"
          :value="deal.lost_on"
        />

        <InfoRow
          :label="__('Lost Reason')"
          :value="deal.lost_reason"
        />
      </div>
    </details>

  </div>
</template>

<script setup>
import {
  computed,
  defineComponent,
  h,
  onMounted,
  reactive,
  ref,
  watch,
} from 'vue'

import {
  useRouter,
} from 'vue-router'

import {
  call,
  toast,
} from 'frappe-ui'

import Link from '@/components/Controls/Link.vue'

import {
  formatCurrency,
} from '@/utils'

const props = defineProps({
  deal: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits([
  'saved',
])

const router = useRouter()

const stages = ref([])

const detailsEditing = ref(false)
const relatedEditing = ref(false)

const detailsSaving = ref(false)
const relatedSaving = ref(false)

const detailsError = ref('')
const relatedError = ref('')

const detailsForm = reactive({
  stage: '',
  amount: '',
  expected_close_date: '',
  deal_owner: '',
  deal_type: '',
  lost_reason: '',
})

const relatedForm = reactive({
  contact: '',
  company: '',
  source_lead: '',
  source: '',
})

const labels = reactive({
  contact: '',
  company: '',
  source_lead: '',
  deal_owner: '',
})

const displayAmount = computed(() => {
  if (
    props.deal?.amount === null ||
    props.deal?.amount === undefined ||
    props.deal?.amount === ''
  ) {
    return '-'
  }

  return formatCurrency(
    props.deal.amount
  )
})

const detailsStage = computed(() => {
  return stages.value.find(
    item =>
      item.name ===
      detailsForm.stage
  )
})

const detailsStageType = computed(() => {
  return (
    detailsStage.value?.stage_type ||
    ''
  )
})

function apiError(e) {
  if (
    Array.isArray(
      e?._server_messages
    )
  ) {
    return e._server_messages.join(', ')
  }

  return (
    e?.message ||
    'Unable to update Deal.'
  )
}

function fillDetails() {
  detailsForm.stage =
    props.deal?.stage ||
    ''

  detailsForm.amount =
    props.deal?.amount ??
    ''

  detailsForm.expected_close_date =
    props.deal
      ?.expected_close_date
      ?.slice(0, 10) ||
    ''

  detailsForm.deal_owner =
    props.deal?.deal_owner ||
    ''

  detailsForm.deal_type =
    props.deal?.deal_type ||
    (
      props.deal?.company
        ? 'COMPANY'
        : props.deal?.contact
          ? 'PERSONAL'
          : ''
    )

  detailsForm.lost_reason =
    props.deal?.lost_reason ||
    ''
}

function fillRelated() {
  relatedForm.contact =
    props.deal?.contact ||
    ''

  relatedForm.company =
    props.deal?.company ||
    ''

  relatedForm.source_lead =
    props.deal?.source_lead ||
    ''

  relatedForm.source =
    props.deal?.source ||
    ''
}

function startEdit(section) {
  if (section === 'details') {
    fillDetails()

    detailsError.value = ''
    detailsEditing.value = true
    relatedEditing.value = false
  }

  if (section === 'related') {
    fillRelated()

    relatedError.value = ''
    relatedEditing.value = true
    detailsEditing.value = false
  }
}

function cancelEdit(section) {
  if (section === 'details') {
    detailsEditing.value = false
    detailsError.value = ''
    fillDetails()
  }

  if (section === 'related') {
    relatedEditing.value = false
    relatedError.value = ''
    fillRelated()
  }
}

async function getDoc(
  doctype,
  name
) {
  if (!name) {
    return null
  }

  try {
    return await call(
      'frappe.client.get',
      {
        doctype,
        name,
      }
    )
  } catch (e) {
    console.error(
      `Unable to load ${doctype}:`,
      e
    )

    return null
  }
}

async function loadStages() {
  try {
    const result = await call(
      'frappe.client.get_list',
      {
        doctype:
          'DoubleT Deal Stage',

        fields: [
          'name',
          'stage_name',
          'stage_type',
          'sort_order',
          'enabled',
        ],

        filters: {
          enabled: 1,
        },

        order_by:
          'sort_order asc',

        limit_page_length:
          200,
      }
    )

    stages.value =
      Array.isArray(result)
        ? result
        : []
  } catch (e) {
    console.error(
      'Load Deal Stages failed:',
      e
    )
  }
}

function onDealTypeChange() {
  if (
    detailsForm.deal_type ===
    'PERSONAL'
  ) {
    relatedForm.company = ''
  }
}

async function onContactChange(
  value
) {
  relatedForm.contact =
    value || ''

  if (!value) {
    return
  }

  const contact =
    await getDoc(
      'DoubleT Contact',
      value
    )

  if (!contact) {
    return
  }

  if (contact.company) {
    relatedForm.company =
      contact.company

    detailsForm.deal_type =
      'COMPANY'
  } else {
    relatedForm.company = ''
    detailsForm.deal_type =
      'PERSONAL'
  }
}

function onCompanyChange(
  value
) {
  relatedForm.company =
    value || ''

  if (relatedForm.company) {
    detailsForm.deal_type =
      'COMPANY'
  }
}

async function onSourceLeadChange(
  value
) {
  relatedForm.source_lead =
    value || ''

  if (!value) {
    return
  }

  const lead =
    await getDoc(
      'DoubleT Lead',
      value
    )

  if (!lead) {
    return
  }

  const contactName =
    lead.converted_contact ||
    ''

  let companyName =
    lead.converted_company ||
    ''

  if (contactName) {
    relatedForm.contact =
      contactName

    if (!companyName) {
      const contact =
        await getDoc(
          'DoubleT Contact',
          contactName
        )

      companyName =
        contact?.company ||
        ''
    }
  }

  if (companyName) {
    relatedForm.company =
      companyName

    detailsForm.deal_type =
      'COMPANY'
  } else if (contactName) {
    relatedForm.company = ''

    detailsForm.deal_type =
      'PERSONAL'
  }
}

async function saveDetails() {
  if (
    !props.deal?.name ||
    detailsSaving.value
  ) {
    return
  }

  detailsError.value = ''

  if (!detailsForm.stage) {
    detailsError.value =
      'Stage is required.'

    return
  }

  if (
    detailsForm.amount !== '' &&
    (
      !Number.isFinite(
        Number(detailsForm.amount)
      ) ||
      Number(detailsForm.amount) < 0
    )
  ) {
    detailsError.value =
      'Amount must be a non-negative number.'

    return
  }

  if (
    ![
      'PERSONAL',
      'COMPANY',
    ].includes(
      detailsForm.deal_type
    )
  ) {
    detailsError.value =
      'Deal Type is required.'

    return
  }

  if (
    detailsStageType.value ===
      'LOST' &&
    !detailsForm.lost_reason.trim()
  ) {
    detailsError.value =
      'Lost Reason is required for a lost deal.'

    return
  }

  detailsSaving.value = true

  try {
    const values = {
      stage:
        detailsForm.stage,

      amount:
        detailsForm.amount === ''
          ? null
          : Number(
              detailsForm.amount
            ),

      expected_close_date:
        detailsForm.expected_close_date ||
        null,

      deal_owner:
        detailsForm.deal_owner ||
        null,

      deal_type:
        detailsForm.deal_type,

      lost_reason:
        detailsStageType.value ===
          'LOST'
          ? detailsForm.lost_reason.trim()
          : null,
    }

    const result = await call(
      'frappe.client.set_value',
      {
        doctype:
          'DoubleT Deal',

        name:
          props.deal.name,

        fieldname:
          values,
      }
    )

    emit(
      'saved',
      result || values
    )

    detailsEditing.value = false

    toast.success(
      __('Deal details updated')
    )
  } catch (e) {
    detailsError.value =
      apiError(e)
  } finally {
    detailsSaving.value = false
  }
}

async function saveRelated() {
  if (
    !props.deal?.name ||
    relatedSaving.value
  ) {
    return
  }

  relatedError.value = ''

  if (
    detailsForm.deal_type ===
      'PERSONAL' &&
    !relatedForm.contact
  ) {
    relatedError.value =
      'Contact is required for a PERSONAL deal.'

    return
  }

  if (
    detailsForm.deal_type ===
      'PERSONAL' &&
    relatedForm.company
  ) {
    relatedError.value =
      'Company must be empty for a PERSONAL deal.'

    return
  }

  if (
    detailsForm.deal_type ===
      'COMPANY' &&
    !relatedForm.company
  ) {
    relatedError.value =
      'Company is required for a COMPANY deal.'

    return
  }

  relatedSaving.value = true

  try {
    const values = {
      contact:
        relatedForm.contact ||
        null,

      company:
        relatedForm.company ||
        null,

      source_lead:
        relatedForm.source_lead ||
        null,

      source:
        relatedForm.source ||
        null,

      deal_type:
        detailsForm.deal_type,
    }

    const result = await call(
      'frappe.client.set_value',
      {
        doctype:
          'DoubleT Deal',

        name:
          props.deal.name,

        fieldname:
          values,
      }
    )

    emit(
      'saved',
      result || values
    )

    relatedEditing.value = false

    toast.success(
      __('Related information updated')
    )
  } catch (e) {
    relatedError.value =
      apiError(e)
  } finally {
    relatedSaving.value = false
  }
}

/* --------------------------------
 * LABELS
 * -------------------------------- */

async function loadLabels() {
  labels.contact = ''
  labels.company = ''
  labels.source_lead = ''
  labels.deal_owner = ''

  const tasks = []

  if (props.deal?.deal_owner) {
    tasks.push(
      getDoc(
        'User',
        props.deal.deal_owner
      ).then(doc => {
        if (!doc) return

        labels.deal_owner =
          doc.full_name ||
          doc.first_name ||
          doc.name
      })
    )
  }

  if (props.deal?.contact) {
    tasks.push(
      getDoc(
        'DoubleT Contact',
        props.deal.contact
      ).then(doc => {
        if (!doc) return

        labels.contact =
          [
            doc.first_name,
            doc.last_name,
          ]
            .filter(Boolean)
            .join(' ') ||
          doc.name
      })
    )
  }

  if (props.deal?.company) {
    tasks.push(
      getDoc(
        'DoubleT Company',
        props.deal.company
      ).then(doc => {
        if (!doc) return

        labels.company =
          doc.company_name ||
          doc.name
      })
    )
  }

  if (props.deal?.source_lead) {
    tasks.push(
      getDoc(
        'DoubleT Lead',
        props.deal.source_lead
      ).then(doc => {
        if (!doc) return

        labels.source_lead =
          [
            doc.first_name,
            doc.last_name,
          ]
            .filter(Boolean)
            .join(' ') ||
          doc.lead_name ||
          doc.title ||
          doc.full_name ||
          doc.name
      })
    )
  }

  await Promise.all(tasks)
}

/* --------------------------------
 * NAVIGATION
 * -------------------------------- */

function openContact() {
  if (!props.deal?.contact) {
    return
  }

  router.push({
    name: 'ContactDetail',
    params: {
      contactId:
        props.deal.contact,
    },
  })
}

function openCompany() {
  if (!props.deal?.company) {
    return
  }

  router.push({
    name: 'CompanyDetail',
    params: {
      companyId:
        props.deal.company,
    },
  })
}

function openSourceLead() {
  if (!props.deal?.source_lead) {
    return
  }

  router.push({
    name: 'LeadDetail',
    params: {
      leadId:
        props.deal.source_lead,
    },
  })
}

watch(
  () => props.deal,
  () => {
    if (!detailsEditing.value) {
      fillDetails()
    }

    if (!relatedEditing.value) {
      fillRelated()
    }

    loadLabels()
  },
  {
    deep: true,
    immediate: true,
  }
)

onMounted(() => {
  loadStages()
})

const InfoRow =
  defineComponent({
    props: {
      label: String,
      value: [
        String,
        Number,
      ],
    },

    setup(props) {
      return () =>
        h(
          'div',
          {
            class:
              'grid grid-cols-[88px_minmax(0,1fr)] gap-3 text-sm',
          },
          [
            h(
              'div',
              {
                class:
                  'text-ink-gray-5',
              },
              props.label
            ),

            h(
              'div',
              {
                class:
                  'min-w-0 break-words text-ink-gray-9',
              },
              props.value ===
                  null ||
                props.value ===
                  undefined ||
                props.value ===
                  ''
                ? '-'
                : String(
                    props.value
                  )
            ),
          ]
        )
    },
  })

const LinkedRow =
  defineComponent({
    props: {
      label: String,
      value: String,
      displayValue: String,
    },

    emits: [
      'open',
    ],

    setup(
      props,
      {
        emit,
      }
    ) {
      return () =>
        h(
          'div',
          {
            class:
              'grid grid-cols-[88px_minmax(0,1fr)] gap-3 text-sm',
          },
          [
            h(
              'div',
              {
                class:
                  'text-ink-gray-5',
              },
              props.label
            ),

            props.value
              ? h(
                  'button',
                  {
                    type: 'button',

                    class:
                      'min-w-0 truncate text-left text-blue-600 hover:underline',

                    onClick:
                      () =>
                        emit('open'),
                  },
                  props.displayValue ||
                    props.value
                )
              : h(
                  'div',
                  {
                    class:
                      'text-ink-gray-9',
                  },
                  '-'
                ),
          ]
        )
    },
  })
</script>