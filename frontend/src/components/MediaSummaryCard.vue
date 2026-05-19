<script setup lang="ts">
import {computed} from "vue";
import type {CatalogEntry} from "@/stores/mediaCatalog";
import type {CardCount} from "@/hooks/useOverviewData";

const props = defineProps<{
  entry: CatalogEntry;
  status: "loading" | "ok" | "error";
  counts: CardCount[];
}>()

// Thin per-library accent stripe down the left edge — enough colour to tell
// the cards apart at a glance without fighting the single-accent theme.
const BAR: Record<string, string> = {
  movie: "bg-violet-500",
  tv: "bg-sky-500",
  anime: "bg-pink-500",
  book: "bg-amber-500",
  album: "bg-emerald-500",
}
const barClass = computed(() => BAR[props.entry.key] ?? "bg-accent")

// Column count is known before data arrives; the skeleton uses it so the
// loading -> loaded transition keeps the same layout.
const tabCount = computed(() => props.entry.group.mediaItemFunctionGroups.length)

const synced = computed(
  () =>
    props.status === "ok" &&
    props.counts.length > 0 &&
    props.counts.every((c) => (c.value ?? 0) === 0),
)
</script>

<template>
  <RouterLink
    :to="`/library/${props.entry.key}`"
    class="group relative flex flex-col gap-5 overflow-hidden rounded-2xl border border-border bg-surface py-6 pl-7 pr-5 transition hover:-translate-y-0.5 hover:border-accent/50 hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg focus-visible:-translate-y-0.5 focus-visible:border-accent/50"
  >
    <span
      aria-hidden="true"
      class="absolute inset-y-0 left-0 w-1"
      :class="barClass"
    ></span>

    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="grid h-11 w-11 place-items-center rounded-xl bg-surface-2 text-2xl">{{ props.entry.icon }}</span>
        <span class="text-lg font-semibold text-content">{{ props.entry.label }}</span>
      </div>
      <span
        v-if="synced"
        class="inline-flex items-center gap-1 rounded-full bg-success/15 px-2.5 py-1 text-xs font-medium text-success"
      >✓ 已同步</span>
      <span
        v-else
        class="text-muted transition group-hover:translate-x-0.5 group-hover:text-accent"
      >→</span>
    </div>

    <div v-if="status === 'loading'" class="flex" aria-hidden="true">
      <div
        v-for="i in tabCount"
        :key="i"
        class="flex flex-1 flex-col items-center gap-2"
      >
        <div class="skeleton h-9 w-12 rounded"></div>
        <div class="skeleton h-3 w-8 rounded"></div>
      </div>
    </div>

    <p v-else-if="status === 'error'" class="text-sm text-danger">数据加载失败</p>

    <div v-else class="flex">
      <div v-for="c in counts" :key="c.name" class="flex-1 text-center">
        <div
          class="text-3xl font-bold tabular-nums"
          :class="
            c.value == null
              ? 'text-muted'
              : c.value > 0
                ? 'text-accent'
                : 'text-success'
          "
        >{{ c.value ?? "—" }}</div>
        <div class="mt-1 text-xs text-muted">{{ c.name }}</div>
      </div>
    </div>
  </RouterLink>
</template>
