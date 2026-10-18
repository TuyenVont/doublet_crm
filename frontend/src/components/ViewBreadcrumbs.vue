<template>
  <div class="flex items-center">
    <router-link
      :to="{ name: routeName }"
      class="px-0.5 py-1 text-lg-medium text-ink-gray-5 hover:text-ink-gray-7 focus:outline-none"
    >
      {{ __(routeName) }}
    </router-link>
    <span class="mx-1 text-base text-ink-gray-4" aria-hidden="true">
      /
    </span>
    <span class="text-lg-medium text-ink-gray-9">
      {{ 'All ' + routeName }}
    </span>
  </div>
</template>

<script setup>
defineProps({
  routeName: { type: String, required: true },
})
</script>
