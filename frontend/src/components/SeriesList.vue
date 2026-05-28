<script setup lang="ts">
import type {SeriesRow} from "@/types";
import SeriesGapCard from "@/components/SeriesGapCard.vue";

defineProps<{ rows: SeriesRow[] }>()
const emit = defineEmits<{
  ignored: [row: SeriesRow, fully: boolean];
}>()
</script>

<template>
  <div class="flex flex-col gap-4">
    <SeriesGapCard
      v-for="row in rows"
      :key="(row.ignoreCollection?.collectionId ?? row.title) + ':' + row.local.length + ':' + row.missing.length"
      :row="row"
      @ignored="(fully) => emit('ignored', row, fully)"
    />
  </div>
</template>
