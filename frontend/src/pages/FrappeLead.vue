<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon
            v-if="item.icon"
            :icon="item.icon"
            class="mr-2 h-4"
          />
        </template>
      </Breadcrumbs>
    </template>

    <template
      v-if="!errorTitle"
      #right-header
    >
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />

      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />

      <AssignTo
        v-model="assignees.data"
        doctype="DoubleT Lead"
        :docname="leadId"
      />

      <Dropdown
        v-if="doc && document.statuses"
        :options="statuses"
        placement="right"
      >
        <template #default="{ open }">
          <Button
            v-if="doc.status"
            :label="statusLabel(doc.status)"
            :iconRight="
              open
                ? 'chevron-up'
                : 'chevron-down'
            "
          >
            <template #prefix>
              <IndicatorIcon
                :class="
                  getLeadStatus(doc.status).color
                "
              />
            </template>
          </Button>
        </template>
      </Dropdown>

<div class="flex items-center gap-2">

  <!-- CHƯA CONVERT -->
  <Button
    v-if="!isConverted"
    :label="__('Convert to Deal')"
    variant="solid"
    @click="openConvertToDeal"
  />

  <!-- ĐÃ CONVERT -->
  <template v-else>
    <Button
      label="Converted"
      variant="subtle"
      disabled
    />

    <Button
      v-if="doc.converted_deal"
      :label="__('Open Deal')"
      variant="solid"
      iconRight="arrow-up-right"
      @click="openConvertedDeal"
    />
  </template>

</div>
    </template>
  </LayoutHeader>

  <!-- MAIN CONTENT -->
  <div
    v-if="doc.name"
    class="flex h-full overflow-hidden"
  >
    <!-- ACTIVITY AREA -->
    <Tabs
      v-model="tabIndex"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col
             [&_[role='tab']]:px-0
             [&_[role='tab']]:shrink-0
             [&_[role='tablist']]:px-5
             [&_[role='tablist']::-webkit-scrollbar]:h-0
             [&_[role='tablist']]:min-h-[45px]
             [&_[role='tablist']]:gap-7.5
             [&_[role='tabpanel']:not([hidden])]:flex
             [&_[role='tabpanel']:not([hidden])]:grow"
    >
   <template #tab-panel>

  <!-- CUSTOM DATA TAB -->
  <DoubleTLeadDataPanel
    v-if="activeTabName === 'Data'"
    :lead="doc"
    @saved="onLeadDataSaved"
  />

  <!-- NORMAL ACTIVITY TABS -->
  <Activities
    v-else
    ref="activities"
    v-model:reload="reload"
    v-model:tabIndex="tabIndex"
    doctype="DoubleT Lead"
    :docname="leadId"
    :tabs="tabs"
    @beforeSave="beforeStatusChange"
    @afterSave="reloadResources"
  />

</template>
    </Tabs>

    <!-- RIGHT SIDEBAR -->
    <Resizer
      class="flex flex-col justify-between border-l"
      side="right"
    >
      <!-- LEAD ID -->
      <div
        class="flex h-[45px] cursor-copy items-center border-b
               px-5 py-2.5 text-lg-medium text-ink-gray-9"
        @click="copyToClipboard(leadId)"
      >
        {{ __(leadId) }}
      </div>

      <!-- PROFILE HEADER -->
      <FileUploader
        :validateFile="validateIsImageFile"
        @success="
          (file) =>
            updateField(
              'image',
              file.file_url
            )
        "
      >
        <template #default="{ openFileSelector }">
          <div
            class="flex items-center justify-start
                   gap-5 border-b p-5"
          >
            <!-- AVATAR -->
            <div class="group relative size-12">
              <Avatar
                size="3xl"
                class="size-12"
                :label="title"
                :image="doc.image"
              />

              <component
                :is="
                  doc.image
                    ? Dropdown
                    : 'div'
                "
                v-bind="
                  doc.image
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label:
                              doc.image
                                ? __('Change Image')
                                : __('Upload Image'),
                            onClick:
                              openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label:
                              __('Remove Image'),
                            onClick:
                              () =>
                                updateField(
                                  'image',
                                  ''
                                ),
                          },
                        ],
                      }
                    : {
                        onClick:
                          openFileSelector,
                      }
                "
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0.5 left-0 right-0.5
                         flex h-9 cursor-pointer items-center
                         justify-center rounded-b-full
                         bg-black bg-opacity-40 pt-3
                         opacity-0 duration-300 ease-in-out
                         group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon
                    class="size-4 cursor-pointer text-white"
                  />
                </div>
              </component>
            </div>

            <!-- NAME + QUICK ACTIONS -->
            <div
              class="flex flex-col gap-2.5 truncate"
            >
              <Tooltip :text="title">
                <div
                  class="truncate text-3xl-medium
                         text-ink-gray-9"
                >
                  {{ title }}
                </div>
              </Tooltip>

              <div class="flex gap-1.5">
                <!-- CALL -->
                <Button
                  v-if="callEnabled"
                  :tooltip="__('Make a Call')"
                  :icon="PhoneIcon"
                  @click="
                    () =>
                      doc.phone ||
                      doc.mobile_no
                        ? makeCall(
                            doc.phone ||
                              doc.mobile_no
                          )
                        : toast.error(
                            __(
                              'Please set a phone number to make calls'
                            )
                          )
                  "
                />

                <!-- EMAIL -->
                <Button
                  :tooltip="
                    __('Send an Email')
                  "
                  :icon="Email2Icon"
                  @click="
                    doc.email
                      ? openEmailBox()
                      : toast.error(
                          __(
                            'Please set an email address to send emails'
                          )
                        )
                  "
                />

                <!-- WEBSITE -->
                <Button
                  v-if="doc.website"
                  :tooltip="
                    __('Go to Website')
                  "
                  :icon="LinkIcon"
                  @click="
                    openWebsite(
                      doc.website
                    )
                  "
                />

                <!-- ATTACHMENT -->
                <Button
                  :tooltip="
                    __('Attach a File')
                  "
                  :icon="AttachmentIcon"
                  @click="
                    showFilesUploader = true
                  "
                />

                <!-- DELETE -->
                <Button
                  v-if="canDelete"
                  :tooltip="__('Delete')"
                  variant="subtle"
                  theme="red"
                  icon="lucide-trash-2"
                  @click="deleteLead"
                />
              </div>

              <ErrorMessage
                :message="__(error)"
              />
            </div>
          </div>
        </template>
      </FileUploader>

      <!-- SLA -->
      <SLASection
        v-if="doc.sla_status"
        v-model="doc"
        @updateField="updateField"
      />

      <!-- NEW DOUBLET LEAD INFORMATION -->
      <div
        class="flex flex-1 flex-col
               overflow-hidden"
      >
        <DoubleTLeadInfoPanel
          :lead="doc"
          @saved="onLeadSidebarSaved"
        />
      </div>
    </Resizer>
  </div>

  <!-- ERROR -->
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />

  <!-- CONVERT MODAL -->
  <DoubleTConvertToDealModal
    v-if="doc?.name"
    v-model="showConvertToDealModal"
    :lead="doc"
    @converted="handleConverted"
  />

  <!-- FILE UPLOADER -->
  <FilesUploader
    v-model="showFilesUploader"
    doctype="DoubleT Lead"
    :docname="leadId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />

  <!-- DELETE MODAL -->
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'DoubleT Lead'"
    :docname="leadId"
    name="Leads"
  />

  <!-- LOST REASON -->
  <LostReasonModal
    v-if="showLostReasonModal"
    v-model="showLostReasonModal"
    doctype="DoubleT Lead"
    :document="document"
  />
</template>

<script setup>
import {
  ref,
  computed,
  watch,
  nextTick,
  onMounted,
} from 'vue'

import {
  useRouter,
  useRoute,
} from 'vue-router'

import {
  FileUploader,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'

import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'

import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'

import LostReasonModal from '@/components/Modals/LostReasonModal.vue'
import DoubleTConvertToDealModal from '@/components/Modals/DoubleTConvertToDealModal.vue'

import DoubleTLeadInfoPanel from '@/components/Lead/DoubleTLeadInfoPanel.vue'
import DoubleTLeadDataPanel from '@/components/Lead/DoubleTLeadDataPanel.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'

import {
  openWebsite,
  setupCustomizations,
  copyToClipboard,
  validateIsImageFile,
  isTranslatable,
} from '@/utils'

import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { whatsappEnabled } from '@/composables/whatsapp'
import { callEnabled } from '@/composables/telephony'
import { useActiveTabManager } from '@/composables/useActiveTabManager'


const { brand } = getSettings()

const {
  $dialog,
  $socket,
  makeCall,
} = globalStore()

const {
  statusOptions,
  getLeadStatus,
} = statusesStore()

const {
  doctypeMeta,
} = getMeta('DoubleT Lead')

const route = useRoute()
const router = useRouter()


const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})
function openConvertedDeal() {
  if (!doc.value?.converted_deal) {
    return
  }

  router.push({
    name: 'DealDetail',
    params: {
      dealId:
        doc.value.converted_deal,
    },
  })
}

const reload = ref(false)
const activities = ref(null)

const errorTitle = ref('')
const errorMessage = ref('')

const showDeleteLinkedDocModal =
  ref(false)

const showConvertToDealModal =
  ref(false)

const showFilesUploader =
  ref(false)


const {
  triggerOnChange,
  triggerOnRender,
  assignees,
  permissions,
  document,
  scripts,
  error,
} = useDocument(
  'DoubleT Lead',
  props.leadId
)


const canDelete = computed(() => {
  return (
    permissions.data
      ?.permissions
      ?.delete ||
    false
  )
})


const doc = computed(() => {
  return document.doc || {}
})


const isConverted = computed(() => {
  return (
    doc.value?.status ===
      'CONVERTED' ||
    Boolean(
      doc.value?.converted_contact
    )
  )
})
async function onLeadSidebarSaved(data) {
  if (
    data &&
    document.doc
  ) {
    Object.assign(
      document.doc,
      data
    )
  }

  if (
    typeof document.reload ===
    'function'
  ) {
    await document.reload()
  }

  reload.value = true
}

/* --------------------------------
 * INITIAL RENDER
 * -------------------------------- */

onMounted(async () => {
  if (document.doc) {
    await triggerOnRender()
  }
})


/* --------------------------------
 * DOCUMENT ERROR
 * -------------------------------- */

watch(
  error,
  (err) => {
    if (err) {
      errorTitle.value = __(
        err.exc_type ===
          'DoesNotExistError'
          ? 'Document not found'
          : 'Error occurred'
      )

      errorMessage.value = __(
        err.messages?.[0] ||
          'An error occurred'
      )
    } else {
      errorTitle.value = ''
      errorMessage.value = ''
    }
  }
)


/* --------------------------------
 * CUSTOM SCRIPTS
 * -------------------------------- */

watch(
  () => document.doc,

  async (_doc) => {
    if (scripts.data?.length) {
      const s =
        await setupCustomizations(
          scripts.data,
          {
            doc: _doc,

            $dialog,
            $socket,

            router,
            toast,

            updateField,

            createToast:
              toast.create,

            deleteDoc:
              deleteLead,

            call,
          }
        )

      document._actions =
        s.actions || []

      document._statuses =
        s.statuses || []
    }
  },

  {
    once: true,
  }
)


/* --------------------------------
 * BREADCRUMBS
 * -------------------------------- */

const breadcrumbs = computed(() => {
  const items = [
    {
      label: __('Leads'),
      route: {
        name: 'Leads',
      },
    },
  ]

  if (
    route.query.view ||
    route.query.viewType
  ) {
    const view = getView(
      route.query.view,
      route.query.viewType,
      'DoubleT Lead'
    )

    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,

        route: {
          name: 'Leads',

          params: {
            viewType:
              route.query.viewType,
          },

          query: {
            view:
              route.query.view,
          },
        },
      })
    }
  }

  items.push({
    label: title.value,

    route: {
      name: 'Lead',

      params: {
        leadId:
          props.leadId,
      },
    },
  })

  return items
})


/* --------------------------------
 * TITLE
 * -------------------------------- */

const title = computed(() => {
  const firstName =
    doc.value?.first_name || ''

  const lastName =
    doc.value?.last_name || ''

  const fullName =
    [
      firstName,
      lastName,
    ]
      .filter(Boolean)
      .join(' ')
      .trim()

  if (fullName) {
    return fullName
  }

  const titleField =
    doctypeMeta.value
      ?.title_field

  if (
    titleField &&
    doc.value?.[titleField]
  ) {
    return doc.value[
      titleField
    ]
  }

  return props.leadId
})


/* --------------------------------
 * STATUS
 * -------------------------------- */

const statuses = computed(() => {
  const customStatuses =
    document.statuses?.length
      ? document.statuses
      : document._statuses ||
        []

  return statusOptions(
    'lead',
    customStatuses,
    triggerStatusChange
  )
})


/* --------------------------------
 * PAGE META
 * -------------------------------- */

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})


/* --------------------------------
 * ACTIVITY TABS
 * -------------------------------- */

const tabs = computed(() => {
  const tabOptions = [
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
      label:
        __('Attachments'),
      icon:
        AttachmentIcon,
    },

    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,

      condition: () =>
        whatsappEnabled.value,
    },
  ]

  return tabOptions.filter(
    (tab) =>
      tab.condition
        ? tab.condition()
        : true
  )
})


const {
  tabIndex,
  changeTabTo,
} = useActiveTabManager(
  tabs,
  'lastLeadTab'
)
const activeTabName = computed(() => {
  return (
    tabs.value?.[
      tabIndex.value
    ]?.name || ''
  )
})
async function onLeadDataSaved(data) {
  if (
    data &&
    document.doc
  ) {
    Object.assign(
      document.doc,
      data
    )
  }

  if (
    typeof document.reload ===
    'function'
  ) {
    await document.reload()
  }

  reload.value = true
}
/* --------------------------------
 * STATUS CHANGE
 * -------------------------------- */

async function triggerStatusChange(
  value
) {
  await triggerOnChange(
    'status',
    value
  )

  setLostReason()
}


/* --------------------------------
 * UPDATE FIELD
 * -------------------------------- */

function updateField(
  name,
  value
) {
  value =
    Array.isArray(name)
      ? ''
      : value

  const oldValues =
    Array.isArray(name)
      ? {}
      : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach(
      (field) => {
        oldValues[field] =
          doc.value[field]

        doc.value[field] =
          value
      }
    )
  } else {
    doc.value[name] =
      value
  }

  document.save.submit(
    null,
    {
      onSuccess: () => {
        reload.value = true
      },

      onError: (err) => {
        if (
          Array.isArray(name)
        ) {
          name.forEach(
            (field) => {
              doc.value[field] =
                oldValues[field]
            }
          )
        } else {
          doc.value[name] =
            oldValues
        }

        toast.error(
          err.messages?.[0] ||
            __(
              'Error updating field'
            )
        )
      },
    }
  )
}


/* --------------------------------
 * DELETE LEAD
 * -------------------------------- */

function deleteLead() {
  showDeleteLinkedDocModal.value =
    true
}


/* --------------------------------
 * EMAIL
 * -------------------------------- */

function openEmailBox() {
  const currentTab =
    tabs.value[
      tabIndex.value
    ]

  if (
    ![
      'Emails',
      'Comments',
      'Activities',
    ].includes(
      currentTab.name
    )
  ) {
    activities.value
      ?.changeTabTo(
        'emails'
      )
  }

  nextTick(() => {
    if (
      activities.value
        ?.emailBox
    ) {
      activities.value
        .emailBox
        .show = true
    }
  })
}


/* --------------------------------
 * CONVERT
 * -------------------------------- */

function openConvertToDeal() {
  if (isConverted.value) {
    return
  }

  showConvertToDealModal.value =
    true
}


async function handleConverted(result) {
  showConvertToDealModal.value = false

  try {
    // -----------------------------------------
    // Reload Lead document từ DB
    // -----------------------------------------
    await document.reload()

    // -----------------------------------------
    // Reload activity/timeline
    // -----------------------------------------
    reload.value = true

    // -----------------------------------------
    // Reload assignees nếu cần
    // -----------------------------------------
    if (
      typeof assignees.reload === 'function'
    ) {
      assignees.reload()
    }

    // -----------------------------------------
    // Thông báo thành công
    // -----------------------------------------
    toast.success(
      result?.deal
        ? __('Lead converted and Deal created successfully')
        : __('Lead converted successfully')
    )

  } catch (e) {
    console.error(
      'Reload converted Lead failed:',
      e
    )

    // Fallback:
    // backend đã convert thành công nên cập nhật local
    // để UI vẫn phản ánh ngay.
    if (result) {
      document.doc.status =
        'CONVERTED'

      document.doc.converted_contact =
        result.contact || null

      document.doc.converted_company =
        result.company || null

      document.doc.converted_deal =
        result.deal || null
    }

    reload.value = true
  }
}

/* --------------------------------
 * STATUS LABEL
 * -------------------------------- */

function statusLabel(status) {
  if (
    isTranslatable(
      'CRM Lead Status'
    )
  ) {
    return __(status)
  }

  return status
}


/* --------------------------------
 * LOST REASON
 * -------------------------------- */

const showLostReasonModal =
  ref(false)


function setLostReason() {
  if (
    getLeadStatus(
      document.doc.status
    ).type !== 'Lost' ||

    (
      document.doc
        .lost_reason &&
      document.doc
        .lost_reason !==
        'Other'
    ) ||

    (
      document.doc
        .lost_reason ===
        'Other' &&
      document.doc
        .lost_notes
    )
  ) {
    document.save.submit(
      null,
      {
        onSuccess: () => {
          reload.value = true
        },
      }
    )

    return
  }

  showLostReasonModal.value =
    true
}


/* --------------------------------
 * BEFORE STATUS CHANGE
 * -------------------------------- */

function beforeStatusChange(
  data
) {
  if (
    Object.hasOwn(
      data ?? {},
      'status'
    ) &&

    getLeadStatus(
      data.status
    ).type === 'Lost'
  ) {
    setLostReason()
  } else {
    document.save.submit(
      null,
      {
        onSuccess: () =>
          reloadResources(
            data
          ),
      }
    )
  }
}


/* --------------------------------
 * RELOAD RESOURCES
 * -------------------------------- */

function reloadResources(
  data
) {
  if (
    Object.hasOwn(
      data ?? {},
      'lead_owner'
    )
  ) {
    assignees.reload()
  }

  reload.value = true
}
</script>