<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Tasks" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="tasksListView?.customListActions"
        :actions="tasksListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="createTask"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="tasks"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Task"
    :options="{
      allowedViews: ['list', 'kanban'],
    }"
  />
  <div class="flex flex-wrap items-center gap-3 border-b px-3 py-2 sm:px-5">
    <label class="flex items-center gap-2 text-sm text-ink-gray-7">
      <input v-model="myTasksOnly" type="checkbox" class="rounded border-outline-gray-2" />
      {{ __('My Tasks') }}
    </label>
    <label class="flex items-center gap-2 text-sm text-ink-gray-7">
      <span>{{ __('Status') }}</span>
      <select v-model="statusFilter" class="rounded border border-outline-gray-2 bg-surface-white px-2 py-1">
        <option value="">{{ __('All') }}</option>
        <option v-for="status in taskStatuses" :key="status" :value="status">{{ __(status) }}</option>
      </select>
    </label>
    <label class="flex items-center gap-2 text-sm text-ink-gray-7">
      <span>{{ __('Due Date') }}</span>
      <select v-model="dueDateFilter" class="rounded border border-outline-gray-2 bg-surface-white px-2 py-1">
        <option value="All">{{ __('All') }}</option>
        <option value="Overdue">{{ __('Overdue') }}</option>
        <option value="Due Today">{{ __('Due Today') }}</option>
        <option value="Upcoming">{{ __('Upcoming') }}</option>
      </select>
    </label>
  </div>
  <KanbanView
    v-if="$route.params.viewType == 'kanban' && rows.length"
    v-model="tasks"
    :options="{
      onClick: (row) => showTask(row.name),
      onNewClick: (column) => createTask(column),
    }"
    @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
  >
    <template #title="{ titleField, itemName }">
      <div class="flex items-center gap-2">
        <div v-if="titleField === 'status'">
          <TaskStatusIcon :status="getRow(itemName, titleField).label" />
        </div>
        <div v-else-if="titleField === 'priority'">
          <TaskPriorityIcon :priority="getRow(itemName, titleField).label" />
        </div>
        <div v-else-if="titleField === 'assigned_to'">
          <Avatar
            v-if="getRow(itemName, titleField).full_name"
            class="flex items-center"
            :image="getRow(itemName, titleField).user_image"
            :label="getRow(itemName, titleField).full_name"
            size="sm"
          />
        </div>
        <div
          v-if="['modified', 'creation'].includes(titleField)"
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, titleField).label">
            <div>{{ getRow(itemName, titleField).timeAgo }}</div>
          </Tooltip>
        </div>
        <div
          v-else-if="getRow(itemName, titleField).label"
          class="truncate text-base"
        >
          {{ getRow(itemName, titleField).label }}
        </div>
        <div v-else class="text-ink-gray-4">{{ __('No Title') }}</div>
      </div>
    </template>
    <template #fields="{ fieldName, itemName }">
      <div
        v-if="getRow(itemName, fieldName).label"
        class="truncate flex items-center gap-2"
        :class="isOverdueTask(getTask(itemName)) ? 'text-ink-red-6 font-medium' : ''"
      >
        <div v-if="fieldName === 'status'">
          <TaskStatusIcon
            class="size-3"
            :status="getRow(itemName, fieldName).label"
          />
        </div>
        <div v-else-if="fieldName === 'priority'">
          <TaskPriorityIcon :priority="getRow(itemName, fieldName).label" />
        </div>
        <div v-else-if="fieldName === 'assigned_to'">
          <Avatar
            v-if="getRow(itemName, fieldName).full_name"
            class="flex items-center"
            :image="getRow(itemName, fieldName).user_image"
            :label="getRow(itemName, fieldName).full_name"
            size="sm"
          />
        </div>
        <div v-if="fieldName === 'due_date' && getRow(itemName, fieldName).label" class="truncate text-base">
          <Tooltip :text="formatDate(getRow(itemName, fieldName).label, 'ddd, MMM D, YYYY | hh:mm a')">
            <span>{{ formatDate(getRow(itemName, fieldName).label, 'D MMM, hh:mm a') }}</span>
          </Tooltip>
        </div>
        <div
          v-else-if="['modified', 'creation'].includes(fieldName)"
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, fieldName).label">
            <div>{{ getRow(itemName, fieldName).timeAgo }}</div>
          </Tooltip>
        </div>
        <div
          v-else-if="fieldName == 'description'"
          class="truncate text-base max-h-44"
        >
          <TextEditor
            v-if="getRow(itemName, fieldName).label"
            :content="getRow(itemName, fieldName).label"
            :editable="false"
            editor-class="!prose-sm max-w-none focus:outline-none"
            class="flex-1 overflow-hidden"
          />
        </div>
        <div v-else class="truncate text-base" :class="isOverdueTask(getTask(itemName)) ? 'text-ink-red-6 font-semibold' : ''">
          {{ getRow(itemName, fieldName).label }}
        </div>
      </div>
    </template>
    <template #actions="{ itemName }">
      <div class="flex gap-2 items-center justify-between">
        <div>
          <Button
            v-if="getRow(itemName, 'reference_docname').label"
            class="-ml-2"
            variant="ghost"
            size="sm"
            :label="
              relatedRecordLabels[getRow(itemName, 'reference_doctype').label]
                ? __(relatedRecordLabels[getRow(itemName, 'reference_doctype').label])
                : getRow(itemName, 'reference_doctype').label
            "
            :iconRight="ArrowUpRightIcon"
            @click.stop="
              redirect(
                getRow(itemName, 'reference_doctype').label,
                getRow(itemName, 'reference_docname').label,
              )
            "
          />
        </div>
        <Dropdown
          class="flex items-center gap-2"
          :options="actions(itemName)"
          variant="ghost"
          @click.stop.prevent
        >
          <Button icon="lucide-more-horizontal" variant="ghost" />
        </Dropdown>
      </div>
    </template>
  </KanbanView>
  <TasksListView
    v-else-if="tasks.data && rows.length"
    ref="tasksListView"
    v-model="tasks.data.page_length_count"
    v-model:list="tasks"
    :rows="rows"
    :columns="columns"
    :isOverdue="isOverdueTask"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: tasks.data.row_count,
      totalCount: tasks.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @showTask="showTask"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="tasks.data && !rows.length"
    name="Tasks"
    :icon="Email2Icon"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import TasksListView from '@/components/ListViews/TasksListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { Tooltip, Avatar, TextEditor, Dropdown, call } from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sessionStore } from '@/stores/session'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Task')
const { getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

const router = useRouter()
const route = useRoute()
const { user } = sessionStore()

const tasksListView = ref(null)

// tasks data is loaded in the ViewControls component
const tasks = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)
const taskStatuses = ['Backlog', 'Todo', 'In Progress', 'Done', 'Canceled']
const myTasksOnly = ref(route.query.my_tasks !== '0')
const statusFilter = ref('')
const dueDateFilter = ref(route.query.due_date_filter || 'All')
const taskFilterKeys = ['assigned_to', 'status', 'due_date', 'due_date_end']

function localDateTime(date) {
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function applyTaskFilters() {
  if (!tasks.value?.params) return
  const filters = { ...(tasks.value.params.filters || {}) }
  taskFilterKeys.forEach((key) => delete filters[key])

  if (myTasksOnly.value && user.value) filters.assigned_to = user.value

  if (dueDateFilter.value === 'Overdue') {
    filters.due_date = ['<', localDateTime(new Date())]
    if (['Done', 'Canceled'].includes(statusFilter.value)) {
      filters.status = '__no_matching_status__'
    } else if (statusFilter.value) {
      filters.status = statusFilter.value
    } else {
      filters.status = ['not in', ['Done', 'Canceled']]
    }
  } else if (dueDateFilter.value === 'Due Today') {
    const start = new Date()
    start.setHours(0, 0, 0, 0)
    const localDate = `${start.getFullYear()}-${String(start.getMonth() + 1).padStart(2, '0')}-${String(start.getDate()).padStart(2, '0')}`
    filters.due_date = ['between', [localDate, localDate]]
    if (statusFilter.value) filters.status = statusFilter.value
  } else if (dueDateFilter.value === 'Upcoming') {
    filters.due_date = ['>', localDateTime(new Date())]
    if (statusFilter.value) filters.status = statusFilter.value
  } else if (statusFilter.value) {
    filters.status = statusFilter.value
  }

  const current = tasks.value.params.filters || {}
  if (JSON.stringify(current) === JSON.stringify(filters)) return
  tasks.value.params.filters = filters
  tasks.value.reload()
}

watch([myTasksOnly, statusFilter, dueDateFilter], () => {
  if (route.query.due_date_filter !== dueDateFilter.value) {
    router.replace({
      query: { ...route.query, due_date_filter: dueDateFilter.value },
    })
  }
  applyTaskFilters()
})
onMounted(() => applyTaskFilters())
watch(
  () => tasks.value?.params,
  () => applyTaskFilters(),
)

function isOverdueTask(task) {
  if (!task?.due_date || ['Done', 'Canceled'].includes(task.status)) return false
  const dueDate = new Date(task.due_date)
  return !Number.isNaN(dueDate.getTime()) && dueDate < new Date()
}

function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object') {
      return value
    }
    return { label: value }
  }
  return getValue(rows.value?.find((row) => row.name == name)?.[field])
}

function getTask(name) {
  const row = rows.value?.find((item) => item.name == name)
  if (row?._task) return row._task
  const data = tasks.value?.data?.data || []
  return data.find((task) => task.name == name) ||
    data.flatMap((column) => column.data || []).find((task) => task.name == name)
}

const rows = computed(() => {
  if (!tasks.value?.data?.data) return []

  if (tasks.value.data.view_type === 'kanban') {
    return getKanbanRows(tasks.value.data.data, tasks.value.data.fields)
  }

  openTaskFromURL()
  return parseRows(tasks.value.data.data, tasks.value?.data.columns)
})

const columns = computed(() => {
  let _columns = tasks.value?.data?.columns || []

  // Set align right for last column
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

function getKanbanRows(data, columns) {
  let _rows = []
  data.forEach((column) => {
    column.data?.forEach((row) => {
      _rows.push(row)
    })
  })
  return parseRows(_rows, columns)
}

function parseRows(rows, columns = []) {
  let view_type = tasks.value.data.view_type
  let key = view_type === 'kanban' ? 'fieldname' : 'key'
  let type = view_type === 'kanban' ? 'fieldtype' : 'type'

  return rows.map((task) => {
    let _rows = {}
    _rows._task = task
    tasks.value?.data.rows.forEach((row) => {
      _rows[row] = task[row]

      let fieldType = columns?.find((col) => (col[key] || col.value) == row)?.[
        type
      ]

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation', 'due_date'].includes(row)
      ) {
        _rows[row] = formatDate(task[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, task)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, task)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, task)
      }

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(task[row])
      } else if (row == 'assigned_to') {
        _rows[row] = {
          label: task.assigned_to && getUser(task.assigned_to).full_name,
          ...(task.assigned_to && getUser(task.assigned_to)),
        }
      }
    })
    return _rows
  })
}

const { showModal } = useDoctypeModal()

const taskCallbacks = {
  afterInsert: () => {
    tasks.value.reload()
    updateOnboardingStep('create_first_task')
    capture('task_created')
  },
  afterUpdate: () => {
    tasks.value.reload()
    capture('task_updated')
  },
}

function showTask(name) {
  showModal({
    name,
    doctype: 'CRM Task',
    title: 'Task',
    callbacks: taskCallbacks,
  })
}

function createTask(column) {
  const defaults = { status: 'Backlog', priority: 'Low' }

  if (column?.column?.name) {
    let column_field = tasks.value.params.column_field
    if (column_field) {
      defaults[column_field] = column.column.name
    }
  }

  showModal({
    doctype: 'CRM Task',
    title: 'Task',
    defaults: defaults,
    callbacks: taskCallbacks,
  })
}

function actions(name) {
  return [
    {
      label: __('Delete'),
      icon: 'trash-2',
      onClick: () => {
        deleteTask(name)
        tasks.value.reload()
      },
    },
  ]
}

async function deleteTask(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Task',
    name,
  })
}

const relatedRecordRoutes = {
  'CRM Lead': (docname) => ({ name: 'LeadDetail', params: { leadId: docname } }),
  'CRM Deal': (docname) => ({ name: 'DealDetail', params: { dealId: docname } }),
  'DoubleT Lead': (docname) => ({
    name: 'LeadDetail',
    params: { leadId: docname },
  }),
  'DoubleT Deal': (docname) => ({
    name: 'DealDetail',
    params: { dealId: docname },
  }),
  'DoubleT Contact': (docname) => ({
    name: 'ContactDetail',
    params: { contactId: docname },
  }),
  'DoubleT Company': (docname) => ({
    name: 'CompanyDetail',
    params: { companyId: docname },
  }),
}

const relatedRecordLabels = {
  'CRM Lead': 'Lead',
  'CRM Deal': 'Deal',
  'DoubleT Lead': 'Lead',
  'DoubleT Deal': 'Deal',
  'DoubleT Contact': 'Contact',
  'DoubleT Company': 'Company',
}

function redirect(doctype, docname) {
  if (!docname) return
  const route = relatedRecordRoutes[doctype]?.(docname)
  if (route) router.push(route)
}

const openTaskFromURL = () => {
  const searchParams = new URLSearchParams(window.location.search)
  const taskName = searchParams.get('open')

  if (taskName && rows.value?.length) {
    showTask(parseInt(taskName))
    searchParams.delete('open')
    window.history.replaceState(null, '', window.location.pathname)
  }
}
</script>
