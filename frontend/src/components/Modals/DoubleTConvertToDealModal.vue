<template>
  <Dialog
    v-model:open="show"
    :title="__('Convert Lead')"
    size="xl"
  >
    <template #default>
      <div class="space-y-5">

        <!-- CONTACT -->
        <div>
          <div class="mb-2 text-sm font-medium text-ink-gray-8">
            {{ __('Contact') }}
          </div>

          <div class="mb-3 flex items-center justify-between">
            <span class="text-sm text-ink-gray-6">
              {{ __('Use existing Contact') }}
            </span>

            <Switch v-model="useExistingContact" />
          </div>

          <Link
            v-if="useExistingContact"
            :value="existingContact"
            doctype="DoubleT Contact"
            :placeholder="__('Select existing Contact')"
            @change="(value) => (existingContact = value)"
          />

          <div
            v-else
            class="rounded-md bg-surface-gray-2 p-3 text-sm text-ink-gray-6"
          >
            {{
              __(
                'A new Contact will be created using this Lead information.'
              )
            }}
          </div>
        </div>

        <!-- COMPANY -->
        <div class="border-t border-outline-gray-2 pt-5">
          <div class="mb-2 text-sm font-medium text-ink-gray-8">
            {{ __('Company') }}
          </div>

          <FormControl
            v-model="companyMode"
            type="select"
            :label="__('Company option')"
            :options="companyOptions"
          />

          <Link
            v-if="companyMode === 'existing'"
            class="mt-3"
            :value="existingCompany"
            doctype="DoubleT Company"
            :placeholder="__('Select existing Company')"
            @change="(value) => (existingCompany = value)"
          />

          <FormControl
            v-if="companyMode === 'new'"
            v-model="companyName"
            class="mt-3"
            type="text"
            :label="__('Company Name')"
            :placeholder="__('Company Name')"
          />
        </div>

        <!-- DEAL -->
        <div class="border-t border-outline-gray-2 pt-5">
          <div class="mb-2 text-sm font-medium text-ink-gray-8">
            {{ __('Deal') }}
          </div>

          <FormControl
            v-model="dealTitle"
            type="text"
            :label="__('Deal Title')"
            :placeholder="__('Deal Title')"
          />

          <div class="mt-3">
            <div class="mb-1.5 text-sm text-ink-gray-5">
              {{ __('Stage') }}
            </div>

            <Link
              :value="stage"
              doctype="DoubleT Deal Stage"
              :placeholder="__('Select Stage')"
              @change="(value) => (stage = value)"
            />
          </div>

          <FormControl
            v-model="amount"
            class="mt-3"
            type="number"
            :label="__('Amount')"
            :placeholder="__('0')"
          />
        </div>

        <!-- SUMMARY -->
        <div class="rounded-md border border-outline-gray-2 p-3">
          <div class="mb-2 text-sm font-medium text-ink-gray-8">
            {{ __('Conversion Summary') }}
          </div>

          <div class="space-y-1 text-sm text-ink-gray-6">
            <div>
              {{ __('Lead') }}:
              <span class="font-medium text-ink-gray-8">
                {{ leadDisplayName }}
              </span>
            </div>

            <div>
              {{ __('Contact') }}:
              <span class="font-medium text-ink-gray-8">
                {{
                  useExistingContact
                    ? existingContact || __('Not selected')
                    : __('Create new')
                }}
              </span>
            </div>

            <div>
              {{ __('Company') }}:
              <span class="font-medium text-ink-gray-8">
                {{ companySummary }}
              </span>
            </div>

            <div>
              {{ __('Deal') }}:
              <span class="font-medium text-ink-gray-8">
                {{ dealTitle || __('Not entered') }}
              </span>
            </div>
          </div>
        </div>

        <ErrorMessage
          v-if="error"
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
          variant="solid"
          :label="__('Convert')"
          :loading="convertResource.loading"
          @click="convertLead"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'

import {
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  Switch,
  call as frappeCall,
  createResource,
} from 'frappe-ui'

import {
  computed,
  onMounted,
  ref,
  watch,
} from 'vue'

const props = defineProps({
  lead: {
    type: Object,
    required: true,
  },
})

const show = defineModel({
  type: Boolean,
  default: false,
})

const emit = defineEmits([
  'converted',
])

const useExistingContact = ref(false)
const existingContact = ref('')

const companyMode = ref('none')
const existingCompany = ref('')
const companyName = ref('')

const dealTitle = ref('')
const stage = ref('')
const amount = ref(0)

const error = ref('')
const companies = ref([])

const companyOptions = [
  {
    label: 'No Company',
    value: 'none',
  },
  {
    label: 'Use Existing Company',
    value: 'existing',
  },
  {
    label: 'Create New Company',
    value: 'new',
  },
]

const leadDisplayName = computed(() => {
  return (
    [
      props.lead?.first_name,
      props.lead?.last_name,
    ]
      .filter(Boolean)
      .join(' ') ||
    props.lead?.name ||
    ''
  )
})

const companySummary = computed(() => {
  if (companyMode.value === 'existing') {
    return (
      existingCompany.value ||
      __('Not selected')
    )
  }

  if (companyMode.value === 'new') {
    return (
      companyName.value ||
      __('Not entered')
    )
  }

  return __('No Company')
})

const convertResource = createResource({
  url:
    'doublet_crm.doublet_crm.doctype.doublet_lead.doublet_lead.convert_lead',
})

async function loadCompanies() {
  try {
    const result = await frappeCall(
      'frappe.client.get_list',
      {
        doctype: 'DoubleT Company',
        fields: ['name', 'company_name'],
        order_by: 'company_name asc',
        limit_page_length: 200,
      }
    )

    companies.value = Array.isArray(result)
      ? result
      : []
  } catch (e) {
    console.error('Load Companies failed:', e)
    companies.value = []
  }
}

function applyLeadCompanyDefault() {
  const leadCompany = String(
    props.lead?.company_name || ''
  ).trim()

  if (!leadCompany) {
    companyMode.value = 'none'
    existingCompany.value = ''
    companyName.value = ''
    return
  }

  const matched = companies.value.find(
    item =>
      String(
        item.company_name || item.name || ''
      ).trim().toLowerCase() ===
      leadCompany.toLowerCase()
  )

  if (matched) {
    companyMode.value = 'existing'
    existingCompany.value = matched.name
    companyName.value = ''
    return
  }

  companyMode.value = 'new'
  existingCompany.value = ''
  companyName.value = leadCompany
}

function resetForm() {
  useExistingContact.value = false
  existingContact.value = ''

  applyLeadCompanyDefault()

  dealTitle.value =
    props.lead?.company_name
      ? `${props.lead.company_name} Deal`
      : leadDisplayName.value
        ? `${leadDisplayName.value} Deal`
        : ''

  stage.value = ''
  amount.value = 0

  error.value = ''
}

function validateForm() {
  if (
    useExistingContact.value &&
    !existingContact.value
  ) {
    return __(
      'Please select an existing Contact'
    )
  }

  if (
    companyMode.value === 'existing' &&
    !existingCompany.value
  ) {
    return __(
      'Please select an existing Company'
    )
  }

  if (
    companyMode.value === 'new' &&
    !companyName.value?.trim()
  ) {
    return __(
      'Company Name is required'
    )
  }

  if (!dealTitle.value?.trim()) {
    return __(
      'Deal Title is required'
    )
  }

  if (!stage.value) {
    return __(
      'Deal Stage is required'
    )
  }

  return null
}

function convertLead() {
  error.value = ''

  const validationError =
    validateForm()

  if (validationError) {
    error.value = validationError
    return
  }

  convertResource.submit(
    {
      lead_name:
        props.lead.name,

      existing_contact:
        useExistingContact.value
          ? existingContact.value
          : '',

      existing_company:
        companyMode.value === 'existing'
          ? existingCompany.value
          : '',

      create_company:
        companyMode.value === 'new'
          ? 1
          : 0,

      company_name:
        companyMode.value === 'new'
          ? companyName.value.trim()
          : '',

      create_deal: 1,

      deal_title:
        dealTitle.value.trim(),

      stage:
        stage.value,

      amount:
        Number(amount.value || 0),
    },

    {
      onSuccess(data) {
        const result =
          data?.message || data

        show.value = false

        emit(
          'converted',
          result
        )

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
            err.error.messages.join('\n')
          return
        }

        error.value =
          err?.message ||
          __(
            'Unable to convert Lead'
          )
      },
    }
  )
}

watch(
  useExistingContact,
  (value) => {
    if (!value) {
      existingContact.value = ''
    }
  }
)

watch(
  companyMode,
  (value) => {
    if (value !== 'existing') {
      existingCompany.value = ''
    }

    if (value !== 'new') {
      companyName.value = ''
    }
  }
)

onMounted(async () => {
  await loadCompanies()

  if (show.value) {
    resetForm()
  }
})

watch(
  show,
  (value) => {
    if (value) {
      resetForm()
    }
  }
)
</script>