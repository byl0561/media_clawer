<script setup lang="ts">
import {computed, onBeforeUnmount, ref, watch} from "vue";
import type {SeriesPoster, SeriesRow} from "@/types";
import {imageUrl} from "@/utils/image";
import {ignoreMovieCollection} from "@/http/api";
import RatingChip from "@/components/RatingChip.vue";
import IgnoreDialog from "@/components/IgnoreDialog.vue";

// Series-gap card: title + score on top (with an optional movie-only "忽略
// 合集" button shown on hover next to the title); a stacked deck of owned
// items on the left (horizontal-only fan, ◀/▶ arrows on hover to cycle the
// front card); a tiled grid of missing items on the right. Vertically
// centered on the row so a tall right grid doesn't make the deck float.
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

// Front-of-deck pointer; ◀/▶ rotate it (modulo length).
const topIndex = ref(0)

// Build the visible 3-card slice rotated so `topIndex` is on top. Behind-cards
// reuse the next entries (cyclic), so a 2-movie collection still fans even
// after cycling. Pure-decorative for layers 1 & 2; the top card is the only
// one that's clickable / carries the score chip.
const deckLayers = computed<SeriesPoster[]>(() => {
  const n = props.row.local.length
  if (n === 0) return []
  const out: SeriesPoster[] = []
  for (let i = 0; i < Math.min(3, n); i++) {
    out.push(props.row.local[(topIndex.value + i) % n])
  }
  return out
})

const canCycle = computed(() => props.row.local.length > 1)
const topCard = computed<SeriesPoster | null>(() => deckLayers.value[0] ?? null)

function next(e: MouseEvent): void {
  e.stopPropagation()
  e.preventDefault()
  const n = props.row.local.length
  if (n > 0) topIndex.value = (topIndex.value + 1) % n
}
function prev(e: MouseEvent): void {
  e.stopPropagation()
  e.preventDefault()
  const n = props.row.local.length
  if (n > 0) topIndex.value = (topIndex.value - 1 + n) % n
}

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

// Escape closes the confirm dialog (matches IgnoreDialog's UX); mount the
// listener only while the dialog is open so we don't intercept keystrokes
// from cards that aren't actively showing the prompt.
function onKeydown(e: KeyboardEvent): void {
  if (e.key === "Escape") confirmOpen.value = false
}
watch(confirmOpen, (open) => {
  if (open) window.addEventListener("keydown", onKeydown)
  else window.removeEventListener("keydown", onKeydown)
})
onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown))
</script>

<template>
  <article
    class="group/card animate-fade-in rounded-2xl border border-border bg-surface-2/40 p-4 backdrop-blur-sm transition hover:border-accent/40"
  >
    <!-- Header: title + (movie-only) ignore button on hover + weighted score -->
    <header class="mb-4 flex items-center justify-between gap-3 border-b border-border/60 pb-3">
      <div class="flex min-w-0 items-center gap-2">
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
        <button
          v-if="row.ignoreCollection"
          type="button"
          @click.stop.prevent="confirmOpen = true"
          title="忽略整个合集"
          class="shrink-0 rounded-md bg-surface px-2 py-0.5 text-xs font-semibold text-muted ring-1 ring-border transition opacity-0 pointer-events-none hover:text-content hover:ring-accent focus-visible:opacity-100 focus-visible:pointer-events-auto group-hover/card:opacity-100 group-hover/card:pointer-events-auto [@media(hover:none)]:opacity-100 [@media(hover:none)]:pointer-events-auto"
        >忽略</button>
      </div>
      <RatingChip :score="row.score" />
    </header>

    <!-- Body: vertically centered deck on the left, tiled grid on the right.
         A thin divider (vertical on md+, horizontal on mobile) separates the
         "owned" and "missing" halves so the boundary stays legible even when
         the right grid wraps to multiple rows. -->
    <div class="flex flex-col gap-4 md:flex-row md:items-center md:gap-5">
      <!-- Left: horizontal-fan stacked deck w/ hover cycle arrows -->
      <div class="shrink-0">
        <p class="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted">
          已有 · {{ row.local.length }} 项
        </p>
        <!-- Container width = card slot (w-32 = 128px) + max fan (16px) so the
             visible bounding box stays centered against the labels above and
             below; the ◀/▶ arrows poke out into the surrounding flex gap. -->
        <div class="group/deck relative w-36">
          <div class="relative aspect-[2/3] w-32">
            <!-- Decorative behind layers: fan to the right, lower z-index.
                 Render in reverse so the back-most layer is painted first. -->
            <template v-for="(p, i) in deckLayers.slice().reverse()" :key="`bg-${(deckLayers.length - 1 - i)}-${p.poster ?? p.title}`">
              <div
                v-if="(deckLayers.length - 1 - i) > 0"
                class="absolute inset-0 overflow-hidden rounded-xl bg-surface-2 ring-1 ring-border"
                :style="{
                  transform: `translateX(${(deckLayers.length - 1 - i) * 8}px)`,
                  zIndex: 10 - (deckLayers.length - 1 - i),
                }"
              >
                <img
                  :src="imageUrl(p.poster)"
                  :alt="p.title"
                  loading="lazy"
                  decoding="async"
                  @error="onImgError"
                  class="h-full w-full object-cover opacity-80"
                />
              </div>
            </template>

            <!-- Top card: clickable, score chip, title overlay at the bottom -->
            <component
              v-if="topCard"
              :is="topCard.link ? 'a' : 'div'"
              :href="topCard.link ?? undefined"
              :target="topCard.link ? '_blank' : undefined"
              rel="noopener noreferrer"
              class="absolute inset-0 block overflow-hidden rounded-xl bg-surface-2 ring-1 ring-border transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/40 hover:ring-accent/60"
              :style="{ zIndex: 20 }"
            >
              <img
                :src="imageUrl(topCard.poster)"
                :alt="topCard.title"
                loading="lazy"
                decoding="async"
                @error="onImgError"
                class="h-full w-full object-cover transition"
              />
              <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/70 via-black/0 to-transparent"></div>
              <div class="absolute left-2 top-2">
                <RatingChip :score="topCard.score" />
              </div>
              <div class="pointer-events-none absolute bottom-1.5 left-1.5 right-1.5 truncate text-xs text-white/90" :title="topCard.title">
                {{ topCard.title }}
              </div>
            </component>
          </div>

          <!-- Cycle arrows (hover-only, only when there's something to cycle) -->
          <button
            v-if="canCycle"
            type="button"
            @click="prev"
            aria-label="上一部"
            class="absolute left-0 top-1/2 z-30 -translate-x-1 -translate-y-1/2 rounded-full bg-black/60 p-1.5 text-white/95 backdrop-blur-sm transition opacity-0 pointer-events-none hover:bg-accent focus-visible:opacity-100 focus-visible:pointer-events-auto group-hover/deck:opacity-100 group-hover/deck:pointer-events-auto [@media(hover:none)]:opacity-100 [@media(hover:none)]:pointer-events-auto"
          >
            <svg class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M12.5 4.5a1 1 0 010 1.4L8.4 10l4.1 4.1a1 1 0 11-1.4 1.4l-4.8-4.8a1 1 0 010-1.4l4.8-4.8a1 1 0 011.4 0z" />
            </svg>
          </button>
          <button
            v-if="canCycle"
            type="button"
            @click="next"
            aria-label="下一部"
            class="absolute right-0 top-1/2 z-30 translate-x-1 -translate-y-1/2 rounded-full bg-black/60 p-1.5 text-white/95 backdrop-blur-sm transition opacity-0 pointer-events-none hover:bg-accent focus-visible:opacity-100 focus-visible:pointer-events-auto group-hover/deck:opacity-100 group-hover/deck:pointer-events-auto [@media(hover:none)]:opacity-100 [@media(hover:none)]:pointer-events-auto"
          >
            <svg class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M7.5 4.5a1 1 0 011.4 0l4.8 4.8a1 1 0 010 1.4l-4.8 4.8a1 1 0 11-1.4-1.4L11.6 10 7.5 5.9a1 1 0 010-1.4z" />
            </svg>
          </button>

          <p v-if="canCycle" class="mt-2 text-center text-xs tabular-nums text-muted">
            {{ topIndex + 1 }} / {{ row.local.length }}
          </p>
        </div>
      </div>

      <!-- Divider between "owned" and "missing"; vertical on md+, horizontal stack on mobile -->
      <div class="hidden self-stretch md:block md:w-px md:bg-border/60" aria-hidden="true"></div>
      <div class="block h-px bg-border/60 md:hidden" aria-hidden="true"></div>

      <!-- Right: tiled missing items, each with its own score chip -->
      <div class="min-w-0 flex-1">
        <p class="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted">
          待加 · {{ row.missing.length }} 项
        </p>
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
              <div class="absolute left-1.5 top-1.5">
                <RatingChip :score="p.score" />
              </div>
              <div class="pointer-events-none absolute bottom-1 left-1.5 right-1.5 truncate text-[11px] font-medium text-white/90" :title="p.title">
                {{ p.title }}
              </div>
            </div>
          </component>
        </div>
      </div>
    </div>

    <!-- Movie ignore-collection confirmation dialog (mirrors IgnoreDialog's
         shell: teleported to body, dimmed backdrop layer, solid bg-surface
         panel — without those it renders transparent over the underlying
         posters and looks broken). -->
    <Teleport to="body">
      <div
        v-if="confirmOpen"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        aria-label="忽略整个合集"
      >
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="confirmOpen = false"
        ></div>

        <div
          class="relative w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-2xl"
        >
          <h3 class="text-base font-semibold text-content">忽略整个合集</h3>
          <p class="mt-2 text-sm text-muted">
            确定要忽略合集
            <span class="font-medium text-content">“{{ row.title }}”</span>
            吗？该合集将不会再出现在续集列表中，本地 {{ row.local.length }} 部电影会各自记录此设置。
          </p>
          <p v-if="ignoreError" class="mt-3 text-sm text-danger">{{ ignoreError }}</p>
          <div class="mt-5 flex justify-end gap-2">
            <button
              type="button"
              class="rounded-lg border border-border px-4 py-2 text-sm text-content transition hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              :disabled="ignoring"
              @click="confirmOpen = false"
            >取消</button>
            <button
              type="button"
              class="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="ignoring"
              @click="confirmIgnore"
            >{{ ignoring ? "处理中…" : "确认忽略" }}</button>
          </div>
        </div>
      </div>
    </Teleport>

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
