<template>
  <section class="min-w-0 flex-1 overflow-y-auto px-5 py-4" :aria-label="__('Call history')">
    <p v-if="error" class="mb-3 text-sm text-red-700" role="alert">{{ error }}</p>
    <p v-if="loading && !rows.length" class="text-sm text-ink-gray-5">{{ __('Loading calls…') }}</p>
    <p v-else-if="!rows.length && !error" class="text-sm text-ink-gray-5">{{ __('No calls linked to this customer.') }}</p>

    <ul v-if="rows.length" class="divide-y divide-outline-gray-1">
      <li v-for="row in rows" :key="row.name">
        <RouterLink
          :to="{ name: 'CallDetail', params: { callId: row.name }, query: { from: 'customer' } }"
          class="flex flex-wrap items-center justify-between gap-2 py-3 hover:text-ink-blue-3"
        >
          <span class="flex min-w-0 items-center gap-2 text-sm font-medium">
            <FeatherIcon name="phone" class="size-4 shrink-0" />
            {{ __(row.call_type) }} · {{ row.customer_number || '—' }}
          </span>
          <span class="flex flex-wrap items-center gap-2 text-sm text-ink-gray-6">
            <Badge :label="__(row.status)" :theme="row.status === 'Missed' ? 'red' : 'gray'" />
            {{ formatCallTime(row.start_time) }}
          </span>
        </RouterLink>
      </li>
    </ul>

    <Button
      v-if="hasMore || error"
      class="mt-3"
      :label="__(error ? 'Retry' : 'Load more')"
      :loading="loading"
      @click="load()"
    />
  </section>
</template>

<script setup>
import { Badge, Button, FeatherIcon, call } from 'frappe-ui'
import { ref, watch } from 'vue'
import { formatCallTime } from '@/utils/contactCenterCalls'

const props = defineProps({
  referenceDoctype: { type: String, required: true },
  referenceName: { type: String, required: true },
})

const rows = ref([])
const loading = ref(false)
const hasMore = ref(false)
const error = ref('')
let requestId = 0

async function load() {
  if (!props.referenceName) return
  const id = ++requestId
  loading.value = true
  error.value = ''
  try {
    const result = await call('doublet_crm.contact_center_calls.get_record_calls', {
      doctype: props.referenceDoctype,
      name: props.referenceName,
      start: rows.value.length,
    })
    if (id !== requestId) return
    rows.value = [...rows.value, ...result.rows]
    hasMore.value = result.has_more
  } catch (e) {
    if (id === requestId) error.value = e.messages?.[0] || __('Unable to load call history.')
  } finally {
    if (id === requestId) loading.value = false
  }
}

watch(() => [props.referenceDoctype, props.referenceName], () => {
  requestId++
  rows.value = []
  hasMore.value = false
  loading.value = false
  error.value = ''
  load()
}, { immediate: true })
</script>
