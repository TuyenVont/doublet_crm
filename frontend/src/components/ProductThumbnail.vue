<template>
  <div class="grid shrink-0 place-items-center overflow-hidden rounded-md bg-surface-gray-2 text-ink-gray-4">
    <img
      v-if="src && !failed"
      :src="src"
      :alt="alt"
      class="h-full w-full object-cover"
      loading="lazy"
      @error="failed = true"
    />
    <span v-else class="lucide-package h-6 w-6" aria-hidden="true" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, default: '' },
  alt: { type: String, default: '' },
})

const failed = ref(false)
watch(() => props.src, () => { failed.value = false })
</script>
