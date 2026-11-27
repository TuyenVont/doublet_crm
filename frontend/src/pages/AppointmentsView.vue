<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header><span class="text-base font-semibold">{{ __('Appointments') }}</span></template>
      <template #right-header><Button v-if="canCreate" variant="solid" :label="__('New Appointment')" iconLeft="plus" @click="openNew" /></template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5">
      <div class="mb-4 flex flex-wrap items-end gap-3">
        <div class="w-full sm:max-w-xs"><TextInput v-model="search" type="search" :placeholder="__('Search appointments...')" /></div>
        <select v-model="status" class="rounded border px-3"><option value="">{{ __('All statuses') }}</option><option v-for="value in ['Scheduled', 'Completed', 'Cancelled']" :key="value" :value="value">{{ __(value) }}</option></select>
        <select v-model="assignee" class="rounded border px-3"><option value="">{{ __('All assignees') }}</option><option v-for="item in users" :key="item.name" :value="item.name">{{ item.full_name || item.name }}</option></select>
        <select v-model="timeFilter" class="rounded border px-3"><option value="all">{{ __('All dates') }}</option><option value="upcoming">{{ __('Upcoming') }}</option><option value="past">{{ __('Past') }}</option></select>
      </div>
      <ErrorMessage v-if="error" class="mb-4" :message="error" />
      <div v-if="loading" class="p-8 text-center">{{ __('Loading appointments...') }}</div>
      <div v-else class="overflow-x-auto rounded border">
        <table class="w-full min-w-[900px] text-left text-sm">
          <thead class="bg-surface-gray-1"><tr><th class="p-3">{{ __('Title') }}</th><th class="p-3">{{ __('Starts On') }}</th><th class="p-3">{{ __('Ends On') }}</th><th class="p-3">{{ __('Status') }}</th><th class="p-3">{{ __('Assigned To') }}</th><th class="p-3">{{ __('Related Record') }}</th></tr></thead>
          <tbody><tr v-for="item in rows" :key="item.name" class="cursor-pointer border-t hover:bg-surface-gray-1" @click="openEdit(item.name)"><td class="p-3 font-medium"><div>{{ item.title }}</div><div class="mt-1 text-xs text-ink-gray-5">{{ reminderLabel(item) }}</div></td><td class="p-3">{{ display(item.starts_on) }}</td><td class="p-3">{{ display(item.ends_on) }}</td><td class="p-3"><span class="rounded px-2 py-1 text-xs font-medium" :class="statusClass(item.status)">{{ __(item.status) }}</span></td><td class="p-3">{{ userLabel(item.assigned_to) }}</td><td class="p-3"><div>{{ item.reference_label || item.reference_docname || '—' }}</div><div v-if="item.reference_label" class="text-xs text-ink-gray-5">{{ item.reference_docname }}</div></td></tr><tr v-if="!rows.length"><td colspan="6" class="p-10 text-center"><div class="font-medium text-ink-gray-7">{{ __('No appointments found') }}</div><div class="mt-1 text-sm text-ink-gray-5">{{ __('Try changing the filters or create a new appointment.') }}</div></td></tr></tbody>
        </table>
      </div>
      <div v-if="total > pageSize" class="mt-4 flex items-center justify-between text-sm text-ink-gray-6">
        <span>{{ __('Showing {0}–{1} of {2}', [pageStart + 1, Math.min(pageStart + pageSize, total), total]) }}</span>
        <div class="flex gap-2"><Button :label="__('Previous')" :disabled="pageStart === 0 || loading" @click="pageStart = Math.max(0, pageStart - pageSize)" /><Button :label="__('Next')" :disabled="pageStart + pageSize >= total || loading" @click="pageStart += pageSize" /></div>
      </div>
    </div>
    <AppointmentModal v-model="modalOpen" :name="editingName" :defaults="defaults" @saved="afterChange" @deleted="afterChange" />
  </div>
</template>

<script setup>
import { Button, TextInput, call } from 'frappe-ui'
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LayoutHeader from '@/components/LayoutHeader.vue'
import AppointmentModal from '@/components/Modals/AppointmentModal.vue'
import { message } from '@/utils/quotation'

const route = useRoute(), router = useRouter()
const rows = ref([]), users = ref([]), loading = ref(true), error = ref(''), canCreate = ref(false), modalOpen = ref(false), editingName = ref(''), defaults = ref({})
const total = ref(0), pageStart = ref(0), pageSize = 20
const search = ref(''), status = ref(''), assignee = ref(''), timeFilter = ref('upcoming')
const display = value => value ? new Date(String(value).replace(' ', 'T')).toLocaleString() : '—'
const userLabel = name => users.value.find(item => item.name === name)?.full_name || name
const statusClass = value => ({ Scheduled: 'bg-blue-50 text-blue-700', Completed: 'bg-green-50 text-green-700', Cancelled: 'bg-red-50 text-red-700' }[value] || 'bg-surface-gray-2')
const reminderLabel = item => !item.reminder_at ? __('Reminder: Not set') : item.reminder_sent_at ? __('Reminder: Sent {0}', [display(item.reminder_sent_at)]) : __('Reminder: Pending {0}', [display(item.reminder_at)])
async function load() {
  loading.value = true; error.value = ''
  try {
    const [appointments, userRows, permission] = await Promise.all([
      call('doublet_crm.doublet_crm.doctype.doublet_appointment.doublet_appointment.list_appointments', { search: search.value.trim(), status: status.value, assigned_to: assignee.value, time_filter: timeFilter.value, limit_start: pageStart.value, limit_page_length: pageSize }),
      call('frappe.client.get_list', { doctype: 'User', fields: ['name', 'full_name'], filters: [['enabled', '=', 1]], limit_page_length: 500 }),
      call('frappe.client.has_permission', { doctype: 'DoubleT Appointment', docname: '', perm_type: 'create' }),
    ])
    rows.value = appointments?.rows || []; total.value = appointments?.total || 0; users.value = userRows || []; canCreate.value = Boolean(permission?.has_permission)
  } catch (e) { error.value = message(e) } finally { loading.value = false }
}
function openNew() { editingName.value = ''; defaults.value = { reference_doctype: route.query.reference_doctype || '', reference_docname: route.query.reference_docname || '' }; modalOpen.value = true }
function openEdit(name) { editingName.value = name; defaults.value = {}; modalOpen.value = true }
async function afterChange() { await router.replace({ name: 'Appointments' }); await load() }
onMounted(async () => { await load(); if (route.name === 'AppointmentCreate') openNew(); else if (route.params.appointmentId) openEdit(route.params.appointmentId) })
let filterTimer
watch([search, status, assignee, timeFilter], () => { pageStart.value = 0; clearTimeout(filterTimer); filterTimer = setTimeout(load, 250) })
watch(pageStart, load)
</script>
