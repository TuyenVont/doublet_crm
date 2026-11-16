<template>
  <div class="flex min-h-0 flex-1 flex-col bg-surface-white">
    <div class="flex min-h-[52px] flex-wrap items-center gap-3 border-b border-outline-gray-2 px-4 py-3">
      <div class="min-w-0 flex-1">
        <h2 class="text-sm font-semibold">{{ __('Zalo OA conversations') }}</h2>
        <p v-if="selected" class="mt-1 truncate text-xs text-ink-gray-5">
          {{ selected.display_name || selected.external_user_id }} · {{ __('OA') }} {{ selected.oa_id }}
        </p>
      </div>
      <select
        v-if="conversations.length > 1"
        v-model="selectedName"
        class="max-w-full rounded-md border border-outline-gray-3 bg-surface-white px-3 py-2 text-sm"
        :aria-label="__('Select a Zalo OA conversation')"
      >
        <option v-for="item in conversations" :key="item.name" :value="item.name">
          {{ item.display_name || item.external_user_id }} · {{ item.oa_id }}
        </option>
      </select>
      <RouterLink
        v-if="selected"
        class="shrink-0 text-sm text-blue-600 underline"
        :to="{ name: 'Inbox', query: { conversation: selected.name } }"
      >
        {{ __('Open in Inbox') }}
      </RouterLink>
      <Button :label="__('Refresh')" :loading="loading" @click="loadConversations" />
    </div>

    <p v-if="loading && !conversations.length" class="m-auto p-5 text-sm text-ink-gray-5">
      {{ __('Loading conversations…') }}
    </p>
    <p v-else-if="restricted" class="m-auto p-5 text-center text-sm text-ink-gray-5">
      {{ __('You do not have access to Zalo OA conversations for this record.') }}
    </p>
    <div v-else-if="error" class="m-auto flex flex-col items-center gap-3 p-5 text-center">
      <p class="text-sm text-red-700" role="alert">{{ error }}</p>
      <Button :label="__('Retry')" @click="loadConversations" />
    </div>
    <p v-else-if="!selected" class="m-auto p-5 text-center text-sm text-ink-gray-5">
      {{ __('No linked Zalo OA conversation was found for this record.') }}
    </p>
    <ZaloConversationThread
      v-else
      :key="`${referenceDoctype}:${referenceName}:${selected.name}`"
      :conversation="selected"
      message-method="doublet_crm.zalo_inbox.get_record_messages"
      reply-method="doublet_crm.zalo_inbox.save_record_mock_reply"
      :request-context="requestContext"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, call } from 'frappe-ui'
import ZaloConversationThread from './ZaloConversationThread.vue'

const props = defineProps({
  referenceDoctype: { type: String, required: true },
  referenceName: { type: String, required: true },
})

const conversations = ref([])
const selectedName = ref('')
const loading = ref(false)
const restricted = ref(false)
const error = ref('')
let listRequest = 0

const selected = computed(() =>
  conversations.value.find((item) => item.name === selectedName.value) || null,
)
const referenceKey = computed(() => `${props.referenceDoctype}:${props.referenceName}`)
const requestContext = computed(() => ({
  reference_doctype: props.referenceDoctype,
  reference_name: props.referenceName,
}))

async function loadConversations() {
  const request = ++listRequest
  const referenceName = props.referenceName
  conversations.value = []
  selectedName.value = ''
  restricted.value = false
  error.value = ''
  loading.value = true
  try {
    const result = await call('doublet_crm.zalo_inbox.list_record_conversations', requestContext.value)
    if (request !== listRequest || referenceName !== props.referenceName) return
    restricted.value = !result.can_read
    conversations.value = result.conversations || []
    selectedName.value = conversations.value[0]?.name || ''
  } catch {
    if (request === listRequest) {
      error.value = __('Could not load Zalo OA conversations. You may not have access to this record.')
    }
  } finally {
    if (request === listRequest) loading.value = false
  }
}

watch(referenceKey, loadConversations, { immediate: true })
</script>
