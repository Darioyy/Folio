<template>
  <div class="user-profile-page">
    <div class="container">
      <!-- 用户信息卡片 -->
      <div v-if="loading" class="profile-loading">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="circle" style="width: 128px; height: 128px" />
            <el-skeleton-item variant="text" style="width: 200px; margin-top: 20px" />
            <el-skeleton-item variant="text" style="width: 150px" />
          </template>
        </el-skeleton>
      </div>

      <div v-else-if="userInfo" class="profile-header">
        <!-- 用户头像和信息 -->
        <div class="user-card">
          <UserAvatar :user="userInfo" :size="128" />
          <div class="user-info">
            <h1 class="user-name">{{ userInfo.nickname || userInfo.username }}</h1>
            <p v-if="userInfo.nickname" class="user-username">@{{ userInfo.username }}</p>
            <p v-if="userInfo.signature" class="user-signature">{{ userInfo.signature }}</p>
            <p class="user-joined">
              <el-icon><Calendar /></el-icon>
              加入于 {{ formatDate(userInfo.created_at) }}
            </p>
          </div>
        </div>

        <!-- 用户统计 -->
        <div v-if="userStats" class="user-stats">
          <div class="stat-item">
            <div class="stat-value">{{ userStats.posts }}</div>
            <div class="stat-label">文章</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ userStats.media }}</div>
            <div class="stat-label">媒体</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ userStats.resources }}</div>
            <div class="stat-label">资源</div>
          </div>
        </div>
      </div>

      <el-empty v-else description="用户不存在" />

      <!-- 内容标签页 -->
      <div v-if="userInfo" class="profile-content">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="全部" name="all">
            <template #label>
              <span class="tab-label">
                <el-icon><List /></el-icon>
                全部
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane name="posts">
            <template #label>
              <span class="tab-label">
                <el-icon><Document /></el-icon>
                文章
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane name="media">
            <template #label>
              <span class="tab-label">
                <el-icon><Picture /></el-icon>
                媒体
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane name="resources">
            <template #label>
              <span class="tab-label">
                <el-icon><Folder /></el-icon>
                资源
              </span>
            </template>
          </el-tab-pane>
        </el-tabs>

        <!-- 内容列表 -->
        <div v-if="contentLoading" class="content-loading">
          <el-skeleton :rows="3" animated />
        </div>

        <div v-else-if="hasContent" class="content-grid">
          <!-- 文章列表 -->
          <template v-if="activeTab === 'all' || activeTab === 'posts'">
            <div v-for="post in currentContent.posts" :key="`post-${post.id}`" class="content-item post-item">
              <div class="post-icon">
                <el-icon :size="24"><Document /></el-icon>
              </div>
              <div class="post-info">
                <h3 class="post-title">{{ post.title }}</h3>
                <p class="post-meta">
                  <span>{{ formatDate(post.created_at) }}</span>
                  <span>{{ post.view_count || 0 }} 次浏览</span>
                </p>
              </div>
              <el-button type="primary" link @click="goToPost(post.id)">查看</el-button>
            </div>
          </template>

          <!-- 媒体列表 -->
          <template v-if="activeTab === 'all' || activeTab === 'media'">
            <div
              v-for="media in currentContent.media"
              :key="`media-${media.id}`"
              class="content-item media-item"
              @click="viewMedia(media)"
            >
              <div class="media-thumb">
                <img
                  :src="getThumbnailUrl(media.id)"
                  :alt="media.title"
                  loading="lazy"
                />
                <div v-if="media.file_type === 'video'" class="play-overlay">
                  <el-icon :size="32"><VideoPlay /></el-icon>
                </div>
              </div>
              <div class="media-info">
                <p class="media-title">{{ media.title }}</p>
              </div>
            </div>
          </template>

          <!-- 资源列表 -->
          <template v-if="activeTab === 'all' || activeTab === 'resources'">
            <div v-for="resource in currentContent.resources" :key="`resource-${resource.id}`" class="content-item resource-item">
              <div class="resource-icon">
                <el-icon :size="32"><Folder /></el-icon>
              </div>
              <div class="resource-info">
                <h3 class="resource-title">{{ resource.title }}</h3>
                <p class="resource-meta">
                  <span>{{ resource.download_count || 0 }} 次下载</span>
                </p>
              </div>
            </div>
          </template>
        </div>

        <el-empty v-else description="暂无公开内容" />
      </div>
    </div>

    <!-- 媒体预览对话框 -->
    <FilePreview
      v-model="previewVisible"
      :file="currentMedia"
      type="media"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Calendar,
  List,
  Document,
  Picture,
  Folder,
  VideoPlay
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import UserAvatar from '@/components/common/UserAvatar.vue'
import FilePreview from '@/components/business/FilePreview.vue'
import { usersApi } from '@/api/modules/users'
import { mediaApi } from '@/api/modules/media'
import type { UserPublicInfo, UserPublicStats, UserPublicContent } from '@/api/modules/users'
import { formatDate } from '@/utils/format'

const route = useRoute()
const username = computed(() => route.params.username as string)

const loading = ref(true)
const contentLoading = ref(false)
const userInfo = ref<UserPublicInfo | null>(null)
const userStats = ref<UserPublicStats | null>(null)
const userContent = ref<UserPublicContent | null>(null)

const activeTab = ref<'all' | 'posts' | 'media' | 'resources'>('all')
const previewVisible = ref(false)
const currentMedia = ref<any>(null)

// 当前显示的内容
const currentContent = computed(() => {
  if (!userContent.value) return { posts: [], media: [], resources: [] }

  if (activeTab.value === 'all') {
    return userContent.value
  }

  return {
    posts: activeTab.value === 'posts' ? userContent.value.posts : [],
    media: activeTab.value === 'media' ? userContent.value.media : [],
    resources: activeTab.value === 'resources' ? userContent.value.resources : []
  }
})

// 是否有内容
const hasContent = computed(() => {
  const content = currentContent.value
  return content.posts.length > 0 || content.media.length > 0 || content.resources.length > 0
})

// 加载用户信息
async function loadUserInfo() {
  loading.value = true
  try {
    const res = await usersApi.getUserByUsername(username.value)
    userInfo.value = res.data
  } catch (error) {
    console.error('加载用户信息失败:', error)
    ElMessage.error('用户不存在')
  } finally {
    loading.value = false
  }
}

// 加载用户统计
async function loadUserStats() {
  try {
    const res = await usersApi.getUserPublicStats(username.value)
    userStats.value = res.data
  } catch (error) {
    console.error('加载用户统计失败:', error)
  }
}

// 加载用户内容
async function loadUserContent() {
  contentLoading.value = true
  try {
    const res = await usersApi.getUserPublicContent(username.value, {
      type: activeTab.value,
      page: 1,
      page_size: 50
    })
    userContent.value = res.data
  } catch (error) {
    console.error('加载用户内容失败:', error)
    ElMessage.error('加载内容失败')
  } finally {
    contentLoading.value = false
  }
}

// 标签切换
function handleTabChange() {
  loadUserContent()
}

// 获取媒体缩略图 URL
function getThumbnailUrl(id: number): string {
  return mediaApi.getThumbnailUrl(id)
}

// 获取媒体 URL
function getMediaUrl(id: number): string {
  return mediaApi.getViewUrl(id)
}

// 查看媒体
function viewMedia(media: any) {
  currentMedia.value = media
  previewVisible.value = true
}

// 跳转到文章详情
function goToPost(id: number) {
  window.open(`/posts/${id}`, '_blank')
}

// 监听用户名变化
watch(username, () => {
  if (username.value) {
    loadUserInfo()
    loadUserStats()
    loadUserContent()
  }
}, { immediate: true })

onMounted(() => {
  if (username.value) {
    loadUserInfo()
    loadUserStats()
    loadUserContent()
  }
})
</script>

<style scoped lang="scss">
.user-profile-page {
  min-height: 100vh;
  background: #f9fafb;

  html.dark & {
    background: #0f172a;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px;
  }
}

.profile-loading {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.profile-header {
  background: #ffffff;
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  html.dark & {
    background: #1e293b;
  }

  .user-card {
    display: flex;
    align-items: center;
    gap: 24px;
    margin-bottom: 24px;

    @media (max-width: 768px) {
      flex-direction: column;
      text-align: center;
    }
  }

  .user-info {
    flex: 1;

    .user-name {
      font-size: 28px;
      font-weight: 600;
      margin: 0 0 8px 0;
      color: var(--el-text-color-primary);
    }

    .user-username {
      font-size: 16px;
      color: var(--el-text-color-secondary);
      margin: 0 0 8px 0;
    }

    .user-signature {
      font-size: 14px;
      color: var(--el-text-color-regular);
      margin: 0 0 12px 0;
    }

    .user-joined {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      color: var(--el-text-color-secondary);
      margin: 0;

      @media (max-width: 768px) {
        justify-content: center;
      }
    }
  }

  .user-stats {
    display: flex;
    gap: 48px;
    padding-top: 24px;
    border-top: 1px solid var(--el-border-color);

    .stat-item {
      text-align: center;

      .stat-value {
        font-size: 32px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .stat-label {
        font-size: 14px;
        color: var(--el-text-color-secondary);
        margin-top: 4px;
      }
    }
  }
}

.profile-content {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  html.dark & {
    background: #1e293b;
  }

  .tab-label {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .content-loading {
    padding: 40px 0;
  }

  .content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
    margin-top: 24px;
  }

  .content-item {
    border: 1px solid var(--el-border-color);
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.2s;

    &:hover {
      border-color: #6366f1;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
    }
  }

  // 文章样式
  .post-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;

    .post-icon {
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      border-radius: 12px;
      color: white;
      flex-shrink: 0;
    }

    .post-info {
      flex: 1;
      min-width: 0;

      .post-title {
        font-size: 16px;
        font-weight: 500;
        margin: 0 0 8px 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .post-meta {
        display: flex;
        gap: 12px;
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin: 0;
      }
    }
  }

  // 媒体样式
  .media-item {
    cursor: pointer;

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

      .media-title {
        font-size: 14px;
        margin: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }

  // 资源样式
  .resource-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;

    .resource-icon {
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #10b981, #059669);
      border-radius: 12px;
      color: white;
      flex-shrink: 0;
    }

    .resource-info {
      flex: 1;
      min-width: 0;

      .resource-title {
        font-size: 16px;
        font-weight: 500;
        margin: 0 0 8px 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .resource-meta {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin: 0;
      }
    }
  }
}
</style>
