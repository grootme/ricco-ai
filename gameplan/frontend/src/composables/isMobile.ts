import { computed } from 'vue'
import { useScreenSize } from './useScreenSize'

export function isMobile() {
  const size = useScreenSize()
  return computed(() => size.width < 640)
}
