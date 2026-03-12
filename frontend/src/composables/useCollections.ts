import { ref } from 'vue'
import { interactionsApi } from '@/api/modules/interactions'
import type { Post } from '@/types/models'

export function useCollections() {
  const showFavorites = ref(false)
  const collectionFiles = ref<Post[]>([])
  const collectionsLoading = ref(false)
  const collectionsLoadingMore = ref(false)
  const collectionsPage = ref(1)
  const collectionsHasMore = ref(false)

  async function loadCollections(reset = true) {
    if (reset) { collectionsPage.value = 1; collectionFiles.value = []; collectionsLoading.value = true }
    else collectionsLoadingMore.value = true
    try {
      const res = await interactionsApi.getMyPostCollections(collectionsPage.value, 20)
      const items: Post[] = res.data?.items || []
      if (reset) collectionFiles.value = items
      else collectionFiles.value.push(...items)
      if (res.data) {
        collectionsHasMore.value = collectionsPage.value < res.data.pages
      }
    } catch { /* 静默失败 */ } finally {
      collectionsLoading.value = false
      collectionsLoadingMore.value = false
    }
  }

  async function loadMoreCollections() {
    collectionsPage.value++
    await loadCollections(false)
  }

  function toggleFavorites() {
    showFavorites.value = !showFavorites.value
    if (showFavorites.value && collectionFiles.value.length === 0) loadCollections()
  }

  return {
    showFavorites, collectionFiles, collectionsLoading, collectionsLoadingMore,
    collectionsPage, collectionsHasMore,
    loadCollections, loadMoreCollections, toggleFavorites,
  }
}
