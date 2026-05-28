import { GPPinnedProject } from '@/types/doctypes'
import { useList } from 'frappe-ui'

export const pinnedSpaces = useList<GPPinnedProject>({
  doctype: 'GP Pinned Project',
  fields: ['project', 'team', 'user', 'name'],
  filters: {
    'project.archived_at': ['=', null],
  },
  initialData: [],
  orderBy: 'creation desc',
  limit: 99999,
  cacheKey: 'pinnedSpaces',
})

export function isPinned(spaceId: string) {
  return pinnedSpaces.data?.some((p) => p.project.toString() === spaceId.toString())
}

export function pinSpace(spaceId: string) {
  return pinnedSpaces.insert.submit({
    project: spaceId,
  })
}

export function unpinSpace(spaceId: string) {
  let pin = pinnedSpaces.data?.find((p) => p.project.toString() === spaceId.toString())
  if (pin) {
    return pinnedSpaces.delete.submit({ name: pin.name.toString() })
  }
  return Promise.resolve()
}

export function isPinActionLoading(spaceId: string) {
  let pin = pinnedSpaces.data?.find((p) => p.project.toString() === spaceId.toString())
  if (pin) {
    return pinnedSpaces.delete.loading && pinnedSpaces.delete.params?.name === pin.name.toString()
  } else {
    return pinnedSpaces.insert.loading && pinnedSpaces.insert.params?.project === spaceId.toString()
  }
}
