<template>
  <div
    class="relative flex h-full flex-col justify-between transition-all duration-300 ease-in-out bg-surface-gray-1"
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
    </div>

    <div class="m-2 flex flex-col gap-1">
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
import { ref } from 'vue'
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
import { Badge } from 'frappe-ui'

const isSidebarCollapsed = ref(localStorage.getItem('isSidebarCollapsed') === 'true')
const unreadNotificationsCount = ref(0)

function toggleCollapse() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  localStorage.setItem('isSidebarCollapsed', String(isSidebarCollapsed.value))
}

const links = [
  { label: 'Dashboard', icon: DashboardIcon, to: 'Dashboard' },
  { label: 'Leads', icon: LeadsIcon, to: 'Leads' },
  { label: 'Deals', icon: DealsIcon, to: 'Deals' },
  { label: 'Contacts', icon: ContactsIcon, to: 'Contacts' },
  { label: 'Companies', icon: OrganizationsIcon, to: 'Companies' },
  { label: 'Notes', icon: NoteIcon, to: 'Notes' },
  { label: 'Tasks', icon: TaskIcon, to: 'Tasks' },
  { label: 'Call Logs', icon: PhoneIcon, to: 'Call Logs' },
]
</script>
