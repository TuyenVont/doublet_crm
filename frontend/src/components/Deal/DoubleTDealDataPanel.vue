<template>
  <div class="flex-1 overflow-y-auto bg-white p-6">
    <div class="mx-auto max-w-5xl">

      <!-- HEADER -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-ink-gray-9">
            {{ __('Data') }}
          </h2>

          <p class="mt-1 text-sm text-ink-gray-5">
            {{ __('Edit deal information directly.') }}
          </p>
        </div>

        <div class="flex items-center gap-2">
          <button
            v-if="dirty"
            type="button"
            class="rounded-lg border px-4 py-2 text-sm"
            :disabled="saving"
            @click="resetForm"
          >
            {{ __('Cancel') }}
          </button>

          <button
            type="button"
            class="rounded-lg bg-gray-900 px-4 py-2 text-sm text-white disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!dirty || saving"
            @click="save"
          >
            {{
              saving
                ? __('Saving...')
                : __('Save')
            }}
          </button>
        </div>
      </div>

      <div
        v-if="error"
        class="mb-5 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600"
      >
        {{ error }}
      </div>

      <!-- DEAL INFORMATION -->
      <section class="rounded-xl border border-outline-gray-2 bg-white">
        <div class="border-b px-5 py-4">
          <h3 class="font-semibold text-ink-gray-9">
            {{ __('Deal Information') }}
          </h3>
        </div>

        <div class="grid grid-cols-1 gap-5 p-5 md:grid-cols-2">

          <!-- TITLE -->
          <label class="space-y-1 md:col-span-2">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Deal Title') }} *
            </span>

            <input
              v-model="form.deal_title"
              type="text"
              maxlength="140"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <!-- AMOUNT -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Amount') }}
            </span>

            <input
              v-model="form.amount"
              type="number"
              min="0"
              step="0.01"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <!-- STAGE -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Stage') }} *
            </span>

            <select
              v-model="form.stage"
              class="w-full rounded-lg border border-outline-gray-2 bg-white px-3 py-2 text-sm"
            >
              <option value="">
                {{ __('Select Stage') }}
              </option>

              <option
                v-for="item in stages"
                :key="item.name"
                :value="item.name"
              >
                {{ item.stage_name || item.name }}
              </option>
            </select>
          </label>

          <!-- DEAL TYPE -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Deal Type') }} *
            </span>

            <select
              v-model="form.deal_type"
              class="w-full rounded-lg border border-outline-gray-2 bg-white px-3 py-2 text-sm"
              @change="onDealTypeChange"
            >
              <option value="">
                {{ __('Not selected') }}
              </option>

              <option value="PERSONAL">
                {{ __('Personal') }}
              </option>

              <option value="COMPANY">
                {{ __('Company') }}
              </option>
            </select>
          </label>

          <!-- CLOSE DATE -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Expected Close Date') }}
            </span>

            <input
              v-model="form.expected_close_date"
              type="date"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <!-- SOURCE -->
          <div class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Source') }}
            </span>

            <Link
              :value="form.source"
              doctype="DoubleT Lead Source"
              :placeholder="__('Select Source')"
              @change="value => (form.source = value || '')"
            />
          </div>

          <!-- PRIMARY OWNER -->
          <div class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Primary Owner') }}
            </span>

            <Link
              :value="form.deal_owner"
              doctype="User"
              :hide-me="true"
              :placeholder="__('Select Primary Owner')"
              @change="value => (form.deal_owner = value || '')"
            />
          </div>

        </div>
      </section>

      <!-- RELATED -->
      <section class="mt-5 rounded-xl border border-outline-gray-2 bg-white">
        <div class="border-b px-5 py-4">
          <h3 class="font-semibold text-ink-gray-9">
            {{ __('Related') }}
          </h3>
        </div>

        <div class="grid grid-cols-1 gap-5 p-5 md:grid-cols-2">

          <!-- CONTACT -->
          <div class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Contact') }}
              <span v-if="form.deal_type === 'PERSONAL'">*</span>
            </span>

            <Link
              :value="form.contact"
              doctype="DoubleT Contact"
              :placeholder="__('Select Contact')"
              @change="onContactChange"
            />
          </div>

          <!-- COMPANY -->
          <div class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Company') }}
              <span v-if="form.deal_type === 'COMPANY'">*</span>
            </span>

            <Link
              :value="form.company"
              doctype="DoubleT Company"
              :placeholder="__('Select Company')"
              :disabled="form.deal_type === 'PERSONAL'"
              @change="onCompanyChange"
            />
          </div>

          <!-- SOURCE LEAD -->
          <div class="space-y-1 md:col-span-2">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Source Lead') }}
            </span>

            <Link
              :value="form.source_lead"
              doctype="DoubleT Lead"
              :placeholder="__('Select Source Lead')"
              @change="onSourceLeadChange"
            >
              <template #target="{ togglePopover }">
                <button
                  type="button"
                  class="flex w-full items-center justify-between rounded-lg border border-outline-gray-2 bg-surface-gray-2 px-3 py-2 text-left text-sm transition hover:bg-surface-gray-3"
                  @click="togglePopover"
                >
                  <span
                    class="truncate"
                    :class="
                      sourceLeadLabel
                        ? 'text-ink-gray-9'
                        : 'text-ink-gray-4'
                    "
                  >
                    {{
                      sourceLeadLabel ||
                      __('Select Source Lead')
                    }}
                  </span>

                  <span
                    class="lucide-chevron-down h-4 w-4 shrink-0 text-ink-gray-5"
                    aria-hidden="true"
                  />
                </button>
              </template>
            </Link>
          </div>

        </div>
      </section>

      <!-- OUTCOME -->
      <section class="mt-5 rounded-xl border border-outline-gray-2 bg-white">
        <div class="border-b px-5 py-4">
          <h3 class="font-semibold text-ink-gray-9">
            {{ __('Outcome') }}
          </h3>
        </div>

        <div class="grid grid-cols-1 gap-5 p-5 md:grid-cols-2">

          <ReadOnlyField
            :label="__('Won On')"
            :value="deal.won_on"
          />

          <ReadOnlyField
            :label="__('Lost On')"
            :value="deal.lost_on"
          />

          <!-- LOST REASON -->
          <label
            v-if="selectedStageType === 'LOST'"
            class="space-y-1 md:col-span-2"
          >
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Lost Reason') }} *
            </span>

            <textarea
              v-model="form.lost_reason"
              rows="4"
              class="w-full resize-y rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
              :placeholder="__('Why was this Deal lost?')"
            />
          </label>

          <ReadOnlyField
            v-else
            class="md:col-span-2"
            :label="__('Lost Reason')"
            :value="deal.lost_reason"
          />

        </div>
      </section>

    </div>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'

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
  call,
  toast,
} from 'frappe-ui'

const props = defineProps({
  deal: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits([
  'saved',
])

const saving = ref(false)
const error = ref('')
const stages = ref([])

/*
 * Label hiển thị cho Source Lead.
 * form.source_lead vẫn giữ ID nội bộ để save.
 */
const sourceLeadLabel = ref('')

const form = reactive({
  deal_title: '',
  amount: '',
  stage: '',
  deal_type: '',
  deal_owner: '',
  source: '',
  contact: '',
  company: '',
  source_lead: '',
  expected_close_date: '',
  lost_reason: '',
})

const editableFields = [
  'deal_title',
  'amount',
  'stage',
  'deal_type',
  'deal_owner',
  'source',
  'contact',
  'company',
  'source_lead',
  'expected_close_date',
  'lost_reason',
]

function normalize(value) {
  return value === null ||
    value === undefined
    ? ''
    : String(value)
}

function fillForm() {
  for (const field of editableFields) {
    form[field] =
      props.deal?.[field] ??
      ''
  }

  if (!form.deal_type) {
    if (form.company) {
      form.deal_type =
        'COMPANY'
    } else if (form.contact) {
      form.deal_type =
        'PERSONAL'
    }
  }

  form.expected_close_date =
    props.deal?.expected_close_date
      ?.slice(0, 10) ||
    ''
}

const dirty = computed(() => {
  return editableFields.some(
    field =>
      normalize(form[field]) !==
      normalize(
        props.deal?.[field]
      )
  )
})

const selectedStage = computed(() => {
  return stages.value.find(
    item =>
      item.name === form.stage
  )
})

const selectedStageType = computed(() => {
  return (
    selectedStage.value?.stage_type ||
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

  if (
    Array.isArray(
      e?.messages
    )
  ) {
    return e.messages.join(', ')
  }

  return (
    e?.message ||
    'Unable to save Deal.'
  )
}

function resetForm() {
  error.value = ''
  fillForm()

  loadSourceLeadLabel(
    form.source_lead
  )
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

/* --------------------------------
 * SOURCE LEAD LABEL
 * -------------------------------- */

async function loadSourceLeadLabel(
  value = form.source_lead
) {
  sourceLeadLabel.value = ''

  if (!value) {
    return
  }

  const lead =
    await getDoc(
      'DoubleT Lead',
      value
    )

  if (!lead) {
    sourceLeadLabel.value =
      value

    return
  }

  /*
   * Ưu tiên các field label phổ biến.
   * Nếu Lead hiện tại có first_name / last_name
   * thì ghép tên.
   */
  const fullName =
    [
      lead.first_name,
      lead.last_name,
    ]
      .filter(Boolean)
      .join(' ')
      .trim()

  sourceLeadLabel.value =
    fullName ||
    lead.lead_name ||
    lead.title ||
    lead.full_name ||
    lead.name
}

/* --------------------------------
 * DEAL TYPE
 * -------------------------------- */

function onDealTypeChange() {
  if (
    form.deal_type ===
    'PERSONAL'
  ) {
    form.company = ''
  }
}

/* --------------------------------
 * CONTACT → COMPANY
 * -------------------------------- */

async function onContactChange(
  value
) {
  form.contact = value || ''

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
    form.company =
      contact.company

    form.deal_type =
      'COMPANY'
  } else {
    form.company = ''

    form.deal_type =
      'PERSONAL'
  }
}

/* --------------------------------
 * COMPANY
 * -------------------------------- */

function onCompanyChange(
  value
) {
  form.company = value || ''

  if (form.company) {
    form.deal_type =
      'COMPANY'
  }
}

/* --------------------------------
 * LEAD → CONTACT → COMPANY
 * -------------------------------- */

async function onSourceLeadChange(
  value
) {
  form.source_lead =
    value || ''

  if (!value) {
    sourceLeadLabel.value = ''
    return
  }

  const lead =
    await getDoc(
      'DoubleT Lead',
      value
    )

  if (!lead) {
    sourceLeadLabel.value =
      value

    return
  }

  const fullName =
    [
      lead.first_name,
      lead.last_name,
    ]
      .filter(Boolean)
      .join(' ')
      .trim()

  sourceLeadLabel.value =
    fullName ||
    lead.lead_name ||
    lead.title ||
    lead.full_name ||
    lead.name

  const contactName =
    lead.converted_contact ||
    ''

  let companyName =
    lead.converted_company ||
    ''

  if (contactName) {
    form.contact =
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
    form.company =
      companyName

    form.deal_type =
      'COMPANY'
  } else if (contactName) {
    form.company = ''

    form.deal_type =
      'PERSONAL'
  }
}

/* --------------------------------
 * SAVE
 * -------------------------------- */

async function save() {
  if (
    !props.deal?.name ||
    saving.value
  ) {
    return
  }

  error.value = ''

  if (
    !form.deal_title.trim()
  ) {
    error.value =
      'Deal Title is required.'

    return
  }

  if (!form.stage) {
    error.value =
      'Stage is required.'

    return
  }

  if (
    form.amount !== '' &&
    (
      !Number.isFinite(
        Number(form.amount)
      ) ||
      Number(form.amount) < 0
    )
  ) {
    error.value =
      'Amount must be a non-negative number.'

    return
  }

  if (
    ![
      'PERSONAL',
      'COMPANY',
    ].includes(
      form.deal_type
    )
  ) {
    error.value =
      'Deal Type is required.'

    return
  }

  if (
    form.deal_type ===
      'PERSONAL' &&
    !form.contact
  ) {
    error.value =
      'Contact is required for a PERSONAL deal.'

    return
  }

  if (
    form.deal_type ===
      'PERSONAL' &&
    form.company
  ) {
    error.value =
      'Company must be empty for a PERSONAL deal.'

    return
  }

  if (
    form.deal_type ===
      'COMPANY' &&
    !form.company
  ) {
    error.value =
      'Company is required for a COMPANY deal.'

    return
  }

  if (
    selectedStageType.value ===
      'LOST' &&
    !form.lost_reason.trim()
  ) {
    error.value =
      'Lost Reason is required for a lost deal.'

    return
  }

  saving.value = true

  try {
    const values = {
      deal_title:
        form.deal_title.trim(),

      amount:
        form.amount === ''
          ? null
          : Number(form.amount),

      stage:
        form.stage,

      deal_type:
        form.deal_type,

      /*
       * deal_owner = primary owner.
       * Không liên quan tới AssignTo / _assign.
       */
      deal_owner:
        form.deal_owner ||
        null,

      source:
        form.source ||
        null,

      contact:
        form.contact ||
        null,

      company:
        form.company ||
        null,

      /*
       * Vẫn save ID nội bộ.
       * UI chỉ hiển thị sourceLeadLabel.
       */
      source_lead:
        form.source_lead ||
        null,

      expected_close_date:
        form.expected_close_date ||
        null,

      lost_reason:
        selectedStageType.value ===
          'LOST'
          ? form.lost_reason.trim()
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

    toast.success(
      __('Deal updated successfully')
    )
  } catch (e) {
    console.error(
      'Save Deal failed:',
      e
    )

    error.value =
      apiError(e)
  } finally {
    saving.value = false
  }
}

watch(
  () => props.deal,
  () => {
    fillForm()

    loadSourceLeadLabel(
      props.deal?.source_lead
    )
  },
  {
    immediate: true,
    deep: true,
  }
)

onMounted(() => {
  loadStages()
})

const ReadOnlyField =
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
              'space-y-1',
          },
          [
            h(
              'div',
              {
                class:
                  'text-xs text-ink-gray-5',
              },
              props.label
            ),

            h(
              'div',
              {
                class:
                  'break-words text-sm text-ink-gray-9',
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
</script>