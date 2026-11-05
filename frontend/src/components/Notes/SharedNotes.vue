<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-y-auto p-5">
    <div class="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <div class="flex items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-semibold text-ink-gray-9">{{ __('Notes') }}</h2>
          <p class="mt-1 text-sm text-ink-gray-5">
            {{ management ? __('Manage notes across CRM records.') : __('Keep notes related to this record.') }}
          </p>
        </div>
        <Button
          :label="__('Add Note')"
          icon-left="plus"
          variant="solid"
          :disabled="(!management && !referenceName) || saving"
          @click="startCreate"
        />
      </div>

      <div v-if="management" class="flex flex-wrap gap-2 rounded-lg border border-outline-gray-2 p-3">
        <input
          v-model="search"
          type="search"
          :placeholder="__('Search notes...')"
          class="min-w-52 flex-1 rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm"
          @keyup.enter="loadNotes"
        />
        <select
          v-model="referenceFilter"
          class="rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm"
          @change="loadNotes"
        >
          <option value="">{{ __('All record types') }}</option>
          <option v-for="doctype in referenceDoctypes" :key="doctype" :value="doctype">
            {{ doctype.replace('DoubleT ', '') }}
          </option>
        </select>
        <Button :label="__('Search')" variant="subtle" :loading="loading" @click="loadNotes" />
      </div>

      <form
        v-if="showEditor"
        class="rounded-lg border border-outline-gray-2 bg-surface-white p-4"
        @submit.prevent="saveNote"
      >
        <div class="mb-4 flex items-center justify-between gap-3">
          <h3 class="font-semibold text-ink-gray-9">
            {{ editingName ? __('Edit Note') : __('New Note') }}
          </h3>
          <Button type="button" variant="ghost" icon="x" :disabled="saving" @click="closeEditor" />
        </div>

        <div v-if="management" class="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-ink-gray-7">
              {{ __('Related Type') }} *
            </span>
            <select
              v-model="form.reference_doctype"
              class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm"
              @change="onReferenceDoctypeChange"
            >
              <option value="">{{ __('Select type') }}</option>
              <option v-for="doctype in referenceDoctypes" :key="doctype" :value="doctype">
                {{ doctype.replace('DoubleT ', '') }}
              </option>
            </select>
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-ink-gray-7">
              {{ __('Related Record') }} *
            </span>
            <select
              v-model="form.reference_name"
              class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm"
              :disabled="!form.reference_doctype || referencesLoading"
            >
              <option value="">
                {{ referencesLoading ? __('Loading...') : __('Select record') }}
              </option>
              <option v-for="record in referenceOptions" :key="record.name" :value="record.name">
                {{ record.label }}
              </option>
            </select>
          </label>
        </div>

        <label class="block">
          <span class="mb-1 block text-sm font-medium text-ink-gray-7">
            {{ __('Title') }} *
          </span>
          <input
            v-model="form.title"
            type="text"
            maxlength="140"
            class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9"
          />
        </label>

        <label class="mt-4 block">
          <span class="mb-1 block text-sm font-medium text-ink-gray-7">
            {{ __('Content') }}
          </span>
          <textarea
            v-model="form.content"
            rows="6"
            class="w-full resize-y rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9"
          />
        </label>

        <p v-if="actionError" role="alert" class="mt-3 text-sm text-red-600">
          {{ actionError }}
        </p>

        <div class="mt-4 flex justify-end gap-2">
          <Button
            type="button"
            :label="__('Cancel')"
            variant="subtle"
            :disabled="saving"
            @click="closeEditor"
          />
          <Button
            type="submit"
            :label="editingName ? __('Save') : __('Create')"
            variant="solid"
            :loading="saving"
          />
        </div>
      </form>

      <p
        v-if="actionError && !showEditor"
        role="alert"
        class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
      >
        {{ actionError }}
      </p>

      <div
        v-if="loadError"
        role="alert"
        class="flex items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
      >
        <span>{{ loadError }}</span>
        <Button :label="__('Retry')" variant="subtle" @click="loadNotes" />
      </div>

      <div v-if="loading" class="flex min-h-40 items-center justify-center text-sm text-ink-gray-5">
        {{ __('Loading Notes...') }}
      </div>

      <div
        v-else-if="!loadError && !notes.length"
        class="flex min-h-40 flex-col items-center justify-center rounded-lg border border-dashed border-outline-gray-2 text-center"
      >
        <div class="font-medium text-ink-gray-8">{{ __('No Notes Found') }}</div>
        <p class="mt-1 text-sm text-ink-gray-5">{{ __('Add a note to this record.') }}</p>
      </div>

      <div v-else-if="notes.length" class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <article
          v-for="note in notes"
          :key="note.name"
          class="rounded-lg border border-outline-gray-2 bg-surface-white p-4"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h3 class="truncate font-semibold text-ink-gray-9">{{ note.title }}</h3>
              <p class="mt-1 text-xs text-ink-gray-5">{{ formatDate(note.modified) }}</p>
            </div>
            <div class="flex shrink-0 gap-1">
              <Button variant="ghost" icon="edit-3" :disabled="saving" @click="startEdit(note)" />
              <Button
                variant="ghost"
                icon="trash-2"
                :loading="deletingName === note.name"
                :disabled="saving || Boolean(deletingName)"
                @click="deleteNote(note)"
              />
            </div>
          </div>
          <button
            v-if="management"
            type="button"
            class="mt-2 text-left text-xs font-medium text-blue-600 hover:underline"
            @click="openReference(note)"
          >
            {{ note.reference_doctype.replace('DoubleT ', '') }} · {{ note.reference_label || note.reference_name }}
          </button>
          <p class="mt-3 whitespace-pre-wrap break-words text-sm text-ink-gray-7">
            {{ note.content || __('No content') }}
          </p>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, call } from 'frappe-ui'

const props = defineProps({
  management: { type: Boolean, default: false },
  referenceDoctype: { type: String, default: '' },
  referenceName: { type: String, default: '' },
})

const router = useRouter()
const referenceDoctypes = ['DoubleT Lead', 'DoubleT Deal', 'DoubleT Contact', 'DoubleT Company']
const referenceRoutes = {
  'DoubleT Lead': ['LeadDetail', 'leadId'],
  'DoubleT Deal': ['DealDetail', 'dealId'],
  'DoubleT Contact': ['ContactDetail', 'contactId'],
  'DoubleT Company': ['CompanyDetail', 'companyId'],
}
const referenceLabelFields = {
  'DoubleT Lead': 'first_name',
  'DoubleT Deal': 'deal_title',
  'DoubleT Contact': 'first_name',
  'DoubleT Company': 'company_name',
}

const notes = ref([])
const loading = ref(false)
const loadError = ref('')
const actionError = ref('')
const showEditor = ref(false)
const editingName = ref('')
const saving = ref(false)
const deletingName = ref('')
const search = ref('')
const referenceFilter = ref('')
const referenceOptions = ref([])
const referencesLoading = ref(false)
const form = reactive({ title: '', content: '', reference_doctype: '', reference_name: '' })
let requestSerial = 0
let referenceRequestSerial = 0

function apiError(error) {
  return error?.messages?.join?.('; ')
    || error?._server_messages?.join?.('; ')
    || error?.message
    || __('Request failed')
}

function isCurrent(doctype, name) {
  if (props.management) return true
  return props.referenceDoctype === doctype && props.referenceName === name
}

function closeEditor() {
  if (saving.value) return
  showEditor.value = false
  editingName.value = ''
  actionError.value = ''
  form.title = ''
  form.content = ''
  form.reference_doctype = ''
  form.reference_name = ''
}

function startCreate() {
  editingName.value = ''
  form.title = ''
  form.content = ''
  form.reference_doctype = props.management ? (referenceFilter.value || 'DoubleT Lead') : props.referenceDoctype
  form.reference_name = props.management ? '' : props.referenceName
  actionError.value = ''
  showEditor.value = true
  if (props.management) loadReferenceOptions()
}

function startEdit(note) {
  editingName.value = note.name
  form.title = note.title || ''
  form.content = note.content || ''
  form.reference_doctype = note.reference_doctype || ''
  form.reference_name = note.reference_name || ''
  actionError.value = ''
  showEditor.value = true
  if (props.management) loadReferenceOptions(true)
}

async function loadNotes() {
  const serial = ++requestSerial
  const doctype = props.referenceDoctype
  const name = props.referenceName
  notes.value = []
  loadError.value = ''

  if (!props.management && (!doctype || !name)) {
    loading.value = false
    return
  }

  loading.value = true
  try {
    const result = props.management
      ? await call('doublet_crm.api.get_notes', {
          search: search.value.trim() || null,
          reference_doctype: referenceFilter.value || null,
        })
      : await call('doublet_crm.api.get_linked_notes', { doctype, docname: name })
    if (serial === requestSerial && isCurrent(doctype, name)) {
      notes.value = result || []
    }
  } catch (error) {
    if (serial === requestSerial && isCurrent(doctype, name)) {
      loadError.value = apiError(error)
    }
  } finally {
    if (serial === requestSerial && isCurrent(doctype, name)) {
      loading.value = false
    }
  }
}

async function saveNote() {
  const title = form.title.trim()
  if (!title) {
    actionError.value = __('Title is required')
    return
  }

  const doctype = props.management ? form.reference_doctype : props.referenceDoctype
  const name = props.management ? form.reference_name : props.referenceName
  if (!doctype || !name) {
    actionError.value = __('Related type and record are required')
    return
  }
  const noteName = editingName.value
  saving.value = true
  actionError.value = ''

  try {
    if (noteName) {
      await call('frappe.client.set_value', {
        doctype: 'DoubleT Note',
        name: noteName,
        fieldname: {
          title,
          content: form.content,
          ...(props.management ? { reference_doctype: doctype, reference_name: name } : {}),
        },
      })
    } else {
      await call('frappe.client.insert', {
        doc: {
          doctype: 'DoubleT Note',
          title,
          content: form.content,
          reference_doctype: doctype,
          reference_name: name,
        },
      })
    }

    if (isCurrent(doctype, name)) {
      showEditor.value = false
      editingName.value = ''
      form.title = ''
      form.content = ''
      form.reference_doctype = ''
      form.reference_name = ''
      await loadNotes()
    }
  } catch (error) {
    if (isCurrent(doctype, name)) actionError.value = apiError(error)
  } finally {
    saving.value = false
  }
}

async function deleteNote(note) {
  if (!window.confirm(__('Delete this note?'))) return

  const doctype = props.referenceDoctype
  const name = props.referenceName
  deletingName.value = note.name
  actionError.value = ''

  try {
    await call('frappe.client.delete', { doctype: 'DoubleT Note', name: note.name })
    if (isCurrent(doctype, name)) await loadNotes()
  } catch (error) {
    if (isCurrent(doctype, name)) actionError.value = apiError(error)
  } finally {
    deletingName.value = ''
  }
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(String(value).replace(' ', 'T'))
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

async function loadReferenceOptions(preserveSelection = false) {
  const serial = ++referenceRequestSerial
  const doctype = form.reference_doctype
  const selected = preserveSelection ? form.reference_name : ''
  referenceOptions.value = []
  if (!preserveSelection) form.reference_name = ''
  if (!doctype) return

  referencesLoading.value = true
  try {
    const labelField = referenceLabelFields[doctype]
    const result = await call('frappe.client.get_list', {
      doctype,
      fields: ['name', labelField],
      order_by: 'modified desc',
      limit_page_length: 500,
    })
    if (serial !== referenceRequestSerial || form.reference_doctype !== doctype) return
    referenceOptions.value = (result || []).map((record) => ({
      name: record.name,
      label: `${record[labelField] || record.name} (${record.name})`,
    }))
    if (selected) {
      form.reference_name = selected
      if (!referenceOptions.value.some((record) => record.name === selected)) {
        referenceOptions.value.unshift({ name: selected, label: selected })
      }
    }
  } catch (error) {
    if (serial === referenceRequestSerial) actionError.value = apiError(error)
  } finally {
    if (serial === referenceRequestSerial) referencesLoading.value = false
  }
}

function onReferenceDoctypeChange() {
  loadReferenceOptions()
}

function openReference(note) {
  const target = referenceRoutes[note.reference_doctype]
  if (!target || !note.reference_name) return
  router.push({ name: target[0], params: { [target[1]]: note.reference_name } })
}

watch(
  () => [props.management, props.referenceDoctype, props.referenceName],
  () => {
    requestSerial += 1
    notes.value = []
    loading.value = false
    loadError.value = ''
    showEditor.value = false
    editingName.value = ''
    actionError.value = ''
    form.title = ''
    form.content = ''
    form.reference_doctype = ''
    form.reference_name = ''
    loadNotes()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  requestSerial += 1
})
</script>
