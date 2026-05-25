<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, ref} from "vue";
import type {AliasTarget, BindLibrary} from "@/types/api";
import {aliasTargets, bindAlias} from "@/http/api";

// The "最新" tab lists rank items missing locally. When the local nfo has a
// non-chinese <title> (TMDB没收录中文翻译时常见) text-similarity match in
// the backend fails, even though the user owns the show. This dialog lets
// the user say "this rank item is actually that local item", appending the
// rank title to the local alias.txt so the next diff matches without code
// changes.

const props = defineProps<{
  library: BindLibrary;
  /** The rank item's title — written as a new alias on the chosen local item. */
  alias: string;
  /** Display title (same as alias here, kept separate for future flexibility). */
  title: string;
}>()

const emit = defineEmits<{
  close: [];
  done: [];
}>()

const loading = ref(true)
const failed = ref(false)
const submitFailed = ref(false)
const submitting = ref(false)
const targets = ref<AliasTarget[]>([])
const query = ref("")
const selectedId = ref<number | null>(null)

const filtered = computed<AliasTarget[]>(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return targets.value
  return targets.value.filter(t =>
    t.title.toLowerCase().includes(q) || String(t.year).includes(q)
  )
})
const canSubmit = computed(() => selectedId.value !== null && !submitting.value)

async function load(): Promise<void> {
  loading.value = true
  failed.value = false
  const res = await aliasTargets(props.library)
  if (!res.success || res.data == null) {
    failed.value = true
  } else {
    targets.value = res.data
  }
  loading.value = false
}

async function submit(): Promise<void> {
  if (!canSubmit.value || selectedId.value === null) return
  submitting.value = true
  submitFailed.value = false
  const res = await bindAlias(props.library, selectedId.value, [props.alias])
  submitting.value = false
  if (!res.success || res.data == null) {
    submitFailed.value = true
    return
  }
  emit("done")
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
      aria-label="绑定本地"
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
            <h2 class="text-base font-semibold text-content">绑定到本地</h2>
            <p class="mt-0.5 line-clamp-1 text-sm text-muted">
              将「{{ props.title }}」作为别名追加到所选本地条目
            </p>
          </div>
          <button
            type="button"
            @click="emit('close')"
            aria-label="关闭"
            class="-mr-1 -mt-1 rounded-lg p-1.5 text-muted transition hover:bg-surface-2 hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >✕</button>
        </header>

        <div class="border-b border-border p-3">
          <input
            v-model="query"
            type="text"
            placeholder="按标题或年份搜索本地条目"
            class="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-content placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          />
        </div>

        <div class="flex-1 overflow-y-auto p-3">
          <div v-if="loading" class="space-y-2">
            <div class="skeleton h-10 w-full rounded-lg"></div>
            <div class="skeleton h-10 w-full rounded-lg"></div>
            <div class="skeleton h-10 w-full rounded-lg"></div>
          </div>

          <div v-else-if="failed" class="space-y-4 py-6 text-center">
            <p class="text-sm text-danger">加载失败，请稍后重试</p>
            <button
              type="button"
              @click="load"
              class="rounded-lg border border-border px-3 py-1.5 text-sm text-content transition hover:border-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >重试</button>
          </div>

          <p
            v-else-if="targets.length === 0"
            class="py-8 text-center text-sm text-muted"
          >本地库为空。</p>

          <p
            v-else-if="filtered.length === 0"
            class="py-8 text-center text-sm text-muted"
          >没有匹配「{{ query }}」的本地条目。</p>

          <ul v-else class="space-y-1">
            <li v-for="t in filtered" :key="t.tmdb_id">
              <button
                type="button"
                @click="selectedId = t.tmdb_id"
                class="flex w-full items-baseline gap-3 rounded-lg border px-3 py-2 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                :class="selectedId === t.tmdb_id
                  ? 'border-accent bg-accent/10 text-content'
                  : 'border-border bg-surface-2/40 text-content hover:border-accent/50'"
              >
                <span class="line-clamp-1 flex-1 text-sm">{{ t.title }}</span>
                <span class="shrink-0 text-xs text-muted tabular-nums">{{ t.year }}</span>
                <span class="shrink-0 text-[10px] text-muted tabular-nums">tmdb {{ t.tmdb_id }}</span>
              </button>
            </li>
          </ul>
        </div>

        <footer class="space-y-3 border-t border-border p-5">
          <p v-if="submitFailed" class="text-sm text-danger">
            绑定失败，已保留你的选择，请重试。
          </p>
          <p class="text-xs text-muted">
            绑定后会在该本地条目目录的 alias.txt 追加一行，已存在则跳过。
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
            >{{ submitting ? "提交中…" : "确认绑定" }}</button>
          </div>
        </footer>
      </div>
    </div>
  </Teleport>
</template>
