<script setup lang="ts">
import {onMounted, ref, watch} from "vue";
import type {CatalogEntry} from "@/stores/mediaCatalog";

const props = defineProps<{ entry: CatalogEntry }>()

interface Count {
  name: string;
  value: number | null;
}

const counts = ref<Count[]>([])
const loading = ref(true)
const failed = ref(false)

async function load(): Promise<void> {
  loading.value = true
  failed.value = false
  const tabs = props.entry.group.mediaItemFunctionGroups
  const results = await Promise.all(
    tabs.map((tab) =>
      tab
        .acquireData()
        .then((data) => (data.valid ? data.mediaItems.length : null))
        .catch(() => null),
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
    class="group flex flex-col gap-4 rounded-2xl border border-border bg-surface p-5 transition hover:-translate-y-0.5 hover:border-accent/50 hover:bg-surface-2"
  >
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="grid h-10 w-10 place-items-center rounded-xl bg-surface-2 text-xl">{{ props.entry.icon }}</span>
        <span class="text-lg font-semibold text-content">{{ props.entry.label }}</span>
      </div>
      <span class="text-muted transition group-hover:translate-x-0.5 group-hover:text-accent">→</span>
    </div>

    <template v-if="loading">
      <div class="skeleton h-9 w-24 rounded"></div>
      <div class="skeleton h-4 w-40 rounded"></div>
    </template>

    <template v-else-if="failed">
      <p class="text-sm text-danger">数据加载失败</p>
    </template>

    <template v-else>
      <div class="flex items-baseline gap-2">
        <span
          class="text-4xl font-bold tabular-nums"
          :class="(counts[0]?.value ?? 0) > 0 ? 'text-accent' : 'text-success'"
        >{{ counts[0]?.value ?? 0 }}</span>
        <span class="text-sm text-muted">{{ counts[0]?.name }}</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="c in counts.slice(1)"
          :key="c.name"
          class="rounded-md bg-surface-2 px-2 py-1 text-xs text-muted"
        >{{ c.name }} <b class="text-content tabular-nums">{{ c.value ?? "—" }}</b></span>
      </div>
    </template>
  </RouterLink>
</template>
