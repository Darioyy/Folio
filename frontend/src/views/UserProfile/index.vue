<template>
  <div class="user-profile-page">
    <AppHeader />

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="user" class="profile-container">
      <!-- 用户信息卡片 -->
      <div class="user-card">
        <div class="user-cover"></div>
        <div class="user-info-section">
          <div class="avatar-wrapper">
            <el-avatar :src="avatarUrl" :size="100" class="user-avatar">
              {{ displayName }}
            </el-avatar>
          </div>

          <div class="user-details">
            <div class="user-header">
              <h1 class="user-name">
                {{ user.nickname || user.username }}
                <el-tag v-if="user.is_root === 1" type="danger" size="small" style="margin-left: 8px">ROOT</el-tag>
                <el-tag v-else-if="user.is_admin === 1" type="warning" size="small" style="margin-left: 8px">ADMIN</el-tag>
              </h1>
              <p class="user-uid">UID: {{ (user as any).uid || '--' }}</p>
              <p class="user-signature">{{ user.signature || '这个人很懒，什么都没留下' }}</p>
            </div>

            <div class="user-stats">
              <div class="stat-item">
                <span class="stat-value">{{ stats.posts || 0 }}</span>
                <span class="stat-label">文章</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ stats.media || 0 }}</span>
                <span class="stat-label">媒体</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ stats.resources || 0 }}</span>
                <span class="stat-label">资源</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item clickable" @click="goToFollowers">
                <span class="stat-value">{{ user.followers_count || 0 }}</span>
                <span class="stat-label">粉丝</span>
              </div>
              <div class="stat-item clickable" @click="goToFollowing">
                <span class="stat-value">{{ user.following_count || 0 }}</span>
                <span class="stat-label">关注</span>
              </div>
            </div>

            <div class="user-actions">
              <el-button
                v-if="!isOwnProfile"
                :type="isFollowing ? 'default' : 'primary'"
                :loading="followLoading"
                @click="handleFollow"
              >
                <el-icon><component :is="isFollowing ? Minus : Plus" /></el-icon>
                {{ isFollowing ? '取消关注' : '关注' }}
              </el-button>
              <el-button v-if="isOwnProfile" type="primary" @click="router.push({ name: 'Space' })">
                <el-icon><Edit /></el-icon>
                编辑资料
              </el-button>
              <el-button @click="router.back()">
                <el-icon><Back /></el-icon>
                返回
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 公开作品 -->
      <div class="content-section">
        <div class="section-header">
          <span class="section-label">公开作品</span>
          <div class="content-tabs">
            <span
              v-for="tab in contentTabs"
              :key="tab.value"
              :class="['tab-item', { active: contentType === tab.value }]"
              @click="handleTabChange(tab.value)"
            >
              <el-icon><component :is="tab.icon" /></el-icon>
              {{ tab.label }}
            </span>
          </div>
        </div>

        <div v-if="contentLoading" class="loading-container">
          <el-skeleton :rows="6" animated />
        </div>

        <div v-else-if="allFiles.length > 0" class="content-grid">
          <FileCard
            v-for="item in allFiles"
            :key="item.id"
            :file="item"
            :show-author="false"
            :show-badge="false"
            @click="handlePreview"
          />
        </div>

        <el-empty v-else description="暂无公开内容" />

        <div v-if="hasMore" class="load-more">
          <el-button @click="loadMore" :loading="loadingMore">加载更多</el-button>
        </div>
      </div>
    </div>

    <FilePreview v-model="previewVisible" :file="currentFile" :type="previewType" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Grid, Picture, VideoPlay, Folder, Edit, Back, Plus, Minus } from '@element-plus/icons-vue'
import AppHeader from '@/components/common/AppHeader.vue'
import FileCard from '@/components/business/FileCard.vue'
import FilePreview from '@/components/business/FilePreview.vue'
import { useUserStore } from '@/stores/user'
import { usersApi } from '@/api/modules/users'
import type { FileItem } from '@/types/models'
import type { UserPublicInfo, UserPublicStats } from '@/api/modules/users'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

type ContentType = '' | 'image' | 'video' | 'resource'

const contentTabs = [
  { value: '' as ContentType, label: '全部', icon: Grid },
  { value: 'image' as ContentType, label: '图片', icon: Picture },
  { value: 'video' as ContentType, label: '视频', icon: VideoPlay },
  { value: 'resource' as ContentType, label: '资源', icon: Folder },
]

const loading = ref(true)
const contentLoading = ref(false)
const loadingMore = ref(false)
const followLoading = ref(false)

const user = ref<UserPublicInfo | null>(null)
const stats = ref<UserPublicStats>({ posts: 0, media: 0, resources: 0 })
const isFollowing = ref(false)

const contentType = ref<ContentType>('')
const currentPage = ref(1)
const allFiles = ref<FileItem[]>([])

const previewVisible = ref(false)
const currentFile = ref<FileItem | null>(null)

const username = computed(() => route.params.username as string)

const isOwnProfile = computed(
  () => userStore.isLoggedIn && userStore.currentUser?.username === username.value
)

const displayName = computed(
  () => user.value?.nickname?.[0] || user.value?.username?.[0] || '?'
)

const avatarUrl = computed(() => {
  if (!user.value?.username) return undefined
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/users/username/${user.value.username}/avatar/view`
})

const hasMore = computed(() => allFiles.value.length >= currentPage.value * 20)

const previewType = computed<'media' | 'resource'>(() => {
  if (!currentFile.value) return 'media'
  return currentFile.value.file_category === 'resource' ? 'resource' : 'media'
})

async function loadUserProfile() {
  loading.value = true
  try {
    const [userRes, statsRes] = await Promise.all([
      usersApi.getUserByUsername(username.value),
      usersApi.getUserPublicStats(username.value)
    ])
    user.value = userRes.data
    stats.value = statsRes.data

    if (!isOwnProfile.value && userStore.isLoggedIn && user.value?.id) {
      try {
        const followRes = await usersApi.checkFollowStatus([user.value.id])
        isFollowing.value = followRes.data[user.value.id] || false
      } catch {
        isFollowing.value = false
      }
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载用户信息失败')
    router.back()
  } finally {
    loading.value = false
  }
}

async function loadContent(reset = true) {
  if (reset) {
    currentPage.value = 1
    allFiles.value = []
  }

  contentLoading.value = reset
  if (!reset) loadingMore.value = true

  try {
    let apiType: 'all' | 'media' | 'resources' = 'all'
    if (contentType.value === 'image' || contentType.value === 'video') apiType = 'media'
    else if (contentType.value === 'resource') apiType = 'resources'

    const res = await usersApi.getUserPublicContent(username.value, {
      type: apiType,
      page: currentPage.value,
      page_size: 20
    })

    const data = res.data
    const mediaList: FileItem[] = (data.media || []).filter((item: FileItem) => {
      if (contentType.value === 'image') return item.file_category === 'image'
      if (contentType.value === 'video') return item.file_category === 'video'
      return true
    })
    const resourceList: FileItem[] = data.resources || []
    const newItems = [...mediaList, ...resourceList]

    reset ? (allFiles.value = newItems) : allFiles.value.push(...newItems)
  } catch {
    // 静默失败，不打扰用户
  } finally {
    contentLoading.value = false
    loadingMore.value = false
  }
}

function handleTabChange(val: ContentType) {
  contentType.value = val
  loadContent(true)
}

function loadMore() {
  currentPage.value++
  loadContent(false)
}

function handlePreview(file: FileItem) {
  router.push({ name: 'FileDetail', params: { id: file.id } })
}

async function handleFollow() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push({ name: 'Login', query: { redirect: route.fullPath } })
    return
  }
  if (!user.value?.id) return

  followLoading.value = true
  try {
    if (isFollowing.value) {
      await usersApi.unfollowUser(user.value.id)
      isFollowing.value = false
      ElMessage.success('已取消关注')
      if (user.value.followers_count !== undefined) user.value.followers_count--
    } else {
      await usersApi.followUser(user.value.id)
      isFollowing.value = true
      ElMessage.success('关注成功')
      if (user.value.followers_count !== undefined) user.value.followers_count++
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    followLoading.value = false
  }
}

function goToFollowers() {
  router.push({ name: 'FollowList', params: { type: 'followers', username: username.value } })
}

function goToFollowing() {
  router.push({ name: 'FollowList', params: { type: 'following', username: username.value } })
}

onMounted(() => {
  loadUserProfile()
  loadContent()
})
</script>

<style scoped lang="scss">
.user-profile-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.profile-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-lg $spacing-md;
  width: 100%;
}

.loading-container {
  padding: $spacing-xl;
}

// 用户信息卡片
.user-card {
  background: var(--el-bg-color);
  border-radius: $radius-xl;
  overflow: hidden;
  box-shadow: $shadow-md;
  margin-bottom: $spacing-lg;
}

.user-cover {
  height: 200px;
  background: linear-gradient(135deg, $color-primary 0%, $color-secondary 100%);
}

.user-info-section {
  padding: 0 $spacing-xl $spacing-lg;
  margin-top: -50px;
}

.avatar-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: $spacing-md;
}

.user-avatar {
  border: 4px solid var(--el-bg-color);
  font-size: 40px;
  font-weight: bold;
  background: linear-gradient(135deg, $color-primary, $color-secondary);
  color: white;
}

.user-details {
  text-align: center;
}

.user-header {
  margin-bottom: $spacing-lg;
}

.user-name {
  font-size: $font-2xl;
  font-weight: 700;
  margin: 0 0 $spacing-sm;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-uid {
  font-size: $font-xs;
  color: var(--el-text-color-placeholder);
  margin: 0 0 4px;
  font-family: monospace;
}

.user-signature {
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  margin: 0;
  line-height: 1.6;
}

.user-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-lg;
  margin-bottom: $spacing-lg;
  padding: $spacing-md 0;
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;

  &.clickable {
    cursor: pointer;
    transition: color $transition-fast;

    &:hover .stat-value {
      color: $color-primary;
    }
  }
}

.stat-value {
  font-size: $font-xl;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stat-label {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  line-height: 1;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: var(--el-border-color-light);
}

.user-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
}

// 公开作品区
.content-section {
  background: var(--el-bg-color);
  border-radius: $radius-xl;
  padding: $spacing-lg;
  box-shadow: $shadow-md;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
  flex-wrap: wrap;
}

.section-label {
  font-size: $font-base;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.content-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  border-bottom: 1px solid var(--el-border-color-light);

  .tab-item {
    display: inline-flex;
    align-items: center;
    gap: $spacing-xs;
    padding: $spacing-sm $spacing-md;
    font-size: $font-sm;
    color: var(--el-text-color-secondary);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: color $transition-fast, border-color $transition-fast;
    white-space: nowrap;

    &:hover {
      color: var(--el-text-color-primary);
    }

    &.active {
      color: $color-primary;
      border-bottom-color: $color-primary;
      font-weight: 500;
    }
  }
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
}

.load-more {
  display: flex;
  justify-content: center;
  padding-top: $spacing-md;
}

// 响应式
@media (max-width: $breakpoint-md) {
  .profile-container {
    padding: $spacing-sm;
  }

  .user-info-section {
    padding: 0 $spacing-md $spacing-md;
  }

  .user-stats {
    gap: $spacing-md;
  }

  .stat-value {
    font-size: $font-lg;
  }

  .content-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: $spacing-sm;
  }
}
</style>
