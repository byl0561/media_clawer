<script setup lang="ts">
import type {MediaItem} from "@/types";
import {imageUrl} from "@/utils/image";
import RatingChip from "@/components/RatingChip.vue";

const props = defineProps<{ item: MediaItem }>()

// A remote poster can still 404 (host down, hotlink, dead URL). Fall back to
// the local placeholder once, guarding against an error loop on the fallback.
function onImgError(e: Event): void {
  const img = e.target as HTMLImageElement
  if (!img.src.endsWith("/images/404.png")) img.src = "/images/404.png"
}
</script>

<template>
  <component
    :is="props.item.link ? 'a' : 'div'"
    :href="props.item.link ?? undefined"
    :target="props.item.link ? '_blank' : undefined"
    rel="noopener noreferrer"
    class="group block animate-fade-in rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
  >
    <div
      class="relative aspect-[2/3] overflow-hidden rounded-xl bg-surface-2 ring-1 ring-border transition duration-300 group-hover:-translate-y-1 group-hover:shadow-lg group-hover:shadow-black/40 group-hover:ring-accent/60 group-focus-visible:-translate-y-1 group-focus-visible:shadow-lg group-focus-visible:shadow-black/40 group-focus-visible:ring-accent/60"
    >
      <img
        :src="imageUrl(props.item.img)"
        :alt="props.item.title"
        loading="lazy"
        decoding="async"
        @error="onImgError"
        class="h-full w-full object-cover transition duration-500 group-hover:scale-105 group-focus-visible:scale-105"
      />
      <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/80 via-black/5 to-transparent"></div>
      <div class="absolute left-2 top-2">
        <RatingChip :score="props.item.score" />
      </div>
    </div>
    <p
      class="mt-2 line-clamp-2 text-sm text-content/90 transition group-hover:text-accent group-focus-visible:text-accent"
      :title="props.item.title"
    >
      {{ props.item.title }}
    </p>
  </component>
</template>
