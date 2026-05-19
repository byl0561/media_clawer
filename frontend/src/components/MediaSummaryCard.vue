<script setup lang="ts">
import {computed, onMounted, ref, watch} from "vue";
import type {CatalogEntry} from "@/stores/mediaCatalog";
import {useMediaCatalog} from "@/stores/mediaCatalog";

const props = defineProps<{ entry: CatalogEntry }>()
const catalog = useMediaCatalog()

interface Count {
  name: string;
  value: number | null;
}

const counts = ref<Count[]>([])
const loading = ref(true)
const failed = ref(false)
// Known before data arrives; the skeleton uses it so the loading -> loaded
// transition keeps the same column layout and doesn't reflow the card.
const tabCount = computed(() => props.entry.group.mediaItemFunctionGroups.length)

async function load(): Promise<void> {
  loading.value = true
  failed.value = false
  const tabs = props.entry.group.mediaItemFunctionGroups
  const results = await catalog.track(
    Promise.all(
      tabs.map((tab) =>
        tab
          .acquireData()
          .then((data) => (data.valid ? data.mediaItems.length : null))
          .catch(() => null),
      ),
    ),
  )
  counts.value = tabs.map((tab, i) => ({name: tab.name, value: results[i]}))
  failed.value = results.every((r) => r == null)
  loading.value = false
}

onMounted(load)
// refresh() swaps every entry for a fresh object (new memoized loaders);
// react to that identity change so the card actually re-fetches.
watch(() => props.entry, load)
</script>

<template>
  <RouterLink
    :to="`/library/${props.entry.key}`"
    class="group flex flex-col gap-4 rounded-2xl border border-border bg-surface p-5 transition hover:-translate-y-0.5 hover:border-accent/50 hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg focus-visible:-translate-y-0.5 focus-visible:border-accent/50"
  >
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="grid h-10 w-10 place-items-center rounded-xl bg-surface-2 text-xl">{{ props.entry.icon }}</span>
        <span class="text-lg font-semibold text-content">{{ props.entry.label }}</span>
      </div>
      <span class="text-muted transition group-hover:translate-x-0.5 group-hover:text-accent">→</span>
    </div>

    <template v-if="loading">
      <div class="flex" aria-hidden="true">
        <div
          v-for="i in tabCount"
          :key="i"
          class="flex flex-1 flex-col items-center gap-2"
        >
          <div class="skeleton h-8 w-10 rounded"></div>
          <div class="skeleton h-3 w-8 rounded"></div>
        </div>
      </div>
    </template>

    <template v-else-if="failed">
      <p class="text-sm text-danger">数据加载失败</p>
    </template>

    <template v-else>
      <div class="flex">
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
    </template>
  </RouterLink>
</template>
