<script setup lang="ts">
import {computed, onMounted, ref, watch} from "vue";
import {useRoute} from "vue-router";
import type {MediaItem, MediaItemGroupData} from "@/types";
import {useMediaCatalog} from "@/stores/mediaCatalog";
import SegmentedTabs from "@/components/SegmentedTabs.vue";
import PosterGrid from "@/components/PosterGrid.vue";
import SkeletonGrid from "@/components/SkeletonGrid.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorState from "@/components/ErrorState.vue";

interface TabState {
  status: "loading" | "ok" | "error";
  data: MediaItemGroupData | null;
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
      count: s?.status === "ok" ? s.data!.mediaItems.length : null,
    }
  })
})

const activeState = computed<TabState | undefined>(() => states.value[active.value])

// Concise, polite announcement for screen readers (the poster grid itself is
// not in a live region — that would read out every title on every change).
const statusText = computed(() => {
  const s = activeState.value
  if (!s || s.status === "loading") return "加载中"
  if (s.status === "error") return "加载失败"
  if (s.data!.mediaItems.length === 0) return "已与榜单同步，无需维护"
  return `已加载 ${s.data!.mediaItems.length} 项`
})

async function loadTab(i: number): Promise<void> {
  const group = entry.value?.group
  if (!group) return
  states.value[i] = {status: "loading", data: null}
  try {
    const data = await group.mediaItemFunctionGroups[i].acquireData()
    states.value[i] = data.valid
      ? {status: "ok", data}
      : {status: "error", data: null}
  } catch {
    states.value[i] = {status: "error", data: null}
  }
}

async function loadAll(): Promise<void> {
  const group = entry.value?.group
  if (!group) {
    states.value = []
    return
  }
  const tabCount = group.mediaItemFunctionGroups.length
  states.value = Array.from({length: tabCount}, () => ({status: "loading", data: null}))
  await Promise.all(group.mediaItemFunctionGroups.map((_, i) => loadTab(i)))
  const firstWithItems = states.value.findIndex(
    (s) => s.status === "ok" && s.data!.mediaItems.length > 0,
  )
  active.value = firstWithItems >= 0 ? firstWithItems : 0
}

// Rebuild only this media type's loaders, then reload — a failed tab can
// retry without re-fetching the other four libraries.
function retry(): void {
  catalog.refreshEntry(key.value)
  catalog.track(loadAll())
}

// Fully ignored: drop the card immediately (no rescan needed).
// Partial: refetch this tab so the card's season list reflects what's left
// — otherwise the just-ignored season would still show in the baked title.
function onIgnored(item: MediaItem, fully: boolean): void {
  if (fully) {
    const data = activeState.value?.data
    if (!data) return
    const idx = data.mediaItems.indexOf(item)
    if (idx !== -1) data.mediaItems.splice(idx, 1)
    return
  }
  catalog.refreshEntry(key.value)
  catalog.track(loadTab(active.value))
}

// Bound to a local item: the alias.txt write means the next diff will match
// this rank entry, so it'll drop from "最新". Remove the card immediately
// (cheap optimism) and also invalidate the cached diff so subsequent
// navigations/refreshes hit a fresh response from the server.
function onBound(item: MediaItem): void {
  const data = activeState.value?.data
  if (data) {
    const idx = data.mediaItems.indexOf(item)
    if (idx !== -1) data.mediaItems.splice(idx, 1)
  }
  catalog.refreshEntry(key.value)
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

      <SkeletonGrid v-if="!activeState || activeState.status === 'loading'" />
      <ErrorState
        v-else-if="activeState.status === 'error'"
        @retry="retry"
      />
      <EmptyState v-else-if="activeState.data!.mediaItems.length === 0" />
      <PosterGrid
        v-else
        :items="activeState.data!.mediaItems"
        @ignored="onIgnored"
        @bound="onBound"
      />
    </template>

    <div v-else class="py-24 text-center text-muted">
      未找到该媒体类型 ·
      <RouterLink to="/" class="text-accent hover:underline">返回概览</RouterLink>
    </div>
  </section>
</template>
