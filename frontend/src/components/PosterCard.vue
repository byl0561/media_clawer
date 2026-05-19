<script setup lang="ts">
import {ref} from "vue";
import type {MediaItem} from "@/types";
import {imageUrl} from "@/utils/image";
import RatingChip from "@/components/RatingChip.vue";
import IgnoreDialog from "@/components/IgnoreDialog.vue";

const props = defineProps<{ item: MediaItem }>()
// Emitted only when the user ignored every gap season up to its latest
// episode — the parent then drops this card without waiting for a rescan.
const emit = defineEmits<{ ignored: [] }>()

const dialogOpen = ref(false)

// A remote poster can still 404 (host down, hotlink, dead URL). Fall back to
// the local placeholder once, guarding against an error loop on the fallback.
function onImgError(e: Event): void {
  const img = e.target as HTMLImageElement
  if (!img.src.endsWith("/images/404.png")) img.src = "/images/404.png"
}

function onDone(payload: { fullyIgnored: boolean }): void {
  dialogOpen.value = false
  if (payload.fullyIgnored) emit("ignored")
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
      <button
        v-if="props.item.ignore"
        type="button"
        @click.stop.prevent="dialogOpen = true"
        title="忽略缺失"
        class="absolute right-2 top-2 rounded-md bg-black/55 px-2 py-0.5 text-xs font-semibold text-white backdrop-blur-sm transition opacity-0 pointer-events-none hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent group-hover:opacity-100 group-hover:pointer-events-auto focus-visible:opacity-100 focus-visible:pointer-events-auto [@media(hover:none)]:opacity-100 [@media(hover:none)]:pointer-events-auto"
      >忽略</button>
    </div>
    <p
      class="mt-2 line-clamp-2 text-sm text-content/90 transition group-hover:text-accent group-focus-visible:text-accent"
      :title="props.item.title"
    >
      {{ props.item.title }}
    </p>

    <IgnoreDialog
      v-if="dialogOpen && props.item.ignore"
      :library="props.item.ignore!.library"
      :tmdb-id="props.item.ignore!.tmdbId"
      :title="props.item.title"
      @close="dialogOpen = false"
      @done="onDone"
    />
  </component>
</template>
