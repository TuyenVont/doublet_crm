<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">{{ __('Notes') }}</div>
      </template>
    </LayoutHeader>
    <SharedNotes management />
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import SharedNotes from '@/components/Notes/SharedNotes.vue'
</script>
