<script setup lang="ts">
import AppBar from "@/components/AppBar.vue";
import AppFooter from "@/components/AppFooter.vue";
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <AppBar />
    <main class="flex-1">
      <RouterView />
    </main>
    <AppFooter />
  </div>
</template>
