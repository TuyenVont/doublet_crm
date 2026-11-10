<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="ProductCategories" />
      </template>
      <template #right-header>
        <Button variant="subtle" :label="__('Back to Products')" @click="router.push({ name: 'Products' })" />
        <Button variant="solid" :label="__('Create Category')" iconLeft="plus" @click="openCreate" />
      </template>
    </LayoutHeader>

    <div class="flex items-center gap-2 border-b border-outline-gray-2/60 px-5 py-3">
      <div class="w-full sm:w-72">
        <TextInput v-model="searchQuery" type="search" :placeholder="__('Search categories...')">
          <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-ink-gray-4" /></template>
        </TextInput>
      </div>
      <Button class="ml-auto" :tooltip="__('Refresh')" icon="refresh-cw" :loading="categoriesResource.loading" @click="reload" />
    </div>

    <div class="relative flex-1 overflow-auto p-5">
      <div v-if="categoriesResource.loading && !categories.length" class="flex h-48 items-center justify-center text-sm text-ink-gray-5">
        {{ __('Loading categories...') }}
      </div>
      <div v-else-if="resourceError" class="mx-auto max-w-xl pt-8"><ErrorMessage :message="resourceError" /></div>
      <template v-else-if="categories.length">
        <ErrorMessage v-if="actionError" class="mb-4" :message="actionError" />
        <div class="overflow-x-auto rounded border border-outline-gray-2">
        <table class="w-full min-w-[600px] text-sm">
          <thead class="bg-surface-gray-1 text-left text-ink-gray-6">
            <tr>
              <th class="px-4 py-3 font-medium">{{ __('Category Name') }}</th>
              <th class="px-4 py-3 font-medium">{{ __('Description') }}</th>
              <th class="w-36 px-4 py-3"><span class="sr-only">{{ __('Actions') }}</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="category in categories" :key="category.name" class="cursor-pointer border-t border-outline-gray-2 hover:bg-surface-gray-1" @click="openEdit(category)">
              <td class="px-4 py-3 font-medium text-ink-gray-9">{{ category.category_name || category.name }}</td>
              <td class="px-4 py-3 text-ink-gray-6">{{ category.description || '-' }}</td>
              <td class="px-4 py-3 text-right">
                <Button variant="subtle" :label="__('Edit')" @click.stop="openEdit(category)" />
                <Button variant="subtle" :label="__('Delete')" :loading="deletingName === category.name" @click.stop="deleteCategory(category)" />
              </td>
            </tr>
          </tbody>
        </table>
        </div>
      </template>
      <EmptyState v-else name="Product Categories" :title="__('No Categories Found')" :description="__('Create a product category to organize your products.')" />
    </div>

    <div v-if="categories.length && categoriesResource.hasNextPage" class="border-t border-outline-gray-2 px-5 py-3 text-center">
      <Button variant="subtle" :label="__('Load More')" :loading="categoriesResource.loading" @click="loadMore" />
    </div>

    <Dialog v-model:open="showModal" :size="'lg'">
      <template #body>
        <div class="bg-surface-elevation-1 px-4 pb-6 pt-5 sm:px-6">
          <div class="mb-5 flex items-center justify-between">
            <h3 class="text-xl font-semibold text-ink-gray-9">{{ editingCategory ? __('Edit Category') : __('New Category') }}</h3>
            <Button variant="ghost" class="w-7" icon="lucide-x" @click="showModal = false" />
          </div>
          <div class="space-y-4">
            <label class="block space-y-1">
              <span class="text-sm text-ink-gray-7">{{ __('Category Name') }} *</span>
              <TextInput v-model="form.category_name" :placeholder="__('Category Name')" />
            </label>
            <label class="block space-y-1">
              <span class="text-sm text-ink-gray-7">{{ __('Description') }}</span>
              <textarea v-model="form.description" rows="4" class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm" />
            </label>
          </div>
          <ErrorMessage v-if="modalError" class="mt-4" :message="modalError" />
        </div>
        <div class="flex justify-end gap-2 px-4 pb-6 pt-4 sm:px-6">
          <Button variant="subtle" :label="__('Cancel')" @click="showModal = false" />
          <Button variant="solid" :label="editingCategory ? __('Save') : __('Create')" :loading="saving" @click="saveCategory" />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Dialog, FeatherIcon, TextInput, call } from 'frappe-ui'

import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'

const pageLength = 20
const categoryFields = ['name', 'category_name', 'description']
const categoriesResource = reactive({
  data: [],
  loading: false,
  error: null,
  hasNextPage: true,
})
let categoryRequestVersion = 0
const router = useRouter()
const searchQuery = ref('')
const showModal = ref(false)
const editingCategory = ref(null)
const saving = ref(false)
const deletingName = ref('')
const modalError = ref('')
const actionError = ref('')
const form = reactive({ category_name: '', description: '' })

const categories = computed(() => categoriesResource.data || [])
const resourceError = computed(() => {
  const error = categoriesResource.error
  return error?.messages?.[0] || error?.message || error || ''
})

async function fetchCategories({ append = false } = {}) {
  if (append && (categoriesResource.loading || !categoriesResource.hasNextPage)) return

  const requestVersion = ++categoryRequestVersion
  const start = append ? categoriesResource.data.length : 0
  if (!append) {
    categoriesResource.data = []
    categoriesResource.hasNextPage = true
  }
  categoriesResource.loading = true
  categoriesResource.error = null

  const search = searchQuery.value.trim()
  try {
    const data = await call('frappe.client.get_list', {
      doctype: 'DoubleT Product Category',
      fields: categoryFields,
      or_filters: search
        ? [
            ['category_name', 'like', `%${search}%`],
            ['description', 'like', `%${search}%`],
          ]
        : undefined,
      order_by: 'category_name asc',
      limit_start: start,
      limit_page_length: pageLength,
    })
    if (requestVersion !== categoryRequestVersion) return

    const page = Array.isArray(data) ? data : []
    categoriesResource.data = append ? categoriesResource.data.concat(page) : page
    categoriesResource.hasNextPage = page.length === pageLength
  } catch (error) {
    if (requestVersion !== categoryRequestVersion) return
    categoriesResource.error = error
  } finally {
    if (requestVersion === categoryRequestVersion) {
      categoriesResource.loading = false
    }
  }
}

function reload() {
  return fetchCategories()
}

function loadMore() {
  return fetchCategories({ append: true })
}

watch(searchQuery, reload)
reload()

function openCreate() {
  editingCategory.value = null
  modalError.value = ''
  Object.assign(form, { category_name: '', description: '' })
  showModal.value = true
}

function openEdit(category) {
  editingCategory.value = category
  modalError.value = ''
  Object.assign(form, { category_name: category.category_name || '', description: category.description || '' })
  showModal.value = true
}

async function saveCategory() {
  const categoryName = form.category_name.trim()
  if (!categoryName) {
    modalError.value = __('Category Name is required.')
    return
  }

  modalError.value = ''
  saving.value = true
  const doc = {
    doctype: 'DoubleT Product Category',
    ...(editingCategory.value ? { name: editingCategory.value.name } : {}),
    category_name: categoryName,
    description: form.description,
  }
  try {
    await call(editingCategory.value ? 'frappe.client.save' : 'frappe.client.insert', { doc })
    showModal.value = false
    reload()
  } catch (error) {
    modalError.value = error?.messages?.[0] || error?.message || __('Unable to save category.')
  } finally {
    saving.value = false
  }
}

async function deleteCategory(category) {
  if (!window.confirm(__('Delete this category? Products using it cannot be deleted until they are reassigned.'))) return

  actionError.value = ''
  deletingName.value = category.name
  try {
    await call('frappe.client.delete', { doctype: 'DoubleT Product Category', name: category.name })
    reload()
  } catch (error) {
    actionError.value = error?.messages?.[0] || error?.message || __('Unable to delete category. Products using it must be reassigned first.')
  } finally {
    deletingName.value = ''
  }
}
</script>
