<template>
  <router-view v-slot="{ Component, route }">
    <PageHeader v-if="!route.meta.hideHeader">
      <div class="flex w-full items-center justify-between gap-3">
        <div class="flex items-center space-x-2">
          <SpaceBreadcrumbs :spaceId="spaceId" />
          <Badge v-if="space?.archived_at">Archived</Badge>
        </div>
        <SpaceHeaderActionsTarget />
      </div>
    </PageHeader>
    <component class="flex-1" v-if="space" :is="Component" :space="space" />
    <div class="body-container pt-5" v-if="spaceList.isFinished && !space">
      <EmptyStateBox>
        <div class="text-ink-gray-6">Page not found</div>
      </EmptyStateBox>
    </div>
  </router-view>
</template>
<script setup lang="ts">
import { onMounted } from 'vue'
import { useDoctype } from 'frappe-ui'
import SpaceHeaderActionsTarget from '@/components/SpaceHeaderActionsTarget.vue'
import { useSpace, spaces as spaceList } from '@/data/spaces'
import { GPProject } from '@/types/doctypes'
import EmptyStateBox from '@/components/EmptyStateBox.vue'
import SpaceBreadcrumbs from '@/components/SpaceBreadcrumbs.vue'

const props = defineProps<{
  spaceId: string
}>()

const spaces = useDoctype<GPProject>('GP Project')
const space = useSpace(() => props.spaceId)

onMounted(() => {
  spaces.runDocMethod.submit({
    method: 'track_visit',
    name: props.spaceId,
  })
})
</script>
