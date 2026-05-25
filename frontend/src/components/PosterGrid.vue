<script setup lang="ts">
import type {MediaItem} from "@/types";
import PosterCard from "@/components/PosterCard.vue";

defineProps<{ items: MediaItem[] }>()
const emit = defineEmits<{
  ignored: [item: MediaItem, fully: boolean];
  bound: [item: MediaItem];
}>()
</script>

<template>
  <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8">
    <PosterCard
      v-for="item in items"
      :key="item.link ?? item.title"
      :item="item"
      @ignored="(fully) => emit('ignored', item, fully)"
      @bound="emit('bound', item)"
    />
  </div>
</template>
