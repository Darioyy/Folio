<template>
  <div class="following-page">
    <div class="following-container">
      <div class="following-layout">
        <!-- 左侧：博文流 -->
        <main class="feed-main">
          <div class="section-header">
            <h2 class="section-title">关注的博文</h2>
          </div>

          <div v-if="loading && posts.length === 0" class="posts-grid">
            <el-skeleton v-for="i in 6" :key="i" animated :rows="4" />
          </div>
          <div v-else-if="posts.length > 0" class="posts-grid">
            <PostCard v-for="post in posts" :key="post.id" :post="post" />
          </div>
          <el-empty v-else description="还没有关注的博文，去发现更多创作者吧" :image-size="80">
            <el-button type="primary" @click="$router.push('/blog')">去发现</el-button>
          </el-empty>

          <div v-if="hasMore" class="load-more">
            <el-button text :loading="loadingMore" @click="loadMore">加载更多</el-button>
          </div>
        </main>

        <!-- 右侧：关注列表 -->
        <aside class="following-sidebar">
          <div class="sidebar-card">
            <div class="sidebar-title">我的关注</div>
            <div v-if="followingLoading" class="sidebar-loading">
              <el-skeleton :rows="3" animated />
            </div>
            <div v-else-if="followingUsers.length > 0" class="sidebar-users">
              <div
                v-for="u in followingUsers"
                :key="u.id"
                class="sidebar-user"
                @click="$router.push('/u/' + u.username)"
              >
                <el-avatar :size="36" :src="getAvatarUrl(u.username)">
                  {{ (u.nickname || u.username)[0] }}
                </el-avatar>
                <span class="sidebar-user-name">{{ u.nickname || u.username }}</span>
              </div>
            </div>
            <div v-else class="sidebar-empty">还没有关注任何人</div>
            <el-button
              v-if="followingTotal > followingUsers.length"
              text
              class="view-all-btn"
              @click="$router.push('/follows/' + userStore.currentUser?.username + '/following')"
            >
              查看全部 {{ followingTotal }}
            </el-button>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PostCard from '@/components/business/PostCard.vue'
import { postsApi } from '@/api/modules/posts'
import { usersApi } from '@/api/modules/users'
import { useUserStore } from '@/stores/user'
import type { Post } from '@/types/models'

defineOptions({ name: 'FollowingView' })

const userStore = useUserStore()

const posts = ref<Post[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(false)

const followingUsers = ref<any[]>([])
const followingLoading = ref(false)
const followingTotal = ref(0)

function getAvatarUrl(username: string) {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/users/username/${username}/avatar/view`
}

async function loadPosts(reset = true) {
  if (reset) {
    loading.value = true
    page.value = 1
    posts.value = []
  } else {
    loadingMore.value = true
  }
  try {
    const res = await postsApi.getFollowingPosts({ page: page.value, page_size: 12 })
    if (res.data) {
      const items = res.data.items || []
      if (reset) posts.value = items
      else posts.value.push(...items)
      hasMore.value = page.value < res.data.pages
    }
  } catch { /* 静默 */ } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function loadFollowing() {
  const userId = userStore.currentUser?.id
  if (!userId) return
  followingLoading.value = true
  try {
    const res = await usersApi.getUserFollowing(userId, 1, 10)
    if (res.data) {
      followingUsers.value = res.data.items || []
      followingTotal.value = res.data.total || 0
    }
  } catch { /* 静默 */ } finally {
    followingLoading.value = false
  }
}

function loadMore() {
  page.value++
  loadPosts(false)
}

onMounted(() => {
  loadPosts()
  loadFollowing()
})
</script>

<style scoped lang="scss">
.following-page {
  min-height: 100vh;
  background: var(--el-bg-color-page);
}

.following-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: $spacing-lg $spacing-md;
}

.following-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: $spacing-lg;
  align-items: start;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;

    .following-sidebar {
      order: -1;
    }
  }
}

.section-header {
  margin-bottom: $spacing-lg;
}

.section-title {
  font-size: $font-xl;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0;
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-md;
  margin-bottom: $spacing-lg;

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.load-more {
  display: flex;
  justify-content: center;
  padding: $spacing-md 0;
}

// 右侧边栏
.following-sidebar {
  position: sticky;
  top: 80px;
}

.sidebar-card {
  background: var(--el-bg-color);
  border-radius: $radius-xl;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
}

.sidebar-title {
  font-size: $font-base;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: $spacing-md;
}

.sidebar-users {
  display: flex;
  flex-direction: column;
  gap: $spacing-xs;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-xs;
  border-radius: $radius-md;
  cursor: pointer;
  transition: background $transition-fast;

  &:hover {
    background: var(--el-fill-color-light);
  }
}

.sidebar-user-name {
  font-size: $font-sm;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-loading,
.sidebar-empty {
  color: var(--el-text-color-secondary);
  font-size: $font-sm;
  padding: $spacing-xs 0;
}

.view-all-btn {
  width: 100%;
  margin-top: $spacing-sm;
  font-size: $font-xs;
}
</style>
