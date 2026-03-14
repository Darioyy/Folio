import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { postsApi } from '@/api/modules/posts'
import { useUserStore } from '@/stores/user'
import type { Post } from '@/types/models'

export type BlogTabType = 'recommend' | 'following' | 'column'

const PAGE_SIZE = 15

export function useBlogFeed() {
  const router = useRouter()
  const userStore = useUserStore()

  const activeTab = ref<BlogTabType>('recommend')
  const posts = ref<Post[]>([])
  const loading = ref(false)
  const loadingMore = ref(false)
  const page = ref(1)
  const hasMore = ref(false)
  const sortMode = ref<'latest' | 'hot'>('hot')
  const selectedCategory = ref<number | null>(null)

  async function loadPosts(reset = false) {
    if (reset) {
      page.value = 1
      loading.value = true
      // 不立即清空 posts，等数据回来后一次性替换，避免内容区高度骤降导致抖动
    } else {
      loadingMore.value = true
    }
    try {
      if (activeTab.value === 'following') {
        const res = await postsApi.getFollowingPosts({ page: page.value, page_size: PAGE_SIZE })
        if (res.data) {
          posts.value = reset ? res.data.items : [...posts.value, ...res.data.items]
          hasMore.value = page.value < res.data.pages
        }
      } else {
        const res = await postsApi.getPaginatedList({
          page: page.value,
          limit: PAGE_SIZE,
          sort: sortMode.value,
          ...(activeTab.value === 'column' && selectedCategory.value ? { category_id: selectedCategory.value } : {}),
        })
        posts.value = reset ? res.items : [...posts.value, ...res.items]
        hasMore.value = page.value < (res.pagination as any).pages
      }
    } catch { /* silent */ } finally {
      loading.value = false
      loadingMore.value = false
    }
  }

  async function switchTab(tab: BlogTabType) {
    if (activeTab.value === tab) return
    if (tab === 'following' && !userStore.isLoggedIn) {
      router.push({ name: 'Login', query: { redirect: '/blog' } })
      return
    }
    activeTab.value = tab
    selectedCategory.value = null
    // 推荐页用热门排序，其他页用最新排序
    sortMode.value = tab === 'recommend' ? 'hot' : 'latest'
    await loadPosts(true)
  }

  async function loadMore() {
    page.value++
    await loadPosts()
  }

  async function selectCategory(id: number) {
    selectedCategory.value = selectedCategory.value === id ? null : id
    activeTab.value = 'column'
    await loadPosts(true)
  }

  return {
    activeTab, posts, loading, loadingMore, hasMore, sortMode, selectedCategory,
    loadPosts, switchTab, loadMore, selectCategory,
  }
}
