<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star, ChatLineRound, View as ViewIcon } from '@element-plus/icons-vue'
import AppHeader from '@/components/common/AppHeader.vue'
import { useUserStore } from '@/stores/user'
import { usersApi } from '@/api/modules/users'
import type { UserPublicInfo } from '@/api/modules/users'
import type { Post } from '@/types/models'
import { fromNow, getFileUrl } from '@/utils/format'

const PAGE_SIZE = 12
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const loadingMore = ref(false)
const followLoading = ref(false)

const user = ref<UserPublicInfo | null>(null)
const postsCount = ref(0)
const likesReceived = ref<number | null>(null)
const collectsReceived = ref<number | null>(null)
const isFollowing = ref(false)
const posts = ref<Post[]>([])
const page = ref(1)
const hasMore = ref(false)

const username = computed(() => route.params.username as string)
const isOwnProfile = computed(() =>
  userStore.isLoggedIn && userStore.currentUser?.username === username.value
)
const avatarUrl = computed(() => {
  if (!user.value?.username) return undefined
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/users/username/${user.value.username}/avatar/view`
})

const coverStyle = computed(() => {
  const cm = user.value?.cover_meta
  if (!cm) return {}
  try {
    const parsed = JSON.parse(cm)
    if (parsed.image) {
      return {
        backgroundImage: parsed.image,
        backgroundSize: parsed.size || 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: parsed.size !== 'cover' ? 'repeat' : 'no-repeat',
      }
    }
  } catch { /* legacy plain string */ }
  return { backgroundImage: cm }
})

async function loadProfile() {
  loading.value = true
  try {
    const [userRes, statsRes] = await Promise.all([
      usersApi.getUserByUsername(username.value),
      usersApi.getUserPublicStats(username.value)
    ])
    user.value = userRes.data
    postsCount.value = statsRes.data?.posts ?? 0
    likesReceived.value = statsRes.data?.likes_received ?? null
    collectsReceived.value = statsRes.data?.collects_received ?? null
    if (!isOwnProfile.value && userStore.isLoggedIn && user.value?.id) {
      const followRes = await usersApi.checkFollowStatus([user.value.id]).catch(() => null)
      isFollowing.value = followRes?.data?.[user.value.id] ?? false
    }
  } catch {
    ElMessage.error('加载用户信息失败')
    router.back()
  } finally {
    loading.value = false
  }
}

async function loadPosts(reset = false) {
  if (reset) { page.value = 1; posts.value = [] }
  loadingMore.value = true
  try {
    const res = await usersApi.getUserPosts(username.value, { page: page.value, page_size: PAGE_SIZE })
    const data = res.data
    posts.value = reset ? data.items : [...posts.value, ...data.items]
    hasMore.value = page.value < data.pages
  } catch { /* 静默 */ } finally {
    loadingMore.value = false
  }
}

async function loadMore() { page.value++; await loadPosts() }

async function handleFollow() {
  if (!userStore.isLoggedIn) {
    router.push({ name: 'Login', query: { redirect: route.fullPath } })
    return
  }
  if (!user.value?.id) return
  followLoading.value = true
  try {
    if (isFollowing.value) {
      await usersApi.unfollowUser(user.value.id)
      isFollowing.value = false
      if (user.value.followers_count !== undefined) user.value.followers_count--
    } else {
      await usersApi.followUser(user.value.id)
      isFollowing.value = true
      if (user.value.followers_count !== undefined) user.value.followers_count++
    }
  } catch { ElMessage.error('操作失败') } finally { followLoading.value = false }
}

// Feed 辅助函数（与 Blog/index.vue 保持一致）
const _BASE = import.meta.env.VITE_API_BASE_URL || ''
function postAvatar(p: Post) {
  return p.author_name ? `${_BASE}/users/username/${p.author_name}/avatar/view` : ''
}
function postCover(p: Post) { return p.cover_image_url ? getFileUrl(p.cover_image_url) : '' }
function postName(p: Post) { return p.author_nickname || p.author_name || '?' }
function postTime(p: Post) { return fromNow(p.published_at || p.created_at) }

onMounted(async () => {
  await loadProfile()
  loadPosts(true)
})
</script>

<template>
  <div class="user-profile-page">
    <AppHeader />

    <div v-if="loading" class="profile-container">
      <el-skeleton :rows="8" animated style="padding: 32px 0" />
    </div>

    <div v-else-if="user" class="profile-container">
      <button class="page-back" @click="router.back()">
        <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="10,3 5,8 10,13"/></svg>
        返回
      </button>

      <!-- 用户卡片 -->
      <div class="user-card">
        <div class="user-cover" :class="{ 'has-custom': !!user.cover_meta }" :style="coverStyle" />
        <div class="user-info-section">
          <div class="avatar-wrap">
            <el-avatar :src="avatarUrl" :size="96" class="user-avatar">
              {{ (user.nickname || user.username || '?')[0].toUpperCase() }}
            </el-avatar>
          </div>
          <h1 class="user-name">
            {{ user.nickname || user.username }}
            <el-tag v-if="user.is_root === 1" type="danger" size="small" style="margin-left:8px">ROOT</el-tag>
            <el-tag v-else-if="user.is_admin === 1" type="warning" size="small" style="margin-left:8px">ADMIN</el-tag>
          </h1>
          <p class="user-uid">@{{ user.username }}</p>
          <p class="user-sig">{{ user.signature || '这个人很懒，什么都没留下' }}</p>
          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-val">{{ postsCount }}</span>
              <span class="stat-lbl">博文</span>
            </div>
            <div class="stat-sep" />
            <div class="stat-item clickable"
              @click="router.push({ name: 'FollowList', params: { username: user!.username, type: 'followers' } })">
              <span class="stat-val">{{ user.followers_count || 0 }}</span>
              <span class="stat-lbl">粉丝</span>
            </div>
            <div class="stat-sep" />
            <div class="stat-item clickable"
              @click="router.push({ name: 'FollowList', params: { username: user!.username, type: 'following' } })">
              <span class="stat-val">{{ user.following_count || 0 }}</span>
              <span class="stat-lbl">关注</span>
            </div>
            <template v-if="likesReceived !== null">
              <div class="stat-sep" />
              <div class="stat-item">
                <span class="stat-val">{{ likesReceived }}</span>
                <span class="stat-lbl">获赞</span>
              </div>
              <div class="stat-sep" />
              <div class="stat-item">
                <span class="stat-val">{{ collectsReceived }}</span>
                <span class="stat-lbl">收藏</span>
              </div>
            </template>
          </div>
          <div class="user-actions">
            <template v-if="!isOwnProfile">
              <button
                class="follow-btn"
                :class="{ 'is-following': isFollowing, 'is-loading': followLoading }"
                :disabled="followLoading"
                @click="handleFollow"
              >
                <span class="btn-default">{{ isFollowing ? '已关注' : '关注' }}</span>
                <span class="btn-hover">取消关注</span>
              </button>
            </template>
            <el-button v-if="isOwnProfile" type="primary" size="small" @click="router.push({ name: 'Space' })">
              编辑资料
            </el-button>
          </div>
        </div>
      </div>

      <!-- 博文列表（feed-item 布局，与发现页一致）-->
      <div class="posts-section">
        <h2 class="section-title">博文</h2>
        <div v-if="loadingMore && posts.length === 0" class="feed-skeleton">
          <el-skeleton v-for="i in 5" :key="i" animated :rows="3" style="margin-bottom:16px" />
        </div>
        <div v-else-if="posts.length > 0" class="feed-list">
          <article v-for="p in posts" :key="p.id" class="feed-item" @click="router.push('/post/'+p.id)">
            <div class="item-hdr">
              <el-avatar :size="22" :src="postAvatar(p)">{{ postName(p)[0]?.toUpperCase() }}</el-avatar>
              <span class="item-author" @click.stop="p.author_name && router.push('/u/'+p.author_name)">{{ postName(p) }}</span>
              <span class="item-time">{{ postTime(p) }}</span>
            </div>
            <div class="item-body">
              <div class="item-text">
                <h3 class="item-title">{{ p.title }}</h3>
                <p v-if="p.summary" class="item-summary">{{ p.summary }}</p>
              </div>
              <img v-if="postCover(p)" :src="postCover(p)" :alt="p.title" class="item-cover" loading="lazy" />
            </div>
            <div class="item-ftr">
              <span v-if="(p as any).status === 'draft'" class="item-status draft">草稿</span>
              <span v-else-if="(p as any).is_hidden" class="item-status hidden">已隐藏</span>
              <span class="item-stat"><el-icon :size="12"><Star /></el-icon>{{ p.like_count }}</span>
              <span class="item-stat"><el-icon :size="12"><ChatLineRound /></el-icon>{{ p.comment_count }}</span>
              <span class="item-stat"><el-icon :size="12"><ViewIcon /></el-icon>{{ p.view_count }}</span>
              <span v-if="p.category_name" class="item-tag">{{ p.category_name }}</span>
            </div>
          </article>
        </div>
        <el-empty v-else description="暂无公开博文" />
        <div v-if="hasMore" class="load-more">
          <el-button :loading="loadingMore" @click="loadMore">加载更多</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.user-profile-page { min-height: 100vh; background: var(--el-bg-color-page); }
.profile-container { max-width: 1100px; margin: 0 auto; padding: $spacing-lg $spacing-md; }
.user-card { background: var(--el-bg-color); border-radius: $radius-xl; overflow: hidden; box-shadow: $shadow-md; margin-bottom: $spacing-lg; }
.user-cover {
  height: 180px;
  background: linear-gradient(135deg, $color-primary 0%, $color-secondary 100%);
  background-size: cover;
  background-position: center;
  &.has-custom { background-color: transparent; }
}
.user-info-section { padding: 0 $spacing-xl $spacing-lg; text-align: center; }
.avatar-wrap { margin-top: -48px; margin-bottom: $spacing-md; display: flex; justify-content: center; }
.user-avatar {
  border: 4px solid var(--el-bg-color);
  font-size: 36px; font-weight: bold;
  background: linear-gradient(135deg, $color-primary, $color-secondary);
  color: white;
  line-height: 1;
}
.user-name {
  font-size: $font-xl; font-weight: 700; margin: 0 0 4px;
  display: flex; align-items: center; justify-content: center;
  color: var(--el-text-color-primary);
}
.user-uid { font-size: $font-sm; color: var(--el-text-color-secondary); margin: 0 0 4px; }
.user-sig { font-size: $font-sm; color: var(--el-text-color-secondary); margin: 0 0 $spacing-md; line-height: 1.6; }
.user-stats {
  display: flex; align-items: center; justify-content: center; gap: $spacing-xl;
  padding: $spacing-md 0;
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
  margin-bottom: $spacing-md;
}
.stat-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  &.clickable { cursor: pointer; &:hover .stat-val { color: $color-primary; } }
}
.stat-val { font-size: $font-xl; font-weight: 700; color: var(--el-text-color-primary); line-height: 1; }
.stat-lbl { font-size: $font-xs; color: var(--el-text-color-secondary); }
.stat-sep { width: 1px; height: 28px; background: var(--el-border-color-light); }
.user-actions { display: flex; align-items: center; justify-content: center; gap: $spacing-sm; }

.follow-btn {
  display: inline-flex;
  align-items: center;
  padding: 8px 22px;
  border-radius: $radius-full;
  border: 1.5px solid $color-primary;
  background: $color-primary;
  color: #fff;
  font-size: $font-sm;
  font-weight: 500;
  cursor: pointer;
  transition: background $transition-base, border-color $transition-base, color $transition-base;

  .btn-hover { display: none; }

  &:hover:not(.is-loading) {
    background: rgba(90, 103, 216, 0.85);
  }

  &.is-following {
    background: transparent;
    border-color: var(--el-border-color);
    color: var(--el-text-color-regular);

    .btn-default { display: inline; }
    .btn-hover { display: none; }

    &:hover:not(.is-loading) {
      border-color: var(--el-color-danger);
      color: var(--el-color-danger);
      background: rgba(239, 68, 68, 0.06);

      .btn-default { display: none; }
      .btn-hover { display: inline; }
    }
  }

  &.is-loading {
    opacity: 0.65;
    cursor: not-allowed;
  }
}

.posts-section {
  background: var(--el-bg-color);
  border-radius: $radius-xl;
  padding: $spacing-lg;
  box-shadow: $shadow-md;
}

.section-title {
  font-size: $font-base;
  font-weight: 600;
  margin: 0 0 $spacing-md;
  color: var(--el-text-color-primary);
}

.feed-list { display: flex; flex-direction: column; }
.feed-item {
  padding: 20px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  &:last-child { border-bottom: none; }
}
.item-hdr { display: flex; align-items: center; gap: 6px; margin-bottom: 10px; }
.item-author { font-size: 13px; font-weight: 500; color: var(--el-text-color-secondary); cursor: pointer; &:hover { color: $color-primary; } }
.item-time { font-size: 12px; color: var(--el-text-color-placeholder); margin-left: auto; }
.item-body { display: flex; align-items: flex-start; gap: $spacing-md; margin-bottom: 10px; }
.item-text { flex: 1; min-width: 0; }
.item-title {
  font-size: 17px; font-weight: 600; color: var(--el-text-color-primary); margin: 0 0 6px;
  overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  line-height: 1.45; transition: color $transition-fast; cursor: pointer;
  &:hover { color: $color-primary; }
}
.item-summary { font-size: 13px; color: var(--el-text-color-secondary); margin: 0; line-height: 1.6; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.item-cover { width: 100px; height: 72px; border-radius: $radius-sm; object-fit: cover; flex-shrink: 0; border: 1px solid var(--el-border-color-lighter); }
.item-ftr { display: flex; align-items: center; gap: $spacing-md; }
.item-stat { display: flex; align-items: center; gap: 3px; font-size: 12px; color: var(--el-text-color-placeholder); }
.item-tag { font-size: 11px; color: var(--el-text-color-secondary); border: 1px solid var(--el-border-color-light); border-radius: $radius-sm; padding: 1px 6px; margin-left: auto; }

.load-more { display: flex; justify-content: center; margin-top: $spacing-md; }

.page-back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px 5px 8px;
  margin-bottom: $spacing-sm;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  font-size: $font-sm;
  border-radius: $radius-md;
  cursor: pointer;
  transition: border-color $transition-fast, color $transition-fast, background $transition-fast;
  &:hover { border-color: $color-primary; color: $color-primary; }
}

.item-status {
  font-size: 11px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: $radius-sm;
  &.draft  { background: rgba(245,158,11,.1); color: #d97706; border: 1px solid rgba(245,158,11,.2); }
  &.hidden { background: rgba(239,68,68,.08); color: #ef4444; border: 1px solid rgba(239,68,68,.15); }
}

@media (max-width: 560px) {
  .profile-container { padding: $spacing-sm; }
  .user-info-section { padding: 0 $spacing-md $spacing-md; }
  .user-stats { gap: $spacing-lg; }
  .item-cover { width: 72px; height: 54px; }
  .item-title { font-size: $font-base; }
}
</style>
