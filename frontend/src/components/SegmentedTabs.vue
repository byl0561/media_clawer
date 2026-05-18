<script setup lang="ts">
interface SegmentTab {
  name: string;
  count: number | null;
}

defineProps<{ tabs: SegmentTab[]; modelValue: number }>()
defineEmits<{ "update:modelValue": [value: number] }>()
</script>

<template>
  <div class="inline-flex flex-wrap gap-1 rounded-xl border border-border bg-surface p-1">
    <button
      v-for="(tab, i) in tabs"
      :key="tab.name"
      type="button"
      @click="$emit('update:modelValue', i)"
      class="rounded-lg px-3.5 py-1.5 text-sm font-medium transition"
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
