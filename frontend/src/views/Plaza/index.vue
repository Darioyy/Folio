<template>
  <div class="plaza-page">
    <div class="container">
      <!-- 页面头部 -->
      <div class="page-header">
        <h1 class="page-title">公共大厅</h1>
        <p class="page-subtitle">发现优质内容，探索社区创作</p>
      </div>

      <!-- 内容类型标签 -->
      <div class="content-tabs">
        <el-radio-group v-model="contentType" @change="handleContentTypeChange">
          <el-radio-button value="all">
            <el-icon><Grid /></el-icon>
            全部
          </el-radio-button>
          <el-radio-button value="posts">
            <el-icon><Document /></el-icon>
            文章
          </el-radio-button>
          <el-radio-button value="images">
            <el-icon><Picture /></el-icon>
            图片
          </el-radio-button>
          <el-radio-button value="videos">
            <el-icon><VideoPlay /></el-icon>
            视频
          </el-radio-button>
          <el-radio-button value="resources">
            <el-icon><Folder /></el-icon>
            资源
          </el-radio-button>
        </el-radio-group>

        <!-- 排序方式 -->
        <el-select v-model="sortBy" @change="loadContent" placeholder="排序方式" style="width: 120px">
          <el-option label="最新" value="latest" />
          <el-option label="热门" value="popular" />
        </el-select>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading && currentPage === 1" class="content-loading">
        <el-skeleton :rows="6" animated />
      </div>

      <!-- 内容网格 -->
      <div v-else-if="hasContent" class="content-grid">
        <!-- 文章卡片 -->
        <template v-if="showPosts">
          <div
            v-for="item in posts"
            :key="`post-${item.id}`"
            class="content-card post-card"
            @click="goToPost(item.id)"
          >
            <div class="post-icon">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="post-info">
              <h4 class="post-title">{{ item.title }}</h4>
              <p v-if="item.summary" class="post-summary">{{ item.summary }}</p>
              <div class="post-meta">
                <span>
                  <el-icon><User /></el-icon>
                  {{ item.author_name || '匿名' }}
                </span>
                <span>
                  <el-icon><View /></el-icon>
                  {{ item.view_count || 0 }}
                </span>
                <span>{{ formatDate(item.created_at) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- 图片卡片 -->
        <template v-if="showImages">
          <div
            v-for="item in imagesList"
            :key="`image-${item.id}`"
            class="content-card media-card"
            @click="viewMedia(item)"
          >
            <div class="media-thumb">
              <img
                :src="getThumbnailUrl(item.id)"
                :alt="item.title"
                loading="lazy"
              />
            </div>
            <div class="media-info">
              <h4 class="media-title">{{ item.title }}</h4>
              <div class="media-meta">
                <span class="author-link" @click.stop="goToUserProfile(item.uploader_id, item.uploader_name)">
                  <el-icon><User /></el-icon>
                  {{ item.uploader_name || '未知用户' }}
                </span>
              </div>
            </div>
          </div>
        </template>

        <!-- 视频卡片 -->
        <template v-if="showVideos">
          <div
            v-for="item in videosList"
            :key="`video-${item.id}`"
            class="content-card media-card"
            @click="viewMedia(item)"
          >
            <div class="media-thumb">
              <img
                :src="getThumbnailUrl(item.id)"
                :alt="item.title"
                loading="lazy"
              />
              <div class="play-overlay">
                <el-icon :size="32"><VideoPlay /></el-icon>
              </div>
            </div>
            <div class="media-info">
              <h4 class="media-title">{{ item.title }}</h4>
              <div class="media-meta">
                <span class="author-link" @click.stop="goToUserProfile(item.uploader_id, item.uploader_name)">
                  <el-icon><User /></el-icon>
                  {{ item.uploader_name || '未知用户' }}
                </span>
              </div>
            </div>
          </div>
        </template>

        <!-- 资源卡片 -->
        <template v-if="showResources">
          <div
            v-for="item in resourceList"
            :key="`resource-${item.id}`"
            class="content-card resource-card"
            @click="viewResource(item)"
          >
            <div class="resource-icon">
              <el-icon :size="48"><Folder /></el-icon>
            </div>
            <div class="resource-info">
              <h4 class="resource-title">{{ item.title }}</h4>
              <div class="resource-meta">
                <span v-if="item.file_size">
                  <el-icon><Document /></el-icon>
                  {{ formatFileSize(item.file_size) }}
                </span>
                <span>
                  <el-icon><Download /></el-icon>
                  {{ item.download_count || 0 }}
                </span>
                <span class="author-link" @click.stop="goToUserProfile(item.uploader_id, item.uploader_name)">
                  <el-icon><User /></el-icon>
                  {{ item.uploader_name || '未知用户' }}
                </span>
              </div>
            </div>
          </div>
        </template>
      </div>

      <el-empty v-else description="暂无公开内容" />

      <!-- 加载更多 -->
      <div v-if="hasMore" class="load-more">
        <el-button @click="loadMore" :loading="loadingMore">
          加载更多
        </el-button>
      </div>
    </div>

    <!-- 媒体预览对话框 -->
    <FilePreview
      v-model="previewVisible"
      :file="currentFile"
      :type="currentFileType"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Grid,
  Document,
  Picture,
  Folder,
  VideoPlay,
  User,
  Download,
  View
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import FilePreview from '@/components/business/FilePreview.vue'
import { hubApi } from '@/api/modules/hub'
import { mediaApi } from '@/api/modules/media'
import { postsApi } from '@/api/modules/posts'
import type { HubMedia, HubResource } from '@/api/modules/hub'
import { formatDate, formatFileSize } from '@/utils/format'

const router = useRouter()

// 内容类型
type ContentType = 'all' | 'posts' | 'images' | 'videos' | 'resources'

const contentType = ref<ContentType>('all')
const sortBy = ref<'latest' | 'popular'>('latest')

const loading = ref(false)
const loadingMore = ref(false)
const currentPage = ref(1)

const posts = ref<any[]>([])
const mediaList = ref<HubMedia[]>([])
const resourceList = ref<HubResource[]>([])

const previewVisible = ref(false)
const currentFile = ref<HubMedia | HubResource | null>(null)
const currentFileType = ref<'media' | 'resource'>('media')

// 是否显示文章
const showPosts = computed(() => contentType.value === 'all' || contentType.value === 'posts')

// 是否显示图片
const showImages = computed(() => contentType.value === 'all' || contentType.value === 'images')

// 是否显示视频
const showVideos = computed(() => contentType.value === 'all' || contentType.value === 'videos')

// 是否显示资源
const showResources = computed(() => contentType.value === 'all' || contentType.value === 'resources')

// 是否有内容
const hasContent = computed(() => {
  return posts.value.length > 0 || mediaList.value.length > 0 || resourceList.value.length > 0
})

// 是否还有更多内容
const hasMore = computed(() => {
  const totalItems = (showPosts.value ? posts.value.length : 0) +
                     (showImages.value ? imagesList.value.length : 0) +
                     (showVideos.value ? videosList.value.length : 0) +
                     (showResources.value ? resourceList.value.length : 0)
  return totalItems >= currentPage.value * 20
})

// 分离的图片和视频列表
const imagesList = computed(() => mediaList.value.filter(m => m.file_type === 'image'))
const videosList = computed(() => mediaList.value.filter(m => m.file_type === 'video'))

// 加载内容
async function loadContent(reset = true) {
  if (reset) {
    currentPage.value = 1
    posts.value = []
    mediaList.value = []
    resourceList.value = []
  }

  loading.value = reset
  if (!reset) loadingMore.value = true

  try {
    // 加载文章
    if (showPosts.value) {
      const postsRes = await postsApi.getList({
        page: currentPage.value,
        limit: 20,
        status: 'published'
      })
      const postsData = postsRes.data || []
      if (reset) {
        posts.value = postsData
      } else {
        posts.value.push(...postsData)
      }
    }

    // 当显示全部时，需要同时加载图片和视频
    if (contentType.value === 'all') {
      // 加载所有媒体
      const mediaRes = await hubApi.getPublicMedia({
        page: currentPage.value,
        page_size: 40
      })
      if (reset) {
        mediaList.value = mediaRes.data.items || []
      } else {
        mediaList.value.push(...(mediaRes.data.items || []))
      }
    } else {
      // 加载图片
      if (showImages.value) {
        const imagesRes = await hubApi.getPublicMedia({
          page: currentPage.value,
          page_size: 20,
          type: 'image'
        })
        if (reset) {
          mediaList.value = imagesRes.data.items || []
        } else {
          mediaList.value.push(...(imagesRes.data.items || []))
        }
      }

      // 加载视频
      if (showVideos.value) {
        const videosRes = await hubApi.getPublicMedia({
          page: currentPage.value,
          page_size: 20,
          type: 'video'
        })
        if (reset) {
          mediaList.value = videosRes.data.items || []
        } else {
          mediaList.value.push(...(videosRes.data.items || []))
        }
      }
    }

    // 加载资源
    if (showResources.value) {
      const resourceRes = await hubApi.getPublicResources({
        page: currentPage.value,
        page_size: 20
      })
      if (reset) {
        resourceList.value = resourceRes.data.items || []
      } else {
        resourceList.value.push(...(resourceRes.data.items || []))
      }
    }

    // 按排序方式排序
    if (sortBy.value === 'popular' && reset) {
      sortContentByPopularity()
    }
  } catch (error) {
    console.error('加载内容失败:', error)
    ElMessage.error('加载内容失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 按热度排序
function sortContentByPopularity() {
  // 文章按浏览量排序
  posts.value.sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
  // 媒体按上传时间排序（暂无互动数据）
  mediaList.value.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  // 资源按下载量排序
  resourceList.value.sort((a, b) => (b.download_count || 0) - (a.download_count || 0))
}

// 内容类型切换
function handleContentTypeChange() {
  loadContent(true)
}

// 加载更多
function loadMore() {
  currentPage.value++
  loadContent(false)
}

// 获取媒体缩略图 URL
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

// 跳转到文章详情
function goToPost(id: number) {
  window.open(`/posts/${id}`, '_blank')
}

// 跳转到用户主页
function goToUserProfile(userId: number, username?: string) {
  if (username) {
    router.push({ name: 'UserProfile', params: { username } })
  } else {
    // 如果没有提供用户名，尝试从列表中查找
    const media = mediaList.value.find(m => m.uploader_id === userId)
    if (media?.uploader_name) {
      router.push({ name: 'UserProfile', params: { username: media.uploader_name } })
    }
  }
}

onMounted(() => {
  loadContent()
})
</script>

<style scoped lang="scss">
.plaza-page {
  min-height: 100vh;
  background: #f9fafb;
  padding-bottom: 40px;

  html.dark & {
    background: #0f172a;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }
}

.page-header {
  text-align: center;
  margin-bottom: 32px;

  .page-title {
    font-size: 32px;
    font-weight: 700;
    margin: 0 0 8px 0;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .page-subtitle {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.content-tabs {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;

  :deep(.el-radio-group) {
    flex-wrap: wrap;
  }

  .type-filter {
    margin-left: auto;

    @media (max-width: 768px) {
      margin-left: 0;
      width: 100%;
    }
  }

  :deep(.el-select) {
    width: 100px !important;
  }
}

.content-loading {
  padding: 40px 0;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.content-card {
  background: #ffffff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  cursor: pointer;

  html.dark & {
    background: #1e293b;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

// 文章卡片
.post-card {
  display: flex;
  flex-direction: column;
  padding: 16px;

  .post-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 8px;
    color: white;
    margin-bottom: 12px;
  }

  .post-info {
    flex: 1;

    .post-title {
      font-size: 16px;
      font-weight: 600;
      margin: 0 0 8px 0;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .post-summary {
      font-size: 13px;
      color: var(--el-text-color-secondary);
      margin: 0 0 8px 0;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .post-meta {
      display: flex;
      gap: 8px;
      font-size: 11px;
      color: var(--el-text-color-secondary);
      flex-wrap: wrap;

      span {
        display: flex;
        align-items: center;
        gap: 3px;
      }
    }
  }
}

// 媒体卡片
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
    padding: 10px;

    .media-title {
      font-size: 13px;
      font-weight: 500;
      margin: 0 0 6px 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .media-meta {
      font-size: 11px;
      color: var(--el-text-color-secondary);

      span {
        display: flex;
        align-items: center;
        gap: 3px;
      }

      .author-link {
        cursor: pointer;
        transition: color 0.2s;

        &:hover {
          color: #6366f1;
        }
      }
    }
  }
}

// 资源卡片
.resource-card {
  display: flex;
  flex-direction: column;
  padding: 16px;

  .resource-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #10b981, #059669);
    border-radius: 8px;
    color: white;
    margin-bottom: 12px;
  }

  .resource-info {
    flex: 1;

    .resource-title {
      font-size: 14px;
      font-weight: 500;
      margin: 0 0 6px 0;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .resource-desc {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin: 0 0 8px 0;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .resource-meta {
      display: flex;
      gap: 8px;
      font-size: 11px;
      color: var(--el-text-color-secondary);
      flex-wrap: wrap;

      span {
        display: flex;
        align-items: center;
        gap: 3px;
      }
    }
  }
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}
</style>
