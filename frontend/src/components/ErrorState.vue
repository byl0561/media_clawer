<script setup lang="ts">
withDefaults(defineProps<{ message?: string }>(), {message: "数据加载失败，请稍后重试"})
defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-4 rounded-2xl border border-border bg-surface/40 py-20 text-center">
    <div class="grid h-14 w-14 place-items-center rounded-full bg-danger/15 text-2xl text-danger">!</div>
    <p class="text-base font-medium text-content">{{ message }}</p>
    <button
      type="button"
      @click="$emit('retry')"
      class="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
    >
      重试
    </button>
  </div>
</template>
