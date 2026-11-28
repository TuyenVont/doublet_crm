<template>
  <div class="flex flex-wrap items-center gap-2">
    <Button v-for="action in conversation.actions" :key="action" :label="actionLabel(action)" @click="open(action)" />
    <Button v-if="conversation.history?.length" :label="__('Handling history')" @click="open('History')" />
  </div>

  <Dialog v-model="dialogOpen" :options="{ title: actionLabel(action) }">
    <template #body-content>
      <ol v-if="action === 'History'" class="max-h-80 space-y-3 overflow-y-auto text-sm">
        <li v-for="event in history" :key="event.name" class="border-b border-outline-gray-2 pb-3">
          <p class="font-medium">{{ __(event.action) }}</p>
          <p class="break-all text-ink-gray-6">{{ event.actor }} · {{ event.occurred_at }}</p>
          <p v-if="event.previous_assignee || event.new_assignee" class="break-all">
            {{ event.previous_assignee || __('Unassigned') }} → {{ event.new_assignee || __('Unassigned') }}
          </p>
          <p v-if="event.customer" class="break-all">
            {{ event.previous_customer ? `${event.previous_customer} → ` : '' }}{{ event.customer_type }} · {{ event.customer }}
          </p>
          <p v-if="event.reason" class="mt-1 whitespace-pre-wrap break-words">{{ event.reason }}</p>
        </li>
      </ol>
      <form v-else class="space-y-3" @submit.prevent="save">
        <label v-if="action === 'Assign'" class="block space-y-1.5 text-sm">
          <span>{{ __('Assignee') }}</span>
          <select v-model="assignee" :disabled="loading" class="block w-full rounded-md border border-outline-gray-3 px-2 py-2" required>
            <option value="" disabled>{{ __('Select an employee') }}</option>
            <option v-for="user in assignees" :key="user.name" :value="user.name">
              {{ user.full_name }} · {{ user.name }}
            </option>
          </select>
        </label>
        <template v-if="action === 'Link Customer'">
          <label class="block space-y-1.5 text-sm">
            <span>{{ __('CRM record type') }}</span>
            <select v-model="customerType" class="block w-full rounded-md border border-outline-gray-3 px-2 py-2" @change="customerName = ''">
              <option value="DoubleT Lead">{{ __('Lead') }}</option>
              <option value="DoubleT Contact">{{ __('Contact') }}</option>
            </select>
          </label>
          <Link :key="customerType" v-model="customerName" :doctype="customerType" :label="__('Search by name, email or phone')" />
          <p v-if="customerName" class="break-all text-sm">
            {{ __('Confirm CRM record ID {0} for OA {1}, Zalo user {2}.', [customerName, conversation.oa_id, conversation.external_user_id]) }}
          </p>
        </template>
        <FormControl v-if="action === 'Create Lead'" v-model="leadName" :label="__('Lead name')" maxlength="140" />
        <FormControl v-if="action !== 'Create Lead'" v-model="reason" type="textarea" :label="reasonRequired ? __('Reason (required)') : __('Reason')" maxlength="500" />
        <p v-if="error" class="break-words text-sm text-red-700" role="alert">{{ error }}</p>
        <Button type="submit" variant="solid" :loading="saving" :disabled="!canSave" :label="actionLabel(action)" />
      </form>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, Dialog, FormControl, call } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { newZaloRequestId } from '@/utils/zaloInbox'

const props = defineProps({ conversation: { type: Object, required: true } })
const emit = defineEmits(['changed'])
const dialogOpen = ref(false)
const action = ref('')
const assignee = ref('')
const assignees = ref([])
const customerType = ref('DoubleT Lead')
const customerName = ref('')
const leadName = ref('')
const reason = ref('')
const error = ref('')
const saving = ref(false)
const loading = ref(false)
let version
let previousRequest

const history = computed(() => [...(props.conversation.history || [])].reverse())
const reasonRequired = computed(() => (
  (action.value === 'Assign' && !!props.conversation.assigned_to)
  || (action.value === 'Link Customer' && props.conversation.customer_linked)
))
const canSave = computed(() => !saving.value && !loading.value && (
  action.value !== 'Assign' || !!assignee.value
) && (
  action.value !== 'Link Customer' || !!customerName.value
) && (
  action.value !== 'Create Lead' || !!leadName.value.trim()
) && (
  !reasonRequired.value || !!reason.value.trim()
))

function actionLabel(value) {
  if (value === 'Assign' && props.conversation.assigned_to) return __('Transfer')
  if (value === 'History') return __('Handling history')
  if (value === 'Link Customer' && props.conversation.customer_linked) return __('Change customer link')
  return __(value)
}

async function open(value) {
  action.value = value
  version = props.conversation.version
  assignee.value = customerName.value = leadName.value = reason.value = error.value = ''
  customerType.value = 'DoubleT Lead'
  dialogOpen.value = true
  if (value !== 'Assign') return
  loading.value = true
  try {
    const users = await call('doublet_crm.zalo_workflow.list_assignees')
    assignees.value = users.filter((user) => user.name !== props.conversation.assigned_to)
  } catch {
    assignees.value = []
    error.value = __('Could not load assignees. Reopen the dialog to retry.')
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!canSave.value) return
  const payload = {
    conversation: props.conversation.name,
    action: action.value,
    version,
    assignee: assignee.value || undefined,
    reason: reason.value.trim() || undefined,
    customer_type: action.value === 'Link Customer' ? customerType.value : undefined,
    customer_name: customerName.value || undefined,
    lead_name: leadName.value.trim() || undefined,
  }
  const signature = JSON.stringify(payload)
  if (previousRequest?.signature !== signature) {
    previousRequest = { signature, id: newZaloRequestId() }
  }
  saving.value = true
  error.value = ''
  try {
    await call('doublet_crm.zalo_workflow.update_conversation', { ...payload, request_id: previousRequest.id })
    dialogOpen.value = false
    emit('changed')
  } catch (e) {
    error.value = e?.messages?.[0] || __('Could not update the conversation. Refresh or try again.')
  } finally {
    saving.value = false
  }
}
</script>
