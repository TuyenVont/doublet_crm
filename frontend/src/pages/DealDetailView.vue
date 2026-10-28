<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">

    <!-- =====================================================
         HEADER
    ====================================================== -->
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-2">

          <Button
            variant="ghost"
            icon="chevron-left"
            @click="router.push({ name: 'Deals' })"
          />

          <div
            class="flex min-w-0 items-center gap-1 text-lg-medium text-ink-gray-9"
          >
            <button
              class="shrink-0 text-ink-gray-6 hover:text-ink-gray-9"
              @click="router.push({ name: 'Deals' })"
            >
              {{ __('Deals') }}
            </button>

            <span class="text-ink-gray-4">
              /
            </span>

            <span class="max-w-[420px] truncate">
              {{ title }}
            </span>
          </div>
        </div>
      </template>

      <template #right-header>
        <div
          v-if="deal"
          class="flex items-center gap-2"
        >
          <!-- ASSIGN -->
          <AssignTo
            v-model="assignees"
            doctype="DoubleT Deal"
            :docname="dealId"
          />

          <!-- STAGE -->
          <select
            v-model="selectedStage"
            :disabled="
              stageSaving ||
              stagesLoading
            "
            class="max-w-[190px] rounded-lg border border-outline-gray-2 bg-white px-3 py-1.5 text-sm"
            @change="changeStage"
          >
            <option
              v-for="stage in stageOptions"
              :key="stage.name"
              :value="stage.name"
            >
              {{
                stage.stage_name ||
                stage.name
              }}
            </option>
          </select>

          <Button
            variant="subtle"
            icon="refresh-cw"
            :loading="loading"
            @click="reloadDeal"
          />
        </div>
      </template>
    </LayoutHeader>

    <!-- =====================================================
         INITIAL LOADING
    ====================================================== -->
    <div
      v-if="loading && !deal"
      class="flex flex-1 items-center justify-center text-ink-gray-5"
    >
      {{ __('Loading Deal...') }}
    </div>

    <!-- =====================================================
         ERROR
    ====================================================== -->
    <div
      v-else-if="error && !deal"
      class="flex flex-1 flex-col items-center justify-center gap-3"
    >
      <div class="text-lg font-medium text-ink-gray-9">
        {{ __('Unable to load Deal') }}
      </div>

      <p class="text-sm text-red-600">
        {{ error }}
      </p>

      <Button
        :label="__('Retry')"
        @click="reloadDeal"
      />
    </div>

    <!-- =====================================================
         MAIN RECORD LAYOUT
    ====================================================== -->
    <div
      v-else-if="deal"
      class="flex min-h-0 flex-1 overflow-hidden"
    >

      <!-- =================================================
           LEFT / MAIN CONTENT
      ================================================== -->
      <Tabs
        v-model="tabIndex"
        :tabs="tabs"
        class="
          flex flex-1 flex-col overflow-hidden
          [&_[role='tab']]:shrink-0
          [&_[role='tab']]:px-0
          [&_[role='tablist']]:min-h-[45px]
          [&_[role='tablist']]:gap-7.5
          [&_[role='tablist']]:px-5
          [&_[role='tablist']::-webkit-scrollbar]:h-0
          [&_[role='tabpanel']:not([hidden])]:flex
          [&_[role='tabpanel']:not([hidden])]:grow
          [&_[role='tabpanel']]:min-h-0
        "
      >
        <template #tab-panel>

          <!-- CUSTOM DATA -->
          <DoubleTDealDataPanel
            v-if="activeTabName === 'Data'"
            :deal="deal"
            @saved="onDealSaved"
          />

          <!-- NORMAL CRM ACTIVITY TABS -->
          <Activities
            v-else
            ref="activities"
            v-model:reload="reloadActivities"
            v-model:tabIndex="tabIndex"
            doctype="DoubleT Deal"
            :docname="dealId"
            :tabs="tabs"
          />

        </template>
      </Tabs>

      <!-- =================================================
           RIGHT SIDEBAR
      ================================================== -->
      <Resizer
        side="right"
        class="flex flex-col border-l"
      >

        <!-- RECORD ID -->
        <div
          class="flex h-[45px] shrink-0 cursor-copy items-center border-b px-5 py-2.5 text-lg-medium text-ink-gray-9"
          :title="__('Click to copy Deal ID')"
          @click="copyDealId"
        >
          <span class="truncate">
            {{ dealId }}
          </span>
        </div>

        <!-- PROFILE -->
        <div
          class="flex shrink-0 items-center gap-4 border-b p-5"
        >
          <div
            class="flex size-11 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-lg font-semibold text-ink-gray-7"
          >
            {{ dealInitial }}
          </div>

          <div class="min-w-0 flex-1">
            <div
              class="truncate text-xl font-semibold text-ink-gray-9"
              :title="title"
            >
              {{ title }}
            </div>

            <div
              class="mt-1 flex flex-wrap items-center gap-2"
            >
              <span
                v-if="deal.stage"
                class="rounded-md bg-surface-gray-2 px-2 py-0.5 text-xs text-ink-gray-7"
              >
                {{ deal.stage }}
              </span>

              <span
                v-if="displayAmount !== '-'"
                class="text-sm font-medium text-ink-gray-7"
              >
                {{ displayAmount }}
              </span>
            </div>
          </div>
        </div>

        <!-- SIDEBAR CONTENT -->
        <div class="min-h-0 flex-1 overflow-y-auto">
          <DoubleTDealInfoPanel
            :deal="deal"
            @saved="onDealSaved"
          />
        </div>

      </Resizer>
    </div>

    <!-- =====================================================
         LOST REASON MODAL
    ====================================================== -->
    <Teleport to="body">
      <div
        v-if="showLostModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        @click.self="cancelLostStage"
      >
        <div
          class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl"
        >
          <div class="mb-4">
            <h2 class="text-lg font-semibold text-ink-gray-9">
              {{ __('Mark Deal as Lost') }}
            </h2>

            <p class="mt-1 text-sm text-ink-gray-5">
              {{
                __(
                  'Enter a reason before moving this Deal to a Lost stage.'
                )
              }}
            </p>
          </div>

          <label class="space-y-1">
            <span class="text-sm font-medium text-ink-gray-8">
              {{ __('Lost Reason') }} *
            </span>

            <textarea
              v-model="lostReason"
              rows="4"
              autofocus
              class="w-full resize-y rounded-lg border border-outline-gray-2 px-3 py-2 text-sm"
              :placeholder="__('Why was this Deal lost?')"
            />
          </label>

          <p
            v-if="lostError"
            class="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600"
          >
            {{ lostError }}
          </p>

          <div class="mt-5 flex justify-end gap-2">
            <Button
              :label="__('Cancel')"
              :disabled="stageSaving"
              @click="cancelLostStage"
            />

            <Button
              variant="solid"
              :label="
                stageSaving
                  ? __('Saving...')
                  : __('Mark Lost')
              "
              :disabled="stageSaving"
              @click="confirmLostStage"
            />
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import {
  computed,
  ref,
  watch,
} from 'vue'

import {
  useRoute,
  useRouter,
} from 'vue-router'

import {
  Button,
  Tabs,
  call,
  toast,
} from 'frappe-ui'

import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import Resizer from '@/components/Resizer.vue'
import AssignTo from '@/components/AssignTo.vue'

import DoubleTDealDataPanel from '@/components/Deal/DoubleTDealDataPanel.vue'
import DoubleTDealInfoPanel from '@/components/Deal/DoubleTDealInfoPanel.vue'

import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'

import {
  formatCurrency,
} from '@/utils'

import {
  useActiveTabManager,
} from '@/composables/useActiveTabManager'

/* =====================================================
 * ROUTE
 * ===================================================== */

const route = useRoute()
const router = useRouter()

const props = defineProps({
  dealId: {
    type: String,
    default: '',
  },
})

const dealId = computed(() => {
  return (
    props.dealId ||
    route.params.dealId ||
    ''
  )
})

/* =====================================================
 * MAIN STATE
 * ===================================================== */

const deal = ref(null)

const loading = ref(false)
const error = ref('')

const activities = ref(null)
const reloadActivities = ref(false)

/*
 * AssignTo itself persists assignments.
 * For now the local array provides the v-model used
 * by the component, matching the Deal record page shell.
 */
const assignees = ref([])

/* =====================================================
 * DEAL STAGE
 * ===================================================== */

const stageOptions = ref([])
const stagesLoading = ref(false)
const stageSaving = ref(false)

const selectedStage = ref('')
const previousStage = ref('')

const pendingLostStage = ref('')

const showLostModal = ref(false)
const lostReason = ref('')
const lostError = ref('')

/* =====================================================
 * DISPLAY
 * ===================================================== */

const title = computed(() => {
  return (
    deal.value?.deal_title ||
    deal.value?.name ||
    dealId.value ||
    __('Deal')
  )
})

const dealInitial = computed(() => {
  const value =
    title.value
      ?.trim()
      ?.charAt(0)
      ?.toUpperCase()

  return value || 'D'
})

const displayAmount = computed(() => {
  const amount =
    deal.value?.amount

  if (
    amount === null ||
    amount === undefined ||
    amount === ''
  ) {
    return '-'
  }

  try {
    return formatCurrency(amount)
  } catch {
    return String(amount)
  }
})

/* =====================================================
 * TABS
 * ===================================================== */

const tabs = computed(() => {
  return [
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },

    {
      name: 'Emails',
      label: __('Emails'),
      icon: EmailIcon,
    },

    {
      name: 'Comments',
      label: __('Comments'),
      icon: CommentIcon,
    },

    {
      name: 'Data',
      label: __('Data'),
      icon: DetailsIcon,
    },

    {
      name: 'Calls',
      label: __('Calls'),
      icon: PhoneIcon,
    },

    {
      name: 'Tasks',
      label: __('Tasks'),
      icon: TaskIcon,
    },

    {
      name: 'Notes',
      label: __('Notes'),
      icon: NoteIcon,
    },

    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
  ]
})

const {
  tabIndex,
} = useActiveTabManager(
  tabs,
  'lastDealTab'
)

const activeTabName = computed(() => {
  return (
    tabs.value?.[
      tabIndex.value
    ]?.name ||
    'Activity'
  )
})

/* =====================================================
 * API ERROR
 * ===================================================== */

function getApiError(e) {
  if (
    Array.isArray(
      e?._server_messages
    )
  ) {
    return e._server_messages.join(', ')
  }

  if (
    Array.isArray(
      e?.messages
    )
  ) {
    return e.messages.join(', ')
  }

  return (
    e?.message ||
    'Unknown server error'
  )
}

/* =====================================================
 * LOAD DEAL
 * ===================================================== */

async function loadDeal() {
  if (!dealId.value) {
    return null
  }

  loading.value = true
  error.value = ''

  try {
    const result = await call(
      'frappe.client.get',
      {
        doctype:
          'DoubleT Deal',

        name:
          dealId.value,
      }
    )

    deal.value = result

    selectedStage.value =
      result?.stage ||
      ''

    previousStage.value =
      result?.stage ||
      ''

    return result
  } catch (e) {
    console.error(
      'Load Deal failed:',
      e
    )

    error.value =
      getApiError(e)

    deal.value = null

    return null
  } finally {
    loading.value = false
  }
}

/* =====================================================
 * LOAD STAGES
 * ===================================================== */

async function loadStages() {
  stagesLoading.value = true

  try {
    const result = await call(
      'frappe.client.get_list',
      {
        doctype:
          'DoubleT Deal Stage',

        fields: [
          'name',
          'stage_name',
          'stage_type',
          'sort_order',
          'enabled',
        ],

        filters: {
          enabled: 1,
        },

        order_by:
          'sort_order asc',

        limit_page_length:
          200,
      }
    )

    stageOptions.value =
      Array.isArray(result)
        ? result
        : []
  } catch (e) {
    console.error(
      'Load Deal Stages failed:',
      e
    )

    toast.error(
      getApiError(e)
    )
  } finally {
    stagesLoading.value = false
  }
}

function getStage(
  stageName
) {
  return stageOptions.value.find(
    item =>
      item.name ===
      stageName
  )
}

/* =====================================================
 * HEADER STAGE CHANGE
 * ===================================================== */

async function changeStage() {
  if (
    !deal.value?.name ||
    stageSaving.value
  ) {
    return
  }

  const nextStageName =
    selectedStage.value

  if (
    !nextStageName ||
    nextStageName ===
      deal.value.stage
  ) {
    return
  }

  const nextStage =
    getStage(
      nextStageName
    )

  if (!nextStage) {
    selectedStage.value =
      deal.value.stage

    return
  }

  /*
   * LOST:
   * ask for reason before calling backend.
   */
  if (
    nextStage.stage_type ===
    'LOST'
  ) {
    pendingLostStage.value =
      nextStageName

    lostReason.value =
      deal.value.lost_reason ||
      ''

    lostError.value = ''

    showLostModal.value = true

    return
  }

  /*
   * WON:
   * require confirmation.
   */
  if (
    nextStage.stage_type ===
    'WON'
  ) {
    const confirmed =
      window.confirm(
        __(
          'Mark this Deal as Won?'
        )
      )

    if (!confirmed) {
      selectedStage.value =
        deal.value.stage

      return
    }
  }

  await saveStage(
    nextStageName,
    null
  )
}

/* =====================================================
 * SAVE STAGE
 * ===================================================== */

async function saveStage(
  stageName,
  reason = null
) {
  if (
    !deal.value?.name ||
    !stageName
  ) {
    return
  }

  stageSaving.value = true
  error.value = ''

  const oldStage =
    deal.value.stage

  try {
    const values = {
      stage:
        stageName,
    }

    const stage =
      getStage(stageName)

    if (
      stage?.stage_type ===
      'LOST'
    ) {
      values.lost_reason =
        reason
    }

    await call(
      'frappe.client.set_value',
      {
        doctype:
          'DoubleT Deal',

        name:
          deal.value.name,

        fieldname:
          values,
      }
    )

    await reloadDeal()

    toast.success(
      __('Deal stage updated')
    )
  } catch (e) {
    console.error(
      'Change Deal Stage failed:',
      e
    )

    selectedStage.value =
      oldStage

    error.value =
      getApiError(e)

    toast.error(
      error.value
    )
  } finally {
    stageSaving.value = false
  }
}

/* =====================================================
 * LOST STAGE
 * ===================================================== */

function cancelLostStage() {
  if (
    stageSaving.value
  ) {
    return
  }

  showLostModal.value = false
  lostReason.value = ''
  lostError.value = ''
  pendingLostStage.value = ''

  selectedStage.value =
    deal.value?.stage ||
    previousStage.value ||
    ''
}

async function confirmLostStage() {
  const reason =
    lostReason.value.trim()

  if (!reason) {
    lostError.value =
      __(
        'Lost Reason is required.'
      )

    return
  }

  if (
    !pendingLostStage.value
  ) {
    return
  }

  lostError.value = ''

  const targetStage =
    pendingLostStage.value

  await saveStage(
    targetStage,
    reason
  )

  if (
    deal.value?.stage ===
    targetStage
  ) {
    showLostModal.value = false
    lostReason.value = ''
    pendingLostStage.value = ''
  }
}

/* =====================================================
 * CHILD COMPONENT SAVED
 * ===================================================== */

async function onDealSaved(
  data
) {
  /*
   * Optimistic update first so sidebar/data react instantly.
   */
  if (
    data &&
    deal.value
  ) {
    Object.assign(
      deal.value,
      data
    )
  }

  /*
   * Then reload authoritative DB values.
   * Important for won_on / lost_on / lost_reason.
   */
  await reloadDeal()

  reloadActivities.value =
    true
}

/* =====================================================
 * FULL RELOAD
 * ===================================================== */

async function reloadDeal() {
  const result =
    await loadDeal()

  if (result) {
    reloadActivities.value =
      true
  }

  return result
}

/* =====================================================
 * COPY ID
 * ===================================================== */

async function copyDealId() {
  if (!dealId.value) {
    return
  }

  try {
    await navigator.clipboard.writeText(
      dealId.value
    )

    toast.success(
      __('Deal ID copied')
    )
  } catch {
    /*
     * Clipboard API may be unavailable in some
     * browser/http contexts.
     */
  }
}

/* =====================================================
 * ROUTE WATCH
 * ===================================================== */

watch(
  dealId,

  async newId => {
    if (!newId) {
      return
    }

    deal.value = null
    error.value = ''

    await Promise.all([
      loadStages(),
      loadDeal(),
    ])
  },

  {
    immediate: true,
  }
)
</script>