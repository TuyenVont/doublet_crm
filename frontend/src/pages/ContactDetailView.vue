<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-2">
          <Button variant="ghost" icon="chevron-left" @click="router.push({ name: 'Contacts' })" />

          <div class="flex min-w-0 items-center gap-1 text-lg-medium text-ink-gray-9">
            <button class="shrink-0 text-ink-gray-6 hover:text-ink-gray-9" @click="router.push({ name: 'Contacts' })">
              {{ __('Contacts') }}
            </button>
            <span class="text-ink-gray-4">/</span>
            <span class="max-w-[420px] truncate">{{ isNew ? __('New Contact') : title }}</span>
          </div>
        </div>
      </template>

      <template #right-header>
        <div v-if="!isNew && contact" class="flex items-center gap-2">
          <AssignTo
            v-model="assignees"
            doctype="DoubleT Contact"
            :docname="contact.name"
          />
          <Button variant="subtle" icon="trash-2" :label="__('Delete')" @click="remove" />
          <Button variant="subtle" icon="refresh-cw" :loading="loading" @click="reloadContact" />
        </div>
      </template>
    </LayoutHeader>

    <div v-if="loading && !contact && !isNew" class="flex flex-1 items-center justify-center text-ink-gray-5">
      {{ __('Loading Contact...') }}
    </div>

    <div v-else-if="error && !contact && !isNew" class="flex flex-1 flex-col items-center justify-center gap-3">
      <div class="text-lg font-medium text-ink-gray-9">{{ __('Unable to load Contact') }}</div>
      <p class="text-sm text-red-600">{{ error }}</p>
      <Button :label="__('Retry')" @click="reloadContact" />
    </div>

    <div v-else-if="isNew" class="flex min-h-0 flex-1 overflow-hidden">
      <DoubleTContactDataPanel
        :contact="null"
        :is-new="true"
        @saved="onCreated"
      />
    </div>

    <div v-else-if="contact" class="flex min-h-0 flex-1 overflow-hidden">
      <Tabs
        v-model="tabIndex"
        :tabs="tabs"
        class="flex flex-1 flex-col overflow-hidden [&_[role='tab']]:shrink-0 [&_[role='tab']]:px-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-7.5 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow [&_[role='tabpanel']]:min-h-0"
      >
        <template #tab-panel>
          <DoubleTContactDataPanel
            v-if="activeTabName === 'Data'"
            :contact="contact"
            @saved="onContactSaved"
          />

          <Activities
            v-else
            ref="activities"
            v-model:reload="reloadActivities"
            v-model:tabIndex="tabIndex"
            doctype="DoubleT Contact"
            :docname="contactId"
            :tabs="tabs"
          />
        </template>
      </Tabs>

      <Resizer side="right" class="flex flex-col border-l">
        <div
          class="flex h-[45px] shrink-0 cursor-copy items-center border-b px-5 py-2.5 text-lg-medium text-ink-gray-9"
          :title="__('Click to copy Contact ID')"
          @click="copyContactId"
        >
          <span class="truncate">{{ contactId }}</span>
        </div>

        <div class="flex shrink-0 items-center gap-4 border-b p-5">
          <div class="flex size-12 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-xl font-semibold text-ink-gray-7">
            {{ contactInitial }}
          </div>

          <div class="min-w-0 flex-1">
            <div class="truncate text-xl font-semibold text-ink-gray-9" :title="title">{{ title }}</div>
            <div v-if="contact.job_title || companyLabel" class="mt-1 flex min-w-0 items-center gap-1 text-sm text-ink-gray-5">
              <span v-if="contact.job_title" class="truncate">{{ contact.job_title }}</span>
              <span v-if="contact.job_title && companyLabel" class="shrink-0">·</span>
              <button
                v-if="companyLabel && contact.company"
                type="button"
                class="min-w-0 truncate text-left text-blue-600 hover:underline"
                @click="openCompany"
              >
                {{ companyLabel }}
              </button>
              <span v-else-if="companyLabel" class="truncate">{{ companyLabel }}</span>
            </div>
            <div class="mt-2 flex flex-wrap items-center gap-2 text-xs text-ink-gray-5">
              <span v-if="contact.email" class="rounded-full bg-surface-gray-2 px-2 py-1">{{ contact.email }}</span>
              <span v-if="contact.phone" class="rounded-full bg-surface-gray-2 px-2 py-1">{{ contact.phone }}</span>
            </div>
          </div>
        </div>

        <div class="min-h-0 flex-1 overflow-y-auto">
          <DoubleTContactInfoPanel :contact="contact" />
        </div>
      </Resizer>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Tabs, call, toast } from 'frappe-ui'

import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import Resizer from '@/components/Resizer.vue'
import AssignTo from '@/components/AssignTo.vue'
import DoubleTContactDataPanel from '@/components/Contact/DoubleTContactDataPanel.vue'
import DoubleTContactInfoPanel from '@/components/Contact/DoubleTContactInfoPanel.vue'

import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const route = useRoute()
const router = useRouter()

const contactId = computed(() => route.params.contactId || '')
const isNew = computed(() => route.name === 'ContactCreate' || !contactId.value)

const contact = ref(null)
const loading = ref(false)
const error = ref('')
const reloadActivities = ref(false)
const activities = ref(null)
const assignees = ref([])
const companyLabel = ref('')

const title = computed(() => {
  if (!contact.value) return __('Contact')
  return [contact.value.first_name, contact.value.last_name].filter(Boolean).join(' ') || contact.value.name
})

const contactInitial = computed(() => title.value?.trim()?.charAt(0)?.toUpperCase() || 'C')

const tabs = computed(() => [
  { name: 'Activity', label: __('Activity'), icon: ActivityIcon },
  { name: 'Emails', label: __('Emails'), icon: EmailIcon },
  { name: 'Comments', label: __('Comments'), icon: CommentIcon },
  { name: 'Data', label: __('Data'), icon: DetailsIcon },
  { name: 'Calls', label: __('Calls'), icon: PhoneIcon },
  { name: 'Tasks', label: __('Tasks'), icon: TaskIcon },
  { name: 'Notes', label: __('Notes'), icon: NoteIcon },
  { name: 'Attachments', label: __('Attachments'), icon: AttachmentIcon },
])

const { tabIndex } = useActiveTabManager(tabs, 'lastContactTab')
const activeTabName = computed(() => tabs.value?.[tabIndex.value]?.name || 'Activity')

function apiError(e) {
  return e?.messages?.join?.('; ') || e?._server_messages?.join?.('; ') || e?.message || __('Request failed')
}

function parseAssignees(value) {
  if (!value) return []
  let names = value
  if (typeof value === 'string') {
    try {
      names = JSON.parse(value)
    } catch {
      names = []
    }
  }
  if (!Array.isArray(names)) return []
  return names.map(name => ({ name, label: name }))
}

async function loadCompanyLabel() {
  companyLabel.value = ''
  if (!contact.value?.company) return
  try {
    const company = await call('frappe.client.get', {
      doctype: 'DoubleT Company',
      name: contact.value.company,
    })
    companyLabel.value = company?.company_name || company?.name || contact.value.company
  } catch {
    companyLabel.value = contact.value.company
  }
}


function openCompany() {
  if (!contact.value?.company) return
  router.push({ name: 'CompanyDetail', params: { companyId: contact.value.company } })
}

async function loadContact() {
  if (isNew.value || !contactId.value) return null
  loading.value = true
  error.value = ''
  try {
    const result = await call('frappe.client.get', {
      doctype: 'DoubleT Contact',
      name: contactId.value,
    })
    contact.value = result
    assignees.value = parseAssignees(result?._assign)
    await loadCompanyLabel()
    return result
  } catch (e) {
    console.error('Load Contact failed:', e)
    error.value = apiError(e)
    contact.value = null
    return null
  } finally {
    loading.value = false
  }
}

async function reloadContact() {
  const result = await loadContact()
  if (result) reloadActivities.value = true
  return result
}

async function onCreated(result) {
  const name = result?.name
  if (!name) {
    toast.error(__('Contact was created but its ID could not be resolved.'))
    return
  }
  await router.replace({ name: 'ContactDetail', params: { contactId: name } })
}

async function onContactSaved(data) {
  if (data && contact.value) Object.assign(contact.value, data)
  await reloadContact()
}

async function remove() {
  if (!contact.value?.name) return
  const ok = window.confirm(__('Delete this contact? This cannot be undone.'))
  if (!ok) return

  try {
    await call('frappe.client.delete', {
      doctype: 'DoubleT Contact',
      name: contact.value.name,
    })
    toast.success(__('Contact deleted'))
    await router.push({ name: 'Contacts' })
  } catch (e) {
    toast.error(apiError(e))
  }
}

async function copyContactId() {
  if (!contactId.value) return
  try {
    await navigator.clipboard.writeText(contactId.value)
    toast.success(__('Contact ID copied'))
  } catch {
    // Clipboard may be unavailable in some local environments.
  }
}

watch(
  [contactId, isNew],
  async () => {
    contact.value = null
    companyLabel.value = ''
    error.value = ''
    if (!isNew.value) await loadContact()
  },
  { immediate: true },
)
</script>
