<template>
  <div class="flex-1 overflow-y-auto bg-white p-6">
    <div class="mx-auto max-w-5xl">
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-ink-gray-9">{{ __('Data') }}</h2>
          <p class="mt-1 text-sm text-ink-gray-5">{{ __('Edit contact information directly.') }}</p>
        </div>

        <div class="flex items-center gap-2">
          <button
            v-if="dirty && !isNew"
            type="button"
            class="rounded-lg border border-outline-gray-2 px-4 py-2 text-sm"
            :disabled="saving"
            @click="resetForm"
          >
            {{ __('Cancel') }}
          </button>

          <button
            type="button"
            class="rounded-lg bg-gray-900 px-4 py-2 text-sm text-white disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="saving || (!isNew && !dirty)"
            @click="save(false)"
          >
            {{ saving ? __('Saving...') : isNew ? __('Create Contact') : __('Save') }}
          </button>
        </div>
      </div>

      <div
        v-if="error"
        class="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
      >
        {{ error }}
      </div>

      <div
        v-if="duplicates.length"
        class="mb-5 rounded-xl border border-orange-200 bg-orange-50 p-4"
      >
        <div class="font-semibold text-orange-900">{{ __('Possible duplicate contact found') }}</div>
        <div class="mt-1 text-sm text-orange-800">
          {{ __('A contact with the same email or phone already exists. Review it before creating another record.') }}
        </div>

        <div class="mt-3 space-y-2">
          <div
            v-for="item in duplicates"
            :key="item.name"
            class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-orange-200 bg-white px-3 py-2"
          >
            <div class="min-w-0">
              <div class="font-medium text-ink-gray-9">{{ contactLabel(item) }}</div>
              <div class="mt-0.5 text-xs text-ink-gray-5">
                {{ [item.email, item.phone].filter(Boolean).join(' · ') || item.name }}
              </div>
            </div>

            <button
              type="button"
              class="rounded-lg border border-outline-gray-2 bg-white px-3 py-1.5 text-sm text-blue-600 hover:bg-surface-gray-1"
              @click="openDuplicate(item.name)"
            >
              {{ __('Open existing') }}
            </button>
          </div>
        </div>

        <div class="mt-3 flex justify-end">
          <button
            type="button"
            class="rounded-lg border border-orange-300 bg-white px-3 py-1.5 text-sm font-medium text-orange-800"
            :disabled="saving"
            @click="save(true)"
          >
            {{ isNew ? __('Create anyway') : __('Save anyway') }}
          </button>
        </div>
      </div>

      <section class="rounded-xl border border-outline-gray-2 bg-white">
        <div class="border-b px-5 py-4">
          <h3 class="font-semibold text-ink-gray-9">{{ __('Contact Information') }}</h3>
        </div>

        <div class="grid grid-cols-1 gap-5 p-5 md:grid-cols-2">
          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">{{ __('First Name') }} *</span>
            <input
              v-model="form.first_name"
              type="text"
              maxlength="140"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">{{ __('Last Name') }}</span>
            <input
              v-model="form.last_name"
              type="text"
              maxlength="140"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">{{ __('Email') }}</span>
            <input
              v-model="form.email"
              type="email"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
              @input="clearDuplicateWarning"
            />
          </label>

          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">{{ __('Phone') }}</span>
            <input
              v-model="form.phone"
              type="text"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
              @input="clearDuplicateWarning"
            />
          </label>

          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">{{ __('Birthday') }}</span>
            <input
              v-model="form.birthday"
              type="date"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">{{ __('Job Title') }}</span>
            <input
              v-model="form.job_title"
              type="text"
              maxlength="140"
              class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            />
          </label>

          <div class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">{{ __('Source') }}</span>
            <Link
              :value="form.source"
              doctype="DoubleT Lead Source"
              :placeholder="__('Select Source')"
              @change="value => (form.source = value || '')"
            />
          </div>

          <div class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">{{ __('Primary Owner') }}</span>
            <Link
              :value="form.contact_owner"
              doctype="User"
              :hide-me="true"
              :placeholder="__('Select Primary Owner')"
              @change="value => (form.contact_owner = value || '')"
            />
          </div>
        </div>
      </section>

      <section class="mt-5 rounded-xl border border-outline-gray-2 bg-white">
        <div class="border-b px-5 py-4">
          <h3 class="font-semibold text-ink-gray-9">{{ __('Organization') }}</h3>
        </div>

        <div class="grid grid-cols-1 gap-5 p-5 md:grid-cols-2">
          <div class="space-y-1 md:col-span-2">
            <span class="text-sm font-medium text-ink-gray-8">{{ __('Company') }}</span>
            <Link
              :value="form.company"
              doctype="DoubleT Company"
              :placeholder="__('Select Company')"
              @change="value => (form.company = value || '')"
            />
          </div>

          <label class="space-y-1 md:col-span-2">
            <span class="text-sm font-medium text-ink-gray-8">{{ __('Address') }}</span>
            <textarea
              v-model="form.address"
              rows="3"
              class="w-full resize-y rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
              :placeholder="__('Street, city, province/state, country...')"
            />
          </label>
        </div>
      </section>

      <section class="mt-5 rounded-xl border border-outline-gray-2 bg-white">
        <div class="border-b px-5 py-4">
          <h3 class="font-semibold text-ink-gray-9">{{ __('Notes') }}</h3>
        </div>

        <div class="p-5">
          <textarea
            v-model="form.notes"
            rows="5"
            class="w-full resize-y rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
            :placeholder="__('Add internal notes about this contact...')"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { call, toast } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'

const props = defineProps({
  contact: { type: Object, default: null },
  isNew: { type: Boolean, default: false },
})

const emit = defineEmits(['saved'])
const router = useRouter()

const saving = ref(false)
const error = ref('')
const duplicates = ref([])

const fields = [
  'first_name',
  'last_name',
  'email',
  'phone',
  'birthday',
  'job_title',
  'source',
  'contact_owner',
  'company',
  'address',
  'notes',
]

const form = reactive(Object.fromEntries(fields.map(field => [field, ''])))

function normalize(value) {
  return value === null || value === undefined ? '' : String(value)
}

function fillForm() {
  for (const field of fields) {
    form[field] = props.contact?.[field] ?? ''
  }
  form.birthday = props.contact?.birthday?.slice?.(0, 10) || props.contact?.birthday || ''
}

const dirty = computed(() => {
  if (props.isNew) return true
  return fields.some(field => normalize(form[field]) !== normalize(props.contact?.[field]))
})

function apiError(e) {
  return e?.messages?.join?.('; ') || e?._server_messages?.join?.('; ') || e?.message || __('Unable to save Contact.')
}

function resetForm() {
  error.value = ''
  duplicates.value = []
  fillForm()
}

function clearDuplicateWarning() {
  duplicates.value = []
}

function contactLabel(item) {
  return [item.first_name, item.last_name].filter(Boolean).join(' ') || item.name
}

function openDuplicate(name) {
  router.push({ name: 'ContactDetail', params: { contactId: name } })
}

function duplicateFilters() {
  const clauses = []
  if (form.email?.trim()) clauses.push(['email', '=', form.email.trim()])
  if (form.phone?.trim()) clauses.push(['phone', '=', form.phone.trim()])
  return clauses
}

async function checkDuplicates() {
  const clauses = duplicateFilters()
  if (!clauses.length) {
    duplicates.value = []
    return []
  }

  const found = []
  for (const clause of clauses) {
    try {
      const rows = await call('frappe.client.get_list', {
        doctype: 'DoubleT Contact',
        filters: [clause],
        fields: ['name', 'first_name', 'last_name', 'email', 'phone', 'company'],
        limit_page_length: 20,
      })
      for (const row of rows || []) {
        if (!props.isNew && row.name === props.contact?.name) continue
        if (!found.some(item => item.name === row.name)) found.push(row)
      }
    } catch (e) {
      console.error('Duplicate check failed:', e)
    }
  }

  duplicates.value = found
  return found
}

async function save(force = false) {
  if (saving.value) return
  error.value = ''

  if (!form.first_name.trim()) {
    error.value = __('First Name is required.')
    return
  }

  if (!force) {
    const found = await checkDuplicates()
    if (found.length) return
  }

  saving.value = true

  try {
    const values = Object.fromEntries(
      fields.map(field => [field, form[field] === '' ? null : form[field]])
    )
    values.first_name = form.first_name.trim()
    values.last_name = form.last_name?.trim() || null
    values.email = form.email?.trim() || null
    values.phone = form.phone?.trim() || null
    values.job_title = form.job_title?.trim() || null

    let result
    if (props.isNew) {
      result = await call('frappe.client.insert', {
        doc: { doctype: 'DoubleT Contact', ...values },
      })
      toast.success(__('Contact created successfully'))
    } else {
      result = await call('frappe.client.set_value', {
        doctype: 'DoubleT Contact',
        name: props.contact.name,
        fieldname: values,
      })
      toast.success(__('Contact updated successfully'))
    }

    duplicates.value = []
    emit('saved', result || values)
  } catch (e) {
    console.error('Save Contact failed:', e)
    error.value = apiError(e)
  } finally {
    saving.value = false
  }
}

watch(
  () => props.contact,
  () => {
    fillForm()
    duplicates.value = []
  },
  { immediate: true, deep: true },
)
</script>
