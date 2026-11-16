<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <p v-if="threadError" class="bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
      {{ threadError }}
    </p>
    <div ref="history" class="min-h-0 flex-1 overflow-y-auto bg-surface-gray-1 px-4 py-4 md:px-6">
      <div v-if="moreMessages" class="mb-4 text-center">
        <Button
          :label="__('Load older messages')"
          :loading="threadPending"
          :disabled="sending"
          @click="loadThread(true)"
        />
      </div>
      <p v-if="threadPending && !messages.length" class="text-center text-sm text-ink-gray-5">
        {{ __('Loading messages…') }}
      </p>
      <p v-else-if="!threadError && !messages.length" class="text-center text-sm text-ink-gray-5">
        {{ __('No messages yet.') }}
      </p>
      <ol class="space-y-3" :aria-label="__('Message history')">
        <li
          v-for="message in messages"
          :key="message.name"
          class="w-fit max-w-[85%] rounded-xl border px-4 py-2 shadow-sm md:max-w-[70%]"
          :class="message.direction === 'outbound' ? 'ml-auto border-blue-200 bg-blue-50' : 'border-outline-gray-2 bg-white'"
        >
          <p class="whitespace-pre-wrap break-words text-sm [overflow-wrap:anywhere]">{{ message.content }}</p>
          <p class="mt-2 flex flex-wrap gap-x-2 text-xs text-ink-gray-5">
            <span>{{ message.direction === 'outbound' ? __('Outbound') : __('Inbound') }}</span>
            <span>{{ message.sent_at }}</span>
            <span v-if="message.is_simulated">
              {{ message.direction === 'outbound' ? __('Mock reply') : __('Mock inbound') }}
            </span>
          </p>
        </li>
      </ol>
    </div>

    <form v-if="canReply" class="space-y-2 border-t border-outline-gray-2 p-4" @submit.prevent="saveReply">
      <label :for="replyId" class="block text-sm font-medium">{{ __('Simulated reply') }}</label>
      <textarea
        :id="replyId"
        v-model="draft"
        rows="2"
        maxlength="10000"
        class="block w-full resize-y rounded-md border border-outline-gray-3 px-3 py-2 text-sm focus:border-outline-gray-5"
        :placeholder="__('Write a reply…')"
        @compositionstart="isComposing = true"
        @compositionend="isComposing = false"
        @keydown="onComposerKeydown"
      />
      <div class="flex flex-wrap items-center justify-between gap-2">
        <p class="text-xs text-ink-gray-5">{{ __('This reply is simulated and saved to the shared conversation history.') }}</p>
        <Button
          type="submit"
          variant="solid"
          :label="__('Save mock reply')"
          :loading="sending"
          :disabled="sending || threadPending || !draft.trim()"
        />
      </div>
      <p v-if="replyError" class="text-sm text-red-700" role="alert">{{ replyError }}</p>
    </form>
    <p v-else-if="!threadPending && !threadError" class="border-t border-outline-gray-2 p-4 text-sm text-ink-gray-5">
      {{ __('You can read this conversation, but you do not have permission to save replies.') }}
    </p>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { Button, call } from 'frappe-ui'

const props = defineProps({
  conversation: { type: Object, required: true },
  messageMethod: { type: String, default: 'doublet_crm.zalo_inbox.get_messages' },
  replyMethod: { type: String, default: 'doublet_crm.zalo_inbox.save_mock_reply' },
  requestContext: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['reply-saved'])

const messages = ref([])
const history = ref(null)
const canReply = ref(false)
const moreMessages = ref(false)
const threadPending = ref(false)
const sending = ref(false)
const draft = ref('')
const threadError = ref('')
const replyError = ref('')
const isComposing = ref(false)
let threadRequest = 0

const conversationName = computed(() => props.conversation?.name || '')
const contextKey = computed(() => JSON.stringify(props.requestContext || {}))
const replyId = computed(() => `zalo-reply-${conversationName.value}`)

function resetThread() {
  ++threadRequest
  messages.value = []
  canReply.value = false
  moreMessages.value = false
  draft.value = ''
  threadError.value = ''
  replyError.value = ''
  threadPending.value = false
  sending.value = false
}

async function loadThread(prepend = false) {
  const conversation = conversationName.value
  if (!conversation) return
  const request = ++threadRequest
  const oldHeight = history.value?.scrollHeight || 0
  threadPending.value = true
  threadError.value = ''
  try {
    const before = prepend ? messages.value[0]?.name : undefined
    const result = await call(props.messageMethod, {
      ...props.requestContext,
      conversation,
      before,
    })
    if (request !== threadRequest || conversation !== conversationName.value) return
    canReply.value = result.can_reply
    moreMessages.value = result.has_more
    messages.value = prepend ? [...result.messages, ...messages.value] : result.messages
    await nextTick()
    if (request === threadRequest && history.value) {
      const newHeight = history.value.scrollHeight
      history.value.scrollTop = prepend ? newHeight - oldHeight : newHeight
    }
  } catch {
    if (request === threadRequest) {
      canReply.value = false
      threadError.value = __('Could not load messages. You may not have access to this conversation.')
    }
  } finally {
    if (request === threadRequest) threadPending.value = false
  }
}

async function saveReply() {
  if (!conversationName.value || sending.value || threadPending.value || !draft.value.trim()) return
  const conversation = conversationName.value
  const content = draft.value
  sending.value = true
  replyError.value = ''
  try {
    const message = await call(props.replyMethod, {
      ...props.requestContext,
      conversation,
      content,
    })
    if (conversation === conversationName.value) {
      if (draft.value === content) draft.value = ''
      if (!messages.value.some((item) => item.name === message.name)) {
        messages.value = [...messages.value, message].sort((a, b) =>
          a.sent_at.localeCompare(b.sent_at) || a.name.localeCompare(b.name),
        )
      }
      emit('reply-saved', message)
      await nextTick()
      if (history.value) history.value.scrollTop = history.value.scrollHeight
    }
  } catch {
    if (conversation === conversationName.value) {
      replyError.value = __('Could not save the mock reply. Your draft has been kept.')
    }
  } finally {
    if (conversation === conversationName.value) sending.value = false
  }
}

function onComposerKeydown(event) {
  if (
    event.key !== 'Enter'
    || event.shiftKey
    || event.isComposing
    || isComposing.value
    || event.keyCode === 229
  ) return

  event.preventDefault()
  saveReply()
}

watch([conversationName, contextKey], () => {
  resetThread()
  loadThread()
}, { immediate: true })

defineExpose({ loadThread })
</script>
