<script setup lang="ts">
withDefaults(defineProps<{ title?: string; hint?: string }>(), {
  title: "已与榜单同步",
  hint: "这里没有需要维护的项目",
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 rounded-2xl border border-border bg-surface/40 py-20 text-center">
    <div class="grid h-14 w-14 place-items-center rounded-full bg-success/15 text-2xl text-success">✓</div>
    <p class="text-base font-medium text-content">{{ title }}</p>
    <p class="text-sm text-muted">{{ hint }}</p>
  </div>
</template>
