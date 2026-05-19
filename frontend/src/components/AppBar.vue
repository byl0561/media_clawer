<script setup lang="ts">
import {useMediaCatalog} from "@/stores/mediaCatalog";

const {entries, refresh, refreshing} = useMediaCatalog()
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-border bg-bg/80 backdrop-blur">
    <div class="mx-auto flex h-16 max-w-screen-2xl items-center gap-3 px-4 sm:px-6">
      <RouterLink
        to="/"
        aria-label="MediaGap 首页"
        class="flex shrink-0 items-center gap-2 rounded-lg font-bold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        <span class="grid h-8 w-8 place-items-center rounded-lg bg-accent text-white" aria-hidden="true">◆</span>
        <span class="hidden text-content sm:inline">MediaGap</span>
      </RouterLink>

      <nav class="edge-fade-x flex flex-1 items-center gap-1 overflow-x-auto">
        <RouterLink
          to="/"
          class="whitespace-nowrap rounded-lg px-3 py-1.5 text-sm text-muted transition hover:bg-surface hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          active-class="!bg-surface !text-content"
        >
          概览
        </RouterLink>
        <RouterLink
          v-for="e in entries"
          :key="e.key"
          :to="`/library/${e.key}`"
          class="whitespace-nowrap rounded-lg px-3 py-1.5 text-sm text-muted transition hover:bg-surface hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          active-class="!bg-surface !text-content"
        >
          {{ e.label }}
        </RouterLink>
      </nav>

      <button
        type="button"
        @click="refresh"
        :disabled="refreshing"
        :aria-busy="refreshing"
        aria-label="重新拉取数据"
        title="重新拉取数据"
        class="flex shrink-0 items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm text-muted transition hover:border-accent/50 hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:border-border disabled:hover:text-muted"
      >
        <span
          class="text-base leading-none"
          :class="{ 'inline-block animate-spin': refreshing }"
          aria-hidden="true"
        >⟳</span>
        <span class="hidden sm:inline">{{ refreshing ? "刷新中" : "刷新" }}</span>
      </button>
    </div>
  </header>
</template>
