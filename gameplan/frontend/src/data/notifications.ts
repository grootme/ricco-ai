import { useCall } from 'frappe-ui'

export let unreadNotifications = useCall({
  cacheKey: 'Unread Notifications Count',
  url: '/api/v2/method/gameplan.api.unread_notifications',
  initialData: 0,
})
