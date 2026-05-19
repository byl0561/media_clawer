<script setup lang="ts">
defineProps<{ score: number | null }>()
</script>

<template>
  <span
    v-if="score != null"
    class="inline-flex items-center gap-1 rounded-md bg-black/55 px-1.5 py-0.5 text-xs font-semibold backdrop-blur-sm"
  >
    <svg class="h-3 w-3 text-amber-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path d="M10 1.6l2.55 5.17 5.7.83-4.13 4.02.98 5.68L10 14.98l-5.1 2.32.98-5.68L1.75 7.6l5.7-.83L10 1.6z" />
    </svg>
    {{ score }}
  </span>
</template>
