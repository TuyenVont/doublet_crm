<template>
  <div class="flex h-full flex-col bg-surface-white overflow-auto">
    <LayoutHeader>
      <template #left-header>
        <Button variant="subtle" icon="arrow-left" @click="router.push({ name: listRoute })" />
        <span class="ml-3 font-semibold">{{ isNew ? `New ${kind}` : (doc?.[titleField] || kind) }}</span>
      </template>
      <template #right-header>
        <Button v-if="!isNew && !editing" label="Edit" @click="editing = true" />
        <Button v-if="!isNew && !editing" label="Delete" variant="subtle" @click="remove" />
        <Button v-if="editing" label="Cancel" variant="subtle" @click="cancel" />
        <Button v-if="editing" variant="solid" :loading="saving" label="Save" @click="save" />
      </template>
    </LayoutHeader>
    <div class="mx-auto w-full max-w-5xl space-y-6 p-6">
      <div v-if="error" role="alert" class="rounded border border-red-300 p-3 text-red-600">{{ error }}</div>
      <div v-if="loading" class="text-ink-gray-5">Loading...</div>
      <template v-else>
        <section class="rounded border border-outline-gray-2 p-5">
          <h2 class="mb-4 text-lg font-semibold">{{ kind }} Information</h2>
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div v-for="field in fields" :key="field.key" class="min-w-0">
              <label class="mb-1 block text-sm text-ink-gray-5">{{ field.label }} <span v-if="field.required">*</span></label>
              <template v-if="editing">
                <textarea v-if="field.multiline" v-model="form[field.key]" rows="3" class="w-full rounded border border-outline-gray-2 bg-transparent p-2" />
                <select v-else-if="field.link" v-model="form[field.key]" class="w-full rounded border border-outline-gray-2 bg-transparent p-2">
                  <option value="">— Select —</option>
                  <option v-if="form[field.key] && !linkOptions[field.key]?.some(x => x.name === form[field.key])" :value="form[field.key]">{{ form[field.key] }}</option>
                  <option v-for="option in linkOptions[field.key] || []" :key="option.name" :value="option.name">{{ option.label }}</option>
                </select>
                <input v-else v-model="form[field.key]" :type="field.type || 'text'" class="w-full rounded border border-outline-gray-2 bg-transparent p-2" />
              </template>
              <template v-else>
                <button v-if="field.key === 'company' && doc?.company" class="text-blue-600 hover:underline" @click="router.push({ name: 'CompanyDetail', params: { companyId: doc.company } })">{{ companyDisplayName }}</button>
                <p v-else class="break-words">{{ doc?.[field.key] || '—' }}</p>
              </template>
            </div>
          </div>
        </section>
        <section v-if="!isNew && !editing" class="rounded border border-outline-gray-2 p-5">
          <h2 class="mb-3 text-lg font-semibold">Related records</h2>
          <div v-for="group in related" :key="group.label" class="mb-5">
            <h3 class="mb-2 font-medium">{{ group.label }} ({{ group.rows.length }})</h3>
            <p v-if="!group.rows.length" class="text-sm text-ink-gray-5">No records</p>
            <button v-for="entry in group.rows" :key="entry.name" class="mb-2 block text-left text-blue-600 hover:underline" @click="router.push({ name: group.route, params: { [group.param]: entry.name } })">{{ entry.label }}</button>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'

const props = defineProps({ kind: { type: String, required: true } })
const router = useRouter()
const route = useRoute()
const isContact = computed(() => props.kind === 'Contact')
const doctype = computed(() => `DoubleT ${props.kind}`)
const listRoute = computed(() => isContact.value ? 'Contacts' : 'Companies')
const titleField = computed(() => isContact.value ? 'first_name' : 'company_name')
const recordName = computed(() => route.params[isContact.value ? 'contactId' : 'companyId'])
const isNew = computed(() => !recordName.value)
const contactFields = [
  { key: 'first_name', label: 'First Name', required: true }, { key: 'last_name', label: 'Last Name' },
  { key: 'phone', label: 'Phone' }, { key: 'email', label: 'Email', type: 'email' },
  { key: 'birthday', label: 'Birthday', type: 'date' }, { key: 'address', label: 'Address', multiline: true },
  { key: 'source', label: 'Source', link: 'DoubleT Lead Source' },
  { key: 'contact_owner', label: 'Contact Owner', link: 'User' },
  { key: 'company', label: 'Company', link: 'DoubleT Company' },
  { key: 'job_title', label: 'Job Title' }, { key: 'notes', label: 'Notes', multiline: true },
]
const companyFields = [
  { key: 'company_name', label: 'Company Name', required: true }, { key: 'tax_id', label: 'Tax ID' },
  { key: 'phone', label: 'Phone' }, { key: 'email', label: 'Email', type: 'email' },
  { key: 'website', label: 'Website', type: 'url' }, { key: 'address', label: 'Address', multiline: true },
  { key: 'industry', label: 'Industry' }, { key: 'size', label: 'Size' },
  { key: 'company_owner', label: 'Company Owner', link: 'User' },
]
const fields = computed(() => isContact.value ? contactFields : companyFields)
const form = reactive({})
const doc = ref(null)
const related = ref([])
const linkOptions = reactive({})
const loading = ref(false)
const saving = ref(false)
const editing = ref(false)
const error = ref('')

const companyDisplayName = computed(() => {
  const companyId = doc.value?.company
  if (!companyId) return '—'

  const option = linkOptions.company?.find(
    (item) => item.name === companyId
  )

  return option?.label || companyId
})

function apiError(e) { return e?.messages?.join('; ') || e?.message || 'Request failed' }
function fillForm(data = {}) {
  for (const field of fields.value) form[field.key] = data[field.key] || ''
}
async function loadLinks() {
  for (const field of fields.value.filter(f => f.link)) {
    try {
      const result = await call('frappe.client.get_list', {
        doctype: field.link, fields: field.link === 'DoubleT Company' ? ['name', 'company_name'] : ['name'],
        limit_page_length: 500, order_by: 'modified desc',
      })
      linkOptions[field.key] = (result || []).map(x => ({ name: x.name, label: x.company_name || x.name }))
    } catch { linkOptions[field.key] = [] }
  }
}
async function getRelated(label, dt, filters, fieldsToGet, routeName, param, labelField) {
  try {
    const result = await call('frappe.client.get_list', { doctype: dt, filters, fields: fieldsToGet, limit_page_length: 100 })
    return { label, route: routeName, param, rows: (result || []).map(x => ({ name: x.name, label: x[labelField] || x.name })) }
  } catch { return { label, route: routeName, param, rows: [] } }
}
async function loadRelated() {
  const name = recordName.value
  if (!name) return
  const tasks = isContact.value ? [
    getRelated('Deals', 'DoubleT Deal', { contact: name }, ['name', 'deal_title'], 'DealDetail', 'dealId', 'deal_title'),
    getRelated('Converted Leads', 'DoubleT Lead', { converted_contact: name }, ['name', 'first_name'], 'LeadDetail', 'leadId', 'first_name'),
  ] : [
    getRelated('Contacts', 'DoubleT Contact', { company: name }, ['name', 'first_name'], 'ContactDetail', 'contactId', 'first_name'),
    getRelated('Deals', 'DoubleT Deal', { company: name }, ['name', 'deal_title'], 'DealDetail', 'dealId', 'deal_title'),
    getRelated('Converted Leads', 'DoubleT Lead', { converted_company: name }, ['name', 'first_name'], 'LeadDetail', 'leadId', 'first_name'),
  ]
  related.value = await Promise.all(tasks)
}
async function load() {
  error.value = ''
  loading.value = true
  editing.value = isNew.value
  doc.value = null
  related.value = []
  try {
    if (!isNew.value) {
      doc.value = await call('frappe.client.get', { doctype: doctype.value, name: recordName.value })
    }
    fillForm(doc.value || {})
    if (!isNew.value) await loadRelated()
    await loadLinks()
  } catch (e) { error.value = apiError(e) }
  finally { loading.value = false }
}
function cancel() {
  if (isNew.value) router.push({ name: listRoute.value })
  else { fillForm(doc.value || {}); editing.value = false; error.value = '' }
}
async function save() {
  error.value = ''
  const required = fields.value.find(f => f.required && !String(form[f.key] || '').trim())
  if (required) { error.value = `${required.label} is required`; return }
  saving.value = true
  try {
    const values = Object.fromEntries(fields.value.map(f => [f.key, form[f.key] || null]))
    if (isNew.value) {
      const result = await call('frappe.client.insert', { doc: { doctype: doctype.value, ...values } })
      await router.replace({ name: isContact.value ? 'ContactDetail' : 'CompanyDetail', params: { [isContact.value ? 'contactId' : 'companyId']: result.name } })
    } else {
      await call('frappe.client.set_value', { doctype: doctype.value, name: recordName.value, fieldname: values })
    }
    await load()
  } catch (e) { error.value = apiError(e) }
  finally { saving.value = false }
}
async function remove() {
  if (!window.confirm(`Delete this ${props.kind.toLowerCase()}? This cannot be undone.`)) return
  error.value = ''
  try {
    await call('frappe.client.delete', { doctype: doctype.value, name: recordName.value })
    await router.push({ name: listRoute.value })
  } catch (e) { error.value = apiError(e) }
}
watch([recordName, () => props.kind], load, { immediate: true })
</script>
