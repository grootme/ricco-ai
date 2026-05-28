<template>
  <ReactionsUI
    :reactionsCount="reactionsCount"
    :toggleReaction="toggleReaction"
    :toolTipText="toolTipText"
    :standardEmojis="standardEmojis"
    :isLoading="isLoading"
  />
  <div class="mt-2 space-y-2" v-if="batchRequestErrors.length">
    <ErrorMessage v-for="error in batchRequestErrors" :message="error" />
  </div>
</template>
<script setup>
import { useScreenSize } from '@/composables/useScreenSize'
import { defineAsyncComponent, computed } from 'vue'
import { useReactions } from '@/data/reactions'

const screenSize = useScreenSize()
const ReactionsMobile = defineAsyncComponent(() => import('./ReactionsMobile.vue'))
const ReactionsDesktop = defineAsyncComponent(() => import('./ReactionsDesktop.vue'))
const ReactionsUI = computed(() => {
  if (screenSize.width < 640) {
    return ReactionsMobile
  } else {
    return ReactionsDesktop
  }
})
const props = defineProps(['reactions', 'doctype', 'name', 'readOnlyMode'])
const emit = defineEmits(['update:reactions'])

const {
  reactionsCount,
  toggleReaction,
  toolTipText,
  standardEmojis,
  batchRequestErrors,
  isLoading,
} = useReactions({
  reactions: () => props.reactions,
  doctype: () => props.doctype,
  name: () => props.name,
  readOnlyMode: () => props.readOnlyMode,
  onUpdate: (reactions) => emit('update:reactions', reactions),
})
</script>
