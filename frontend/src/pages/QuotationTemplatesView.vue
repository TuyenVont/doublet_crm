<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header><ViewBreadcrumbs routeName="QuotationTemplates" /></template>
      <template #right-header>
        <Button variant="subtle" :label="__('Quotations')" @click="router.push({ name: 'Quotations' })" />
        <Button v-if="canCreate" variant="solid" :label="__('Create Template')" iconLeft="plus" @click="openCreate" />
      </template>
    </LayoutHeader>

    <div class="flex flex-wrap items-center gap-2 border-b border-outline-gray-2/60 px-5 py-3">
      <div class="w-full sm:w-72">
        <TextInput v-model="searchQuery" type="search" :placeholder="__('Search templates...')" @keyup.enter="load(true)">
          <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-ink-gray-4" /></template>
        </TextInput>
      </div>
      <select v-model="selectedStatus" class="rounded border px-2 py-1 text-sm" @change="load(true)">
        <option value="">{{ __('All statuses') }}</option>
        <option value="active">{{ __('Active') }}</option>
        <option value="inactive">{{ __('Inactive') }}</option>
      </select>
      <Button :label="__('Search')" @click="load(true)" />
      <Button class="ml-auto" :tooltip="__('Refresh')" icon="refresh-cw" :loading="loading" @click="load(true)" />
    </div>

    <div class="relative flex-1 overflow-auto p-5">
      <ErrorMessage v-if="error" class="mb-4" :message="error" />
      <div v-if="loading && !rows.length" class="flex h-48 items-center justify-center text-sm text-ink-gray-5">
        {{ __('Loading quotation templates...') }}
      </div>
      <div v-else-if="rows.length" class="overflow-x-auto rounded border border-outline-gray-2">
        <table class="w-full min-w-[760px] text-left text-sm">
          <thead class="bg-surface-gray-1 text-ink-gray-6">
            <tr>
              <th class="px-4 py-3 font-medium">{{ __('Template Name') }}</th>
              <th class="px-4 py-3 font-medium">{{ __('Product / Service Group') }}</th>
              <th class="px-4 py-3 font-medium">{{ __('Description') }}</th>
              <th class="px-4 py-3 font-medium">{{ __('Status') }}</th>
              <th class="px-4 py-3 font-medium">{{ __('Last Modified') }}</th>
              <th v-if="canWrite" class="w-40 px-4 py-3 text-right">{{ __('Actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.name" class="border-t border-outline-gray-2 hover:bg-surface-gray-1">
              <td class="px-4 py-3 font-medium text-ink-gray-9">{{ row.template_name || row.name }}</td>
              <td class="px-4 py-3 text-ink-gray-6">{{ row.product_category || '—' }}</td>
              <td class="max-w-xs truncate px-4 py-3 text-ink-gray-6">{{ row.description || '—' }}</td>
              <td class="px-4 py-3">
                <span
                  class="rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="isActive(row) ? 'bg-green-100 text-green-800' : 'bg-surface-gray-2 text-ink-gray-6'"
                >
                  {{ isActive(row) ? __('Active') : __('Inactive') }}
                </span>
              </td>
              <td class="px-4 py-3 text-ink-gray-6">{{ row.modified || '—' }}</td>
              <td v-if="canWrite" class="px-4 py-3 text-right">
                <div class="flex justify-end gap-2">
                  <Button variant="subtle" :label="isActive(row) ? __('Deactivate') : __('Activate')" @click="toggleActive(row)" />
                  <Button variant="subtle" :label="__('Edit')" @click="openEdit(row)" />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="p-8 text-center text-sm text-ink-gray-5">
        {{ __('No quotation templates found.') }}
      </div>
    </div>

    <div v-if="hasMore" class="border-t border-outline-gray-2 px-5 py-3 text-center">
      <Button variant="subtle" :label="__('Load More')" :loading="loading" @click="load(false)" />
    </div>

    <QuotationTemplateModal v-model="showModal" :template="selectedTemplate" @saved="load(true)" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, ErrorMessage, FeatherIcon, TextInput, call } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import QuotationTemplateModal from '@/components/Modals/QuotationTemplateModal.vue'
import { message } from '@/utils/quotation'

const router = useRouter()
const searchQuery = ref('')
const selectedStatus = ref('')
const rows = ref([])
const loading = ref(false)
const hasMore = ref(false)
const error = ref('')
const showModal = ref(false)
const selectedTemplate = ref(null)
const canCreate = ref(false)
const canWrite = ref(false)

function isActive(row) {
  return row.is_active === 1 || row.is_active === '1' || row.is_active === true
}

async function load(reset) {
  if (loading.value) return
  loading.value = true
  error.value = ''
  if (reset) {
    rows.value = []
    hasMore.value = false
  }
  try {
    const filters = []
    if (searchQuery.value.trim()) filters.push(['template_name', 'like', `%${searchQuery.value.trim()}%`])
    if (selectedStatus.value === 'active') filters.push(['is_active', '=', 1])
    if (selectedStatus.value === 'inactive') filters.push(['is_active', '=', 0])
    const data = await call('frappe.client.get_list', {
      doctype: 'DoubleT Quotation Template',
      fields: ['name', 'template_name', 'product_category', 'description', 'is_active', 'modified'],
      filters,
      order_by: 'modified desc',
      limit_start: rows.value.length,
      limit_page_length: 20,
    })
    rows.value.push(...(data || []))
    hasMore.value = data?.length === 20
  } catch (e) {
    error.value = message(e)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  selectedTemplate.value = null
  showModal.value = true
}

async function openEdit(row) {
  error.value = ''
  try {
    selectedTemplate.value = await call('frappe.client.get', {
      doctype: 'DoubleT Quotation Template',
      name: row.name,
    })
    showModal.value = true
  } catch (e) {
    error.value = message(e)
  }
}

async function toggleActive(row) {
  error.value = ''
  try {
    const fullDoc = await call('frappe.client.get', {
      doctype: 'DoubleT Quotation Template',
      name: row.name,
    })
    await call('frappe.client.save', {
      doc: { ...fullDoc, is_active: isActive(row) ? 0 : 1 },
    })
    await load(true)
  } catch (e) {
    error.value = message(e)
  }
}

onMounted(async () => {
  load(true)
  const [createPerm, writePerm] = await Promise.allSettled([
    call('frappe.client.has_permission', { doctype: 'DoubleT Quotation Template', docname: '', perm_type: 'create' }),
    call('frappe.client.has_permission', { doctype: 'DoubleT Quotation Template', docname: '', perm_type: 'write' }),
  ])
  canCreate.value = createPerm.status === 'fulfilled' && Boolean(createPerm.value?.has_permission)
  canWrite.value = writePerm.status === 'fulfilled' && Boolean(writePerm.value?.has_permission)
})
</script>
