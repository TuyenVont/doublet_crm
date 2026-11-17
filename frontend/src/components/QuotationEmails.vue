<template>
  <section
    class="rounded-lg border border-outline-gray-2 bg-surface-white"
    :class="isQuotation ? 'overflow-hidden' : 'm-4 flex-1 overflow-y-auto'"
  >
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-outline-gray-2 px-4 py-3">
      <div>
        <h2 class="text-sm font-semibold text-ink-gray-9">{{ isQuotation ? __('Quotation Emails') : __('Emails') }}</h2>
        <p class="mt-1 text-xs text-ink-gray-5">{{ description }}</p>
      </div>
      <div class="flex gap-2">
        <Button :label="__('Refresh')" :loading="loading" @click="refreshEmails" />
        <Button
          v-if="canSendPdf"
          variant="solid"
          :label="__('Send quotation PDF')"
          @click="emit('send-pdf')"
        />
      </div>
    </div>

    <div v-if="loading && !emails.length" class="p-8 text-center text-sm text-ink-gray-5">
      {{ __('Loading emails…') }}
    </div>
    <div v-else-if="error" class="flex flex-col items-center gap-3 p-8 text-center">
      <p class="text-sm text-red-700" role="alert">{{ error }}</p>
      <Button :label="__('Retry')" @click="loadEmails" />
    </div>
    <div v-else-if="!emails.length" class="p-8 text-center text-sm text-ink-gray-5">
      <p class="font-medium text-ink-gray-7">{{ emptyTitle }}</p>
      <p class="mt-1">{{ emptyDescription }}</p>
    </div>
    <div v-else class="divide-y divide-outline-gray-2">
      <article v-for="item in emails" :key="item.name" class="space-y-3 p-4">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <Badge
                :label="item.sent_or_received === 'Received' ? __('Received') : __('Outgoing')"
                variant="subtle"
                :theme="item.sent_or_received === 'Received' ? 'blue' : 'green'"
              />
              <Badge
                v-if="item.sent_or_received === 'Sent' && item.delivery_status"
                :label="__(item.delivery_status)"
                variant="subtle"
                :theme="statusTheme(item.delivery_status)"
              />
              <span class="text-xs text-ink-gray-5">{{ formatTimestamp(item.communication_date) }}</span>
              <button
                v-if="item.quotation"
                type="button"
                class="text-xs font-medium text-ink-blue-3 hover:underline"
                @click="openQuotation(item.quotation)"
              >
                {{ item.quotation }} ↗
              </button>
            </div>
            <h3 class="mt-2 break-words text-base font-medium text-ink-gray-9">{{ item.subject || __('(No subject)') }}</h3>
            <dl class="mt-2 grid gap-1 text-sm text-ink-gray-7">
              <div><dt class="inline text-ink-gray-5">{{ __('From') }}:</dt> <dd class="inline">{{ sender(item) }}</dd></div>
              <div><dt class="inline text-ink-gray-5">{{ __('To') }}:</dt> <dd class="inline">{{ item.recipients || '—' }}</dd></div>
              <div v-if="item.cc"><dt class="inline text-ink-gray-5">{{ __('CC') }}:</dt> <dd class="inline">{{ item.cc }}</dd></div>
            </dl>
          </div>
          <Button
            v-if="canReply && item.sent_or_received === 'Received' && item.reply_to"
            :label="__('Reply')"
            variant="subtle"
            @click="startReply(item)"
          />
        </div>

        <div class="rounded-md border border-outline-gray-2 p-3">
          <EmailContent :key="`${item.name}:${item.content}`" :content="item.content || ''" />
        </div>

        <p v-if="item.delivery_error" class="text-sm text-red-700" role="alert">
          {{ item.delivery_error }}
        </p>

        <div v-if="item.attachments?.length" class="flex flex-wrap items-center gap-2">
          <span class="text-xs text-ink-gray-5">{{ __('Attachments') }}:</span>
          <AttachmentItem
            v-for="attachment in item.attachments"
            :key="attachment.name"
            :label="attachment.file_name"
            :url="attachment.file_url"
          />
        </div>

      </article>
    </div>
  </section>

  <Dialog
    v-model:open="showReplyDialog"
    :title="__('Reply to quotation email')"
    size="3xl"
    :dismissible="!sendingReply"
    :showCloseButton="!sendingReply"
  >
    <form class="flex max-h-[80vh] min-h-0 flex-col" @submit.prevent="submitReply">
      <div class="min-h-0 flex-1 space-y-4 overflow-y-auto px-1 pb-4">
        <label class="email-field">{{ __('To') }}
          <TextInput v-model="draft.recipient" type="email" required disabled />
        </label>
        <p class="text-xs text-ink-gray-5">{{ __('Recipient is taken from the original received email.') }}</p>
        <label class="email-field">{{ __('Subject') }}
          <TextInput v-model="draft.subject" maxlength="140" required :disabled="sendingReply" />
        </label>
        <label class="email-field">{{ __('Message') }}
          <textarea v-model="draft.body" rows="9" maxlength="10000" required :disabled="sendingReply" />
        </label>
        <p v-if="replyError" class="text-sm text-red-700" role="alert">{{ replyError }}</p>
      </div>
      <div class="flex shrink-0 flex-wrap justify-end gap-2 border-t border-outline-gray-2 bg-surface-white pt-3">
        <Button type="button" :label="__('Cancel')" :disabled="sendingReply" @click="cancelReply" />
        <Button type="submit" variant="solid" :label="__('Send reply')" :loading="sendingReply" />
      </div>
    </form>
  </Dialog>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Badge, Button, Dialog, TextInput, call } from 'frappe-ui'
import AttachmentItem from '@/components/AttachmentItem.vue'
import EmailContent from '@/components/Activities/EmailContent.vue'
import { message } from '@/utils/quotation'

const props = defineProps({
  quotation: { type: String, default: '' },
  referenceDoctype: { type: String, default: '' },
  referenceName: { type: String, default: '' },
  status: { type: String, default: '' },
  canWrite: { type: Boolean, default: false },
  refreshKey: { type: Number, default: 0 },
})
const emit = defineEmits(['send-pdf'])
const router = useRouter()

const emails = ref([])
const loading = ref(false)
const error = ref('')
const apiCanWrite = ref(false)
const replyingTo = ref('')
const showReplyDialog = ref(false)
const sendingReply = ref(false)
const replyError = ref('')
const draft = reactive({ recipient: '', subject: '', body: '' })
let requestSerial = 0
let pollTimer = null
let pollAttempts = 0
const maxPollAttempts = 15

const canReply = computed(() => props.canWrite && apiCanWrite.value)
const canSendPdf = computed(() => canReply.value && props.status === 'Draft')
const isQuotation = computed(() => Boolean(props.quotation))
const description = computed(() => isQuotation.value
  ? __('Incoming and outgoing email linked to this quotation.')
  : __('Email linked directly to this record and email from its related quotations.'))
const emptyTitle = computed(() => isQuotation.value
  ? __('No emails linked to this quotation yet.')
  : __('No emails linked to this record yet.'))
const emptyDescription = computed(() => isQuotation.value
  ? __('New incoming messages and quotation emails will appear here.')
  : __('Direct messages and related quotation emails will appear here.'))

function stopPolling() {
  clearTimeout(pollTimer)
  pollTimer = null
}

function schedulePolling() {
  stopPolling()
  if (!emails.value.some((item) => item.sent_or_received === 'Sent' && item.delivery_status === 'Queued')) return
  if (pollAttempts >= maxPollAttempts) return
  pollTimer = setTimeout(async () => {
    pollAttempts += 1
    await loadEmails(true)
  }, 2000)
}

async function loadEmails(background = false) {
  const request = ++requestSerial
  if (!background) loading.value = true
  error.value = ''
  try {
    const method = isQuotation.value
      ? 'doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email.get_quotation_emails'
      : 'doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email.get_record_emails'
    const params = isQuotation.value
      ? { name: props.quotation }
      : { reference_doctype: props.referenceDoctype, reference_name: props.referenceName }
    const result = await call(method, params)
    if (request !== requestSerial) return
    emails.value = result.emails || []
    apiCanWrite.value = Boolean(result.can_write)
    schedulePolling()
  } catch (exception) {
    if (request === requestSerial) error.value = message(exception) || __('Unable to load emails.')
  } finally {
    if (request === requestSerial && !background) loading.value = false
  }
}

function refreshEmails() {
  pollAttempts = 0
  return loadEmails()
}

function sender(item) {
  return item.sender_full_name ? `${item.sender_full_name} <${item.sender}>` : (item.sender || '—')
}

function formatTimestamp(value) {
  if (!value) return ''
  const date = new Date(String(value).replace(' ', 'T'))
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function statusTheme(status) {
  if (status === 'Sent') return 'green'
  if (status === 'Failed') return 'red'
  if (status === 'Unknown') return 'gray'
  return 'orange'
}

function openQuotation(quotation) {
  router.push({ name: 'QuotationDetail', params: { quotationId: quotation } })
}

function startReply(item) {
  replyingTo.value = item.name
  draft.recipient = item.reply_to || ''
  draft.subject = /^Re:/i.test(item.subject || '') ? item.subject : `Re: ${item.subject || ''}`
  draft.body = ''
  replyError.value = ''
  showReplyDialog.value = true
}

function cancelReply() {
  showReplyDialog.value = false
  replyingTo.value = ''
  replyError.value = ''
}

async function submitReply() {
  if (sendingReply.value || !replyingTo.value) return
  sendingReply.value = true
  replyError.value = ''
  try {
    await call(
      'doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email.reply_quotation_email',
      {
        name: props.quotation,
        communication: replyingTo.value,
        recipient: draft.recipient,
        subject: draft.subject,
        body: draft.body,
      },
    )
    showReplyDialog.value = false
    replyingTo.value = ''
    draft.body = ''
    pollAttempts = 0
    await loadEmails()
  } catch (exception) {
    replyError.value = message(exception) || __('Unable to send the reply.')
  } finally {
    sendingReply.value = false
  }
}

watch(() => [props.quotation, props.referenceDoctype, props.referenceName, props.refreshKey], () => {
  stopPolling()
  emails.value = []
  showReplyDialog.value = false
  replyingTo.value = ''
  pollAttempts = 0
  loadEmails()
})
onMounted(refreshEmails)
onBeforeUnmount(stopPolling)
</script>

<style scoped>
.email-field { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.875rem; }
textarea { width: 100%; border: 1px solid #d1d5db; border-radius: 0.25rem; padding: 0.5rem; background: white; }
</style>
