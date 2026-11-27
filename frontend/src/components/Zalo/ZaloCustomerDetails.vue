<template>
  <aside class="flex min-h-0 w-full shrink-0 flex-col bg-surface-white md:w-80 md:border-l md:border-outline-gray-2">
    <header class="flex min-h-[52px] items-center gap-3 border-b border-outline-gray-2 px-4 py-3">
      <Button class="md:hidden" :label="__('Back to chat')" @click="emit('close')" />
      <h2 class="min-w-0 flex-1 truncate text-sm font-semibold">{{ __('Customer details') }}</h2>
      <Button class="hidden md:inline-flex" icon="x" variant="ghost" :aria-label="__('Close customer details')" @click="emit('close')" />
    </header>

    <p v-if="loading" class="p-5 text-sm text-ink-gray-5">{{ __('Loading customer details…') }}</p>
    <div v-else-if="error" class="space-y-3 p-5">
      <p class="text-sm text-red-700" role="alert">{{ error }}</p>
      <Button :label="__('Retry')" @click="load" />
    </div>
    <div v-else-if="details" class="min-h-0 flex-1 space-y-5 overflow-y-auto p-5">
      <section>
        <p class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">{{ __('Zalo customer') }}</p>
        <p class="mt-2 break-words text-sm font-semibold text-ink-gray-9">
          {{ conversation.display_name || __(conversation.customer_linked ? 'Linked customer' : 'Unidentified Customer') }}
        </p>
        <dl class="mt-3 space-y-2 text-sm">
          <div class="flex justify-between gap-3">
            <dt class="text-ink-gray-5">{{ __('Zalo user ID') }}</dt>
            <dd class="break-all text-right">{{ details.external_user_id }}</dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-ink-gray-5">{{ __('OA') }}</dt>
            <dd class="break-all text-right">{{ details.oa_id }}</dd>
          </div>
          <div v-if="details.lead" class="flex justify-between gap-3">
            <dt class="text-ink-gray-5">{{ __('Source') }}</dt>
            <dd class="text-right">{{ details.lead.source || '—' }}</dd>
          </div>
          <div v-if="details.lead" class="flex justify-between gap-3">
            <dt class="text-ink-gray-5">{{ __('Lead status') }}</dt>
            <dd class="text-right">{{ details.lead.status || '—' }}</dd>
          </div>
        </dl>
      </section>

      <section>
        <p class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">{{ __('CRM records') }}</p>
        <div class="mt-2 divide-y divide-outline-gray-1 rounded border border-outline-gray-2">
          <RouterLink
            v-for="item in recordLinks"
            :key="item.kind"
            class="flex items-center justify-between gap-3 px-3 py-3 text-sm hover:bg-surface-gray-1"
            :to="item.to"
          >
            <span class="text-ink-gray-5">{{ item.kind }}</span>
            <span class="min-w-0 truncate text-right font-medium text-blue-600">{{ item.record.label }}</span>
          </RouterLink>
          <p v-if="!recordLinks.length" class="px-3 py-4 text-sm text-ink-gray-5">
            {{ __('No readable linked CRM records.') }}
          </p>
        </div>
      </section>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, call } from 'frappe-ui'

const props = defineProps({
  conversation: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const details = ref(null)
const loading = ref(false)
const error = ref('')
let requestId = 0

const conversationName = computed(() => props.conversation?.name || '')
const recordLinks = computed(() => {
  if (!details.value) return []
  const definitions = [
    ['Lead', 'lead', 'LeadDetail', 'leadId'],
    ['Contact', 'contact', 'ContactDetail', 'contactId'],
    ['Deal', 'deal', 'DealDetail', 'dealId'],
    ['Company', 'company', 'CompanyDetail', 'companyId'],
  ]
  return definitions.flatMap(([kind, key, route, param]) => {
    const record = details.value[key]
    return record ? [{ kind: __(kind), record, to: { name: route, params: { [param]: record.name } } }] : []
  })
})

async function load() {
  const conversation = conversationName.value
  if (!conversation) return
  const request = ++requestId
  loading.value = true
  error.value = ''
  details.value = null
  try {
    const result = await call('doublet_crm.zalo_inbox.get_customer_details', { conversation })
    if (request === requestId && conversation === conversationName.value) details.value = result
  } catch {
    if (request === requestId) {
      error.value = __('Could not load customer details. Some records may not be accessible.')
    }
  } finally {
    if (request === requestId) loading.value = false
  }
}

watch([conversationName, () => props.conversation.version], load, { immediate: true })
</script>
