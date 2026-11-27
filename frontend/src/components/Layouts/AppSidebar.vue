<template>
  <div
    class="relative flex h-full shrink-0 flex-col justify-between transition-all duration-300 ease-in-out bg-surface-gray-1"
    :class="isSidebarCollapsed ? 'w-12' : 'w-[220px]'"
  >
    <div class="p-2">
      <UserDropdown :isCollapsed="isSidebarCollapsed" />
    </div>

    <div class="flex-1 overflow-y-auto">
      <div class="flex flex-col">
        <SidebarLink
          id="notifications-btn"
          :label="__('Notifications')"
          :icon="NotificationsIcon"
          :isCollapsed="isSidebarCollapsed"
          class="relative mx-2 my-[1.5px]"
        >
          <template #right>
            <Badge
              v-if="!isSidebarCollapsed && unreadNotificationsCount"
              :label="unreadNotificationsCount"
              variant="subtle"
            />
            <div
              v-else-if="unreadNotificationsCount"
              class="absolute -left-1.5 top-1 z-20 h-[5px] w-[5px] translate-x-6 translate-y-1 rounded-full bg-surface-gray-9 ring-1 ring-white"
            />
          </template>
        </SidebarLink>
      </div>

      <div class="mx-2 my-1.5" />
      <Section
        :label="__('All Views')"
        :hideLabel="false"
        :opened="true"
      >
        <template #header="{ opened, hide, toggle }">
          <div
            v-if="!hide"
            class="flex items-center cursor-pointer gap-1.5 text-base text-ink-gray-5 transition-all duration-300 ease-in-out"
            :class="
              isSidebarCollapsed
                ? 'h-0 overflow-hidden opacity-0'
                : 'px-4 pt-[11px] pb-2.5 w-auto opacity-100'
            "
            @click="toggle()"
          >
            <span
              class="lucide-chevron-right h-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
              :class="{ 'rotate-90': opened }"
              aria-hidden="true"
            />
            <span>{{ __('All Views') }}</span>
          </div>
        </template>
        <nav class="flex flex-col">
          <SidebarLink
            v-for="link in links"
            :key="link.label"
            :icon="link.icon"
            :label="__(link.label)"
            :to="link.to"
            :isCollapsed="isSidebarCollapsed"
            class="mx-2 my-[1.5px]"
          />
        </nav>
      </Section>
      <Section
        :key="forceCompactRail"
        :label="__('Contact Center')"
        :header-class="isSidebarCollapsed ? 'hidden' : 'px-4 pt-[11px] pb-2.5'"
        label-class="!text-ink-gray-5"
      >
        <nav class="flex flex-col" :aria-label="__('Contact Center')">
          <SidebarLink
            v-for="link in contactCenterLinks"
            :key="link.to"
            :icon="link.icon"
            :label="__(link.label)"
            :to="link.to"
            :isCollapsed="isSidebarCollapsed"
            class="mx-2 my-[1.5px]"
          />
        </nav>
      </Section>
    </div>

    <div v-if="!forceCompactRail" class="m-2 flex flex-col gap-1">
      <SidebarLink
        :label="isSidebarCollapsed ? __('Expand') : __('Collapse')"
        :icon="CollapseSidebar"
        :isCollapsed="isSidebarCollapsed"
        class="mx-2 my-[1.5px]"
        @click="toggleCollapse"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useMediaQuery } from '@vueuse/core'
import { useRoute } from 'vue-router'
import { Badge, call } from 'frappe-ui'
import UserDropdown from '@/components/UserDropdown.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import Section from '@/components/CollapsibleSection.vue'
import DashboardIcon from '@/components/Icons/DashboardIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CollapseSidebar from '@/components/Icons/CollapseSidebar.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import { REPORTS_HOME_ROUTE } from '@/utils/reports'

const route = useRoute()
const narrow = useMediaQuery('(max-width: 1023px)')
const compactRoutes = new Set(['Inbox', 'Calls', 'Call Logs', 'LeadDetail'])
const forceCompactRail = computed(() => narrow.value && route.matched.some((record) => compactRoutes.has(record.name)))
const collapsedPreference = ref(localStorage.getItem('isSidebarCollapsed') === 'true')
const isSidebarCollapsed = computed(() => collapsedPreference.value || forceCompactRail.value)
const unreadNotificationsCount = ref(0)

function toggleCollapse() {
  collapsedPreference.value = !collapsedPreference.value
  localStorage.setItem('isSidebarCollapsed', String(collapsedPreference.value))
}

const canReadOrders = ref(true)
const canReadAppointments = ref(true)
onMounted(() => {
  call('frappe.client.has_permission', { doctype: 'DoubleT Order', docname: '', perm_type: 'read' })
    .then((res) => { canReadOrders.value = Boolean(res?.has_permission) })
    .catch(() => { canReadOrders.value = false })
  call('frappe.client.has_permission', { doctype: 'DoubleT Appointment', docname: '', perm_type: 'read' })
    .then((res) => { canReadAppointments.value = Boolean(res?.has_permission) })
    .catch(() => { canReadAppointments.value = false })
})

const links = computed(() => [
  { label: 'Dashboard', icon: DashboardIcon, to: 'Dashboard' },
  { label: 'Reports', icon: 'bar-chart-2', to: REPORTS_HOME_ROUTE },
  { label: 'Leads', icon: LeadsIcon, to: 'Leads' },
  { label: 'Deals', icon: DealsIcon, to: 'Deals' },
  { label: 'Contacts', icon: ContactsIcon, to: 'Contacts' },
  { label: 'Companies', icon: OrganizationsIcon, to: 'Companies' },
  { label: 'Products', icon: 'package', to: 'Products' },
  { label: 'Price Lists', icon: 'tags', to: 'PriceLists' },
  { label: 'Quotations', icon: 'file-text', to: 'Quotations' },
  { label: 'Quotation Templates', icon: 'layers', to: 'QuotationTemplates' },
  ...(canReadOrders.value ? [{ label: 'Orders', icon: 'shopping-cart', to: 'Orders' }] : []),
  ...(canReadAppointments.value ? [{ label: 'Appointments', icon: 'calendar', to: 'Appointments' }] : []),
  { label: 'Notes', icon: NoteIcon, to: 'Notes' },
  { label: 'Tasks', icon: TaskIcon, to: 'Tasks' },
])

const contactCenterLinks = [
  { label: 'Inbox', icon: 'inbox', to: 'Inbox' },
  { label: 'Calls', icon: PhoneIcon, to: 'Calls' },
  { label: 'Call Logs', icon: 'list', to: 'Call Logs' },
]
</script>
