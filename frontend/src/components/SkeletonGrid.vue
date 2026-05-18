<script setup lang="ts">
withDefaults(defineProps<{ count?: number }>(), {count: 16})
</script>

<template>
  <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8">
    <div v-for="n in count" :key="n">
      <div class="skeleton aspect-[2/3] rounded-xl"></div>
      <div class="skeleton mt-2 h-3.5 w-3/4 rounded"></div>
    </div>
  </div>
</template>
