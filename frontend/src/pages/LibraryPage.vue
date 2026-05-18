<script setup lang="ts">
import {computed, onMounted, ref, watch} from "vue";
import {useRoute} from "vue-router";
import type {MediaItemGroupData} from "@/types";
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

onMounted(loadAll)
watch(key, loadAll)
watch(catalog.version, loadAll)
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

      <SkeletonGrid v-if="!activeState || activeState.status === 'loading'" />
      <ErrorState
        v-else-if="activeState.status === 'error'"
        @retry="catalog.refresh()"
      />
      <EmptyState v-else-if="activeState.data!.mediaItems.length === 0" />
      <PosterGrid v-else :items="activeState.data!.mediaItems" />
    </template>

    <div v-else class="py-24 text-center text-muted">
      未找到该媒体类型 ·
      <RouterLink to="/" class="text-accent hover:underline">返回概览</RouterLink>
    </div>
  </section>
</template>
