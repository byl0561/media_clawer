<script setup lang="ts">
import {computed, onBeforeUnmount, ref, watch} from "vue";
import type {MediaItem} from "@/types";
import {ignoreAlbumLyric, ignoreMovieSubtitle} from "@/http/api";
import {imageUrl} from "@/utils/image";
import RatingChip from "@/components/RatingChip.vue";
import IgnoreDialog from "@/components/IgnoreDialog.vue";
import BindAliasDialog from "@/components/BindAliasDialog.vue";

const props = defineProps<{ item: MediaItem }>()
// `fully` is true when every gap season was ignored up to its latest episode
// (parent drops the card); false when only some seasons were ignored (parent
// refetches so the remaining seasons render with an updated title). The
// subtitle/lyric flag actions are always "fully" — one click, one item gone.
const emit = defineEmits<{
  ignored: [fully: boolean];
  bound: [];
}>()

const ignoreDialogOpen = ref(false)
const bindDialogOpen = ref(false)

// Subtitle / lyric flag actions use a small confirm popup (no per-episode
// picker like IgnoreDialog).
const confirmSubtitle = ref(false)
const confirmLyric = ref(false)
const flagBusy = ref(false)
const flagError = ref<string | null>(null)

const ignoreMode = computed<"series" | "subtitle">(
  () => props.item.ignore?.mode ?? "series",
)

// A remote poster can still 404 (host down, hotlink, dead URL). Fall back to
// the local placeholder once, guarding against an error loop on the fallback.
function onImgError(e: Event): void {
  const img = e.target as HTMLImageElement
  if (!img.src.endsWith("/images/404.png")) img.src = "/images/404.png"
}

function onIgnoreDone(payload: { fullyIgnored: boolean }): void {
  ignoreDialogOpen.value = false
  emit("ignored", payload.fullyIgnored)
}

function onBindDone(): void {
  bindDialogOpen.value = false
  emit("bound")
}

async function applySubtitleIgnore(): Promise<void> {
  if (!props.item.ignoreSubtitle) return
  flagBusy.value = true
  flagError.value = null
  const res = await ignoreMovieSubtitle(props.item.ignoreSubtitle.tmdbId)
  flagBusy.value = false
  if (!res.success) {
    flagError.value = "请求失败，请重试"
    return
  }
  confirmSubtitle.value = false
  emit("ignored", true)
}

async function applyLyricIgnore(): Promise<void> {
  if (!props.item.ignoreLyric) return
  flagBusy.value = true
  flagError.value = null
  const res = await ignoreAlbumLyric(props.item.ignoreLyric.token)
  flagBusy.value = false
  if (!res.success) {
    flagError.value = "请求失败，请重试"
    return
  }
  confirmLyric.value = false
  emit("ignored", true)
}

function onKeydown(e: KeyboardEvent): void {
  if (e.key !== "Escape") return
  if (confirmSubtitle.value) confirmSubtitle.value = false
  if (confirmLyric.value) confirmLyric.value = false
}
watch([confirmSubtitle, confirmLyric], ([s, l]) => {
  if (s || l) window.addEventListener("keydown", onKeydown)
  else window.removeEventListener("keydown", onKeydown)
})
onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown))
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
        @click.stop.prevent="ignoreDialogOpen = true"
        title="忽略缺失"
        class="absolute right-2 top-2 rounded-md bg-black/55 px-2 py-0.5 text-xs font-semibold text-white backdrop-blur-sm transition opacity-0 pointer-events-none hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent group-hover:opacity-100 group-hover:pointer-events-auto focus-visible:opacity-100 focus-visible:pointer-events-auto [@media(hover:none)]:opacity-100 [@media(hover:none)]:pointer-events-auto"
      >忽略</button>
      <button
        v-if="props.item.bind"
        type="button"
        @click.stop.prevent="bindDialogOpen = true"
        title="绑定到本地条目"
        class="absolute right-2 top-2 rounded-md bg-black/55 px-2 py-0.5 text-xs font-semibold text-white backdrop-blur-sm transition opacity-0 pointer-events-none hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent group-hover:opacity-100 group-hover:pointer-events-auto focus-visible:opacity-100 focus-visible:pointer-events-auto [@media(hover:none)]:opacity-100 [@media(hover:none)]:pointer-events-auto"
      >绑定</button>
      <button
        v-if="props.item.ignoreSubtitle"
        type="button"
        @click.stop.prevent="confirmSubtitle = true"
        title="忽略字幕检查"
        class="absolute right-2 top-2 rounded-md bg-black/55 px-2 py-0.5 text-xs font-semibold text-white backdrop-blur-sm transition opacity-0 pointer-events-none hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent group-hover:opacity-100 group-hover:pointer-events-auto focus-visible:opacity-100 focus-visible:pointer-events-auto [@media(hover:none)]:opacity-100 [@media(hover:none)]:pointer-events-auto"
      >忽略</button>
      <button
        v-if="props.item.ignoreLyric"
        type="button"
        @click.stop.prevent="confirmLyric = true"
        title="忽略歌词检查"
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
      v-if="ignoreDialogOpen && props.item.ignore"
      :library="props.item.ignore!.library"
      :tmdb-id="props.item.ignore!.tmdbId"
      :mode="ignoreMode"
      :title="props.item.title"
      @close="ignoreDialogOpen = false"
      @done="onIgnoreDone"
    />

    <BindAliasDialog
      v-if="bindDialogOpen && props.item.bind"
      :library="props.item.bind!.library"
      :alias="props.item.bind!.alias"
      :title="props.item.title"
      @close="bindDialogOpen = false"
      @done="onBindDone"
    />

    <!-- Subtitle / lyric flag confirm popup (Teleport mirrors IgnoreDialog
         so it renders above everything regardless of card layout). -->
    <Teleport to="body">
      <div
        v-if="confirmSubtitle || confirmLyric"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
      >
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="confirmSubtitle = false; confirmLyric = false"
        ></div>
        <div class="relative w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-2xl">
          <h3 class="text-base font-semibold text-content">
            {{ confirmSubtitle ? "忽略字幕检查" : "忽略歌词检查" }}
          </h3>
          <p class="mt-2 text-sm text-muted">
            <template v-if="confirmSubtitle">
              确定不再检查
              <span class="font-medium text-content">“{{ props.item.title }}”</span>
              的字幕？以后该电影不会再出现在字幕缺失列表里。
            </template>
            <template v-else>
              确定不再检查
              <span class="font-medium text-content">“{{ props.item.title }}”</span>
              的歌词？以后整张专辑不会再出现在歌词缺失列表里。
            </template>
          </p>
          <p v-if="flagError" class="mt-3 text-sm text-danger">{{ flagError }}</p>
          <div class="mt-5 flex justify-end gap-2">
            <button
              type="button"
              class="rounded-lg border border-border px-4 py-2 text-sm text-content transition hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              :disabled="flagBusy"
              @click="confirmSubtitle = false; confirmLyric = false; flagError = null"
            >取消</button>
            <button
              type="button"
              class="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="flagBusy"
              @click="confirmSubtitle ? applySubtitleIgnore() : applyLyricIgnore()"
            >{{ flagBusy ? "处理中…" : "确认忽略" }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </component>
</template>
