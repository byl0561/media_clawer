<script setup lang="ts">
import {useMediaCatalog} from "@/stores/mediaCatalog";

const {entries, refresh} = useMediaCatalog()
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-border bg-bg/80 backdrop-blur">
    <div class="mx-auto flex h-16 max-w-screen-2xl items-center gap-3 px-4 sm:px-6">
      <RouterLink to="/" class="flex shrink-0 items-center gap-2 font-bold">
        <span class="grid h-8 w-8 place-items-center rounded-lg bg-accent text-white">◆</span>
        <span class="hidden text-content sm:inline">MediaGap</span>
      </RouterLink>

      <nav class="flex flex-1 items-center gap-1 overflow-x-auto">
        <RouterLink
          v-for="e in entries"
          :key="e.key"
          :to="`/library/${e.key}`"
          class="whitespace-nowrap rounded-lg px-3 py-1.5 text-sm text-muted transition hover:bg-surface hover:text-content"
          active-class="!bg-surface !text-content"
        >
          {{ e.label }}
        </RouterLink>
      </nav>

      <button
        type="button"
        @click="refresh"
        class="flex shrink-0 items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm text-muted transition hover:border-accent/50 hover:text-content"
        title="重新拉取数据"
      >
        <span class="text-base leading-none">⟳</span>
        <span class="hidden sm:inline">刷新</span>
      </button>
    </div>
  </header>
</template>
