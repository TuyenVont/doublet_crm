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
              {{ __('Deals') }}
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
          :disabled="!deal"
          @click="openDesk"
        />
      </template>
    </LayoutHeader>

    <div
      v-if="loading"
      class="flex flex-1 items-center justify-center text-ink-gray-5"
    >
      {{ __('Loading deal...') }}
    </div>

    <div
      v-else-if="error"
      class="flex flex-1 items-center justify-center"
    >
      <div class="text-center">
        <div class="text-lg-medium text-ink-gray-8">
          {{ __('Unable to load deal') }}
        </div>

        <div class="mt-1 text-sm text-ink-gray-5">
          {{ error }}
        </div>
      </div>
    </div>

    <div v-else-if="deal" class="flex-1 overflow-auto bg-surface-gray-1">
      <div class="mx-auto max-w-6xl p-5">
        <div class="mb-5 rounded-lg border bg-surface-white p-5">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div class="text-2xl font-semibold text-ink-gray-9">
                {{ deal.deal_title || deal.name }}
              </div>

              <div class="mt-1 text-sm text-ink-gray-5">
                {{ deal.name }}
              </div>
            </div>

            <Badge
              v-if="deal.stage"
              :label="deal.stage"
              theme="blue"
              variant="subtle"
            />
          </div>

          <div class="mt-5 grid gap-4 sm:grid-cols-3">
            <div>
              <div class="text-xs text-ink-gray-5">
                {{ __('Amount') }}
              </div>
              <div class="mt-1 text-base-medium text-ink-gray-9">
                {{ displayAmount }}
              </div>
            </div>

            <div>
              <div class="text-xs text-ink-gray-5">
                {{ __('Expected Close Date') }}
              </div>
              <div class="mt-1 text-base text-ink-gray-8">
                {{ dateValue(deal.expected_close_date) }}
              </div>
            </div>

            <div>
              <div class="text-xs text-ink-gray-5">
                {{ __('Owner') }}
              </div>
              <div class="mt-1 text-base text-ink-gray-8">
                {{ deal.deal_owner || deal.owner || '-' }}
              </div>
            </div>
          </div>
        </div>

        <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <section class="rounded-lg border bg-surface-white">
            <div class="border-b px-5 py-4">
              <div class="text-lg-medium text-ink-gray-9">
                {{ __('Deal Information') }}
              </div>
            </div>

            <div class="grid gap-x-8 gap-y-5 p-5 sm:grid-cols-2">
              <InfoField :label="__('Deal Title')" :value="deal.deal_title" />
              <InfoField :label="__('Stage')" :value="deal.stage" />
              <InfoField :label="__('Deal Type')" :value="deal.deal_type" />
              <InfoField :label="__('Amount')" :value="displayAmount" />
              <InfoField
                :label="__('Expected Close Date')"
                :value="dateValue(deal.expected_close_date)"
              />
              <InfoField
                :label="__('Won On')"
                :value="dateValue(deal.won_on)"
              />
              <InfoField
                :label="__('Lost On')"
                :value="dateValue(deal.lost_on)"
              />
              <InfoField
                :label="__('Lost Reason')"
                :value="deal.lost_reason"
              />
              <InfoField
                :label="__('Created')"
                :value="dateValue(deal.creation)"
              />
              <InfoField
                :label="__('Last Modified')"
                :value="dateValue(deal.modified)"
              />
            </div>
          </section>

          <aside class="space-y-5">
            <section class="rounded-lg border bg-surface-white">
              <div class="border-b px-5 py-4">
                <div class="text-lg-medium text-ink-gray-9">
                  {{ __('Related') }}
                </div>
              </div>

              <div class="space-y-5 p-5">
                <InfoField :label="__('Contact')" :value="deal.contact" />
                <InfoField :label="__('Company')" :value="deal.company" />
                <InfoField
                  :label="__('Source Lead')"
                  :value="deal.source_lead"
                />
                <InfoField
                  :label="__('Deal Owner')"
                  :value="deal.deal_owner || deal.owner"
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
import { formatCurrency, formatDate } from '@/utils'

const route = useRoute()
const router = useRouter()

const deal = ref(null)
const loading = ref(false)
const error = ref('')

const title = computed(() => {
  return deal.value?.deal_title || deal.value?.name || __('Deal')
})

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
    return value
  }
}

async function loadDeal() {
  loading.value = true
  error.value = ''

  try {
    deal.value = await call('frappe.client.get', {
      doctype: 'DoubleT Deal',
      name: route.params.dealId,
    })
  } catch (e) {
    console.error(e)
    error.value = e?.message || __('Deal not found')
    deal.value = null
  } finally {
    loading.value = false
  }
}

function openDesk() {
  if (!deal.value?.name) return

  window.open(
    `/app/doublet-deal/${encodeURIComponent(deal.value.name)}`,
    '_blank'
  )
}

watch(
  () => route.params.dealId,
  () => loadDeal(),
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
