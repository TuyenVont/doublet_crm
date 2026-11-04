
<template>
  <Dialog
    v-model:open="show"
    :title="editingName ? __('Edit Task') : __('Create Task')"
    size="xl"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="form.title"
          type="text"
          :label="__('Title')"
          :placeholder="__('What needs to be done?')"
          required
        />

        <FormControl
          v-model="form.description"
          type="textarea"
          :label="__('Description')"
          :placeholder="__('Add more details about this task...')"
        />

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <FormControl
            v-model="form.status"
            type="select"
            :label="__('Status')"
            :options="statusOptions"
          />

          <FormControl
            v-model="form.priority"
            type="select"
            :label="__('Priority')"
            :options="priorityOptions"
          />
        </div>

        <FormControl
          v-model="form.due_date"
          type="datetime-local"
          :label="__('Due Date')"
        />

        <FormControl
          v-model="form.assigned_to"
          type="select"
          :label="__('Assign To')"
          :options="userOptions"
        />

        <div
          class="border-t border-outline-gray-2 pt-3 text-sm font-medium text-ink-gray-7"
        >
          {{ __('Related record') }}
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <FormControl
            v-model="form.reference_doctype"
            type="select"
            :label="__('Related Type')"
            :options="referenceTypeOptions"
            @update:model-value="onReferenceTypeChange"
          />

          <FormControl
            v-if="form.reference_doctype"
            v-model="form.reference_docname"
            type="select"
            :label="__('Related Record')"
            :options="relatedRecordOptions"
            required
          />
        </div>

        <ErrorMessage
          v-if="error"
          :message="error"
        />
      </div>
    </template>

    <template #actions>
      <div class="flex items-center gap-2">
        <Button
          v-if="editingName"
          variant="subtle"
          :label="__('Delete')"
          :disabled="saving"
          @click="removeTask"
        />

        <div class="flex flex-1 justify-end gap-2">
          <Button
            :label="__('Cancel')"
            :disabled="saving"
            @click="close"
          />

          <Button
            variant="solid"
            :label="
              editingName
                ? __('Save Changes')
                : __('Create Task')
            "
            :loading="saving"
            :disabled="saving"
            @click="saveTask"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { call } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { sessionStore } from '@/stores/session'

const TASK_DOCTYPE = 'DoubleT Task'

const statuses = [
  'Backlog',
  'Todo',
  'In Progress',
  'Done',
  'Canceled',
]

const priorities = [
  'Low',
  'Medium',
  'High',
  'Urgent',
]

const referenceTitleField = {
  'DoubleT Lead': 'first_name',
  'DoubleT Deal': 'deal_title',
  'DoubleT Contact': 'first_name',
  'DoubleT Company': 'company_name',
}

const props = defineProps({
  doctype: {
    type: String,
    default: '',
  },
  doc: {
    type: Object,
    default: () => ({}),
  },
  name: {
    type: String,
    default: '',
  },
  defaults: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits([
  'afterInsert',
  'afterUpdate',
])

const show = defineModel({
  type: Boolean,
  default: false,
})

const { user } = sessionStore()

const editingName = ref('')
const saving = ref(false)
const error = ref('')

const users = ref([])
const relatedRecords = ref([])

const statusOptions = statuses.map((value) => ({
  label: value,
  value,
}))

const priorityOptions = priorities.map((value) => ({
  label: value,
  value,
}))

const referenceTypeOptions = [
  {
    label: __('None'),
    value: '',
  },
  ...Object.keys(referenceTitleField).map((value) => ({
    label: value.replace('DoubleT ', ''),
    value,
  })),
]

const userOptions = computed(() => [
  {
    label: __('Unassigned'),
    value: '',
  },
  ...users.value.map((item) => ({
    label: item.full_name || item.name,
    value: item.name,
  })),
])

const relatedRecordOptions = computed(() => [
  {
    label: __('Select record'),
    value: '',
  },
  ...relatedRecords.value.map((item) => ({
    label: item.label,
    value: item.name,
  })),
])

function currentUser() {
  return user?.value || ''
}

function emptyForm() {
  return {
    title: '',
    description: '',
    status: 'Backlog',
    priority: 'Low',
    due_date: '',
    assigned_to: currentUser(),
    reference_doctype: '',
    reference_docname: '',
  }
}

const form = ref(emptyForm())

function toInputDate(value) {
  if (!value) return ''

  return String(value)
    .replace(' ', 'T')
    .slice(0, 16)
}

function toServerDate(value) {
  if (!value) return null

  const normalized = String(value).replace('T', ' ')

  return normalized.length === 16
    ? normalized + ':00'
    : normalized
}

function resetForm() {
  editingName.value = props.name || ''
  error.value = ''
  relatedRecords.value = []

  form.value = {
    ...emptyForm(),
    ...(props.defaults || {}),
  }
}

function onReferenceTypeChange() {
  form.value.reference_docname = ''
}

async function loadUsers() {
  try {
    const result = await call('frappe.client.get_list', {
      doctype: 'User',
      fields: ['name', 'full_name'],
      filters: [
        ['enabled', '=', 1],
        ['name', '!=', 'Guest'],
      ],
      limit_page_length: 500,
    })

    users.value = Array.isArray(result) ? result : []
  } catch (err) {
    console.warn('Unable to load users:', err)

    const username = currentUser()

    users.value = username
      ? [{ name: username, full_name: username }]
      : []
  }
}

let relatedFetchId = 0

async function loadRelatedRecords(doctype) {
  const requestId = ++relatedFetchId

  relatedRecords.value = []

  if (!doctype) return

  const titleField = referenceTitleField[doctype]

  if (!titleField) return

  try {
    const result = await call('frappe.client.get_list', {
      doctype,
      fields: ['name', titleField],
      limit_page_length: 500,
      order_by: 'modified desc',
    })

    if (requestId !== relatedFetchId) return

    const records = Array.isArray(result) ? result : []

    relatedRecords.value = records.map((item) => ({
      name: item.name,
      label: `${item[titleField] || item.name} (${item.name})`,
    }))

    const selected = form.value.reference_docname

    if (
      selected &&
      !relatedRecords.value.some(
        (item) => item.name === selected,
      )
    ) {
      relatedRecords.value.unshift({
        name: selected,
        label: selected,
      })
    }
  } catch (err) {
    if (requestId !== relatedFetchId) return

    error.value =
      err.message || __('Unable to load related records')
  }
}

async function loadTask(name) {
  try {
    const task = await call('frappe.client.get', {
      doctype: TASK_DOCTYPE,
      name,
    })

    // Ignore an outdated response after modal closes.
    if (!show.value || editingName.value !== name) return

    form.value = {
      ...emptyForm(),
      ...task,
      due_date: toInputDate(task.due_date),
    }
  } catch (err) {
    if (!show.value) return

    error.value =
      err.message || __('Unable to load task')
  }
}

watch(
  () => form.value.reference_doctype,
  (doctype) => {
    if (show.value) {
      loadRelatedRecords(doctype)
    }
  },
)

watch(
  () => show.value,
  (open) => {
    if (!open) {
      relatedFetchId++
      return
    }

    resetForm()

    loadUsers()

    if (form.value.reference_doctype) {
      loadRelatedRecords(form.value.reference_doctype)
    }

    if (props.name) {
      loadTask(props.name)
    }
  },
)

async function saveTask() {
  if (saving.value) return

  const title = String(form.value.title || '').trim()

  if (!title) {
    error.value = __('Title is required')
    return
  }

  if (
    form.value.reference_doctype &&
    !form.value.reference_docname
  ) {
    error.value = __('Related record is required')
    return
  }

  saving.value = true
  error.value = ''

  const data = {
    title,
    description: form.value.description || '',
    status: form.value.status || 'Backlog',
    priority: form.value.priority || 'Low',
    due_date: toServerDate(form.value.due_date),
    assigned_to: form.value.assigned_to || null,
    reference_doctype:
      form.value.reference_doctype || '',
    reference_docname:
      form.value.reference_doctype
        ? form.value.reference_docname
        : '',
  }

  try {
    if (editingName.value) {
      const taskName = editingName.value

      await call('frappe.client.set_value', {
        doctype: TASK_DOCTYPE,
        name: taskName,
        fieldname: data,
      })

      show.value = false

      emit('afterUpdate', {
        ...data,
        doctype: TASK_DOCTYPE,
        name: taskName,
      })
    } else {
      const created = await call('frappe.client.insert', {
        doc: {
          doctype: TASK_DOCTYPE,
          ...data,
        },
      })

      show.value = false
      emit('afterInsert', created)
    }
  } catch (err) {
    error.value =
      err.message || __('Unable to save task')
  } finally {
    saving.value = false
  }
}

async function removeTask() {
  if (!editingName.value || saving.value) return

  if (!window.confirm(__('Delete this task?'))) {
    return
  }

  saving.value = true
  error.value = ''

  try {
    const taskName = editingName.value

    await call('frappe.client.delete', {
      doctype: TASK_DOCTYPE,
      name: taskName,
    })

    show.value = false

    emit('afterUpdate', {
      doctype: TASK_DOCTYPE,
      name: taskName,
    })
  } catch (err) {
    error.value =
      err.message || __('Unable to delete task')
  } finally {
    saving.value = false
  }
}

function close() {
  if (saving.value) return

  show.value = false
}
</script>
