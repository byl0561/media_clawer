<script setup lang="ts">
import {computed, onMounted, ref, watch} from "vue";
import {useRoute} from "vue-router";
import type {MediaItem, MediaItemFunctionGroup, MediaItemGroupData, SeriesGroupData, SeriesRow} from "@/types";
import {useMediaCatalog} from "@/stores/mediaCatalog";
import SegmentedTabs from "@/components/SegmentedTabs.vue";
import PosterGrid from "@/components/PosterGrid.vue";
import SeriesList from "@/components/SeriesList.vue";
import SkeletonGrid from "@/components/SkeletonGrid.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";

// Two tab kinds coexist: legacy flat poster grid (最新/过时) and the new
// series-card list (续集). Each tab is tagged by which one its data matches.
interface ItemsState {
  kind: "items";
  status: "loading" | "ok" | "error";
  step: string;
  pct: number;
  data: MediaItemGroupData | null;
}
interface SeriesState {
  kind: "series";
  status: "loading" | "ok" | "error";
  step: string;
  pct: number;
  data: SeriesGroupData | null;
}
type TabState = ItemsState | SeriesState

function tabKind(tab: MediaItemFunctionGroup): "items" | "series" {
  return tab.acquireSeries ? "series" : "items"
}

function itemCount(state: TabState): number {
  if (state.status !== "ok" || state.data == null) return 0
  return state.kind === "items"
    ? state.data.mediaItems.length
    : state.data.rows.length
}

const route = useRoute()
const catalog = useMediaCatalog()

const key = computed(() => String(route.params.type))
const entry = computed(() => catalog.find(key.value))

const states = ref<TabState[]>([])
const active = ref(0)

const tabs = computed(() => {
  const groups = entry.value?.group.mediaItemFunctionGroups ?? []
  return groups.map((tab, i) => {
    const s = states.value[i]
    return {
      name: tab.name,
      count: s?.status === "ok" ? itemCount(s) : null,
    }
  })
})

const activeState = computed<TabState | undefined>(() => states.value[active.value])

const statusText = computed(() => {
  const s = activeState.value
  if (!s || s.status === "loading") return s?.step || "加载中"
  if (s.status === "error") return "加载失败"
  const n = itemCount(s)
  if (n === 0) return "已与榜单同步，无需维护"
  return `已加载 ${n} 项`
})

async function loadTab(i: number): Promise<void> {
  const group = entry.value?.group
  if (!group) return
  const tab = group.mediaItemFunctionGroups[i]
  const kind = tabKind(tab)
  const onProgress = (step: string, pct: number) => {
    const s = states.value[i]
    if (s?.status === "loading") { s.step = step; s.pct = pct }
  }
  if (kind === "series") {
    states.value[i] = {kind: "series", status: "loading", step: "", pct: 0, data: null}
    try {
      const data = await tab.acquireSeries!(onProgress)
      states.value[i] = data.valid
        ? {kind: "series", status: "ok", step: "", pct: 0, data}
        : {kind: "series", status: "error", step: "", pct: 0, data: null}
    } catch {
      states.value[i] = {kind: "series", status: "error", step: "", pct: 0, data: null}
    }
  } else {
    states.value[i] = {kind: "items", status: "loading", step: "", pct: 0, data: null}
    try {
      const data = await tab.acquireData!(onProgress)
      states.value[i] = data.valid
        ? {kind: "items", status: "ok", step: "", pct: 0, data}
        : {kind: "items", status: "error", step: "", pct: 0, data: null}
    } catch {
      states.value[i] = {kind: "items", status: "error", step: "", pct: 0, data: null}
    }
  }
}

async function loadAll(): Promise<void> {
  const group = entry.value?.group
  if (!group) {
    states.value = []
    return
  }
  const tabCount = group.mediaItemFunctionGroups.length
  states.value = Array.from({length: tabCount}, (_, i) =>
    tabKind(group.mediaItemFunctionGroups[i]) === "series"
      ? {kind: "series", status: "loading", step: "", pct: 0, data: null} as TabState
      : {kind: "items", status: "loading", step: "", pct: 0, data: null} as TabState,
  )
  await Promise.all(group.mediaItemFunctionGroups.map((_, i) => loadTab(i)))
  const firstWithItems = states.value.findIndex(
    (s) => s.status === "ok" && itemCount(s) > 0,
  )
  active.value = firstWithItems >= 0 ? firstWithItems : 0
}

function retry(): void {
  catalog.refreshEntry(key.value)
  catalog.track(loadAll())
}

// Items-tab ignore (TV/anime "最新" / "过时" don't carry this, only the legacy
// per-poster ignore on 续集 did; kept for backward compat with the flat list).
function onItemIgnored(item: MediaItem, fully: boolean): void {
  if (fully) {
    const s = activeState.value
    if (!s || s.kind !== "items" || !s.data) return
    const idx = s.data.mediaItems.indexOf(item)
    if (idx !== -1) s.data.mediaItems.splice(idx, 1)
    return
  }
  catalog.refreshEntry(key.value)
  catalog.track(loadTab(active.value))
}

function onItemBound(item: MediaItem): void {
  const s = activeState.value
  if (s && s.kind === "items" && s.data) {
    const idx = s.data.mediaItems.indexOf(item)
    if (idx !== -1) s.data.mediaItems.splice(idx, 1)
  }
  catalog.refreshEntry(key.value)
}

// Series-tab ignore. Movie collection: always fully — drop the row. TV/anime
// per-season: only fully drop when every gap season was ignored; otherwise
// refetch so the surviving seasons re-render with updated tiles.
function onSeriesIgnored(row: SeriesRow, fully: boolean): void {
  if (fully) {
    const s = activeState.value
    if (s && s.kind === "series" && s.data) {
      const idx = s.data.rows.indexOf(row)
      if (idx !== -1) s.data.rows.splice(idx, 1)
    }
    catalog.refreshEntry(key.value)
    return
  }
  catalog.refreshEntry(key.value)
  catalog.track(loadTab(active.value))
}

onMounted(() => catalog.track(loadAll()))
watch(key, () => catalog.track(loadAll()))
watch(catalog.version, () => catalog.track(loadAll()))
</script>

<template>
  <section class="mx-auto max-w-screen-2xl px-4 py-8 sm:px-6">
    <template v-if="entry">
      <nav class="mb-2 text-sm text-muted">
        <RouterLink to="/" class="transition hover:text-content">概览</RouterLink>
        <span class="mx-1.5">/</span>
        <span class="text-content">{{ entry.label }}</span>
      </nav>

      <div class="mb-6 flex flex-wrap items-center gap-4">
        <h1 class="flex items-center gap-2 text-2xl font-bold text-content">
          <span>{{ entry.icon }}</span>{{ entry.label }}
        </h1>
        <SegmentedTabs :tabs="tabs" v-model="active" />
      </div>

      <p class="sr-only" role="status" aria-live="polite">{{ statusText }}</p>

      <template v-if="!activeState || activeState.status === 'loading'">
        <p class="mb-1 text-sm text-muted">{{ statusText }}</p>
        <div class="mb-4 h-1 w-full overflow-hidden rounded-full bg-surface-2">
          <div
            class="h-full rounded-full bg-accent transition-[width] duration-300"
            :style="{width: (activeState?.pct ?? 0) + '%'}"
          ></div>
        </div>
        <SkeletonGrid />
      </template>
      <ErrorState
        v-else-if="activeState.status === 'error'"
        @retry="retry"
      />
      <EmptyState v-else-if="itemCount(activeState) === 0" />
      <PosterGrid
        v-else-if="activeState.kind === 'items'"
        :items="activeState.data!.mediaItems"
        @ignored="onItemIgnored"
        @bound="onItemBound"
      />
      <SeriesList
        v-else-if="activeState.kind === 'series'"
        :rows="activeState.data!.rows"
        @ignored="(row, fully) => onSeriesIgnored(row, fully)"
      />
    </template>

    <div v-else class="py-24 text-center text-muted">
      未找到该媒体类型 ·
      <RouterLink to="/" class="text-accent hover:underline">返回概览</RouterLink>
    </div>
  </section>
</template>
