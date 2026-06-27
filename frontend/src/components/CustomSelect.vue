<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  modelValue: number | string
  options: { value: number | string; label: string }[]
  placeholder?: string
  disabled?: boolean
}>()
const emit = defineEmits<{ 'update:modelValue': [val: number | string] }>()

const open = ref(false)
const triggerEl = ref<HTMLElement | null>(null)
const menuEl   = ref<HTMLElement | null>(null)
const menuStyle = ref<Record<string, string>>({})

const selectedLabel = computed(() =>
  props.options.find(o => o.value === props.modelValue)?.label ?? ''
)
const isEmpty = computed(() => props.modelValue === '' || props.modelValue == null)

function toggle() {
  if (props.disabled) return
  open.value ? close() : openMenu()
}
function openMenu() {
  open.value = true
  nextTick(updatePos)
}
function close() { open.value = false }
function pick(val: number | string) { emit('update:modelValue', val); close() }

const MENU_MAX_H = 260
function updatePos() {
  if (!triggerEl.value) return
  const r = triggerEl.value.getBoundingClientRect()
  const below = window.innerHeight - r.bottom
  const above  = below < MENU_MAX_H + 8
  menuStyle.value = {
    position: 'fixed',
    left:  `${r.left}px`,
    width: `${r.width}px`,
    zIndex: '300',
    ...(above
      ? { bottom: `${window.innerHeight - r.top + 4}px`, top: 'auto' }
      : { top: `${r.bottom + 4}px`, bottom: 'auto' }),
  }
}

function onPointerDown(e: PointerEvent) {
  if (!open.value) return
  if (triggerEl.value?.contains(e.target as Node)) return
  if (!menuEl.value?.contains(e.target as Node)) close()
}
function onKey(e: KeyboardEvent) { if (e.key === 'Escape') close() }
function onScroll() { if (open.value) updatePos() }

onMounted(() => {
  document.addEventListener('pointerdown', onPointerDown)
  document.addEventListener('keydown', onKey)
  window.addEventListener('resize', onScroll)
  window.addEventListener('scroll', onScroll, true)
})
onUnmounted(() => {
  document.removeEventListener('pointerdown', onPointerDown)
  document.removeEventListener('keydown', onKey)
  window.removeEventListener('resize', onScroll)
  window.removeEventListener('scroll', onScroll, true)
})
</script>

<template>
  <!-- 触发按钮 -->
  <div
    ref="triggerEl"
    role="combobox"
    :aria-expanded="open"
    :aria-disabled="disabled"
    tabindex="0"
    class="relative flex w-full cursor-pointer select-none items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm transition"
    :class="[
      disabled ? 'cursor-not-allowed opacity-50' : 'hover:border-accent/50',
      open ? 'border-accent/70 ring-2 ring-accent/30 outline-none' : '',
    ]"
    @click="toggle"
    @keydown.enter.prevent="toggle"
    @keydown.space.prevent="toggle"
  >
    <span class="flex-1 truncate" :class="isEmpty ? 'text-muted' : 'text-content'">
      {{ isEmpty ? (placeholder ?? '选择…') : selectedLabel }}
    </span>
    <svg
      class="h-4 w-4 shrink-0 text-muted transition-transform duration-150"
      :class="{ 'rotate-180': open }"
      viewBox="0 0 20 20" fill="none"
      stroke="currentColor" stroke-width="1.6"
      stroke-linecap="round" stroke-linejoin="round"
      aria-hidden="true"
    >
      <path d="M6 8l4 4 4-4"/>
    </svg>
  </div>

  <!-- 下拉菜单（Teleport 到 body 避免 overflow 裁剪）-->
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="opacity-0 scale-95 -translate-y-1"
      leave-active-class="transition duration-75 ease-in"
      leave-to-class="opacity-0 scale-95 -translate-y-1"
    >
      <div
        v-if="open"
        ref="menuEl"
        :style="menuStyle"
        class="overflow-hidden rounded-xl border border-border bg-surface-2 shadow-2xl"
        style="max-height: 260px; overflow-y: auto;"
      >
        <div
          v-for="opt in options"
          :key="opt.value"
          role="option"
          :aria-selected="opt.value === modelValue"
          class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm transition"
          :class="
            opt.value === modelValue
              ? 'bg-accent/10 text-accent font-medium'
              : 'text-content hover:bg-white/5'
          "
          @click="pick(opt.value)"
        >
          <svg
            v-if="opt.value === modelValue"
            class="h-3.5 w-3.5 shrink-0"
            viewBox="0 0 16 16" fill="none"
            stroke="currentColor" stroke-width="2.2"
            stroke-linecap="round" stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M3 8l4 4 6-7"/>
          </svg>
          <span v-else class="h-3.5 w-3.5 shrink-0"/>
          <span class="truncate">{{ opt.label }}</span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
