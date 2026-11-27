<template>
  <Dialog v-model:open="show" :title="name ? __('Edit Appointment') : __('New Appointment')" size="xl">
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl v-model="form.title" :label="__('Title')" required />
        <FormControl v-model="form.description" type="textarea" :label="__('Description')" />
        <div class="grid gap-4 md:grid-cols-2">
          <FormControl v-model="form.starts_on" type="datetime-local" :label="__('Starts On')" required />
          <FormControl v-model="form.ends_on" type="datetime-local" :label="__('Ends On')" required />
          <FormControl v-model="form.assigned_to" type="select" :label="__('Assigned To')" :options="userOptions" required />
          <FormControl v-model="form.status" type="select" :label="__('Status')" :options="statusOptions" />
          <FormControl v-model="form.meeting_type" type="select" :label="__('Meeting Type')" :options="meetingOptions" />
          <FormControl v-model="form.location" :label="__('Location or Meeting Link')" />
          <FormControl v-model="form.reference_doctype" type="select" :label="__('Related Type')" :options="referenceTypeOptions" @update:model-value="referenceTypeChanged" />
          <div v-if="form.reference_doctype" class="space-y-2"><TextInput v-model="recordSearch" type="search" :placeholder="__('Search related records...')" /><FormControl v-model="form.reference_docname" type="select" :label="__('Related Record')" :options="recordOptions" required /></div>
          <FormControl v-model="form.reminder_type" type="select" :label="__('Reminder')" :options="reminderOptions" />
          <FormControl v-if="form.reminder_type === 'Custom'" v-model="form.reminder_at" type="datetime-local" :label="__('Custom reminder date and time')" required />
          <div v-else-if="form.reminder_at" class="rounded bg-surface-gray-1 px-3 py-2 text-sm text-ink-gray-6">{{ __('Reminder at {0}', [displayDate(form.reminder_at)]) }}</div>
        </div>
        <ErrorMessage v-if="error" :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex w-full items-center gap-2">
        <Button v-if="name && canDelete" variant="subtle" :label="__('Delete')" :disabled="saving" @click="remove" />
        <div class="ml-auto flex gap-2">
          <Button :label="__('Cancel')" :disabled="saving" @click="show = false" />
          <Button variant="solid" :label="name ? __('Save Changes') : __('Create Appointment')" :loading="saving" @click="save" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { call } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { sessionStore } from '@/stores/session'
import { message } from '@/utils/quotation'

const props = defineProps({ name: { type: String, default: '' }, defaults: { type: Object, default: () => ({}) } })
const emit = defineEmits(['saved', 'deleted'])
const show = defineModel({ type: Boolean, default: false })
const { user } = sessionStore()
const saving = ref(false), error = ref(''), users = ref([]), records = ref([]), canDelete = ref(false)
const form = ref({})
const referenceTitleField = { 'DoubleT Lead': 'first_name', 'DoubleT Deal': 'deal_title', 'DoubleT Contact': 'first_name', 'DoubleT Company': 'company_name' }
const optionize = values => values.map(value => ({ label: __(value), value }))
const statusOptions = optionize(['Scheduled', 'Completed', 'Cancelled'])
const meetingOptions = optionize(['In Person', 'Phone', 'Video', 'Other'])
const reminderOptions = optionize(['No Reminder', '15 Minutes Before', '30 Minutes Before', '1 Hour Before', '1 Day Before', 'Custom'])
const reminderOffsets = { '15 Minutes Before': 15, '30 Minutes Before': 30, '1 Hour Before': 60, '1 Day Before': 1440 }
const referenceTypeOptions = [{ label: __('None'), value: '' }, ...Object.keys(referenceTitleField).map(value => ({ label: __(value.replace('DoubleT ', '')), value }))]
const userOptions = computed(() => users.value.map(item => ({ label: item.full_name || item.name, value: item.name })))
const recordOptions = computed(() => [{ label: __('Select record'), value: '' }, ...records.value.map(item => ({ label: `${item.label || item.name} (${item.name})`, value: item.name }))])
const toInput = value => value ? String(value).replace(' ', 'T').slice(0, 16) : ''
const toServer = value => value ? `${String(value).replace('T', ' ').slice(0, 16)}:00` : null
const displayDate = value => value ? new Date(value).toLocaleString() : '—'
const toLocalInput = date => {
  const pad = value => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}
const recordSearch = ref('')

function blank() {
  return { title: '', description: '', starts_on: '', ends_on: '', assigned_to: user?.value || '', status: 'Scheduled', meeting_type: 'In Person', location: '', reference_doctype: '', reference_docname: '', reminder_type: 'No Reminder', reminder_at: '', ...props.defaults }
}
async function loadUsers() {
  users.value = await call('frappe.client.get_list', { doctype: 'User', fields: ['name', 'full_name'], filters: [['enabled', '=', 1], ['name', '!=', 'Guest']], limit_page_length: 500 }) || []
}
async function loadRecords(doctype, search = '') {
  records.value = []
  if (!doctype) return
  const title = referenceTitleField[doctype]
  const pattern = `%${search.trim()}%`
  const rows = await call('frappe.client.get_list', { doctype, fields: ['name', title], or_filters: search.trim() ? [['name', 'like', pattern], [title, 'like', pattern]] : [], order_by: 'modified desc', limit_page_length: 20 }) || []
  records.value = rows.map(row => ({ name: row.name, label: row[title] || row.name }))
  if (form.value.reference_docname && !records.value.some(row => row.name === form.value.reference_docname)) records.value.unshift({ name: form.value.reference_docname, label: form.value.reference_docname })
}
function referenceTypeChanged() { form.value.reference_docname = ''; recordSearch.value = ''; loadRecords(form.value.reference_doctype) }
function updateRelativeReminder() {
  const offset = reminderOffsets[form.value.reminder_type]
  if (form.value.reminder_type === 'No Reminder') { form.value.reminder_at = ''; return }
  if (!offset || !form.value.starts_on) return
  const date = new Date(form.value.starts_on)
  date.setMinutes(date.getMinutes() - offset)
  form.value.reminder_at = toLocalInput(date)
}
async function open() {
  error.value = ''; canDelete.value = false; recordSearch.value = ''; form.value = blank()
  await loadUsers()
  if (props.name) {
    const [doc, access] = await Promise.all([
      call('frappe.client.get', { doctype: 'DoubleT Appointment', name: props.name }),
      call('frappe.client.get_doc_permissions', { doctype: 'DoubleT Appointment', docname: props.name }),
    ])
    form.value = { ...doc, starts_on: toInput(doc.starts_on), ends_on: toInput(doc.ends_on), reminder_at: toInput(doc.reminder_at) }
    canDelete.value = Boolean(access?.permissions?.delete)
  } else {
    const defaults = await call('doublet_crm.doublet_crm.doctype.doublet_appointment.doublet_appointment.get_appointment_defaults')
    if (!props.defaults.starts_on) form.value.starts_on = toInput(defaults.starts_on)
    if (!props.defaults.ends_on) form.value.ends_on = toInput(defaults.ends_on)
  }
  await loadRecords(form.value.reference_doctype)
}
async function save() {
  if (saving.value) return
  if (!form.value.title?.trim() || !form.value.starts_on || !form.value.ends_on || !form.value.assigned_to) { error.value = __('Complete the required appointment fields.'); return }
  if (new Date(form.value.ends_on) < new Date(form.value.starts_on)) { error.value = __('End time cannot be before start time.'); return }
  if (form.value.reminder_at && new Date(form.value.reminder_at) > new Date(form.value.starts_on)) { error.value = __('Reminder time cannot be after the appointment start time.'); return }
  saving.value = true; error.value = ''
  const data = { ...form.value, title: form.value.title.trim(), starts_on: toServer(form.value.starts_on), ends_on: toServer(form.value.ends_on), reminder_at: toServer(form.value.reminder_at), reference_docname: form.value.reference_doctype ? form.value.reference_docname : '' }
  try {
    const result = props.name
      ? await call('frappe.client.save', { doc: data })
      : await call('frappe.client.insert', { doc: { ...data, doctype: 'DoubleT Appointment' } })
    show.value = false; emit('saved', result)
  } catch (e) { error.value = message(e) } finally { saving.value = false }
}
async function remove() {
  if (!canDelete.value || saving.value || !window.confirm(__('Delete this appointment?'))) return
  saving.value = true
  try { await call('frappe.client.delete', { doctype: 'DoubleT Appointment', name: props.name }); show.value = false; emit('deleted', props.name) }
  catch (e) { error.value = message(e) } finally { saving.value = false }
}
watch(show, value => { if (value) open().catch(e => { error.value = message(e) }) })
let recordTimer
watch(recordSearch, value => { if (!show.value || !form.value.reference_doctype) return; clearTimeout(recordTimer); recordTimer = setTimeout(() => loadRecords(form.value.reference_doctype, value), 250) })
watch(() => [form.value.starts_on, form.value.reminder_type], updateRelativeReminder)
</script>
