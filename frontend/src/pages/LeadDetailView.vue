<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            icon="chevron-left"
            @click="router.push({ name: 'Leads' })"
          />

          <div class="flex items-center gap-1 text-lg-medium text-ink-gray-9">
            <button
              class="text-ink-gray-6 hover:text-ink-gray-9"
              @click="router.push({ name: 'Leads' })"
            >
              {{ __('Leads') }}
            </button>

            <span class="text-ink-gray-4">/</span>

            <span class="max-w-[420px] truncate">
              {{ title }}
            </span>
          </div>
        </div>
      </template>

      <template #right-header>
        <Button
          variant="solid"
          :label="__('Edit')"
          iconLeft="edit-3"
          :disabled="!lead"
          @click="openDesk"
        />
      </template>
    </LayoutHeader>

    <div
      v-if="loading"
      class="flex flex-1 items-center justify-center text-ink-gray-5"
    >
      {{ __('Loading lead...') }}
    </div>

    <div
      v-else-if="error"
      class="flex flex-1 items-center justify-center"
    >
      <div class="text-center">
        <div class="text-lg-medium text-ink-gray-8">
          {{ __('Unable to load lead') }}
        </div>

        <div class="mt-1 text-sm text-ink-gray-5">
          {{ error }}
        </div>
      </div>
    </div>

    <div v-else-if="lead" class="flex-1 overflow-auto bg-surface-gray-1">
      <div class="mx-auto max-w-6xl p-5">
        <div class="mb-5 rounded-lg border bg-surface-white p-5">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div class="text-2xl font-semibold text-ink-gray-9">
                {{ title }}
              </div>

              <div class="mt-1 text-sm text-ink-gray-5">
                {{ lead.name }}
              </div>
            </div>

            <Badge
              v-if="lead.status"
              :label="lead.status"
              :theme="statusTheme"
              variant="subtle"
            />
          </div>

          <div class="mt-5 grid gap-4 sm:grid-cols-3">
            <div>
              <div class="text-xs text-ink-gray-5">
                {{ __('Company') }}
              </div>
              <div class="mt-1 text-base text-ink-gray-8">
                {{ lead.company_name || '-' }}
              </div>
            </div>

            <div>
              <div class="text-xs text-ink-gray-5">
                {{ __('Phone') }}
              </div>
              <div class="mt-1 text-base text-ink-gray-8">
                {{ lead.phone || '-' }}
              </div>
            </div>

            <div>
              <div class="text-xs text-ink-gray-5">
                {{ __('Owner') }}
              </div>
              <div class="mt-1 text-base text-ink-gray-8">
                {{ lead.lead_owner || lead.owner || '-' }}
              </div>
            </div>
          </div>
        </div>

        <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <section class="rounded-lg border bg-surface-white">
            <div class="border-b px-5 py-4">
              <div class="text-lg-medium text-ink-gray-9">
                {{ __('Lead Information') }}
              </div>
            </div>

            <div class="grid gap-x-8 gap-y-5 p-5 sm:grid-cols-2">
              <InfoField :label="__('First Name')" :value="lead.first_name" />
              <InfoField :label="__('Last Name')" :value="lead.last_name" />
              <InfoField :label="__('Email')" :value="lead.email" />
              <InfoField :label="__('Phone')" :value="lead.phone" />
              <InfoField
                :label="__('Company Name')"
                :value="lead.company_name"
              />
              <InfoField :label="__('Source')" :value="lead.source" />
              <InfoField :label="__('Status')" :value="lead.status" />
              <InfoField
                :label="__('Lead Owner')"
                :value="lead.lead_owner || lead.owner"
              />
              <InfoField
                :label="__('Converted On')"
                :value="dateValue(lead.converted_on)"
              />
              <InfoField
                :label="__('Created')"
                :value="dateValue(lead.creation)"
              />
              <InfoField
                :label="__('Last Modified')"
                :value="dateValue(lead.modified)"
              />
            </div>

            <div
              v-if="lead.notes"
              class="border-t px-5 py-5"
            >
              <div class="text-xs text-ink-gray-5">
                {{ __('Notes') }}
              </div>

              <div class="mt-2 whitespace-pre-wrap text-base text-ink-gray-8">
                {{ lead.notes }}
              </div>
            </div>
          </section>

          <aside>
            <section class="rounded-lg border bg-surface-white">
              <div class="border-b px-5 py-4">
                <div class="text-lg-medium text-ink-gray-9">
                  {{ __('Conversion') }}
                </div>
              </div>

              <div class="space-y-5 p-5">
                <InfoField
                  :label="__('Converted Contact')"
                  :value="lead.converted_contact"
                />
                <InfoField
                  :label="__('Converted Company')"
                  :value="lead.converted_company"
                />
                <InfoField
                  :label="__('Converted Deal')"
                  :value="lead.converted_deal"
                />
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Badge, Button, call } from 'frappe-ui'

import LayoutHeader from '@/components/LayoutHeader.vue'
import { formatDate } from '@/utils'

const route = useRoute()
const router = useRouter()

const lead = ref(null)
const loading = ref(false)
const error = ref('')

const title = computed(() => {
  if (!lead.value) return __('Lead')

  const fullName = [
    lead.value.first_name,
    lead.value.last_name,
  ]
    .filter(Boolean)
    .join(' ')

  return fullName || lead.value.name
})

const statusTheme = computed(() => {
  const status = lead.value?.status

  if (status === 'CONVERTED' || status === 'QUALIFIED') {
    return 'green'
  }

  if (status === 'UNQUALIFIED' || status === 'JUNK') {
    return 'red'
  }

  if (status === 'CONTACTED') {
    return 'orange'
  }

  return 'blue'
})

function dateValue(value) {
  if (!value) return '-'

  try {
    return formatDate(value)
  } catch {
    return value
  }
}

async function loadLead() {
  loading.value = true
  error.value = ''

  try {
    lead.value = await call('frappe.client.get', {
      doctype: 'DoubleT Lead',
      name: route.params.leadId,
    })
  } catch (e) {
    console.error(e)
    error.value = e?.message || __('Lead not found')
    lead.value = null
  } finally {
    loading.value = false
  }
}

function openDesk() {
  if (!lead.value?.name) return

  window.open(
    `/app/doublet-lead/${encodeURIComponent(lead.value.name)}`,
    '_blank'
  )
}

watch(
  () => route.params.leadId,
  () => loadLead(),
  { immediate: true }
)

const InfoField = defineComponent({
  props: {
    label: String,
    value: [String, Number],
  },

  setup(props) {
    return () =>
      h('div', {}, [
        h(
          'div',
          { class: 'text-xs text-ink-gray-5' },
          props.label
        ),
        h(
          'div',
          {
            class:
              'mt-1 break-words text-base text-ink-gray-8',
          },
          props.value || '-'
        ),
      ])
  },
})
</script>
