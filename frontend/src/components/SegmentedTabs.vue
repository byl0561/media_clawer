<script setup lang="ts">
interface SegmentTab {
  name: string;
  count: number | null;
}

const props = defineProps<{ tabs: SegmentTab[]; modelValue: number }>()
const emit = defineEmits<{ "update:modelValue": [value: number] }>()

// Roving-tabindex arrow-key navigation (ARIA tablist pattern): move
// selection and focus the newly-selected tab, wrapping at both ends.
function onKeydown(e: KeyboardEvent): void {
  if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return
  e.preventDefault()
  const n = props.tabs.length
  if (n === 0) return
  const dir = e.key === "ArrowRight" ? 1 : -1
  const next = (props.modelValue + dir + n) % n
  emit("update:modelValue", next)
  const tabs = (e.currentTarget as HTMLElement).querySelectorAll<HTMLButtonElement>(
    '[role="tab"]',
  )
  tabs[next]?.focus()
}
</script>

<template>
  <div
    role="tablist"
    @keydown="onKeydown"
    class="inline-flex flex-wrap gap-1 rounded-xl border border-border bg-surface p-1"
  >
    <button
      v-for="(tab, i) in tabs"
      :key="tab.name"
      type="button"
      role="tab"
      :aria-selected="modelValue === i"
      :tabindex="modelValue === i ? 0 : -1"
      @click="$emit('update:modelValue', i)"
      class="rounded-lg px-3.5 py-1.5 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      :class="modelValue === i ? 'bg-accent text-white' : 'text-muted hover:text-content'"
    >
      {{ tab.name }}
      <span
        v-if="tab.count != null"
        class="ml-1 rounded-md px-1.5 text-xs tabular-nums"
        :class="modelValue === i ? 'bg-white/20' : 'bg-surface-2 text-muted'"
      >{{ tab.count }}</span>
    </button>
  </div>
</template>
