<script setup lang="ts">
import {computed} from "vue";
import {useOverviewData} from "@/hooks/useOverviewData";
import MediaSummaryCard from "@/components/MediaSummaryCard.vue";

const {cards, totals, anyLoading} = useOverviewData()

const stats = computed(() => [
  {label: "待维护合计", value: totals.value.all, primary: true},
  {label: "缺失最新", value: totals.value.latest, primary: false},
  {label: "缺失续集", value: totals.value.sequel, primary: false},
  {label: "已过时", value: totals.value.outdated, primary: false},
  {label: "缺失字幕", value: totals.value.subtitle, primary: false},
  {label: "缺失歌词", value: totals.value.lyric, primary: false},
])
</script>

<template>
  <section class="mx-auto max-w-6xl px-4 py-8 sm:px-6">
    <header
      class="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-accent-soft to-surface p-6 sm:p-8"
    >
      <h1 class="text-2xl font-bold text-content">库维护概览</h1>
      <p class="mt-1 text-sm text-muted">榜单与本地库的差异一览，点击卡片查看明细</p>

      <div class="mt-7 grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-3 lg:grid-cols-6">
        <div v-for="s in stats" :key="s.label">
          <div v-if="anyLoading" class="skeleton rounded" :class="s.primary ? 'h-10 w-20' : 'h-8 w-14'"></div>
          <div
            v-else
            class="font-bold tabular-nums"
            :class="[
              s.primary ? 'text-4xl' : 'text-2xl',
              s.primary
                ? s.value > 0
                  ? 'text-accent'
                  : 'text-success'
                : 'text-content',
            ]"
          >{{ s.value }}</div>
          <div class="mt-1 text-xs text-muted">{{ s.label }}</div>
        </div>
      </div>

      <p
        v-if="!anyLoading && totals.all === 0"
        class="mt-5 inline-flex items-center gap-1.5 rounded-full bg-success/15 px-3 py-1 text-sm font-medium text-success"
      >
        ✓ 所有媒体库均已与榜单同步
      </p>
    </header>

    <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <MediaSummaryCard
        v-for="card in cards"
        :key="card.entry.key"
        :entry="card.entry"
        :status="card.status"
        :step="card.step"
        :counts="card.counts"
      />
    </div>
  </section>
</template>
