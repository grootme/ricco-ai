import { useCall, useDoctype } from 'frappe-ui'
import { GPProject } from '@/types/doctypes'
import { reactive } from 'vue'

interface ProjectUnreadCount {
  [spaceId: string]: number
}

const unreadCounts = reactive<ProjectUnreadCount>({})

const unreadCountByProjects = useCall<ProjectUnreadCount, { projects?: string[] }>({
  url: '/api/v2/method/GP Unread Record/get_unread_count',
  method: 'POST',
  immediate: false,
  onSuccess(data) {
    for (const [spaceId, count] of Object.entries(data)) {
      unreadCounts[spaceId] = count
    }
  },
})

// load unread count for all projects once
unreadCountByProjects.submit({})

export function getProjectUnreadCount(spaceId: string) {
  return unreadCounts[spaceId] ?? 0
}

const Project = useDoctype<GPProject>('GP Project')

export function markSpaceAsRead(spaceId: string) {
  return Project.runDocMethod
    .submit({
      name: spaceId,
      method: 'mark_all_as_read',
    })
    .then(() => {
      return refreshUnreadCountForProjects([spaceId])
    })
}

export function markSpacesAsRead(spaceIds: string[]) {
  return Project.runMethod
    .submit({
      method: 'mark_all_as_read',
      params: {
        spaces: spaceIds,
      },
    })
    .then(() => {
      return refreshUnreadCountForProjects(spaceIds)
    })
}

export function refreshUnreadCountForProjects(projects: string[]) {
  return unreadCountByProjects.submit({ projects })
}
