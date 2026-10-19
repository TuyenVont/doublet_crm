<template>
  <div class="h-full flex flex-col p-6">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-ink-gray-9">{{ title }}</h1>
        <p class="text-sm text-ink-gray-5 mt-1">{{ description }}</p>
      </div>
      <Button variant="solid" :label="'Create ' + title.slice(0, -1)" />
    </div>

    <div class="flex-1 rounded-xl border border-dashed border-outline-gray-3 bg-surface-gray-1 p-8 flex flex-col items-center justify-center text-center">
      <div class="size-12 rounded-full bg-surface-gray-3 flex items-center justify-center text-ink-gray-7 mb-3 text-lg font-bold">
        {{ title.charAt(0) }}
      </div>
      <h3 class="text-base font-medium text-ink-gray-9">DoubleT CRM Shell Active</h3>
      <p class="text-sm text-ink-gray-5 mt-1 max-w-sm">
        Trang <span class="font-semibold text-ink-gray-8">{{ title }}</span> hoạt động trên UI Shell độc lập của DoubleT CRM.
      </p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: 'View' },
  description: { type: String, default: '' },
})
</script>
