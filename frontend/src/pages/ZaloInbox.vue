<template>
  <div class="flex h-full min-h-0 flex-col bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <h1 class="text-lg-medium text-ink-gray-9">{{ __('Inbox') }}</h1>
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" :loading="listPending" @click="refresh" />
      </template>
    </LayoutHeader>

    <p v-if="listError" class="border-b border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
      {{ listError }}
    </p>
    <p v-if="!canRead" class="p-5 text-sm text-ink-gray-5">{{ __('You do not have access to the Inbox.') }}</p>
    <div v-else class="flex min-h-0 flex-1 flex-col md:flex-row">
      <aside
        class="flex min-h-0 w-full shrink-0 flex-col border-b border-outline-gray-2 md:w-80 md:max-w-[40%] md:border-b-0 md:border-r"
        :class="selected ? 'hidden md:flex' : 'max-h-full'"
        :aria-label="__('Zalo OA conversations')"
      >
        <h2 class="border-b border-outline-gray-2 px-4 py-3 text-sm font-semibold">{{ __('Zalo OA conversations') }}</h2>
        <div class="space-y-2 border-b border-outline-gray-2 p-3">
          <input
            v-model="searchQuery"
            type="search"
            class="block w-full rounded-md border border-outline-gray-3 px-3 py-2 text-sm"
            :placeholder="__('Search customer or Zalo user ID')"
            :aria-label="__('Search conversations')"
          />
          <div class="grid grid-cols-2 gap-2">
            <select v-model="oaFilter" class="min-w-0 rounded-md border border-outline-gray-3 bg-surface-white px-2 py-2 text-sm">
              <option value="">{{ __('All OAs') }}</option>
              <option v-for="oa in oaOptions" :key="oa" :value="oa">{{ oa }}</option>
            </select>
            <select v-model="replyFilter" class="min-w-0 rounded-md border border-outline-gray-3 bg-surface-white px-2 py-2 text-sm">
              <option value="All">{{ __('All') }}</option>
              <option value="Needs reply">{{ __('Needs reply') }}</option>
              <option value="Replied">{{ __('Replied') }}</option>
            </select>
          </div>
          <p class="text-xs text-ink-gray-5">{{ __('{0} conversations', [totalConversations]) }}</p>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto">
          <p v-if="listPending && !conversations.length" class="p-4 text-sm text-ink-gray-5">
            {{ __('Loading conversations…') }}
          </p>
          <p v-else-if="!listError && !conversations.length" class="p-4 text-sm text-ink-gray-5">
            {{ __('No conversations match these filters.') }}
          </p>
          <button
            v-for="item in conversations"
            :key="item.name"
            type="button"
            class="block w-full border-b border-outline-gray-1 px-4 py-3 text-left hover:bg-surface-gray-1"
            :class="{ 'bg-surface-gray-2': selected?.name === item.name }"
            :aria-pressed="selected?.name === item.name"
            @click="openConversation(item)"
          >
            <span class="flex items-start justify-between gap-2">
              <span class="min-w-0 truncate text-sm font-medium">{{ item.display_name || item.external_user_id }}</span>
              <span class="shrink-0 text-[11px] text-ink-gray-5">{{ formatMessageTime(item.last_message_sent_at) }}</span>
            </span>
            <span class="mt-1 flex items-center justify-between gap-2 text-xs text-ink-gray-5">
              <span class="truncate">{{ __('OA') }} {{ item.oa_id }}</span>
              <span
                v-if="item.reply_status"
                class="shrink-0 rounded-full px-2 py-0.5"
                :class="item.reply_status === 'Needs reply' ? 'bg-orange-50 text-orange-700' : 'bg-green-50 text-green-700'"
              >{{ __(item.reply_status) }}</span>
            </span>
            <span class="mt-2 block truncate text-xs text-ink-gray-7">
              {{ item.last_message_content || __('No messages yet.') }}
            </span>
          </button>
          <div v-if="moreConversations" class="p-3">
            <Button :label="__('Load more conversations')" :loading="listPending" @click="loadConversations(true)" />
          </div>
        </div>
      </aside>

      <div v-if="selected" class="flex min-h-0 min-w-0 flex-1 flex-col">
        <header class="flex flex-wrap items-center gap-3 border-b border-outline-gray-2 px-4 py-3">
          <Button class="md:hidden" :label="__('Conversations')" @click="closeConversation" />
          <div class="min-w-0 flex-1">
            <h2 class="truncate text-sm font-semibold">{{ selected.display_name || selected.external_user_id }}</h2>
            <p class="mt-1 truncate text-xs text-ink-gray-5">{{ __('Zalo OA') }} · {{ selected.oa_id }}</p>
          </div>
          <Button
            :label="detailsOpen ? __('Hide customer details') : __('Customer details')"
            @click="detailsOpen = !detailsOpen"
          />
        </header>

        <div class="flex min-h-0 flex-1">
          <ZaloConversationThread
            v-if="selected"
            ref="thread"
            class="min-w-0"
            :class="detailsOpen ? 'hidden md:flex' : 'flex'"
            :conversation="selected"
            @reply-saved="onReplySaved"
          />
          <ZaloCustomerDetails
            v-if="detailsOpen"
            :conversation="selected"
            @close="detailsOpen = false"
          />
        </div>
      </div>
      <p v-else class="hidden flex-1 place-content-center text-center text-sm text-ink-gray-5 md:grid">
        {{ __('Select a conversation to view its messages.') }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, call } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ZaloConversationThread from '@/components/Zalo/ZaloConversationThread.vue'
import ZaloCustomerDetails from '@/components/Zalo/ZaloCustomerDetails.vue'

const conversations = ref([])
const selected = ref(null)
const thread = ref(null)
const canRead = ref(true)
const moreConversations = ref(false)
const listPending = ref(false)
const listError = ref('')
const searchQuery = ref('')
const oaFilter = ref('')
const replyFilter = ref('All')
const oaOptions = ref([])
const totalConversations = ref(0)
const detailsOpen = ref(false)
const route = useRoute()
const router = useRouter()
let listRequest = 0
let filterTimer = null

async function loadConversations(append = false) {
  if (append && listPending.value) return
  const request = ++listRequest
  listPending.value = true
  listError.value = ''
  try {
    const start = append ? conversations.value.length : 0
    const result = await call('doublet_crm.zalo_inbox.list_conversations', {
      start,
      search: searchQuery.value,
      oa_id: oaFilter.value,
      reply_status: replyFilter.value,
    })
    if (request !== listRequest) return
    canRead.value = result.can_read
    moreConversations.value = result.has_more
    oaOptions.value = result.oa_options || []
    totalConversations.value = result.total || 0
    conversations.value = append ? [...conversations.value, ...result.conversations] : result.conversations
    if (!canRead.value) {
      closeConversation()
    } else if (selected.value) {
      selected.value = conversations.value.find((item) => item.name === selected.value.name) || selected.value
    }
  } catch {
    if (request === listRequest) listError.value = __('Could not load conversations. Try refreshing.')
  } finally {
    if (request === listRequest) listPending.value = false
  }
}

function closeConversation() {
  selected.value = null
  detailsOpen.value = false
  if (route.query.conversation) {
    const query = { ...route.query }
    delete query.conversation
    router.replace({ query })
  }
}

function openConversation(item, updateRoute = true) {
  if (selected.value?.name === item.name) return
  selected.value = item
  detailsOpen.value = false
  if (updateRoute && route.query.conversation !== item.name) {
    router.replace({ query: { ...route.query, conversation: item.name } })
  }
}

async function openRequestedConversation() {
  const conversation = route.query.conversation
  if (!conversation || selected.value?.name === conversation) return
  try {
    const item = conversations.value.find((row) => row.name === conversation)
      || await call('doublet_crm.zalo_inbox.get_conversation_info', { conversation })
    openConversation(item, false)
  } catch {
    listError.value = __('Could not open the requested conversation. You may not have access to it.')
  }
}

async function refresh() {
  await loadConversations()
  await openRequestedConversation()
  if (selected.value) thread.value?.loadThread()
}

function formatMessageTime(value) {
  if (!value) return ''
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function onReplySaved(message) {
  const conversation = selected.value?.name
  if (!conversation) return
  const summary = {
    last_message_content: message.content,
    last_message_direction: message.direction,
    last_message_sent_at: message.sent_at,
    last_message_is_simulated: message.is_simulated,
    reply_status: 'Replied',
  }
  selected.value = { ...selected.value, ...summary }
  conversations.value = conversations.value
    .map((item) => item.name === conversation ? { ...item, ...summary } : item)
    .filter((item) => replyFilter.value !== 'Needs reply' || item.reply_status === 'Needs reply')
    .sort((a, b) =>
      String(b.last_message_sent_at || '').localeCompare(String(a.last_message_sent_at || ''))
      || b.name.localeCompare(a.name),
    )
  loadConversations()
}

function scheduleFilterReload() {
  if (filterTimer) clearTimeout(filterTimer)
  filterTimer = setTimeout(() => loadConversations(), 250)
}

onMounted(async () => {
  await loadConversations()
  await openRequestedConversation()
})

watch(() => route.query.conversation, (conversation) => {
  if (!conversation) {
    selected.value = null
    return
  }
  openRequestedConversation()
})

watch([searchQuery, oaFilter, replyFilter], scheduleFilterReload)
onBeforeUnmount(() => {
  if (filterTimer) clearTimeout(filterTimer)
})
</script>
