<template>
  <Teleport v-if="showHeader" to="#app-header">
    <slot>
      <header
        class="flex h-10.5 items-center justify-between py-[7px] sm:pl-5 pl-2"
        :class="{ 'max-md:h-auto max-md:flex-col max-md:items-stretch max-md:gap-1': stackOnMobile }"
      >
        <div class="flex items-center gap-2">
          <slot name="left-header" />
        </div>
        <div class="flex items-center gap-2" :class="{ 'max-md:flex-wrap': stackOnMobile }">
          <slot name="right-header" class="flex items-center gap-2" />
        </div>
      </header>
    </slot>
  </Teleport>
</template>
<script setup>
import { ref, nextTick } from 'vue'

defineProps({ stackOnMobile: Boolean })

const showHeader = ref(false)

nextTick(() => {
  showHeader.value = true
})
</script>
