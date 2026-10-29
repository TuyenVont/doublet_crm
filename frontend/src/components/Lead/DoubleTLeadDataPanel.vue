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
            {{ __('Edit lead information directly.') }}
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

      <!-- ERROR -->
      <div
        v-if="error"
        class="mb-5 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600"
      >
        {{ error }}
      </div>

      <!-- LEAD INFORMATION -->
      <section class="rounded-xl border border-outline-gray-2 bg-white">
        <div class="border-b px-5 py-4">
          <h3 class="font-semibold text-ink-gray-9">
            {{ __('Lead Information') }}
          </h3>
        </div>

        <div class="grid grid-cols-1 gap-5 p-5 md:grid-cols-2">

          <!-- FIRST NAME -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('First Name') }} *
            </span>

            <input
              v-model="form.first_name"
              type="text"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <!-- LAST NAME -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Last Name') }}
            </span>

            <input
              v-model="form.last_name"
              type="text"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <!-- EMAIL -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Email') }}
            </span>

            <input
              v-model="form.email"
              type="email"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <!-- PHONE -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Phone') }}
            </span>

            <input
              v-model="form.phone"
              type="text"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <!-- COMPANY NAME -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Company Name') }}
            </span>

            <input
              v-model="form.company_name"
              type="text"
              list="doublet-lead-company-options"
              autocomplete="off"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
              :placeholder="__('Type a new company or choose an existing one')"
            />

            <datalist id="doublet-lead-company-options">
              <option
                v-for="item in companies"
                :key="item.name"
                :value="item.company_name || item.name"
              />
            </datalist>

            <p class="text-xs text-ink-gray-5">
              {{ __('You can select an existing company or enter a new company name.') }}
            </p>
          </label>

          <!-- SOURCE -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Source') }}
            </span>

            <select
              v-model="form.source"
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

          <!-- STATUS -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Status') }} *
            </span>

            <select
              v-model="form.status"
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

          <!-- OWNER -->
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Primary Owner') }}
            </span>

            <select
              v-model="form.lead_owner"
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

          <!-- NOTES -->
          <label class="space-y-1 md:col-span-2">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Notes') }}
            </span>

            <textarea
              v-model="form.notes"
              rows="5"
              class="w-full resize-y rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

        </div>
      </section>

      <!-- CONVERSION -->
      <section
        v-if="showConversion"
        class="mt-5 rounded-xl border border-outline-gray-2 bg-white"
      >
        <div class="border-b px-5 py-4">
          <div class="flex items-center justify-between">
            <h3 class="font-semibold text-ink-gray-9">
              {{ __('Conversion') }}
            </h3>

            <span class="text-xs text-ink-gray-5">
              {{ __('Read only') }}
            </span>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-5 p-5 md:grid-cols-2">

          <ReadOnlyField
            :label="__('Converted On')"
            :value="lead.converted_on"
          />

          <ReadOnlyField
            :label="__('Converted Contact')"
            :value="lead.converted_contact"
          />

          <ReadOnlyField
            :label="__('Converted Company')"
            :value="lead.converted_company"
          />

          <ReadOnlyField
            :label="__('Converted Deal')"
            :value="lead.converted_deal"
          />

        </div>
      </section>

    </div>
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

const saving = ref(false)
const error = ref('')

const sources = ref([])
const users = ref([])
const companies = ref([])

const statuses = [
  'NEW',
  'CONTACTED',
  'NURTURE',
  'QUALIFIED',
  'CONVERTED',
  'UNQUALIFIED',
  'JUNK',
]

const form = reactive({
  first_name: '',
  last_name: '',
  phone: '',
  email: '',
  company_name: '',
  source: '',
  status: 'NEW',
  lead_owner: '',
  notes: '',
})

const editableFields = [
  'first_name',
  'last_name',
  'phone',
  'email',
  'company_name',
  'source',
  'status',
  'lead_owner',
  'notes',
]

function fillForm() {
  for (const field of editableFields) {
    form[field] =
      props.lead?.[field] ??
      ''
  }

  if (!form.status) {
    form.status = 'NEW'
  }
}

const dirty = computed(() => {
  return editableFields.some(
    field =>
      String(form[field] ?? '') !==
      String(props.lead?.[field] ?? '')
  )
})

const showConversion = computed(() => {
  return Boolean(
    props.lead?.converted_on ||
    props.lead?.converted_contact ||
    props.lead?.converted_company ||
    props.lead?.converted_deal
  )
})

function getApiError(e) {
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
    'Unable to save Lead.'
  )
}

function resetForm() {
  error.value = ''
  fillForm()
}

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
      'Load Lead Sources failed:',
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
      'Load Companies failed:',
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
      'Load Users failed:',
      e
    )
  }
}

async function save() {
  if (
    !props.lead?.name ||
    saving.value
  ) {
    return
  }

  error.value = ''

  if (
    !form.first_name.trim()
  ) {
    error.value =
      'First Name is required.'

    return
  }

  if (
    !form.status
  ) {
    error.value =
      'Status is required.'

    return
  }

  if (
    form.email &&
    !String(form.email).includes('@')
  ) {
    error.value =
      'Please enter a valid email address.'

    return
  }

  saving.value = true

  try {
    const values = {
      first_name:
        form.first_name.trim(),

      last_name:
        form.last_name.trim() ||
        null,

      phone:
        form.phone.trim() ||
        null,

      email:
        form.email.trim() ||
        null,

      company_name:
        form.company_name.trim() ||
        null,

      source:
        form.source ||
        null,

      status:
        form.status,

      lead_owner:
        form.lead_owner ||
        null,

      notes:
        form.notes.trim() ||
        null,
    }

    const result = await call(
      'frappe.client.set_value',
      {
        doctype:
          'DoubleT Lead',

        name:
          props.lead.name,

        fieldname:
          values,
      }
    )

    emit(
      'saved',
      result || values
    )

    toast.success(
      __('Lead updated successfully')
    )

  } catch (e) {
    console.error(
      'Save Lead failed:',
      e
    )

    error.value =
      getApiError(e)

  } finally {
    saving.value = false
  }
}

watch(
  () => props.lead,
  () => {
    fillForm()
  },
  {
    immediate: true,
    deep: true,
  }
)

onMounted(() => {
  loadSources()
  loadUsers()
  loadCompanies()
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
          {},
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
                  'mt-1 break-words text-sm text-ink-gray-9',
              },
              props.value ||
                '-'
            ),
          ]
        )
    },
  })
</script>
