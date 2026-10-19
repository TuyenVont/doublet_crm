<template>
  <div class="flex h-screen w-screen overflow-hidden bg-white">
    <AppSidebar />

    <div class="flex min-w-0 flex-1 flex-col bg-white">
      <AppHeader />

      <main class="min-h-0 flex-1 overflow-auto">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
</script>
