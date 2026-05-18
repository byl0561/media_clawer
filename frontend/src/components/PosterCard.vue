<script setup lang="ts">
import type {MediaItem} from "@/types";
import {imageUrl} from "@/utils/image";
import RatingChip from "@/components/RatingChip.vue";

const props = defineProps<{ item: MediaItem }>()
</script>

<template>
  <component
    :is="props.item.link ? 'a' : 'div'"
    :href="props.item.link ?? undefined"
    :target="props.item.link ? '_blank' : undefined"
    rel="noopener noreferrer"
    class="group block animate-fade-in"
  >
    <div
      class="relative aspect-[2/3] overflow-hidden rounded-xl bg-surface-2 ring-1 ring-border transition duration-300 group-hover:-translate-y-1 group-hover:shadow-lg group-hover:shadow-black/40 group-hover:ring-accent/60"
    >
      <img
        :src="imageUrl(props.item.img)"
        :alt="props.item.title"
        loading="lazy"
        class="h-full w-full object-cover transition duration-500 group-hover:scale-105"
      />
      <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/80 via-black/5 to-transparent"></div>
      <div class="absolute left-2 top-2">
        <RatingChip :score="props.item.score" />
      </div>
    </div>
    <p
      class="mt-2 line-clamp-2 text-sm text-content/90 transition group-hover:text-accent"
      :title="props.item.title"
    >
      {{ props.item.title }}
    </p>
  </component>
</template>
