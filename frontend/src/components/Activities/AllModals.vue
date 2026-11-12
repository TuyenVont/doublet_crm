
<template>
  <TaskModal
    v-model="taskModal.show"
    :name="taskModal.name"
    :defaults="taskModal.defaults"
    :doctype="doctype"
    :doc="doc"
    @after-insert="(d) => afterDoctype(d, true)"
    @after-update="(d) => afterDoctype(d, false)"
  />
</template>

<script setup>
import { reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { useDoctypeModal } from '@/composables/doctypeModal'
import TaskModal from '@/components/Modals/TaskModal.vue'

const props = defineProps({
  doctype: { type: String, default: '' },
  doc: { type: Object, default: () => ({}) },
  docname: { type: String, default: '' },
})

const activities = defineModel({ type: Object })

const emit = defineEmits(['task-changed'])

const { showModal } = useDoctypeModal()
const onboarding = useOnboarding('frappecrm')
const { capture } = useTelemetry()

const route = useRoute()
const router = useRouter()

const taskModal = reactive({
  show: false,
  name: '',
  defaults: {},
})

function referenceDocname() {
  return props.doc?.name || props.docname || ''
}

// ==============================
// TASKS
// ==============================

function showTask(task) {
  taskModal.name = task?.name || ''

  taskModal.defaults = {
    reference_doctype: props.doctype,
    reference_docname: referenceDocname(),
  }

  taskModal.show = true
}

async function deleteTask(name) {
  await call('frappe.client.delete', {
    doctype: 'DoubleT Task',
    name,
  })

  emit('task-changed')
}

async function updateTaskStatus(status, task) {
  await call('frappe.client.set_value', {
    doctype: 'DoubleT Task',
    name: task.name,
    fieldname: 'status',
    value: status,
  })

  emit('task-changed')
}

// ==============================
// NOTES
// ==============================

function showNote(note) {
  showModal({
    name: note?.name,
    doctype: 'DoubleT Note',
    title: 'Note',
    defaults: {
      reference_doctype: props.doctype,
      reference_name: referenceDocname(),
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: (d) => afterDoctype(d, false),
    },
  })
}

// ==============================
// AFTER SAVE / UPDATE
// ==============================

function afterDoctype(d, isInsert = false) {
  if (!d) return

  // DoubleT Task uses its own resource.
  if (d.doctype === 'DoubleT Task') {
    emit('task-changed')
    redirect('tasks')
    return
  }

  // Preserve legacy Notes / Call Logs behavior.
  activities.value?.reload?.()

  const name =
    d.doctype === 'DoubleT Note'
      ? 'note'
      : 'call_log'

  const redirectHash =
    d.doctype === 'DoubleT Call Log'
      ? 'calls'
      : name + 's'

  if (isInsert) {
    try {
      onboarding?.updateOnboardingStep?.(
        'create_first_' + name,
      )
    } catch (error) {
      console.warn('Onboarding update failed:', error)
    }

    try {
      capture(name + '_created')
    } catch (error) {
      console.warn('Telemetry failed:', error)
    }
  } else {
    try {
      capture(name + '_updated')
    } catch (error) {
      console.warn('Telemetry failed:', error)
    }
  }

  redirect(redirectHash)
}

// ==============================
// CALL LOGS
// ==============================

function createCallLog() {
  showModal({
    doctype: 'DoubleT Call Log',
    title: 'Call Log',
    defaults: {
      reference_doctype: props.doctype,
      reference_name: referenceDocname(),
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: (d) => afterDoctype(d, false),
    },
  })
}

// ==============================
// NAVIGATION
// ==============================

function redirect(tabName) {
  const supportedRoutes = [
    'Lead',
    'Deal',
    'LeadDetail',
    'DealDetail',
    'ContactDetail',
    'CompanyDetail',
  ]

  if (!supportedRoutes.includes(route.name)) return

  const hash = '#' + tabName

  if (route.hash !== hash) {
    router.push({
      path: route.path,
      query: route.query,
      hash,
    })
  }
}

// ==============================
// EXPOSE TO ACTIVITY HEADER
// ==============================

defineExpose({
  showTask,
  deleteTask,
  updateTaskStatus,
  showNote,
  createCallLog,
})
</script>
