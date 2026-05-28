<script setup lang="ts">
import {computed, ref} from "vue";
import type {SeriesPoster, SeriesRow} from "@/types";
import {imageUrl} from "@/utils/image";
import {ignoreMovieCollection} from "@/http/api";
import RatingChip from "@/components/RatingChip.vue";
import IgnoreDialog from "@/components/IgnoreDialog.vue";

// Renders one series row: left stacked-deck of owned items + right tiled grid
// of missing items + title and (vote-weighted) score below. The deck's top-
// right "忽略" button is only present on the movie variant — it asks for
// confirmation, then POSTs ignore-collection, which writes skip_collections
// onto every local movie tied to this collection so the row disappears next
// reload. TV/anime right tiles carry an `ignore` ref so clicking opens the
// existing per-season IgnoreDialog.
const props = defineProps<{ row: SeriesRow }>()
const emit = defineEmits<{
  // fully=true: parent drops the row immediately.
  // fully=false: parent refetches the 续集 tab so partial-ignored shows
  //   redraw with the surviving seasons.
  ignored: [fully: boolean]
}>()

const confirmOpen = ref(false)
const ignoring = ref(false)
const ignoreError = ref<string | null>(null)
const activeIgnore = ref<SeriesPoster | null>(null)

// The top-of-deck poster is the first; lower layers fan out behind it.
// We render only the first 3 with offset transforms — beyond that gets a
// "+N" badge in the corner of the bottom layer.
const deckLayers = computed(() => props.row.local.slice(0, 3))
const overflow = computed(() => Math.max(0, props.row.local.length - 3))

function onImgError(e: Event): void {
  const img = e.target as HTMLImageElement
  if (!img.src.endsWith("/images/404.png")) img.src = "/images/404.png"
}

async function confirmIgnore(): Promise<void> {
  if (!props.row.ignoreCollection) return
  ignoring.value = true
  ignoreError.value = null
  const res = await ignoreMovieCollection(props.row.ignoreCollection.collectionId)
  ignoring.value = false
  if (!res.success) {
    ignoreError.value = "请求失败，请重试"
    return
  }
  confirmOpen.value = false
  emit("ignored", true)
}

function onIgnoreDialogDone(payload: { fullyIgnored: boolean }): void {
  activeIgnore.value = null
  emit("ignored", payload.fullyIgnored)
}

function onMissingClick(p: SeriesPoster, e: MouseEvent): void {
  // TV/anime missing season: intercept and open the per-show ignore dialog.
  // Movie missing: do nothing — the anchor's default navigation to TMDB runs.
  if (p.ignore && !p.link) {
    e.preventDefault()
    activeIgnore.value = p
  }
}
</script>

<template>
  <article
    class="animate-fade-in rounded-2xl border border-border bg-surface-2/40 p-4 backdrop-blur-sm transition hover:border-accent/40"
  >
    <div class="flex flex-col gap-4 md:flex-row md:items-start">
      <!-- Left: stacked-deck of owned items -->
      <div class="shrink-0">
        <div class="relative w-32 sm:w-36">
          <div class="relative aspect-[2/3]">
            <!-- Decorative layers behind (reverse-order so first stays on top) -->
            <template v-for="(p, i) in deckLayers.slice().reverse()" :key="`bg-${deckLayers.length - 1 - i}`">
              <div
                v-if="(deckLayers.length - 1 - i) > 0"
                class="absolute inset-0 overflow-hidden rounded-xl bg-surface-2 ring-1 ring-border"
                :style="{
                  transform: `translate(${(deckLayers.length - 1 - i) * 6}px, ${(deckLayers.length - 1 - i) * 6}px)`,
                  zIndex: 10 - (deckLayers.length - 1 - i),
                }"
              >
                <img
                  :src="imageUrl(p.poster)"
                  :alt="p.title"
                  loading="lazy"
                  decoding="async"
                  @error="onImgError"
                  class="h-full w-full object-cover opacity-90"
                />
              </div>
            </template>
            <!-- Top layer (first poster), always interactive -->
            <component
              v-if="deckLayers.length > 0"
              :is="row.local[0].link ? 'a' : 'div'"
              :href="row.local[0].link ?? undefined"
              :target="row.local[0].link ? '_blank' : undefined"
              rel="noopener noreferrer"
              class="group absolute inset-0 block overflow-hidden rounded-xl bg-surface-2 ring-1 ring-border transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/40 hover:ring-accent/60"
              :style="{ zIndex: 20 }"
            >
              <img
                :src="imageUrl(row.local[0].poster)"
                :alt="row.local[0].title"
                loading="lazy"
                decoding="async"
                @error="onImgError"
                class="h-full w-full object-cover transition group-hover:scale-105"
              />
              <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/70 via-black/0 to-transparent"></div>
              <button
                v-if="row.ignoreCollection"
                type="button"
                @click.stop.prevent="confirmOpen = true"
                title="忽略整个合集"
                class="absolute right-2 top-2 rounded-md bg-black/65 px-2 py-0.5 text-xs font-semibold text-white backdrop-blur-sm transition hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              >忽略</button>
              <div class="pointer-events-none absolute bottom-1.5 left-1.5 right-1.5 truncate text-xs text-white/90" :title="row.local[0].title">
                {{ row.local[0].title }}
              </div>
            </component>
            <div
              v-if="overflow > 0"
              class="absolute -bottom-2 -right-2 rounded-full bg-accent/90 px-2 py-0.5 text-xs font-semibold text-bg shadow"
              :style="{ zIndex: 30 }"
            >+{{ overflow }}</div>
          </div>
          <p class="mt-2 text-center text-xs text-muted">已有 {{ row.local.length }} 部</p>
        </div>
      </div>

      <!-- Right: tiled missing items -->
      <div class="min-w-0 flex-1">
        <div class="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
          <component
            v-for="(p, idx) in row.missing"
            :key="`missing-${idx}-${p.poster ?? p.title}`"
            :is="p.link ? 'a' : (p.ignore ? 'button' : 'div')"
            :type="p.ignore && !p.link ? 'button' : undefined"
            :href="p.link ?? undefined"
            :target="p.link ? '_blank' : undefined"
            rel="noopener noreferrer"
            class="group block text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
            @click="onMissingClick(p, $event)"
          >
            <div class="relative aspect-[2/3] overflow-hidden rounded-lg bg-surface-2 ring-1 ring-border transition group-hover:-translate-y-0.5 group-hover:shadow-md group-hover:shadow-black/40 group-hover:ring-accent/60">
              <img
                :src="imageUrl(p.poster)"
                :alt="p.title"
                loading="lazy"
                decoding="async"
                @error="onImgError"
                class="h-full w-full object-cover transition group-hover:scale-105"
              />
              <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/75 via-black/0 to-transparent"></div>
              <div class="pointer-events-none absolute bottom-1 left-1.5 right-1.5 truncate text-[11px] font-medium text-white/90" :title="p.title">
                {{ p.title }}
              </div>
            </div>
          </component>
        </div>
      </div>
    </div>

    <!-- Footer: title + score -->
    <div class="mt-4 flex items-baseline justify-between gap-3 border-t border-border/60 pt-3">
      <component
        :is="row.link ? 'a' : 'div'"
        :href="row.link ?? undefined"
        :target="row.link ? '_blank' : undefined"
        rel="noopener noreferrer"
        class="min-w-0 truncate text-sm font-semibold text-content transition hover:text-accent"
        :title="row.title"
      >
        {{ row.title }}
      </component>
      <RatingChip :score="row.score" />
    </div>

    <!-- Movie ignore-collection confirmation dialog -->
    <div
      v-if="confirmOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      @click.self="confirmOpen = false"
    >
      <div class="w-full max-w-md rounded-2xl border border-border bg-surface-1 p-6 shadow-2xl">
        <h3 class="text-lg font-semibold text-content">忽略整个合集</h3>
        <p class="mt-2 text-sm text-muted">
          确定要忽略合集
          <span class="font-medium text-content">"{{ row.title }}"</span>
          吗？该合集将不会再出现在续集列表中，本地 {{ row.local.length }} 部电影会各自记录此设置。
        </p>
        <p v-if="ignoreError" class="mt-2 text-sm text-red-400">{{ ignoreError }}</p>
        <div class="mt-5 flex justify-end gap-2">
          <button
            type="button"
            class="rounded-md border border-border px-3 py-1.5 text-sm text-content transition hover:bg-surface-2"
            :disabled="ignoring"
            @click="confirmOpen = false"
          >取消</button>
          <button
            type="button"
            class="rounded-md bg-accent px-3 py-1.5 text-sm font-semibold text-bg transition hover:opacity-90 disabled:opacity-50"
            :disabled="ignoring"
            @click="confirmIgnore"
          >{{ ignoring ? "处理中…" : "确认忽略" }}</button>
        </div>
      </div>
    </div>

    <!-- TV/anime per-season IgnoreDialog (reused from the old flow) -->
    <IgnoreDialog
      v-if="activeIgnore && activeIgnore.ignore"
      :library="activeIgnore.ignore!.library"
      :tmdb-id="activeIgnore.ignore!.tmdbId"
      :title="row.title"
      @close="activeIgnore = null"
      @done="onIgnoreDialogDone"
    />
  </article>
</template>
