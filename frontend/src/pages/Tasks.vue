
<template>
  <div class="task-page flex h-full flex-col overflow-hidden">
    <!-- Header -->
    <header class="task-header">
      <div>
        <h1 class="task-heading">{{ __('Tasks') }}</h1>
        <p class="task-subtitle">
          Manage, organize and track your work
        </p>
      </div>
      <Button
        variant="solid"
        iconLeft="plus"
        :label="__('Create Task')"
        @click="startCreate"
      />
    </header>

    <!-- Statistics -->
    <section class="task-stats">
      <div class="task-stat-card">
        <span class="stat-label">Total tasks</span>
        <strong class="stat-number">{{ tasks.length }}</strong>
        <span class="stat-hint">Currently loaded</span>
      </div>

      <div class="task-stat-card">
        <span class="stat-label">In progress</span>
        <strong class="stat-number">
          {{ tasks.filter(t => t.status === 'In Progress').length }}
        </strong>
        <span class="stat-hint">Active tasks</span>
      </div>

      <div class="task-stat-card">
        <span class="stat-label">Overdue</span>
        <strong class="stat-number stat-danger">
          {{ tasks.filter(t => isOverdue(t)).length }}
        </strong>
        <span class="stat-hint">Need attention</span>
      </div>
    </section>

    <!-- Filters -->
    <section class="task-toolbar">
      <div class="task-toolbar-left">
        <label class="task-check">
          <input v-model="myTasks" type="checkbox" />
          <span>{{ __('My Tasks') }}</span>
        </label>

        <div class="task-filter">
          <span>{{ __('Status') }}</span>
          <select v-model="statusFilter">
            <option value="">{{ __('All') }}</option>
            <option
              v-for="status in statuses"
              :key="status"
              :value="status"
            >
              {{ __(status) }}
            </option>
          </select>
        </div>

        <div class="task-filter">
          <span>{{ __('Due Date') }}</span>
          <select v-model="dueFilter">
            <option
              v-for="option in [
                'All', 'Overdue', 'Due Today', 'Upcoming'
              ]"
              :key="option"
              :value="option"
            >
              {{ __(option) }}
            </option>
          </select>
        </div>
      </div>

      <Button
        variant="subtle"
        icon="refresh-cw"
        :label="__('Refresh')"
        :loading="loading"
        @click="loadTasks"
      />
    </section>

    <!-- Content -->
    <main class="task-content">
      <div v-if="error" class="task-error">{{ error }}</div>

      <div v-if="loading" class="task-empty">
        {{ __('Loading tasks...') }}
      </div>

      <div v-else-if="!tasks.length" class="task-empty">
        <div class="empty-icon">✓</div>
        <h3>{{ __('No tasks found') }}</h3>
        <p>Create a task or adjust your filters.</p>
        <Button
          variant="solid"
          iconLeft="plus"
          :label="__('Create Task')"
          @click="startCreate"
        />
      </div>

      <div v-else class="task-table-wrap">
        <table class="task-table">
          <thead>
            <tr>
              <th>{{ __('Task') }}</th>
              <th>{{ __('Status') }}</th>
              <th>{{ __('Priority') }}</th>
              <th>{{ __('Due Date') }}</th>
              <th>{{ __('Assigned To') }}</th>
              <th>{{ __('Related Record') }}</th>
              <th></th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="task in tasks" :key="task.name">
              <td>
                <button
                  type="button"
                  class="task-title-button"
                  @click="startEdit(task)"
                >
                  {{ task.title }}
                </button>
                <div v-if="task.description" class="task-description">
                  {{ task.description }}
                </div>
              </td>

              <td>
                <span
                  class="task-status"
                  :class="'status-' + task.status.toLowerCase().replaceAll(' ', '-')"
                >
                  <span class="status-dot"></span>
                  {{ __(task.status) }}
                </span>
              </td>

              <td>
                <span
                  class="task-priority"
                  :class="'priority-' + (task.priority || 'low').toLowerCase()"
                >
                  <span class="priority-dot"></span>
                  {{ __(task.priority || 'Low') }}
                </span>
              </td>

              <td>
                <span
                  class="task-due"
                  :class="{ 'task-due-overdue': isOverdue(task) }"
                >
                  {{ displayDue(task.due_date) }}
                </span>
              </td>

              <td>
                <span class="task-assignee">
                  <span class="assignee-avatar">
                    {{ (users.find(u => u.name === task.assigned_to)?.full_name || task.assigned_to || '?').charAt(0).toUpperCase() }}
                  </span>
                  <span>
                    {{ users.find(u => u.name === task.assigned_to)?.full_name || task.assigned_to || 'Unassigned' }}
                  </span>
                </span>
              </td>

              <td>
                <button
                  v-if="task.reference_docname && routeFor(task)"
                  type="button"
                  class="task-related-link"
                  @click="goToRecord(task)"
                >
                  {{ relatedLabel(task.reference_doctype) }}:
                  {{ task.reference_docname }}
                  ↗
                </button>
                <span v-else class="task-muted">—</span>
              </td>

              <td class="task-action-cell">
                <Button
                  size="sm"
                  variant="subtle"
                  :label="__('Edit')"
                  @click="startEdit(task)"
                />
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="hasMore" class="task-load-more">
          <Button
            :label="__('Load more')"
            :loading="loadingMore"
            @click="loadMore"
          />
        </div>
      </div>
    </main>

    <!-- Create/Edit modal -->
    <div
      v-if="editorOpen"
      class="task-modal-overlay"
      @click.self="!saving && (editorOpen = false)"
    >
      <div
        class="task-modal"
        role="dialog"
        aria-modal="true"
        :aria-label="editingName ? 'Edit Task' : 'Create Task'"
      >
        <div class="task-modal-header">
          <div>
            <h2>{{ editingName ? __('Edit Task') : __('Create Task') }}</h2>
            <p>Keep your work organized and on track.</p>
          </div>
          <button
            type="button"
            class="task-close"
            :disabled="saving"
            @click="editorOpen = false"
          >
            ✕
          </button>
        </div>

        <form @submit.prevent="saveTask">
          <div class="task-modal-body">
            <label class="task-field">
              <span>{{ __('Title') }} <b>*</b></span>
              <input
                v-model.trim="form.title"
                required
                maxlength="140"
                placeholder="What needs to be done?"
              />
            </label>

            <label class="task-field">
              <span>{{ __('Description') }}</span>
              <textarea
                v-model="form.description"
                rows="3"
                placeholder="Add more details about this task..."
              ></textarea>
            </label>

            <div class="task-form-grid">
              <label class="task-field">
                <span>{{ __('Status') }}</span>
                <select v-model="form.status">
                  <option
                    v-for="value in statuses"
                    :key="value"
                    :value="value"
                  >
                    {{ __(value) }}
                  </option>
                </select>
              </label>

              <label class="task-field">
                <span>{{ __('Priority') }}</span>
                <select v-model="form.priority">
                  <option
                    v-for="value in priorities"
                    :key="value"
                    :value="value"
                  >
                    {{ __(value) }}
                  </option>
                </select>
              </label>
            </div>

            <label class="task-field">
              <span>{{ __('Due Date') }}</span>
              <input
                v-model="form.due_date"
                type="datetime-local"
              />
            </label>

            <label class="task-field">
              <span>{{ __('Assign To') }}</span>
              <select v-model="form.assigned_to">
                <option value="">{{ __('Unassigned') }}</option>
                <option
                  v-for="u in users"
                  :key="u.name"
                  :value="u.name"
                >
                  {{ u.full_name || u.name }}
                </option>
              </select>
            </label>

            <div class="task-section-title">Related record</div>

            <div class="task-form-grid">
              <label class="task-field">
                <span>{{ __('Related Type') }}</span>
                <select
                  v-model="form.reference_doctype"
                  @change="form.reference_docname = ''"
                >
                  <option value="">{{ __('None') }}</option>
                  <option
                    v-for="value in referenceTypes"
                    :key="value"
                    :value="value"
                  >
                    {{ relatedLabel(value) }}
                  </option>
                </select>
              </label>

              <label
                v-if="form.reference_doctype"
                class="task-field"
              >
                <span>{{ __('Related Record') }} <b>*</b></span>
                <select v-model="form.reference_docname" required>
                  <option value="">{{ __('Select record') }}</option>
                  <option
                    v-for="record in relatedRecords"
                    :key="record.name"
                    :value="record.name"
                  >
                    {{ record.label }}
                  </option>
                </select>
              </label>
            </div>

            <p v-if="saveError" class="task-error">
              {{ saveError }}
            </p>
          </div>

          <div class="task-modal-footer">
            <Button
              v-if="editingName"
              variant="subtle"
              :label="__('Delete')"
              :loading="saving"
              @click="deleteTask"
            />

            <div class="task-footer-spacer"></div>

            <Button
              :label="__('Cancel')"
              :disabled="saving"
              @click="editorOpen = false"
            />
            <Button
              variant="solid"
              type="submit"
              :loading="saving"
              :label="editingName ? __('Save Changes') : __('Create Task')"
            />
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { call } from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sessionStore } from '@/stores/session'

const TASK_DOCTYPE = 'DoubleT Task'
const statuses = ['Backlog', 'Todo', 'In Progress', 'Done', 'Canceled']
const priorities = ['Low', 'Medium', 'High', 'Urgent']
const referenceTypes = ['DoubleT Lead', 'DoubleT Deal', 'DoubleT Contact', 'DoubleT Company']
const referenceRouteNames = {
  'DoubleT Lead': ['LeadDetail', 'leadId'],
  'DoubleT Deal': ['DealDetail', 'dealId'],
  'DoubleT Contact': ['ContactDetail', 'contactId'],
  'DoubleT Company': ['CompanyDetail', 'companyId'],
}
const route = useRoute()
const router = useRouter()
const { user } = sessionStore()
const myTasks = ref(route.query.my_tasks !== '0')
const statusFilter = ref('')
const dueFilter = ref(['All', 'Overdue', 'Due Today', 'Upcoming'].includes(route.query.due_date_filter) ? route.query.due_date_filter : 'All')
const tasks = ref([])
const users = ref([])
const relatedRecords = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref('')
const editorOpen = ref(false)
const editingName = ref('')
const saving = ref(false)
const saveError = ref('')
const pageSize = 100
const page = ref(0)
const hasMore = ref(false)
const emptyForm = () => ({ title: '', description: '', status: 'Backlog', priority: 'Low', due_date: '', assigned_to: user.value || '', reference_doctype: '', reference_docname: '' })
const form = ref(emptyForm())

function localDate(date) {
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}
function localDateTime(date) { return `${localDate(date)} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}` }
function dateValue(value) { return value ? new Date(value.replace(' ', 'T')) : null }
function isOverdue(task) { const value = dateValue(task.due_date); return value && value < new Date() && !['Done', 'Canceled'].includes(task.status) }
function displayDue(value) { const date = dateValue(value); return date && !Number.isNaN(date.getTime()) ? date.toLocaleString() : '—' }
function relatedLabel(value) { return value?.replace('DoubleT ', '') || '' }
function routeFor(task) {
  const target = referenceRouteNames[task.reference_doctype]
  return task.reference_docname && target ? { name: target[0], params: { [target[1]]: task.reference_docname } } : null
}
function goToRecord(task) { const target = routeFor(task); if (target) router.push(target) }

const filters = computed(() => {
  const result = []
  if (myTasks.value && user.value) result.push(['assigned_to', '=', user.value])
  if (statusFilter.value) result.push(['status', '=', statusFilter.value])
  const now = new Date()
  if (dueFilter.value === 'Overdue') {
    result.push(['due_date', '<', localDateTime(now)])
    result.push(['status', 'not in', ['Done', 'Canceled']])
  } else if (dueFilter.value === 'Due Today') {
    const today = localDate(now)
    result.push(['due_date', 'between', [`${today} 00:00:00`, `${today} 23:59:59`]])
  } else if (dueFilter.value === 'Upcoming') {
    result.push(['due_date', '>', localDateTime(now)])
  }
  return result
})
const taskFields = ['name', 'title', 'description', 'status', 'priority', 'due_date', 'assigned_to', 'reference_doctype', 'reference_docname', 'modified']
async function fetchPage(index) {
  return call('frappe.client.get_list', { doctype: TASK_DOCTYPE, fields: taskFields, filters: filters.value, order_by: 'modified desc', limit_start: index * pageSize, limit_page_length: pageSize })
}
let fetchId = 0
async function loadTasks() {
  const currentId = ++fetchId
  loading.value = true
  error.value = ''
  try {
    const result = await fetchPage(0)
    if (currentId !== fetchId) return
    tasks.value = result || []
    page.value = 1
    hasMore.value = tasks.value.length === pageSize
  } catch (e) { if (currentId === fetchId) error.value = e.message || __('Unable to load tasks') }
  finally { if (currentId === fetchId) loading.value = false }
}
async function loadMore() {
  loadingMore.value = true
  try { const result = await fetchPage(page.value); tasks.value.push(...(result || [])); page.value++; hasMore.value = result?.length === pageSize }
  catch (e) { error.value = e.message || __('Unable to load more tasks') }
  finally { loadingMore.value = false }
}
watch([myTasks, statusFilter, dueFilter], () => {
  router.replace({ query: { ...route.query, my_tasks: myTasks.value ? '1' : '0', due_date_filter: dueFilter.value } })
  loadTasks()
})
async function loadUsers() {
  try { users.value = await call('frappe.client.get_list', { doctype: 'User', fields: ['name', 'full_name'], filters: [['enabled', '=', 1], ['name', '!=', 'Guest']], limit_page_length: 500 }) || [] }
  catch (e) { users.value = user.value ? [{ name: user.value, full_name: user.value }] : [] }
}
const referenceTitleField = { 'DoubleT Lead': 'first_name', 'DoubleT Deal': 'deal_title', 'DoubleT Contact': 'first_name', 'DoubleT Company': 'company_name' }
let referenceFetchId = 0
watch(() => form.value.reference_doctype, async (doctype) => {
  const currentId = ++referenceFetchId
  relatedRecords.value = []
  if (!doctype) return
  try {
    const titleField = referenceTitleField[doctype]
    const data = await call('frappe.client.get_list', { doctype, fields: ['name', titleField], limit_page_length: 500, order_by: 'modified desc' })
    if (currentId !== referenceFetchId) return
    relatedRecords.value = (data || []).map((item) => ({ name: item.name, label: `${item[titleField] || item.name} (${item.name})` }))
    if (form.value.reference_docname && !relatedRecords.value.some((r) => r.name === form.value.reference_docname)) relatedRecords.value.unshift({ name: form.value.reference_docname, label: form.value.reference_docname })
  } catch (e) { saveError.value = e.message || __('Unable to load related records') }
})
function startCreate() { editingName.value = ''; form.value = emptyForm(); saveError.value = ''; editorOpen.value = true; loadUsers() }
function startEdit(task) {
  editingName.value = task.name
  form.value = { ...emptyForm(), ...task, due_date: task.due_date ? task.due_date.replace(' ', 'T').slice(0, 16) : '' }
  saveError.value = ''; editorOpen.value = true; loadUsers()
}
async function saveTask() {
  saving.value = true; saveError.value = ''
  try {
    const data = { ...form.value }
    delete data.name; delete data.modified
    data.due_date = data.due_date ? `${data.due_date.replace('T', ' ')}:00` : null
    if (!data.reference_doctype) data.reference_docname = ''
    if (editingName.value) {
      await call('frappe.client.set_value', { doctype: TASK_DOCTYPE, name: editingName.value, fieldname: data })
    } else {
      await call('frappe.client.insert', { doc: { doctype: TASK_DOCTYPE, ...data } })
    }
    editorOpen.value = false
    await loadTasks()
  } catch (e) { saveError.value = e.message || __('Unable to save task') }
  finally { saving.value = false }
}
async function deleteTask() {
  if (!window.confirm(__('Delete this task?'))) return
  saving.value = true; saveError.value = ''
  try { await call('frappe.client.delete', { doctype: TASK_DOCTYPE, name: editingName.value }); editorOpen.value = false; await loadTasks() }
  catch (e) { saveError.value = e.message || __('Unable to delete task') }
  finally { saving.value = false }
}
onMounted(() => loadTasks())
</script>

<style scoped>
.task-page {
  background: #f8fafc;
  color: #172033;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 24px 30px;
  background: #fff;
  border-bottom: 1px solid #e9edf3;
}

.task-heading {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.7px;
}

.task-subtitle {
  margin-top: 4px;
  color: #8893a3;
  font-size: 13px;
}

.task-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  padding: 22px 30px;
}

.task-stat-card {
  display: flex;
  flex-direction: column;
  gap: 7px;
  background: #fff;
  padding: 18px 20px;
  border: 1px solid #e9edf3;
  border-radius: 12px;
}

.stat-label {
  font-size: 13px;
  color: #778397;
}

.stat-number {
  font-size: 29px;
  font-weight: 700;
  letter-spacing: -1px;
}

.stat-danger {
  color: #dc4545;
}

.stat-hint {
  font-size: 12px;
  color: #a0a8b6;
}

.task-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  margin: 0 30px 16px;
  padding: 14px 18px;
  border: 1px solid #e9edf3;
  border-radius: 12px;
  background: #fff;
}

.task-toolbar-left {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 20px;
}

.task-check,
.task-filter {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 13px;
  font-weight: 500;
}

.task-check input {
  width: 15px;
  height: 15px;
  accent-color: #4f46e5;
}

.task-filter select {
  padding: 8px 30px 8px 12px;
  background: #fff;
  border: 1px solid #e1e6ee;
  border-radius: 8px;
  outline: none;
}

.task-filter select:focus {
  border-color: #818cf8;
}

.task-content {
  margin: 0 30px 24px;
  overflow: auto;
  min-height: 0;
  background: #fff;
  border: 1px solid #e9edf3;
  border-radius: 12px;
  flex: 1;
}

.task-table-wrap {
  overflow-x: auto;
}

.task-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;
  white-space: nowrap;
}

.task-table th {
  padding: 17px 20px;
  background: #fafbfc;
  color: #8490a2;
  font-weight: 600;
  border-bottom: 1px solid #edf0f5;
}

.task-table td {
  padding: 18px 20px;
  border-bottom: 1px solid #f0f2f6;
}

.task-table tbody tr:hover {
  background: #f8faff;
}

.task-title-button {
  font-weight: 600;
  color: #253047;
  text-align: left;
}

.task-title-button:hover {
  color: #4f46e5;
}

.task-description {
  margin-top: 5px;
  color: #98a2b3;
  font-size: 12px;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-status,
.task-priority {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 600;
}

.task-status {
  padding: 6px 10px;
  border-radius: 20px;
  background: #f1f3f6;
  color: #64748b;
}

.status-dot,
.priority-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.status-todo {
  background: #eff6ff;
  color: #2563eb;
}

.status-in-progress {
  background: #fff7ed;
  color: #ea580c;
}

.status-done {
  background: #ecfdf5;
  color: #059669;
}

.status-canceled {
  background: #fef2f2;
  color: #dc2626;
}

.priority-low {
  color: #64748b;
}

.priority-medium {
  color: #2563eb;
}

.priority-high {
  color: #ea580c;
}

.priority-urgent {
  color: #dc2626;
}

.task-due {
  color: #68758a;
  font-size: 12px;
}

.task-due-overdue {
  color: #dc2626;
  font-weight: 600;
}

.task-assignee {
  display: inline-flex;
  align-items: center;
  gap: 9px;
}

.assignee-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 29px;
  height: 29px;
  border-radius: 50%;
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 700;
  flex-shrink: 0;
}

.task-related-link {
  color: #4f46e5;
  font-weight: 500;
}

.task-related-link:hover {
  text-decoration: underline;
}

.task-muted {
  color: #a0a8b6;
}

.task-action-cell {
  text-align: right;
}

.task-load-more {
  display: flex;
  justify-content: center;
  padding: 18px;
}

.task-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 340px;
  color: #8993a3;
}

.task-empty h3 {
  font-size: 17px;
  font-weight: 600;
  color: #344054;
}

.task-empty p {
  font-size: 13px;
}

.empty-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  border-radius: 16px;
  background: #eef2ff;
  color: #4f46e5;
  font-size: 28px;
}

/* Modal */
.task-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, .48);
  backdrop-filter: blur(3px);
}

.task-modal {
  width: 100%;
  max-width: 580px;
  max-height: 90vh;
  overflow-y: auto;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 25px 70px rgba(0, 0, 0, .16);
}

.task-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 24px 26px 20px;
  border-bottom: 1px solid #edf0f4;
}

.task-modal-header h2 {
  font-size: 19px;
  font-weight: 700;
}

.task-modal-header p {
  margin-top: 5px;
  font-size: 12px;
  color: #98a2b3;
}

.task-close {
  border: none;
  background: #f3f5f8;
  border-radius: 8px;
  width: 30px;
  height: 30px;
  cursor: pointer;
}

.task-modal-body {
  display: grid;
  gap: 18px;
  padding: 24px 26px;
}

.task-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-field > span {
  font-size: 12px;
  font-weight: 600;
  color: #475467;
}

.task-field b {
  color: #ef4444;
}

.task-field input,
.task-field select,
.task-field textarea {
  width: 100%;
  min-width: 0;
  padding: 11px 13px;
  border: 1px solid #dfe4ec;
  border-radius: 9px;
  background: #fff;
  color: #253047;
  font-size: 13px;
  outline: none;
  transition: border-color .15s, box-shadow .15s;
}

.task-field textarea {
  resize: vertical;
}

.task-field input:focus,
.task-field select:focus,
.task-field textarea:focus {
  border-color: #818cf8;
  box-shadow: 0 0 0 3px rgba(99,102,241,.1);
}

.task-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.task-section-title {
  padding-top: 10px;
  border-top: 1px solid #edf0f4;
  font-size: 13px;
  font-weight: 700;
  color: #344054;
}

.task-modal-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 17px 26px;
  background: #fafbfc;
  border-top: 1px solid #edf0f4;
}

.task-footer-spacer {
  flex: 1;
}

.task-error {
  margin: 12px 0;
  padding: 12px;
  background: #fef2f2;
  border-radius: 8px;
  color: #dc2626;
  font-size: 12px;
}

@media (max-width: 768px) {
  .task-header {
    padding: 18px;
  }

  .task-stats {
    padding: 16px;
    gap: 8px;
  }

  .task-stat-card {
    padding: 12px;
  }

  .stat-number {
    font-size: 23px;
  }

  .task-toolbar {
    margin: 0 16px 16px;
  }

  .task-content {
    margin: 0 16px 16px;
  }

  .task-form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
