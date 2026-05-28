import { useLocalStorage } from '@vueuse/core'

export type PreferredHomePage = 'Discussions' | 'Spaces'

export function usePreferredHomePage() {
  return useLocalStorage<PreferredHomePage>('preferredHomePage', 'Discussions')
}
