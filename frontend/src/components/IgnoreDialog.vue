<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, ref} from "vue";
import type {IgnoreLibrary, IgnoreOptions, IgnoreSelection} from "@/types/api";
import {applyIgnore, ignoreOptions} from "@/http/api";

const props = defineProps<{
  library: IgnoreLibrary;
  tmdbId: number;
  title: string;
  // "series" (default) → /ignore-options + /ignore (writes checked_episode)
  // "subtitle"        → /subtitle-ignore-options + /ignore-subtitle
  //                     (writes subtitle_checked_episode)
  mode?: "series" | "subtitle";
}>()

const emit = defineEmits<{
  close: [];
  // fullyIgnored: every gap season was ignored up to its latest episode,
  // so the poster can be closed immediately (decided by the backend).
  done: [payload: { fullyIgnored: boolean }];
}>()

const loading = ref(true)
const failed = ref(false)
// Kept separate from `failed` so a failed POST shows an inline message and
// keeps the user's per-season picks, instead of resetting the whole form.
const submitFailed = ref(false)
const submitting = ref(false)
const options = ref<IgnoreOptions | null>(null)
/** season_num -> chosen episode, or "" for the default "不忽略". */
const picked = ref<Record<number, number | "">>({})

const selections = computed<IgnoreSelection[]>(() =>
  Object.entries(picked.value)
    .filter(([, ep]) => ep !== "")
    .map(([num, ep]) => ({season_num: Number(num), episode: Number(ep)})),
)
const canSubmit = computed(() => selections.value.length > 0 && !submitting.value)

async function load(): Promise<void> {
  loading.value = true
  failed.value = false
  const res = await ignoreOptions(props.library, props.tmdbId, props.mode ?? "series")
  if (!res.success || res.data == null) {
    failed.value = true
  } else {
    options.value = res.data
    const init: Record<number, number | ""> = {}
    for (const s of res.data.seasons) init[s.season_num] = ""
    picked.value = init
  }
  loading.value = false
}

async function submit(): Promise<void> {
  if (!canSubmit.value) return
  submitting.value = true
  submitFailed.value = false
  const res = await applyIgnore(
    props.library,
    props.tmdbId,
    selections.value,
    props.mode ?? "series",
  )
  submitting.value = false
  if (!res.success || res.data == null) {
    submitFailed.value = true
    return
  }
  emit("done", {fullyIgnored: res.data.fully_ignored})
}

function onKeydown(e: KeyboardEvent): void {
  if (e.key === "Escape") emit("close")
}

onMounted(() => {
  window.addEventListener("keydown", onKeydown)
  void load()
})
onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown))
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-[100] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label="忽略缺失"
    >
      <div
        class="absolute inset-0 bg-black/60 backdrop-blur-sm"
        @click="emit('close')"
      ></div>

      <div
        class="relative flex max-h-[85vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-2xl"
      >
        <header class="flex items-start justify-between gap-3 border-b border-border p-5">
          <div>
            <h2 class="text-base font-semibold text-content">忽略缺失</h2>
            <p class="mt-0.5 line-clamp-1 text-sm text-muted">{{ props.title }}</p>
          </div>
          <button
            type="button"
            @click="emit('close')"
            aria-label="关闭"
            class="-mr-1 -mt-1 rounded-lg p-1.5 text-muted transition hover:bg-surface-2 hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >✕</button>
        </header>

        <div class="flex-1 overflow-y-auto p-5">
          <div v-if="loading" class="space-y-3">
            <div class="skeleton h-5 w-40 rounded"></div>
            <div class="skeleton h-10 w-full rounded-lg"></div>
            <div class="skeleton h-10 w-full rounded-lg"></div>
          </div>

          <div v-else-if="failed" class="space-y-4 text-center">
            <p class="text-sm text-danger">操作失败，请稍后重试</p>
            <button
              type="button"
              @click="load"
              class="rounded-lg border border-border px-3 py-1.5 text-sm text-content transition hover:border-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >重试</button>
          </div>

          <p
            v-else-if="!options || options.seasons.length === 0"
            class="py-6 text-center text-sm text-muted"
          >该剧集暂无可忽略的缺失。</p>

          <div v-else class="space-y-4">
            <div
              v-for="s in options.seasons"
              :key="s.season_num"
              class="rounded-xl border border-border bg-surface-2/40 p-3.5"
            >
              <div class="mb-2 flex items-baseline justify-between gap-2">
                <span class="text-sm font-medium text-content">
                  {{ s.season_name }}
                  <span class="text-muted">· 第 {{ s.season_num }} 季</span>
                </span>
                <span class="shrink-0 text-xs text-muted tabular-nums">
                  已有至 {{ s.local_max_episode }} · 缺 {{ s.episodes.length }} 集
                </span>
              </div>
              <select
                v-model="picked[s.season_num]"
                class="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              >
                <option value="">不忽略（默认）</option>
                <option
                  v-for="ep in s.episodes"
                  :key="ep.num"
                  :value="ep.num"
                >
                  忽略到 第 {{ ep.num }} 集 · {{ ep.name }}
                  {{ ep.num === s.latest_episode ? "（最新 · 整季）" : "" }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <footer class="space-y-3 border-t border-border p-5">
          <p v-if="submitFailed" class="text-sm text-danger">
            提交失败，已保留你的选择，请重试。
          </p>
          <p class="text-xs text-muted">
            仅写入已选的季；当每个缺失季都选到最新集时，海报会立即关闭，否则刷新后更新。
          </p>
          <div class="flex justify-end gap-2">
            <button
              type="button"
              @click="emit('close')"
              class="rounded-lg border border-border px-4 py-2 text-sm text-content transition hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >取消</button>
            <button
              type="button"
              :disabled="!canSubmit"
              @click="submit"
              class="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-accent"
            >{{ submitting ? "提交中…" : "确认忽略" }}</button>
          </div>
        </footer>
      </div>
    </div>
  </Teleport>
</template>
