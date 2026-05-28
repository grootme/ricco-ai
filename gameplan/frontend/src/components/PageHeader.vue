<template>
  <header ref="headerRef" :class="headerClasses" @click="handleHeaderClick">
    <div class="flex items-center justify-between">
      <slot></slot>
    </div>
  </header>
  <div v-if="fixedOnMobile" class="sm:hidden" :style="spacerStyle" aria-hidden="true" />
</template>

<script setup lang="ts">
import { computed, useTemplateRef } from 'vue'
import { useElementSize } from '@vueuse/core'
import { scrollToTop } from '@/utils/scrollContainer'

interface Props {
  fixedOnMobile?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  fixedOnMobile: true,
})

const headerRef = useTemplateRef('headerRef')
const { height } = useElementSize(headerRef)

const headerClasses = computed(() => {
  const base = 'z-10 border-b bg-surface-white px-3 sm:px-5 flex flex-col justify-center min-h-12'
  const position = props.fixedOnMobile ? 'fixed inset-x-0 top-0 sm:sticky sm:top-0' : 'sticky top-0'

  return [base, position]
})

const spacerStyle = computed(() => ({
  height: `${height.value || 0}px`,
}))

function handleHeaderClick(event: MouseEvent) {
  const target = event.target as HTMLElement | null
  if (!target) return
  if (
    target.closest(
      'a, button, input, textarea, select, label, [role="button"], [data-no-scroll-top]',
    )
  ) {
    return
  }
  scrollToTop()
}
</script>
