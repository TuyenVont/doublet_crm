<template>
  <div class="flex flex-col overflow-y-auto">

    <!-- DETAILS -->
    <details open class="border-b">
      <summary
        class="flex cursor-pointer items-center justify-between px-5 py-4 text-sm font-semibold text-ink-gray-9"
      >
        <span>{{ __('Details') }}</span>

        <button
          type="button"
          class="rounded-md px-2 py-1 text-xs font-normal text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9"
          @click.prevent.stop="startEdit('details')"
        >
          {{ detailsEditing ? __('Editing') : __('Edit') }}
        </button>
      </summary>

      <!-- VIEW -->
      <div
        v-if="!detailsEditing"
        class="space-y-4 px-5 pb-5"
      >
        <InfoRow
          :label="__('Company')"
          :value="lead.company_name"
        />

        <InfoRow
          :label="__('Source')"
          :value="lead.source"
        />

        <InfoRow
          :label="__('Status')"
          :value="lead.status"
        />

        <InfoRow
          :label="__('Lead Owner')"
          :value="lead.lead_owner"
        />
      </div>

      <!-- EDIT -->
      <div
        v-else
        class="space-y-4 px-5 pb-5"
      >
        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Company') }}
          </span>

          <input
            v-model="detailsForm.company_name"
            type="text"
            list="doublet-lead-sidebar-company-options"
            autocomplete="off"
            class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            :placeholder="__('Type a new company or choose an existing one')"
          />

          <datalist id="doublet-lead-sidebar-company-options">
            <option
              v-for="item in companies"
              :key="item.name"
              :value="item.company_name || item.name"
            />
          </datalist>
        </label>

        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Source') }}
          </span>

          <select
            v-model="detailsForm.source"
            class="w-full rounded-lg border border-outline-gray-2 bg-white px-3 py-2 text-sm"
          >
            <option value="">
              {{ __('Not selected') }}
            </option>

            <option
              v-for="item in sources"
              :key="item.name"
              :value="item.name"
            >
              {{ item.source_name || item.name }}
            </option>
          </select>
        </label>

        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Status') }}
          </span>

          <select
            v-model="detailsForm.status"
            class="w-full rounded-lg border border-outline-gray-2 bg-white px-3 py-2 text-sm"
          >
            <option
              v-for="status in statuses"
              :key="status"
              :value="status"
            >
              {{ status }}
            </option>
          </select>
        </label>

        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Primary Owner') }}
          </span>

          <select
            v-model="detailsForm.lead_owner"
            class="w-full rounded-lg border border-outline-gray-2 bg-white px-3 py-2 text-sm"
          >
            <option value="">
              {{ __('Unassigned') }}
            </option>

            <option
              v-for="item in users"
              :key="item.name"
              :value="item.name"
            >
              {{ item.full_name || item.name }}
            </option>
          </select>
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

    <!-- PERSON -->
    <details open class="border-b">
      <summary
        class="flex cursor-pointer items-center justify-between px-5 py-4 text-sm font-semibold text-ink-gray-9"
      >
        <span>{{ __('Person') }}</span>

        <button
          type="button"
          class="rounded-md px-2 py-1 text-xs font-normal text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9"
          @click.prevent.stop="startEdit('person')"
        >
          {{ personEditing ? __('Editing') : __('Edit') }}
        </button>
      </summary>

      <!-- VIEW -->
      <div
        v-if="!personEditing"
        class="space-y-4 px-5 pb-5"
      >
        <InfoRow
          :label="__('First Name')"
          :value="lead.first_name"
        />

        <InfoRow
          :label="__('Last Name')"
          :value="lead.last_name"
        />

        <InfoRow
          :label="__('Email')"
          :value="lead.email"
        />

        <InfoRow
          :label="__('Phone')"
          :value="lead.phone"
        />
      </div>

      <!-- EDIT -->
      <div
        v-else
        class="space-y-4 px-5 pb-5"
      >
        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('First Name') }} *
          </span>

          <input
            v-model="personForm.first_name"
            type="text"
            class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
          />
        </label>

        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Last Name') }}
          </span>

          <input
            v-model="personForm.last_name"
            type="text"
            class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
          />
        </label>

        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Email') }}
          </span>

          <input
            v-model="personForm.email"
            type="email"
            class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
          />
        </label>

        <label class="block space-y-1">
          <span class="text-xs text-ink-gray-5">
            {{ __('Phone') }}
          </span>

          <input
            v-model="personForm.phone"
            type="text"
            class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
          />
        </label>

        <p
          v-if="personError"
          class="rounded-md bg-red-50 px-3 py-2 text-xs text-red-600"
        >
          {{ personError }}
        </p>

        <div class="flex justify-end gap-2">
          <button
            type="button"
            class="rounded-lg border px-3 py-1.5 text-sm"
            :disabled="personSaving"
            @click="cancelEdit('person')"
          >
            {{ __('Cancel') }}
          </button>

          <button
            type="button"
            class="rounded-lg bg-gray-900 px-3 py-1.5 text-sm text-white disabled:opacity-50"
            :disabled="personSaving"
            @click="savePerson"
          >
            {{
              personSaving
                ? __('Saving...')
                : __('Save')
            }}
          </button>
        </div>
      </div>
    </details>

    <!-- CONVERSION -->
    <details
      v-if="isConverted"
      open
      class="border-b"
    >
      <summary
        class="cursor-pointer px-5 py-4 text-sm font-semibold text-ink-gray-9"
      >
        {{ __('Conversion') }}
      </summary>

      <div class="space-y-4 px-5 pb-5">

        <!-- CONTACT -->
        <LinkedRow
          :label="__('Contact')"
          :value="lead.converted_contact"
          :display-value="convertedLabels.contact"
          @open="openConvertedContact"
        />

        <!-- COMPANY -->
        <LinkedRow
          :label="__('Company')"
          :value="lead.converted_company"
          :display-value="convertedLabels.company"
          @open="openConvertedCompany"
        />

        <!-- DEAL -->
        <LinkedRow
          :label="__('Deal')"
          :value="lead.converted_deal"
          :display-value="convertedLabels.deal"
          @open="openConvertedDeal"
        />

        <InfoRow
          :label="__('Converted On')"
          :value="lead.converted_on"
        />
      </div>
    </details>

    <!-- NOTES -->
    <details
      v-if="lead.notes"
      class="border-b"
    >
      <summary
        class="cursor-pointer px-5 py-4 text-sm font-semibold text-ink-gray-9"
      >
        {{ __('Notes') }}
      </summary>

      <div
        class="whitespace-pre-wrap px-5 pb-5 text-sm text-ink-gray-7"
      >
        {{ lead.notes }}
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

const props = defineProps({
  lead: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits([
  'saved',
])

const router = useRouter()

const statuses = [
  'NEW',
  'CONTACTED',
  'NURTURE',
  'QUALIFIED',
  'CONVERTED',
  'UNQUALIFIED',
  'JUNK',
]

const sources = ref([])
const users = ref([])
const companies = ref([])

const detailsEditing = ref(false)
const personEditing = ref(false)

const detailsSaving = ref(false)
const personSaving = ref(false)

const detailsError = ref('')
const personError = ref('')

const detailsForm = reactive({
  company_name: '',
  source: '',
  status: 'NEW',
  lead_owner: '',
})

const personForm = reactive({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
})

const convertedLabels = reactive({
  contact: '',
  company: '',
  deal: '',
})

const isConverted = computed(() => {
  return (
    props.lead?.status === 'CONVERTED' ||
    Boolean(props.lead?.converted_contact) ||
    Boolean(props.lead?.converted_company) ||
    Boolean(props.lead?.converted_deal)
  )
})

function getApiError(e) {
  if (Array.isArray(e?._server_messages)) {
    return e._server_messages.join(', ')
  }

  if (Array.isArray(e?.messages)) {
    return e.messages.join(', ')
  }

  return (
    e?.message ||
    'Unable to update Lead.'
  )
}

function fillDetailsForm() {
  detailsForm.company_name =
    props.lead?.company_name || ''

  detailsForm.source =
    props.lead?.source || ''

  detailsForm.status =
    props.lead?.status || 'NEW'

  detailsForm.lead_owner =
    props.lead?.lead_owner || ''
}

function fillPersonForm() {
  personForm.first_name =
    props.lead?.first_name || ''

  personForm.last_name =
    props.lead?.last_name || ''

  personForm.email =
    props.lead?.email || ''

  personForm.phone =
    props.lead?.phone || ''
}

function startEdit(section) {
  if (section === 'details') {
    fillDetailsForm()
    detailsError.value = ''
    detailsEditing.value = true
    personEditing.value = false
  }

  if (section === 'person') {
    fillPersonForm()
    personError.value = ''
    personEditing.value = true
    detailsEditing.value = false
  }
}

function cancelEdit(section) {
  if (section === 'details') {
    detailsEditing.value = false
    detailsError.value = ''
    fillDetailsForm()
  }

  if (section === 'person') {
    personEditing.value = false
    personError.value = ''
    fillPersonForm()
  }
}

async function saveDetails() {
  if (
    !props.lead?.name ||
    detailsSaving.value
  ) {
    return
  }

  detailsError.value = ''

  if (!detailsForm.status) {
    detailsError.value =
      'Status is required.'

    return
  }

  detailsSaving.value = true

  try {
    const values = {
      company_name:
        detailsForm.company_name.trim() ||
        null,

      source:
        detailsForm.source ||
        null,

      status:
        detailsForm.status,

      lead_owner:
        detailsForm.lead_owner ||
        null,
    }

    const result = await call(
      'frappe.client.set_value',
      {
        doctype: 'DoubleT Lead',
        name: props.lead.name,
        fieldname: values,
      }
    )

    emit(
      'saved',
      result || values
    )

    detailsEditing.value = false

    toast.success(
      __('Lead details updated')
    )
  } catch (e) {
    console.error(
      'Save Lead details failed:',
      e
    )

    detailsError.value =
      getApiError(e)
  } finally {
    detailsSaving.value = false
  }
}

async function savePerson() {
  if (
    !props.lead?.name ||
    personSaving.value
  ) {
    return
  }

  personError.value = ''

  if (!personForm.first_name.trim()) {
    personError.value =
      'First Name is required.'

    return
  }

  if (
    personForm.email &&
    !String(
      personForm.email
    ).includes('@')
  ) {
    personError.value =
      'Please enter a valid email address.'

    return
  }

  personSaving.value = true

  try {
    const values = {
      first_name:
        personForm.first_name.trim(),

      last_name:
        personForm.last_name.trim() ||
        null,

      email:
        personForm.email.trim() ||
        null,

      phone:
        personForm.phone.trim() ||
        null,
    }

    const result = await call(
      'frappe.client.set_value',
      {
        doctype: 'DoubleT Lead',
        name: props.lead.name,
        fieldname: values,
      }
    )

    emit(
      'saved',
      result || values
    )

    personEditing.value = false

    toast.success(
      __('Person information updated')
    )
  } catch (e) {
    console.error(
      'Save Lead person failed:',
      e
    )

    personError.value =
      getApiError(e)
  } finally {
    personSaving.value = false
  }
}

/* =====================================================
 * LOAD CONVERTED RECORD LABELS
 * ===================================================== */

async function loadConvertedLabels() {
  convertedLabels.contact = ''
  convertedLabels.company = ''
  convertedLabels.deal = ''

  const tasks = []

  if (props.lead?.converted_contact) {
    tasks.push(
      call(
        'frappe.client.get',
        {
          doctype: 'DoubleT Contact',
          name:
            props.lead.converted_contact,
        }
      )
        .then(doc => {
          convertedLabels.contact =
            [
              doc.first_name,
              doc.last_name,
            ]
              .filter(Boolean)
              .join(' ') ||
            doc.name
        })
        .catch(() => {
          convertedLabels.contact =
            props.lead.converted_contact
        })
    )
  }

  if (props.lead?.converted_company) {
    tasks.push(
      call(
        'frappe.client.get',
        {
          doctype: 'DoubleT Company',
          name:
            props.lead.converted_company,
        }
      )
        .then(doc => {
          convertedLabels.company =
            doc.company_name ||
            doc.name
        })
        .catch(() => {
          convertedLabels.company =
            props.lead.converted_company
        })
    )
  }

  if (props.lead?.converted_deal) {
    tasks.push(
      call(
        'frappe.client.get',
        {
          doctype: 'DoubleT Deal',
          name:
            props.lead.converted_deal,
        }
      )
        .then(doc => {
          convertedLabels.deal =
            doc.deal_title ||
            doc.name
        })
        .catch(() => {
          convertedLabels.deal =
            props.lead.converted_deal
        })
    )
  }

  await Promise.all(tasks)
}

/* =====================================================
 * NAVIGATION
 * ===================================================== */

function openConvertedContact() {
  if (!props.lead?.converted_contact) {
    return
  }

  router.push({
    name: 'ContactDetail',
    params: {
      contactId:
        props.lead.converted_contact,
    },
  })
}

function openConvertedCompany() {
  if (!props.lead?.converted_company) {
    return
  }

  router.push({
    name: 'CompanyDetail',
    params: {
      companyId:
        props.lead.converted_company,
    },
  })
}

function openConvertedDeal() {
  if (!props.lead?.converted_deal) {
    return
  }

  router.push({
    name: 'DealDetail',
    params: {
      dealId:
        props.lead.converted_deal,
    },
  })
}

/* =====================================================
 * OPTIONS
 * ===================================================== */

async function loadSources() {
  try {
    const result = await call(
      'frappe.client.get_list',
      {
        doctype:
          'DoubleT Lead Source',

        fields: [
          'name',
          'source_name',
        ],

        filters: {
          is_active: 1,
        },

        order_by:
          'source_name asc',

        limit_page_length:
          200,
      }
    )

    sources.value =
      Array.isArray(result)
        ? result
        : []
  } catch (e) {
    console.error(
      'Load sources failed:',
      e
    )
  }
}


async function loadCompanies() {
  try {
    const result = await call(
      'frappe.client.get_list',
      {
        doctype: 'DoubleT Company',
        fields: [
          'name',
          'company_name',
        ],
        order_by: 'company_name asc',
        limit_page_length: 200,
      }
    )

    companies.value =
      Array.isArray(result)
        ? result
        : []
  } catch (e) {
    console.error(
      'Load companies failed:',
      e
    )
  }
}

async function loadUsers() {
  try {
    const result = await call(
      'frappe.client.get_list',
      {
        doctype: 'User',

        fields: [
          'name',
          'full_name',
        ],

        filters: {
          enabled: 1,
        },

        order_by:
          'full_name asc',

        limit_page_length:
          200,
      }
    )

    users.value =
      Array.isArray(result)
        ? result
        : []
  } catch (e) {
    console.error(
      'Load users failed:',
      e
    )
  }
}

watch(
  () => props.lead,
  () => {
    if (!detailsEditing.value) {
      fillDetailsForm()
    }

    if (!personEditing.value) {
      fillPersonForm()
    }

    loadConvertedLabels()
  },
  {
    deep: true,
    immediate: true,
  }
)

onMounted(() => {
  loadSources()
  loadUsers()
  loadCompanies()
})

/* =====================================================
 * DISPLAY ROW
 * ===================================================== */

const InfoRow = defineComponent({
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
            'grid grid-cols-[110px_minmax(0,1fr)] gap-3 text-sm',
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
                'break-words text-ink-gray-9',
            },
            props.value === null ||
              props.value === undefined ||
              props.value === ''
              ? '-'
              : String(props.value)
          ),
        ]
      )
  },
})

/* =====================================================
 * CLICKABLE LINK ROW
 * ===================================================== */

const LinkedRow = defineComponent({
  props: {
    label: String,
    value: String,
    displayValue: String,
  },

  emits: [
    'open',
  ],

  setup(props, { emit }) {
    return () =>
      h(
        'div',
        {
          class:
            'grid grid-cols-[110px_minmax(0,1fr)] gap-3 text-sm',
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
                    'min-w-0 break-words text-left font-medium text-blue-600 hover:underline',
                  onClick: () =>
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
