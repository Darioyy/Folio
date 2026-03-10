<template>
  <div class="user-profile-page" :class="{ 'is-dark': isDarkMode }">
    <AppHeader />

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="user" class="profile-container">
      <!-- 用户信息卡片 -->
      <div class="user-card">
        <div class="user-cover"></div>
        <div class="user-info-section">
          <!-- 头像 -->
          <div class="avatar-wrapper">
            <el-avatar :src="avatarUrl" :size="100" class="user-avatar">
              {{ displayName }}
            </el-avatar>
          </div>

          <!-- 用户信息 -->
          <div class="user-details">
            <div class="user-header">
              <h1 class="user-name">
                {{ user.nickname || user.username }}
                <el-tag v-if="user.is_root === 1" type="danger" size="small" style="margin-left: 8px">ROOT</el-tag>
                <el-tag v-else-if="user.is_admin === 1" type="warning" size="small" style="margin-left: 8px">ADMIN</el-tag>
              </h1>
              <p class="user-signature">{{ user.signature || '这个人很懒，什么都没留下' }}</p>
            </div>

            <!-- 统计数据 -->
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

            <!-- 操作按钮 -->
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
              <el-button
                v-if="isOwnProfile"
                type="primary"
                @click="goToEditProfile"
              >
                <el-icon><Edit /></el-icon>
                编辑资料
              </el-button>
              <el-button @click="goToBack">
                <el-icon><Back /></el-icon>
                返回
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 公开内容 -->
      <div class="content-section">
        <div class="section-header">
          <h2 class="section-title">
            <el-icon><Grid /></el-icon>
            公开作品
          </h2>
          <el-radio-group v-model="contentType" @change="loadContent">
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button value="image">图片</el-radio-button>
            <el-radio-button value="video">视频</el-radio-button>
            <el-radio-button value="resource">资源</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 加载状态 -->
        <div v-if="contentLoading" class="loading-container">
          <el-skeleton :rows="6" animated />
        </div>

        <!-- 内容网格 -->
        <div v-else-if="contentItems.length > 0" class="content-grid">
          <!-- 媒体卡片 -->
          <div
            v-for="item in mediaItems"
            :key="`media-${item.id}`"
            class="content-card media-card"
            @click="viewMedia(item)"
          >
            <div class="media-thumb">
              <img
                :src="getThumbnailUrl(item.id)"
                :alt="item.title"
                loading="lazy"
              />
              <div v-if="item.file_type === 'video'" class="play-overlay">
                <el-icon :size="32"><VideoPlay /></el-icon>
              </div>
            </div>
            <div class="media-info">
              <h4 class="media-title">{{ item.title }}</h4>
              <p class="media-meta">{{ formatDate(item.created_at) }}</p>
            </div>
          </div>

          <!-- 资源卡片 -->
          <div
            v-for="item in resourceItems"
            :key="`resource-${item.id}`"
            class="content-card resource-card"
            @click="viewResource(item)"
          >
            <div class="resource-icon">
              <el-icon :size="48"><Folder /></el-icon>
            </div>
            <div class="resource-info">
              <h4 class="resource-title">{{ item.title }}</h4>
              <p class="resource-meta">
                <span v-if="item.file_size">{{ formatSize(item.file_size) }}</span>
                <span>{{ formatDate(item.created_at) }}</span>
              </p>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty v-else description="暂无公开内容" />

        <!-- 加载更多 -->
        <div v-if="hasMore" class="load-more">
          <el-button @click="loadMore" :loading="loadingMore">
            加载更多
          </el-button>
        </div>
      </div>
    </div>

    <!-- 文件预览对话框 -->
    <FilePreview
      v-model="previewVisible"
      :file="currentFile"
      :type="currentFileType"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Grid, VideoPlay, Folder, Edit, Back, Plus, Minus
} from '@element-plus/icons-vue'
import AppHeader from '@/components/common/AppHeader.vue'
import FilePreview from '@/components/business/FilePreview.vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { usersApi } from '@/api/modules/users'
import { mediaApi } from '@/api/modules/media'
import type { HubMedia, HubResource } from '@/api/modules/hub'
import type { UserPublicInfo, UserPublicStats } from '@/api/modules/users'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()
const isDarkMode = computed(() => appStore.isDarkMode)

const loading = ref(true)
const contentLoading = ref(false)
const loadingMore = ref(false)
const followLoading = ref(false)

const user = ref<UserPublicInfo | null>(null)
const stats = ref<UserPublicStats>({ posts: 0, media: 0, resources: 0 })
const isFollowing = ref(false)

const contentType = ref('')
const currentPage = ref(1)
const mediaItems = ref<HubMedia[]>([])
const resourceItems = ref<HubResource[]>([])

const previewVisible = ref(false)
const currentFile = ref<HubMedia | HubResource | null>(null)
const currentFileType = ref<'media' | 'resource'>('media')

const username = computed(() => route.params.username as string)
const isOwnProfile = computed(() => {
  return userStore.isLoggedIn && userStore.currentUser?.username === username.value
})

// 显示名称
const displayName = computed(() => {
  return user.value?.nickname?.[0] || user.value?.username?.[0] || '?'
})

// 头像 URL
const avatarUrl = computed(() => {
  if (user.value?.username) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    return `${baseUrl}/users/username/${user.value.username}/avatar/view`
  }
  return undefined
})

// 内容列表
const contentItems = computed(() => {
  return [...mediaItems.value, ...resourceItems.value]
})

// 是否有更多内容
const hasMore = computed(() => {
  return contentItems.value.length >= currentPage.value * 20
})

// 加载用户信息
async function loadUserProfile() {
  loading.value = true
  try {
    // 并行获取用户信息和统计数据
    const [userRes, statsRes] = await Promise.all([
      usersApi.getUserByUsername(username.value),
      usersApi.getUserPublicStats(username.value)
    ])

    user.value = userRes.data
    stats.value = statsRes.data

    // 检查是否已关注（如果不是自己的主页且已登录）
    if (!isOwnProfile.value && userStore.isLoggedIn && user.value?.id) {
      try {
        const followRes = await usersApi.checkFollowStatus([user.value.id])
        isFollowing.value = followRes.data[user.value.id] || false
      } catch {
        // 忽略关注状态检查失败
        isFollowing.value = false
      }
    }
  } catch (error: any) {
    console.error('加载用户信息失败:', error)
    ElMessage.error(error.response?.data?.message || '加载用户信息失败')
    // 返回上一页
    router.back()
  } finally {
    loading.value = false
  }
}

// 加载内容
async function loadContent(reset = true) {
  if (reset) {
    currentPage.value = 1
    mediaItems.value = []
    resourceItems.value = []
  }

  contentLoading.value = reset
  if (!reset) loadingMore.value = true

  try {
    // 映射内容类型到API参数
    let apiType: 'all' | 'posts' | 'media' | 'resources' = 'all'
    if (contentType.value === 'image' || contentType.value === 'video') {
      apiType = 'media'
    } else if (contentType.value === 'resource') {
      apiType = 'resources'
    }

    const res = await usersApi.getUserPublicContent(username.value, {
      type: apiType,
      page: currentPage.value,
      page_size: 20
    })

    const data = res.data
    const newMediaItems = (data.media || []).filter((item: any) => {
      if (contentType.value === 'image') return item.file_type === 'image'
      if (contentType.value === 'video') return item.file_type === 'video'
      return true
    })

    const newResourceItems = data.resources || []

    if (reset) {
      mediaItems.value = newMediaItems
      resourceItems.value = newResourceItems
    } else {
      mediaItems.value.push(...newMediaItems)
      resourceItems.value.push(...newResourceItems)
    }
  } catch (error) {
    console.error('加载内容失败:', error)
  } finally {
    contentLoading.value = false
    loadingMore.value = false
  }
}

// 加载更多
function loadMore() {
  currentPage.value++
  loadContent(false)
}

// 获取缩略图 URL
function getThumbnailUrl(id: number): string {
  return mediaApi.getThumbnailUrl(id)
}

// 查看媒体
function viewMedia(media: HubMedia) {
  currentFile.value = media
  currentFileType.value = 'media'
  previewVisible.value = true
}

// 查看资源
function viewResource(resource: HubResource) {
  currentFile.value = resource
  currentFileType.value = 'resource'
  previewVisible.value = true
}

// 关注/取消关注
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
      if (user.value.followers_count !== undefined) {
        user.value.followers_count--
      }
    } else {
      await usersApi.followUser(user.value.id)
      isFollowing.value = true
      ElMessage.success('关注成功')
      if (user.value.followers_count !== undefined) {
        user.value.followers_count++
      }
    }
  } catch (error: any) {
    console.error('关注操作失败:', error)
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    followLoading.value = false
  }
}

// 跳转到粉丝列表
function goToFollowers() {
  router.push({ name: 'FollowList', params: { type: 'followers', username: username.value } })
}

// 跳转到关注列表
function goToFollowing() {
  router.push({ name: 'FollowList', params: { type: 'following', username: username.value } })
}

// 编辑资料
function goToEditProfile() {
  router.push({ name: 'Profile' })
}

// 返回
function goToBack() {
  router.back()
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (!bytes) return '未知'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// 格式化日期
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
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
  background: #f9fafb;

  html.dark & {
    background: #0f172a;
  }
}

.profile-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  width: 100%;
}

.loading-container {
  padding: 40px;
}

// 用户卡片
.user-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;

  html.dark & {
    background: #1e293b;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }
}

.user-cover {
  height: 200px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

.user-info-section {
  padding: 0 32px 24px;
  margin-top: -50px;
}

.avatar-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.user-avatar {
  border: 4px solid #ffffff;
  font-size: 40px;
  font-weight: bold;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;

  html.dark & {
    border-color: #1e293b;
  }
}

.user-details {
  text-align: center;
}

.user-header {
  margin-bottom: 20px;
}

.user-name {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-signature {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0;
  line-height: 1.6;
}

.user-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  margin-bottom: 20px;
  padding: 16px 0;
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;

  html.dark & {
    border-color: #334155;
  }
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;

  &.clickable {
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      .stat-value {
        color: #6366f1;
      }
    }
  }
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: #e5e7eb;

  html.dark & {
    background: #334155;
  }
}

.user-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

// 内容区域
.content-section {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

  html.dark & {
    background: #1e293b;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;

  html.dark & {
    border-bottom-color: #334155;
  }
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--el-text-color-primary);

  .el-icon {
    font-size: 20px;
    color: #6366f1;
  }
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.content-card {
  background: #f9fafb;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;

  html.dark & {
    background: rgba(255, 255, 255, 0.05);
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

.media-card {
  .media-thumb {
    aspect-ratio: 16 / 9;
    position: relative;
    overflow: hidden;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .play-overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.3);
      color: white;
    }
  }

  .media-info {
    padding: 12px;
  }

  .media-title {
    font-size: 14px;
    font-weight: 500;
    margin: 0 0 4px 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--el-text-color-primary);
  }

  .media-meta {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.resource-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;

  .resource-icon {
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #10b981, #059669);
    border-radius: 12px;
    color: white;
    margin-bottom: 12px;
  }

  .resource-title {
    font-size: 14px;
    font-weight: 500;
    margin: 0 0 8px 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--el-text-color-primary);
  }

  .resource-meta {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin: 0;

    span {
      &:not(:last-child)::after {
        content: '·';
        margin: 0 4px;
      }
    }
  }
}

.load-more {
  display: flex;
  justify-content: center;
  padding-top: 16px;
}

// 响应式
@media (max-width: 768px) {
  .profile-container {
    padding: 12px;
  }

  .user-info-section {
    padding: 0 16px 20px;
  }

  .user-stats {
    gap: 16px;
  }

  .stat-value {
    font-size: 18px;
  }

  .content-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
}
</style>
