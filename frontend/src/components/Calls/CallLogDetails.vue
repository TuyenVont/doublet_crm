<template>
  <CallLogDetailModal
    v-if="log"
    :model-value="true"
    v-model:section="section"
    :call-log="log"
    @update:model-value="close"
  >
    <template #feedback>
      <p v-if="actionError" class="shrink-0 border-b border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-800 sm:px-6" role="alert">
        {{ actionError }}
      </p>
      <p v-else-if="actionSuccess" class="shrink-0 border-b border-green-200 bg-green-50 px-4 py-2.5 text-sm text-green-800 sm:px-6" role="status">
        {{ actionSuccess }}
      </p>
    </template>

    <template #customer-actions>
      <form
        v-if="log.can_link"
        class="mt-3 grid gap-3 border-t border-outline-gray-2 pt-3"
        @submit.prevent="linkCustomer"
      >
        <FormControl
          v-model="customerType"
          type="select"
          :label="__('Customer type')"
          :options="customerTypes"
          :disabled="saving"
        />
        <Link
          :key="customerType"
          v-model="customerName"
          :doctype="customerType"
          :placeholder="__('Search by customer or phone number')"
          :disabled="saving"
        />
        <Button
          type="submit"
          :label="__('Link customer')"
          :loading="saving"
          :disabled="saving || !customerName"
          class="justify-self-start"
        />
      </form>
    </template>

    <template #handling>
      <div class="space-y-3 sm:space-y-4">
        <section class="rounded-xl border border-outline-gray-2 bg-white p-3.5 sm:p-4">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <h3 class="text-sm font-semibold text-ink-gray-9">{{ __('Assignment') }}</h3>
            <Badge
              :label="__(log.handling_status || 'History only')"
              :theme="caseStatusTheme[log.handling_status]"
            />
          </div>

          <dl class="mt-3 space-y-0.5">
            <dt class="text-xs text-ink-gray-5">{{ __('Assignee') }}</dt>
            <dd class="break-words text-sm font-medium text-ink-gray-9">{{ log.assignee_label || __('Unassigned') }}</dd>
          </dl>

          <form
            v-if="log.can_manage && isOpen"
            class="mt-3 grid gap-3 border-t border-outline-gray-2 pt-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end"
            @submit.prevent="updateCall('assign_call', { assignee: assigneeDraft })"
          >
            <FormControl
              v-model="assigneeDraft"
              type="select"
              :label="__('Assign to')"
              :options="assigneeOptions"
              :disabled="saving || assigneesLoading || Boolean(assigneeError)"
              class="min-w-0"
            />
            <Button
              type="submit"
              :label="__(log.assigned_to ? 'Transfer case' : 'Assign case')"
              :disabled="saving || assigneesLoading || Boolean(assigneeError) || assigneeDraft === (log.assigned_to || '')"
              :loading="saving"
              class="justify-self-start"
            />
            <div v-if="assigneeError" class="flex flex-wrap items-center gap-2 sm:col-span-2" role="alert">
              <span class="text-sm text-red-700">{{ assigneeError }}</span>
              <Button type="button" variant="subtle" :label="__('Retry')" @click="loadAssignees" />
            </div>
          </form>

          <Button
            v-if="!log.callback_required && log.handling_status === 'Waiting' && log.assigned_to"
            class="mt-3"
            variant="solid"
            :label="__('Start case')"
            :loading="saving"
            :disabled="saving"
            @click="updateCall('start_call')"
          />
        </section>

        <section v-if="log.callback_required" class="space-y-3 rounded-xl border border-outline-gray-2 bg-white p-3.5 sm:p-4">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <h3 class="text-sm font-semibold text-ink-gray-9">{{ __('Callback task') }}</h3>
            <Badge
              v-if="log.callback_task"
              :label="__(log.callback_task.status)"
              :theme="log.callback_task.status === 'Done' ? 'green' : 'gray'"
            />
          </div>
          <div v-if="log.callback_task" class="space-y-2">
            <RouterLink
              :to="{ name: 'Tasks', query: { task: log.callback_task.name } }"
              class="inline-flex items-center gap-1.5 text-sm font-medium text-ink-blue-6 hover:underline"
            >
              {{ __('Open callback task') }}
              <FeatherIcon name="arrow-up-right" class="size-3.5" aria-hidden="true" />
            </RouterLink>
            <div v-if="log.callback_task.callback_result || log.callback_task.callback_notes" class="space-y-1 rounded-md bg-surface-gray-1 p-2.5">
              <p v-if="log.callback_task.callback_result" class="text-sm text-ink-gray-8">
                {{ __('Last callback outcome') }} · {{ __(log.callback_task.callback_result) }}
              </p>
              <p v-if="log.callback_task.callback_notes" class="whitespace-pre-wrap break-words text-sm text-ink-gray-7">
                {{ log.callback_task.callback_notes }}
              </p>
            </div>
          </div>
          <p v-else-if="!log.assigned_to" class="text-sm text-ink-gray-6">
            {{ __('Assign this case before creating a callback task.') }}
          </p>

          <form v-if="isOpen && hasOpenTask" class="grid gap-3 border-t border-outline-gray-2 pt-3" @submit.prevent="saveCallbackResult">
            <FormControl
              v-model="outcome"
              type="select"
              :label="__('Callback outcome')"
              :options="callbackResults"
              :disabled="saving"
            />
            <FormControl
              v-model="notes"
              type="textarea"
              :label="__('Callback notes')"
              :disabled="saving"
              maxlength="2000"
            />
            <Button
              type="submit"
              :label="__('Save outcome')"
              :loading="saving"
              :disabled="saving || !outcome"
              class="justify-self-start"
            />
          </form>

          <Button
            v-if="isOpen && log.assigned_to && !hasOpenTask"
            variant="solid"
            :label="__(log.callback_task ? 'Reopen callback task' : 'Create callback task')"
            :loading="saving"
            :disabled="saving"
            @click="updateCall('open_callback')"
          />
          <div v-if="isOpen && needsCustomerLink" class="space-y-2 rounded-md bg-amber-50 p-2.5 text-sm text-amber-900">
            <p>{{ __('Link a Lead or Contact before resolving this missed call.') }}</p>
            <Button v-if="log.can_link" :label="__('Link a customer')" @click="showCustomerForm" />
          </div>
        </section>
      </div>
    </template>

    <template #history>
      <section class="rounded-xl border border-outline-gray-2 bg-white p-3.5 sm:p-4">
        <h3 class="text-sm font-semibold text-ink-gray-9">{{ __('Case history') }}</h3>
        <p v-if="!log.history?.length" class="mt-2 text-sm text-ink-gray-6">
          {{ __('No case activity yet.') }}
        </p>
        <ol v-else class="ml-1 mt-3 space-y-4 border-l border-outline-gray-2 pl-4">
          <li v-for="event in log.history" :key="event.name" class="relative text-sm text-ink-gray-8">
            <span class="absolute -left-[20px] top-1.5 size-[7px] rounded-full bg-surface-gray-5" aria-hidden="true" />
            <div class="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-0.5">
              <span class="font-medium text-ink-gray-9">{{ __(event.action) }}</span>
              <time class="text-xs text-ink-gray-5">{{ formatCallTime(event.occurred_at) }}</time>
            </div>
            <p class="break-words text-ink-gray-6">{{ event.actor_label }}</p>
            <p v-if="event.action === 'Assignment changed'" class="mt-1 break-words">
              {{ event.previous_label || __('Unassigned') }} → {{ event.new_label || __('Unassigned') }}
            </p>
            <p v-if="event.details" class="mt-1 whitespace-pre-wrap break-words text-ink-gray-7">{{ event.details }}</p>
          </li>
        </ol>
      </section>
    </template>

    <template v-if="canResolve" #footer>
      <footer class="flex shrink-0 justify-end border-t border-outline-gray-2 bg-white px-4 py-3 sm:px-6">
        <Button
          variant="solid"
          :label="__('Resolve case')"
          :loading="saving"
          :disabled="saving"
          @click="updateCall('resolve_call')"
        />
      </footer>
    </template>
  </CallLogDetailModal>

  <Dialog
    v-else
    :model-value="true"
    :options="{ title: __('Call details') }"
    @update:model-value="close"
  >
    <template #body-content>
      <div v-if="error" class="space-y-3">
        <p class="text-sm text-red-700" role="alert">{{ error }}</p>
        <Button variant="subtle" :label="__('Retry')" @click="loadCall(callId)" />
      </div>
      <p v-else class="text-sm text-ink-gray-5" role="status">{{ __('Loading call…') }}</p>
    </template>
  </Dialog>
</template>

<script setup>
import { Badge, Button, Dialog, FeatherIcon, FormControl, call } from 'frappe-ui'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CallLogDetailModal from '@/components/Modals/CallLogDetailModal.vue'
import Link from '@/components/Controls/Link.vue'
import { globalStore } from '@/stores/global'
import { callCustomerRoute, caseStatusTheme, formatCallTime } from '@/utils/contactCenterCalls'

const props = defineProps({ callId: { type: String, required: true } })
const emit = defineEmits(['changed'])
const route = useRoute()
const router = useRouter()
const { $socket } = globalStore()
const log = ref(null)
const section = ref('overview')
const error = ref('')
const actionError = ref('')
const actionSuccess = ref('')
const assignees = ref([])
const assigneesLoading = ref(false)
const assigneeError = ref('')
const assigneesLoaded = ref(false)
const assigneeDraft = ref('')
const saving = ref(false)
const outcome = ref('')
const notes = ref('')
const customerType = ref('DoubleT Contact')
const customerName = ref('')
const isOpen = computed(() => ['Waiting', 'In Progress'].includes(log.value?.handling_status))
const assigneeOptions = computed(() => {
  const options = assignees.value.map((user) => ({ value: user.name, label: user.full_name || user.name }))
  if (log.value?.assigned_to && !options.some((option) => option.value === log.value.assigned_to)) {
    options.unshift({ value: log.value.assigned_to, label: log.value.assignee_label })
  }
  if (log.value?.handling_status === 'Waiting') options.unshift({ value: '', label: __('Unassigned') })
  return options
})
const hasOpenTask = computed(() => ['Backlog', 'Todo', 'In Progress'].includes(log.value?.callback_task?.status))
const needsCustomerLink = computed(() => log.value?.callback_required && log.value.link_state !== 'Linked')
const canResolve = computed(() => log.value?.can_handle &&
  log.value.handling_status === 'In Progress' &&
  !needsCustomerLink.value &&
  (!log.value.callback_required || (hasOpenTask.value && log.value.callback_task.callback_result === 'Reached')),
)
const callbackResults = [
  { value: '', label: __('Select outcome') },
  { value: 'No Answer', label: __('No Answer') },
  { value: 'Reached', label: __('Customer reached') },
]
const customerTypes = [
  { value: 'DoubleT Contact', label: __('Contact') },
  { value: 'DoubleT Lead', label: __('Lead') },
]
const successMessages = {
  assign_call: 'Assignment updated.',
  link_customer: 'Customer linked.',
  start_call: 'Case started.',
  open_callback: 'Callback task ready.',
  record_callback_result: 'Callback outcome saved.',
  resolve_call: 'Case resolved.',
}
let requestId = 0
let refreshPending = false

watch(customerType, () => { customerName.value = '' })
watch(() => log.value?.assigned_to, (assignee) => { assigneeDraft.value = assignee || '' })
watch(() => section.value === 'handling' && log.value?.can_manage && isOpen.value, (available) => {
  if (available && !assigneesLoaded.value && !assigneesLoading.value) loadAssignees()
})

async function loadAssignees() {
  assigneesLoading.value = true
  assigneeError.value = ''
  try {
    const [, users] = await call('doublet_crm.api.get_assignment_users')
    assignees.value = users
    assigneesLoaded.value = true
  } catch (e) {
    assigneeError.value = e.messages?.[0] || __('Unable to load assignees.')
  } finally {
    assigneesLoading.value = false
  }
}

function resetCaseDrafts() {
  section.value = 'overview'
  outcome.value = ''
  notes.value = ''
  actionError.value = ''
  actionSuccess.value = ''
}

async function loadCall(name, background = false) {
  const id = ++requestId
  if (!background) {
    log.value = null
    error.value = ''
    customerName.value = ''
    resetCaseDrafts()
  }
  try {
    const result = await call('doublet_crm.contact_center_calls.get_call', { name })
    if (id !== requestId) return
    if (log.value?.can_handle && !result.can_handle) resetCaseDrafts()
    log.value = result
  } catch (e) {
    if (id === requestId) {
      resetCaseDrafts()
      log.value = null
      error.value = e.messages?.[0] || __('Unable to open this call.')
    }
  }
}

function refreshOnCaseChange(message) {
  if (message?.name !== props.callId) return
  if (saving.value) refreshPending = true
  else loadCall(props.callId, true)
}

watch(() => props.callId, (name) => loadCall(name), { immediate: true })
onMounted(() => $socket?.on('doublet_calls_changed', refreshOnCaseChange))
onUnmounted(() => {
  requestId++
  $socket?.off('doublet_calls_changed', refreshOnCaseChange)
})

async function showCustomerForm() {
  section.value = 'overview'
  await nextTick()
  document.getElementById('call-customer-details')?.scrollIntoView({ block: 'nearest' })
}

async function linkCustomer() {
  if (!customerName.value) return
  const linked = await updateCall('link_customer', {
    doctype: customerType.value,
    customer_name: customerName.value,
  })
  if (linked) customerName.value = ''
}

async function updateCall(method, values = {}) {
  if (saving.value) return false
  // A local mutation supersedes any background refresh already in flight.
  const id = ++requestId
  saving.value = true
  actionError.value = ''
  actionSuccess.value = ''
  try {
    const result = await call('doublet_crm.contact_center_calls.' + method, { name: props.callId, ...values })
    if (id !== requestId) return false
    log.value = result
    actionSuccess.value = __(successMessages[method])
    emit('changed')
    return true
  } catch (e) {
    if (id === requestId) actionError.value = e.messages?.[0] || __('Unable to update the call.')
    return false
  } finally {
    saving.value = false
    if (refreshPending && id === requestId) {
      refreshPending = false
      loadCall(props.callId, true)
    }
  }
}

async function saveCallbackResult() {
  if (!outcome.value) return
  if (await updateCall('record_callback_result', { outcome: outcome.value, notes: notes.value })) {
    outcome.value = ''
    notes.value = ''
  }
}

function close() {
  if (route.query.from === 'task' && log.value?.callback_task) {
    return router.push({ name: 'Tasks', query: { task: log.value.callback_task.name } })
  }
  if (route.query.from === 'customer') {
    const target = callCustomerRoute(log.value?.customer)
    if (target) return router.push(target)
  }
  return router.push({ name: route.name === 'CallHistoryDetail' ? 'Call Logs' : 'Calls' })
}
</script>
