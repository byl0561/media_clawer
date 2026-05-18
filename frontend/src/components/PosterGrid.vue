<script setup lang="ts">
import type {MediaItem} from "@/types";
import PosterCard from "@/components/PosterCard.vue";

defineProps<{ items: MediaItem[] }>()
</script>

<template>
  <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8">
    <PosterCard v-for="(item, i) in items" :key="`${item.title}-${i}`" :item="item" />
  </div>
</template>
