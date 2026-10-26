
<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            icon="chevron-left"
            @click="router.push({ name: 'Deals' })"
          />
          <div class="flex items-center gap-1 text-lg-medium text-ink-gray-9">
            <button
              class="text-ink-gray-6 hover:text-ink-gray-9"
              @click="router.push({ name: 'Deals' })"
            >
              Deals
            </button>
            <span class="text-ink-gray-4">/</span>
            <span class="max-w-[420px] truncate">{{ title }}</span>
          </div>
        </div>
      </template>

      <template #right-header>
        <Button
          variant="subtle"
          label="Refresh"
          :loading="loading"
          @click="loadDeal"
        />
        <Button
          variant="solid"
          label="Edit"
          iconLeft="edit-3"
          :disabled="!deal || loading"
          @click="openEdit"
        />
      </template>
    </LayoutHeader>

    <!-- LOADING -->
    <div
      v-if="loading && !deal"
      class="flex flex-1 items-center justify-center text-ink-gray-5"
    >
      Loading Deal...
    </div>

    <!-- ERROR -->
    <div
      v-else-if="error && !deal"
      class="flex flex-1 flex-col items-center justify-center gap-3"
    >
      <div class="text-lg font-medium">Unable to load Deal</div>
      <p class="text-sm text-red-600">{{ error }}</p>
      <Button label="Retry" @click="loadDeal" />
    </div>

    <!-- DEAL DETAIL -->
    <div
      v-else-if="deal"
      class="flex-1 overflow-auto bg-surface-gray-1"
    >
      <div class="mx-auto max-w-6xl p-5">

        <!-- MAIN HEADER -->
        <section class="mb-5 rounded-lg border bg-surface-white p-5">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 class="text-2xl font-semibold text-ink-gray-9">
                {{ deal.deal_title || deal.name }}
              </h1>
              <p class="mt-1 text-sm text-ink-gray-5">
                {{ deal.name }}
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-2">
              <Badge
                v-if="deal.stage"
                :label="deal.stage"
                theme="blue"
                variant="subtle"
              />

              <label for="deal-stage" class="text-sm">
                Change Stage
              </label>

              <select
                id="deal-stage"
                v-model="selectedStage"
                :disabled="stageSaving || stagesLoading || loading"
                class="rounded-lg border bg-white px-3 py-2 text-sm"
                @change="saveStage"
              >
                <option
                  v-if="!stageOptions.some(s => s.name === selectedStage)"
                  :value="selectedStage"
                >
                  {{ selectedStage || 'Select Stage' }}
                </option>
                <option
                  v-for="stage in stageOptions"
                  :key="stage.name"
                  :value="stage.name"
                >
                  {{ stage.stage_name || stage.name }}
                </option>
              </select>
            </div>
          </div>

          <p
            v-if="stageError"
            role="alert"
            class="mt-3 text-sm text-red-600"
          >
            {{ stageError }}
          </p>

          <p
            v-if="error"
            role="alert"
            class="mt-3 text-sm text-red-600"
          >
            {{ error }}
          </p>

          <!-- SUMMARY -->
          <div class="mt-6 grid gap-5 sm:grid-cols-3">
            <div>
              <p class="text-xs text-ink-gray-5">Amount</p>
              <p class="mt-1 text-lg font-semibold">
                {{ displayAmount }}
              </p>
            </div>

            <div>
              <p class="text-xs text-ink-gray-5">
                Expected Close Date
              </p>
              <p class="mt-1">
                {{ dateValue(deal.expected_close_date) }}
              </p>
            </div>

            <div>
              <p class="text-xs text-ink-gray-5">Owner</p>
              <p class="mt-1">
                {{ displayLink('deal_owner', deal.deal_owner) || deal.owner || '-' }}
              </p>
            </div>
          </div>
        </section>

        <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">

          <!-- DEAL INFORMATION -->
          <section class="rounded-lg border bg-surface-white">
            <div class="border-b px-5 py-4">
              <h2 class="text-lg font-semibold">
                Deal Information
              </h2>
            </div>

            <div class="grid gap-x-8 gap-y-5 p-5 sm:grid-cols-2">
<InfoField label="Deal Title" :value="deal.deal_title" />
<InfoField label="Stage" :value="deal.stage" />
<InfoField label="Deal Type" :value="deal.deal_type" />
<InfoField label="Source" :value="deal.source" />
<InfoField label="Amount" :value="displayAmount" />

              <InfoField
                label="Expected Close Date"
                :value="dateValue(deal.expected_close_date)"
              />
              <InfoField
                label="Won On"
                :value="dateValue(deal.won_on)"
              />
              <InfoField
                label="Lost On"
                :value="dateValue(deal.lost_on)"
              />
              <InfoField
                label="Lost Reason"
                :value="deal.lost_reason"
              />
              <InfoField
                label="Created"
                :value="dateValue(deal.creation)"
              />
              <InfoField
                label="Last Modified"
                :value="dateValue(deal.modified)"
              />
            </div>
          </section>

          <!-- RELATED INFORMATION -->
          <aside class="space-y-5">
            <section class="rounded-lg border bg-surface-white">
              <div class="border-b px-5 py-4">
                <h2 class="text-lg font-semibold">
                  Related Information
                </h2>
              </div>

              <div class="space-y-5 p-5">
                <InfoField
                  label="Contact"
                  :value="displayLink('contact', deal.contact)"
                />
                <InfoField
                  label="Company"
                  :value="displayLink('company', deal.company)"
                />
                <InfoField
                  label="Source Lead"
                  :value="deal.source_lead"
                />
                <InfoField
                  label="Deal Owner"
                  :value="displayLink('deal_owner', deal.deal_owner) || deal.owner"
                />
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  </div>

  <!-- EDIT MODAL -->
  <Teleport to="body">
    <div
      v-if="showEdit"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      @click.self="closeEdit"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-deal-title"
        class="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl"
      >
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h2
              id="edit-deal-title"
              class="text-xl font-semibold text-gray-900"
            >
              Edit Deal
            </h2>
            <p class="text-xs text-gray-500">
              {{ deal?.name }}
            </p>
          </div>

          <button
            type="button"
            class="rounded-lg p-2 hover:bg-gray-100"
            :disabled="editSaving"
            @click="closeEdit"
          >
            ✕
          </button>
        </div>

        <form @submit.prevent="saveEdit">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">

            <!-- TITLE -->
            <label class="space-y-1 sm:col-span-2">
              <span class="text-sm font-medium">
                Deal Title *
              </span>
              <input
                v-model.trim="editForm.deal_title"
                required
                maxlength="140"
                class="w-full rounded-lg border border-gray-300 p-2"
              />
            </label>

            <!-- AMOUNT -->
            <label class="space-y-1">
              <span class="text-sm font-medium">Amount</span>
              <input
                v-model="editForm.amount"
                type="number"
                min="0"
                step="0.01"
                class="w-full rounded-lg border border-gray-300 p-2"
              />
            </label>

            <!-- DEAL TYPE -->
            <label class="space-y-1">
              <span class="text-sm font-medium">Deal Type</span>
              <select
                v-model="editForm.deal_type"
                class="w-full rounded-lg border border-gray-300 p-2"
              >
                <option value="">Not selected</option>
                <option value="PERSONAL">Personal</option>
                <option value="COMPANY">Company</option>
              </select>
            </label>

            <!-- OWNER SEARCH -->
            <div class="relative space-y-1">
              <label class="text-sm font-medium" for="edit-owner">
                Deal Owner
              </label>
              <input
                id="edit-owner"
                v-model="linkSearch.deal_owner"
                autocomplete="off"
                placeholder="Search users..."
                class="w-full rounded-lg border border-gray-300 p-2"
                @input="onLinkInput('deal_owner')"
                @focus="searchLinks('deal_owner')"
              />

              <div
                v-if="linkOpen.deal_owner"
                class="absolute z-20 max-h-44 w-full overflow-y-auto rounded-lg border bg-white shadow-lg"
              >
                <button
                  v-for="item in linkResults.deal_owner"
                  :key="item.value"
                  type="button"
                  class="block w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
                  @mousedown.prevent="chooseLink('deal_owner', item)"
                >
                  <span class="block font-medium">
                    {{ item.label }}
                  </span>
                  <span
                    v-if="item.label !== item.value"
                    class="block text-xs text-gray-500"
                  >
                    {{ item.value }}
                  </span>
                </button>

                <p
                  v-if="!linkResults.deal_owner.length"
                  class="p-3 text-xs text-gray-500"
                >
                  No results
                </p>
              </div>
            </div>

            <!-- DATE -->
            <label class="space-y-1">
              <span class="text-sm font-medium">
                Expected Close Date
              </span>
              <input
                v-model="editForm.expected_close_date"
                type="date"
                class="w-full rounded-lg border border-gray-300 p-2"
              />
            </label>

            <!-- CONTACT SEARCH -->
            <div class="relative space-y-1">
              <label class="text-sm font-medium" for="edit-contact">
                Contact
              </label>

              <input
                id="edit-contact"
                v-model="linkSearch.contact"
                autocomplete="off"
                placeholder="Search contacts..."
                class="w-full rounded-lg border border-gray-300 p-2"
                @input="onLinkInput('contact')"
                @focus="searchLinks('contact')"
              />

              <div
                v-if="linkOpen.contact"
                class="absolute z-20 max-h-44 w-full overflow-y-auto rounded-lg border bg-white shadow-lg"
              >
                <button
                  v-for="item in linkResults.contact"
                  :key="item.value"
                  type="button"
                  class="block w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
                  @mousedown.prevent="chooseLink('contact', item)"
                >
                  <span class="block font-medium">
                    {{ item.label }}
                  </span>
                  <span
                    v-if="item.label !== item.value"
                    class="block text-xs text-gray-500"
                  >
                    {{ item.value }}
                  </span>
                </button>

                <p
                  v-if="!linkResults.contact.length"
                  class="p-3 text-xs text-gray-500"
                >
                  No results
                </p>
              </div>
            </div>

            <!-- COMPANY SEARCH -->
            <div class="relative space-y-1">
              <label class="text-sm font-medium" for="edit-company">
                Company
              </label>

              <input
                id="edit-company"
                v-model="linkSearch.company"
                autocomplete="off"
                placeholder="Search companies..."
                class="w-full rounded-lg border border-gray-300 p-2"
                @input="onLinkInput('company')"
                @focus="searchLinks('company')"
              />

              <div
                v-if="linkOpen.company"
                class="absolute z-20 max-h-44 w-full overflow-y-auto rounded-lg border bg-white shadow-lg"
              >
                <button
                  v-for="item in linkResults.company"
                  :key="item.value"
                  type="button"
                  class="block w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
                  @mousedown.prevent="chooseLink('company', item)"
                >
                  <span class="block font-medium">
                    {{ item.label }}
                  </span>
                  <span
                    v-if="item.label !== item.value"
                    class="block text-xs text-gray-500"
                  >
                    {{ item.value }}
                  </span>
                </button>

                <p
                  v-if="!linkResults.company.length"
                  class="p-3 text-xs text-gray-500"
                >
                  No results
                </p>
              </div>
            </div>

          </div>

          <p class="mt-3 text-xs text-gray-500">
            For Contact, Company and Owner, select a result
            from the search list. Empty fields will be cleared.
          </p>

          <!-- ERROR -->
          <p
            v-if="editError"
            role="alert"
            class="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-600"
          >
            {{ editError }}
          </p>

          <!-- ACTIONS -->
          <div class="mt-6 flex justify-end gap-3">
            <button
              type="button"
              class="rounded-lg border px-4 py-2"
              :disabled="editSaving"
              @click="closeEdit"
            >
              Cancel
            </button>

            <button
              type="submit"
              :disabled="editSaving"
              class="rounded-lg bg-gray-900 px-5 py-2 text-white disabled:opacity-50"
            >
              {{ editSaving ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import {
  computed,
  defineComponent,
  h,
  reactive,
  ref,
  watch,
} from 'vue'

import { useRoute, useRouter } from 'vue-router'
import { Badge, Button, call } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { formatCurrency, formatDate } from '@/utils'

const route = useRoute()
const router = useRouter()

// API DOCTYPES
const LINK_DOCTYPES = {
  contact: 'DoubleT Contact',
  company: 'DoubleT Company',
  deal_owner: 'User',
}

// MAIN STATE
const deal = ref(null)
const loading = ref(false)
const error = ref('')

// STAGE STATE
const stageOptions = ref([])
const selectedStage = ref('')
const stageSaving = ref(false)
const stagesLoading = ref(false)
const stageError = ref('')

// EDIT STATE
const showEdit = ref(false)
const editSaving = ref(false)
const editError = ref('')

const editForm = reactive({
  deal_title: '',
  amount: '',
  deal_type: '',
  deal_owner: '',
  contact: '',
  company: '',
  expected_close_date: '',
})

// LINK SEARCH STATE
const linkSearch = reactive({
  contact: '',
  company: '',
  deal_owner: '',
})

const linkResults = reactive({
  contact: [],
  company: [],
  deal_owner: [],
})

const linkOpen = reactive({
  contact: false,
  company: false,
  deal_owner: false,
})

const linkLabels = reactive({
  contact: {},
  company: {},
  deal_owner: {},
})

const searchTimers = {}
const searchVersions = {
  contact: 0,
  company: 0,
  deal_owner: 0,
}

// COMPUTED VALUES
const title = computed(
  () => deal.value?.deal_title || deal.value?.name || 'Deal'
)

const displayAmount = computed(() => {
  const amount = deal.value?.amount

  if (amount === null || amount === undefined || amount === '') {
    return '-'
  }

  return formatCurrency(amount)
})

function dateValue(value) {
  if (!value) return '-'

  try {
    return formatDate(value)
  } catch {
    return String(value)
  }
}

function displayLink(field, value) {
  if (!value) return '-'
  return linkLabels[field]?.[value] || value
}

function getApiError(e) {
  if (Array.isArray(e?._server_messages)) {
    return e._server_messages.join(', ')
  }

  return e?.message || 'Unknown server error'
}

// LOAD DEAL
async function loadDeal() {
  loading.value = true
  error.value = ''

  try {
    const result = await call('frappe.client.get', {
      doctype: 'DoubleT Deal',
      name: route.params.dealId,
    })

    deal.value = result
    selectedStage.value = result?.stage || ''

    return result
  } catch (e) {
    console.error('Load Deal failed:', e)
    error.value = getApiError(e)
    throw e
  } finally {
    loading.value = false
  }
}

// LOAD STAGE OPTIONS
async function loadStages() {
  stagesLoading.value = true

  try {
    const result = await call('frappe.client.get_list', {
      doctype: 'DoubleT Deal Stage',
      fields: ['name', 'stage_name', 'sort_order'],
      order_by: 'sort_order asc',
      limit_page_length: 100,
    })

    stageOptions.value = Array.isArray(result) ? result : []
  } catch (e) {
    stageError.value = getApiError(e)
  } finally {
    stagesLoading.value = false
  }
}

// UPDATE STAGE
async function saveStage() {
  if (
    !deal.value?.name ||
    !selectedStage.value ||
    selectedStage.value === deal.value.stage
  ) {
    return
  }

  stageSaving.value = true
  stageError.value = ''

  const previous = deal.value.stage

  try {
    await call('frappe.client.set_value', {
      doctype: 'DoubleT Deal',
      name: deal.value.name,
      fieldname: 'stage',
      value: selectedStage.value,
    })

    await loadDeal()
  } catch (e) {
    selectedStage.value = previous
    stageError.value = getApiError(e)
  } finally {
    stageSaving.value = false
  }
}

// SEARCH FRAPPE LINK RECORDS
async function searchLinks(field) {
  const doctype = LINK_DOCTYPES[field]
  if (!doctype) return

  const version = ++searchVersions[field]

  try {
    const result = await call(
      'frappe.desk.search.search_link',
      {
        doctype,
        txt: linkSearch[field] || '',
        page_length: 20,
      }
    )

    if (version !== searchVersions[field] || !showEdit.value) {
      return
    }

    const items = Array.isArray(result)
      ? result
      : Array.isArray(result?.results)
        ? result.results
        : []

    linkResults[field] = items
      .map(item => {
        const value = String(item.value || item.name || '')
        const label = String(
          item.label || item.description || value
        )
        return { value, label }
      })
      .filter(item => item.value)

    for (const item of linkResults[field]) {
      linkLabels[field][item.value] = item.label
    }

    linkOpen[field] = true
  } catch (e) {
    if (version !== searchVersions[field]) return
    console.error(`Search ${field} failed:`, e)
    linkResults[field] = []
    linkOpen[field] = false
    editError.value = `Unable to search ${doctype}: ${getApiError(e)}`
  }
}

// SEARCH WHEN INPUT CHANGES
function onLinkInput(field) {
  editForm[field] = ''

  if (searchTimers[field]) {
    clearTimeout(searchTimers[field])
  }

  ++searchVersions[field]

  searchTimers[field] = setTimeout(() => {
    searchLinks(field)
  }, 250)
}

// CHOOSE SEARCH RESULT
function chooseLink(field, item) {
  editForm[field] = item.value
  linkSearch[field] = item.label
  linkLabels[field][item.value] = item.label
  linkOpen[field] = false
  ++searchVersions[field]

  if (searchTimers[field]) {
    clearTimeout(searchTimers[field])
  }
}

function closeAllSearches() {
  for (const field of Object.keys(LINK_DOCTYPES)) {
    linkOpen[field] = false
    ++searchVersions[field]

    if (searchTimers[field]) {
      clearTimeout(searchTimers[field])
    }
  }
}

// PRELOAD LABELS FROM LINK SEARCH
async function preloadLinkLabel(field, value) {
  if (!value) return

  try {
    const result = await call(
      'frappe.desk.search.search_link',
      {
        doctype: LINK_DOCTYPES[field],
        txt: value,
        page_length: 20,
      }
    )

    const items = Array.isArray(result)
      ? result
      : result?.results || []

    const match = items.find(
      item => String(item.value || item.name) === value
    )

    if (match) {
      linkLabels[field][value] = String(
        match.label || match.description || value
      )
    }
  } catch (e) {
    // Fallback: display the record ID.
    console.debug(`Label lookup failed for ${field}`, e)
  }
}

// OPEN EDIT MODAL
function openEdit() {
  if (!deal.value) return

  editError.value = ''

  Object.assign(editForm, {
    deal_title: deal.value.deal_title || '',
    amount: deal.value.amount ?? '',
    deal_type: deal.value.deal_type || '',
    deal_owner: deal.value.deal_owner || '',
    contact: deal.value.contact || '',
    company: deal.value.company || '',
    expected_close_date:
      deal.value.expected_close_date?.slice(0, 10) || '',
  })

  for (const field of Object.keys(LINK_DOCTYPES)) {
    linkSearch[field] = editForm[field]
      ? displayLink(field, editForm[field])
      : ''
    linkResults[field] = []
    linkOpen[field] = false
  }

  showEdit.value = true
}

// CLOSE EDIT
function closeEdit() {
  if (editSaving.value) return

  showEdit.value = false
  editError.value = ''
  closeAllSearches()
}

// CHECK VALID LINK INPUTS
function validateLinks() {
  for (const field of Object.keys(LINK_DOCTYPES)) {
    if (linkSearch[field].trim() && !editForm[field]) {
      editError.value =
        `Please select a valid ${field.replace('_', ' ')} from search results.`
      return false
    }
  }
  return true
}

// SAVE EDIT
async function saveEdit() {
  if (!deal.value?.name || editSaving.value) return

  editError.value = ''

  if (!editForm.deal_title.trim()) {
    editError.value = 'Deal Title is required.'
    return
  }

  if (
    editForm.amount !== '' &&
    (!Number.isFinite(Number(editForm.amount)) ||
      Number(editForm.amount) < 0)
  ) {
    editError.value = 'Amount must be a non-negative number.'
    return
  }

  if (!validateLinks()) return

  editSaving.value = true
  closeAllSearches()

  try {
    const values = {
      deal_title: editForm.deal_title.trim(),
      amount: editForm.amount === ''
        ? 0
        : Number(editForm.amount),
      deal_type: editForm.deal_type || null,
      deal_owner: editForm.deal_owner || null,
      contact: editForm.contact || null,
      company: editForm.company || null,
      expected_close_date:
        editForm.expected_close_date || null,
    }

    await call('frappe.client.set_value', {
      doctype: 'DoubleT Deal',
      name: deal.value.name,
      fieldname: values,
    })

    await loadDeal()

    showEdit.value = false
    editError.value = ''
  } catch (e) {
    console.error('Save Deal failed:', e)
    editError.value = getApiError(e)
  } finally {
    editSaving.value = false
  }
}

// INITIAL LOAD
loadStages()

watch(
  () => route.params.dealId,
  newId => {
    showEdit.value = false
    closeAllSearches()
    deal.value = null

    if (newId) {
      loadDeal()
        .then(async result => {
          if (!result) return

          await Promise.all([
            preloadLinkLabel('contact', result.contact),
            preloadLinkLabel('company', result.company),
            preloadLinkLabel('deal_owner', result.deal_owner),
          ])
        })
        .catch(() => {})
    }
  },
  { immediate: true }
)

// REUSABLE DISPLAY COMPONENT
const InfoField = defineComponent({
  props: {
    label: String,
    value: [String, Number],
  },

  setup(props) {
    return () =>
      h('div', {}, [
        h('div', {
          class: 'text-xs text-ink-gray-5',
        }, props.label),

        h('div', {
          class: 'mt-1 break-words text-base text-ink-gray-8',
        },
        props.value === null ||
        props.value === undefined ||
        props.value === ''
          ? '-'
          : String(props.value)),
      ])
  },
})
</script>
