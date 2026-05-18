<script setup lang="ts">
import {useMediaCatalog} from "@/stores/mediaCatalog";
import MediaSummaryCard from "@/components/MediaSummaryCard.vue";

const {entries} = useMediaCatalog()
</script>

<template>
  <section class="mx-auto max-w-screen-2xl px-4 py-8 sm:px-6">
    <header class="mb-6">
      <h1 class="text-2xl font-bold text-content">库维护概览</h1>
      <p class="mt-1 text-sm text-muted">榜单与本地库的差异一览，点击进入查看明细</p>
    </header>

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <MediaSummaryCard v-for="entry in entries" :key="entry.key" :entry="entry" />
    </div>
  </section>
</template>
