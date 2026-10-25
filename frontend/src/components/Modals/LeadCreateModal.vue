<template>
  <Dialog
    v-model:open="show"
    :title="__('Create Lead')"
    size="xl"
  >
    <template #default>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">

        <!-- First Name -->
        <FormControl
          v-model="lead.first_name"
          type="text"
          :label="__('First Name')"
          :placeholder="__('First Name')"
        />

        <!-- Last Name -->
        <FormControl
          v-model="lead.last_name"
          type="text"
          :label="__('Last Name')"
          :placeholder="__('Last Name')"
        />

        <!-- Email -->
        <FormControl
          v-model="lead.email"
          type="text"
          :label="__('Email')"
          :placeholder="__('Email')"
        />

        <!-- Phone -->
        <FormControl
          v-model="lead.phone"
          type="text"
          :label="__('Phone')"
          :placeholder="__('Phone')"
        />

        <!-- Company -->
        <FormControl
          v-model="lead.company_name"
          type="text"
          :label="__('Company Name')"
          :placeholder="__('Company Name')"
        />

        <!-- Source -->
        <div>
          <div class="mb-1.5 text-sm text-ink-gray-5">
            {{ __('Source') }}
          </div>

          <Link
            :value="lead.source"
            doctype="DoubleT Lead Source"
            :placeholder="__('Select Source')"
            @change="(value) => (lead.source = value)"
          />
        </div>

        <!-- Status -->
        <FormControl
          v-model="lead.status"
          type="select"
          :label="__('Status')"
          :options="statusOptions"
        />

        <!-- Owner -->
        <div>
          <div class="mb-1.5 text-sm text-ink-gray-5">
            {{ __('Lead Owner') }}
          </div>

          <Link
            :value="lead.lead_owner"
            doctype="User"
            :placeholder="__('Select Lead Owner')"
            @change="(value) => (lead.lead_owner = value)"
          />
        </div>

        <!-- Notes -->
        <FormControl
          v-model="lead.notes"
          class="md:col-span-2"
          type="textarea"
          :label="__('Notes')"
          :placeholder="__('Notes')"
        />
        <!-- Duplicate Warning -->
<div
  v-if="duplicateMatches.length"
  class="md:col-span-2 rounded-lg border border-orange-200 bg-orange-50 p-4"
>
  <div class="mb-3">
    <div class="font-medium text-orange-900">
      {{ __('Possible duplicate found') }}
    </div>

    <div class="mt-1 text-sm text-orange-700">
      {{
        __(
          'A Lead or Contact with the same email or phone already exists.'
        )
      }}
    </div>
  </div>

  <div class="space-y-2">
    <div
      v-for="item in duplicateMatches"
      :key="`${item.doctype}-${item.name}`"
      class="rounded-md border border-orange-200 bg-white p-3"
    >
      <div class="flex items-start justify-between gap-3">

        <div>
          <div class="font-medium text-ink-gray-9">
            {{
              item.full_name ||
              item.name
            }}
          </div>

          <div class="mt-1 text-xs text-ink-gray-5">
            {{ item.doctype }}
            ·
            {{ item.name }}
          </div>
        </div>

        <div
          class="rounded bg-orange-100 px-2 py-1 text-xs font-medium text-orange-700"
        >
          {{
            item.matched_by
              .join(' + ')
          }}
        </div>

      </div>

      <div class="mt-2 grid grid-cols-2 gap-2 text-sm">

        <div v-if="item.email">
          <span class="text-ink-gray-5">
            Email:
          </span>

          {{ item.email }}
        </div>

        <div v-if="item.phone">
          <span class="text-ink-gray-5">
            Phone:
          </span>

          {{ item.phone }}
        </div>

        <div v-if="item.company">
          <span class="text-ink-gray-5">
            Company:
          </span>

          {{ item.company }}
        </div>

        <div v-if="item.status">
          <span class="text-ink-gray-5">
            Status:
          </span>

          {{ item.status }}
        </div>

      </div>
    </div>
  </div>

  <div class="mt-3 text-sm text-orange-700">
    {{
      __(
        'Review the existing record before creating another Lead.'
      )
    }}
  </div>
</div>

        <!-- Error -->
        <ErrorMessage
          v-if="error"
          class="md:col-span-2"
          :message="error"
        />

      </div>
    </template>

    <template #actions>
  <div class="flex justify-end gap-2">

    <Button
      :label="__('Cancel')"
      @click="show = false"
    />

   <Button
  v-if="duplicateMatches.length"
  variant="solid"
  :label="__('Create Anyway')"
  :loading="insertLead.loading"
  @click="createLeadAnyway"
/>

    <Button
      v-else
      variant="solid"
      :label="__('Create')"
      :loading="
        insertLead.loading ||
        duplicateCheck.loading
      "
      @click="createLead"
    />

  </div>
</template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { sessionStore } from '@/stores/session'

import {
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  createResource,
} from 'frappe-ui'

import {
  reactive,
  ref,
  watch,
} from 'vue'

const show = defineModel({
  type: Boolean,
  default: false,
})

const emit = defineEmits([
  'created',
])

const session = sessionStore()

const error = ref('')
const duplicateMatches = ref([])

const statusOptions = [
  { label: 'NEW', value: 'NEW' },
  { label: 'CONTACTED', value: 'CONTACTED' },
  { label: 'NURTURE', value: 'NURTURE' },
  { label: 'QUALIFIED', value: 'QUALIFIED' },
  { label: 'UNQUALIFIED', value: 'UNQUALIFIED' },
  { label: 'JUNK', value: 'JUNK' },
]

function getEmptyLead() {
  return {
    first_name: '',
    last_name: '',
    phone: '',
    email: '',
    company_name: '',
    source: '',
    status: 'NEW',
    lead_owner:
      session.user || 'Administrator',
    notes: '',
  }
}

const lead = reactive(
  getEmptyLead()
)

function resetForm() {
  Object.assign(
    lead,
    getEmptyLead()
  )

  error.value = ''
  duplicateMatches.value = []
}
function validateLead() {
  if (!lead.first_name?.trim()) {
    return __('First Name is required')
  }

  const email = String(
    lead.email || ''
  )
    .trim()
    .toLowerCase()

  if (
    email &&
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  ) {
    return __('Invalid email address')
  }

  lead.email = email

  if (
    lead.phone &&
    isNaN(
      lead.phone.replace(
        /[-+() ]/g,
        ''
      )
    )
  ) {
    return __('Phone should be a number')
  }

  if (!lead.status) {
    return __('Status is required')
  }

  return null
}
const duplicateCheck = createResource({
  url:
    'doublet_crm.doublet_crm.doctype.doublet_lead.doublet_lead.check_duplicate_lead',
})
const insertLead = createResource({
  url: 'frappe.client.insert',
})

function createLead() {
  error.value = ''
  duplicateMatches.value = []

  const validationError =
    validateLead()

  if (validationError) {
    error.value = validationError
    return
  }

  const email =
    lead.email?.trim() || ''

  const phone =
    lead.phone?.trim() || ''

  // Không có email và phone thì tạo luôn
  if (!email && !phone) {
    insertLeadNow()
    return
  }

  duplicateCheck.submit(
    {
      email,
      phone,
    },
    {
      onSuccess(data) {
        const result =
          data?.message || data

        const matches =
          result?.matches || []

        if (matches.length) {
          duplicateMatches.value =
            matches
          return
        }

        insertLeadNow()
      },

      onError(err) {
        error.value =
          err?.message ||
          __(
            'Unable to check duplicate Lead'
          )
      },
    }
  )
}

function createLeadAnyway() {
  duplicateMatches.value = []
  insertLeadNow()
}

function insertLeadNow() {
  error.value = ''

  insertLead.submit(
    {
      doc: {
        doctype:
          'DoubleT Lead',

        first_name:
          lead.first_name.trim(),

        last_name:
          lead.last_name?.trim(),

        phone:
          lead.phone?.trim(),

        email:
          lead.email?.trim(),

        company_name:
          lead.company_name?.trim(),

        source:
          lead.source || null,

        status:
          lead.status,

        lead_owner:
          lead.lead_owner || null,

        notes:
          lead.notes?.trim(),
      },
    },

    {
      onSuccess(doc) {
        emit(
          'created',
          doc
        )

        show.value = false
        resetForm()
      },

      onError(err) {
        if (
          err?.messages?.length
        ) {
          error.value =
            err.messages.join('\n')
          return
        }

        if (
          err?.error?.messages?.length
        ) {
          error.value =
            err.error.messages.join(
              '\n'
            )
          return
        }

        error.value =
          err?.message ||
          __(
            'Unable to create Lead'
          )
      },
    }
  )
}
watch(
  [
    () => lead.email,
    () => lead.phone,
  ],
  () => {
    duplicateMatches.value = []
  }
)

watch(
  show,
  (value) => {
    if (value) {
      resetForm()
    }
  }
)
</script>
