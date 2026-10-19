<template>
  <Dropdown :options="dropdownItems" v-bind="$attrs">
    <template #default="{ open }">
      <button
        class="flex h-12 items-center rounded-md py-2 duration-300 ease-in-out"
        :class="
          isCollapsed
            ? 'w-auto px-0'
            : open
              ? 'w-full px-2 bg-surface-base shadow-sm'
              : 'w-full px-2 hover:bg-surface-gray-3'
        "
      >
        <BrandLogo class="size-8 shrink-0 rounded" />
        <div
          class="flex flex-1 flex-col text-left duration-300 ease-in-out truncate"
          :class="
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          <div class="text-base-medium leading-none text-ink-gray-9 truncate font-semibold">
            {{ brandName }}
          </div>
          <div class="mt-1 text-xs leading-none text-ink-gray-6 truncate">
            {{ userFullName }}
          </div>
        </div>
        <div
          class="duration-300 ease-in-out"
          :class="
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          <span
            class="lucide-chevron-down size-4 text-ink-gray-5"
            aria-hidden="true"
          />
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import BrandLogo from '@/components/BrandLogo.vue'
import { Dropdown } from 'frappe-ui'
import { computed } from 'vue'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

const brandName = computed(() => 'DoubleT CRM')
const userFullName = computed(() => window.boot?.user || 'Administrator')

const dropdownItems = computed(() => [
  {
    group: 'Actions',
    hideLabel: true,
    items: [
      {
        label: 'Frappe Desk',
        icon: 'external-link',
        onClick: () => window.open('/app', '_blank'),
      },
      {
        label: 'Switch Theme',
        icon: 'sun',
        onClick: () => {
          const current = localStorage.getItem('theme') || 'light'
          const next = current === 'dark' ? 'light' : 'dark'
          localStorage.setItem('theme', next)
          document.documentElement.setAttribute('data-theme', next)
        },
      },
      {
        label: 'Log out',
        icon: 'log-out',
        onClick: () => {
          window.location.href = '/api/method/logout'
        },
      },
    ],
  },
])
</script>
