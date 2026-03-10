<template>
  <div class="private-files-page">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <div class="page-title">
        <h2>私有文件库</h2>
        <p class="page-subtitle">管理您的私有文件，控制访问权限</p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon :size="28"><Picture /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ mediaItems.length }}</div>
          <div class="stat-label">媒体文件</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon :size="28"><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ resourceItems.length }}</div>
          <div class="stat-label">资源文件</div>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-radio-group v-model="fileType" size="small" @change="loadFiles">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="image">图片</el-radio-button>
        <el-radio-button value="video">视频</el-radio-button>
      </el-radio-group>

      <el-divider direction="vertical" style="height: 24px" />

      <el-radio-group v-model="visibility" size="small" @change="loadFiles">
        <el-radio-button value="private">私有</el-radio-button>
        <el-radio-button value="public">公共</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 文件列表 -->
    <div v-else-if="mediaItems.length > 0 || resourceItems.length > 0" class="file-list">
      <!-- 媒体文件 -->
      <div v-if="mediaItems.length > 0" class="section">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Picture /></el-icon>
            媒体文件
          </h3>
          <el-tag size="small">{{ mediaItems.length }}</el-tag>
        </div>
        <div class="file-grid">
          <div
            v-for="file in mediaItems"
            :key="file.id"
            class="file-card media-card"
            :class="{ 'is-public': file.visibility === 'public' }"
          >
            <div class="file-preview" @click="handlePreview(file)">
              <img
                v-if="file.file_type === 'image'"
                :src="getFileUrl(file.thumbnail_path || file.file_path)"
                :alt="file.title"
                @error="(e) => { if (file.thumbnail_path) (e.target as HTMLImageElement).src = getFileUrl(file.file_path) }"
              />
              <video
                v-else
                :src="getFileUrl(file.file_path)"
                :poster="file.thumbnail_path ? getFileUrl(file.thumbnail_path) : undefined"
                muted
                preload="none"
              />
              <div class="file-visibility" :class="file.visibility">
                <el-icon>
                  <Lock v-if="file.visibility === 'private'" />
                  <Unlock v-else />
                </el-icon>
              </div>
            </div>
            <div class="file-info">
              <h4 class="file-title" :title="file.title">{{ file.title }}</h4>
              <p class="file-meta">
                <span>{{ file.file_type === 'image' ? '图片' : '视频' }}</span>
                <span v-if="file.file_size">· {{ formatSize(file.file_size) }}</span>
              </p>
            </div>
            <div class="file-actions">
              <el-switch
                :model-value="file.visibility === 'public'"
                @change="handleToggleVisibility(file)"
                size="small"
                :disabled="toggleLoading === file.id"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 资源文件 -->
      <div v-if="resourceItems.length > 0" class="section">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Document /></el-icon>
            资源文件
          </h3>
          <el-tag size="small">{{ resourceItems.length }}</el-tag>
        </div>
        <div class="file-grid">
          <div
            v-for="file in resourceItems"
            :key="file.id"
            class="file-card resource-card"
            :class="{ 'is-public': file.visibility === 'public' }"
          >
            <div class="file-preview document">
              <el-icon><Document /></el-icon>
              <div class="file-visibility" :class="file.visibility">
                <el-icon>
                  <Lock v-if="file.visibility === 'private'" />
                  <Unlock v-else />
                </el-icon>
              </div>
            </div>
            <div class="file-info">
              <h4 class="file-title" :title="file.title">{{ file.title }}</h4>
              <p class="file-meta">
                <span>{{ file.file_name.split('.').pop()?.toUpperCase() }}</span>
                <span v-if="file.file_size">· {{ formatSize(file.file_size) }}</span>
              </p>
            </div>
            <div class="file-actions">
              <el-switch
                :model-value="file.visibility === 'public'"
                @change="handleToggleResourceVisibility(file)"
                size="small"
                :disabled="toggleLoading === file.id"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty description="暂无文件">
        <el-button type="primary" @click="goToUpload">上传文件</el-button>
      </el-empty>
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
import { useRouter } from 'vue-router'
import {
  Picture,
  Document,
  Lock,
  Unlock
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import FilePreview from '@/components/business/FilePreview.vue'
import { hubApi } from '@/api/modules/hub'
import type { HubMedia, HubResource } from '@/api/modules/hub'

const router = useRouter()

const fileType = ref<string>('')
const visibility = ref<string>('')
const loading = ref(false)
const toggleLoading = ref<number | null>(null)

const mediaItems = ref<HubMedia[]>([])
const resourceItems = ref<HubResource[]>([])

// 预览相关
const previewVisible = ref(false)
const currentFile = ref<HubMedia | null>(null)
const currentFileType = ref<'media' | 'resource'>('media')

// 总文件数
const totalCount = computed(() => mediaItems.value.length + resourceItems.value.length)

// 私有文件数
const privateCount = computed(() => {
  const mediaPrivate = mediaItems.value.filter(f => f.visibility === 'private').length
  const resourcePrivate = resourceItems.value.filter(f => f.visibility === 'private').length
  return mediaPrivate + resourcePrivate
})

// 加载文件列表
async function loadFiles() {
  loading.value = true
  try {
    const [mediaRes, resourceRes] = await Promise.all([
      hubApi.getUserMedia({
        page: 1,
        page_size: 100,
        visibility: visibility || undefined,
        type: fileType || undefined
      }),
      hubApi.getUserResources({
        page: 1,
        page_size: 100,
        visibility: visibility || undefined
      })
    ])

    mediaItems.value = mediaRes.data.items
    resourceItems.value = resourceRes.data.items
  } catch (error) {
    console.error('加载文件失败:', error)
    ElMessage.error('加载文件失败')
  } finally {
    loading.value = false
  }
}

// 获取文件 URL
function getFileUrl(path: string): string {
  if (import.meta.env.DEV) {
    return `http://localhost:5000/uploads/${path}`
  }
  return `/uploads/${path}`
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (!bytes) return '未知'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// 切换可见性
async function handleToggleVisibility(file: HubMedia) {
  toggleLoading.value = file.id
  try {
    const res = await hubApi.toggleMediaVisibility(file.id)
    file.visibility = res.data.visibility as 'private' | 'public'
    ElMessage.success(res.data.visibility === 'public' ? '已设为公共' : '已设为私有')
  } catch (error) {
    console.error('切换可见性失败:', error)
    ElMessage.error('切换可见性失败')
  } finally {
    toggleLoading.value = null
  }
}

// 切换资源可见性
async function handleToggleResourceVisibility(file: HubResource) {
  toggleLoading.value = file.id
  try {
    const res = await hubApi.toggleResourceVisibility(file.id)
    file.visibility = res.data.visibility as 'private' | 'public'
    ElMessage.success(res.data.visibility === 'public' ? '已设为公共' : '已设为私有')
  } catch (error) {
    console.error('切换可见性失败:', error)
    ElMessage.error('切换可见性失败')
  } finally {
    toggleLoading.value = null
  }
}

// 预览文件
function handlePreview(file: HubMedia) {
  currentFile.value = file
  currentFileType.value = 'media'
  previewVisible.value = true
}

// 跳转到上传
function goToUpload() {
  router.push('/hub/private')
}

onMounted(() => {
  loadFiles()
})
</script>

<style scoped lang="scss">
.private-files-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;

  .page-title {
    h2 {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 24px;
      font-weight: 600;
      margin: 0 0 4px 0;
      color: var(--el-text-color-primary);
    }

    .page-subtitle {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      margin: 0;
    }
  }
}

// 统计卡片
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;

  .stat-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

    html.dark & {
      background: #1e293b;
    }

    .stat-icon {
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

    .stat-content {
      .stat-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--el-text-color-primary);
        line-height: 1;
      }

      .stat-label {
        font-size: 13px;
        color: var(--el-text-color-secondary);
        margin-top: 4px;
      }
    }
  }
}

// 筛选栏
.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  html.dark & {
    background: #1e293b;
  }
}

// 文件列表
.file-list {
  .section {
    margin-bottom: 32px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
      margin: 0;
      color: var(--el-text-color-primary);
    }
  }

  .file-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }
}

.file-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;

  html.dark & {
    background: #1e293b;
    border-color: #334155;
  }

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
  }

  &.is-public {
    border-color: #10b981;
  }

  .file-preview {
    position: relative;
    aspect-ratio: 16 / 10;
    overflow: hidden;
    cursor: pointer;

    img,
    video {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    &.document {
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f9fafb;

      html.dark & {
        background: rgba(255, 255, 255, 0.05);
      }

      > .el-icon {
        font-size: 48px;
        color: var(--el-text-color-placeholder);
      }
    }

    .file-visibility {
      position: absolute;
      top: 8px;
      right: 8px;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;

      &.private {
        background: #6366f1;
        color: #fff;
      }

      &.public {
        background: #10b981;
        color: #fff;
      }
    }
  }

  .file-info {
    padding: 12px 16px;

    .file-title {
      font-size: 14px;
      font-weight: 500;
      margin: 0 0 6px 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--el-text-color-primary);
    }

    .file-meta {
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

  .file-actions {
    padding: 8px 16px 12px;
    border-top: 1px solid #f3f4f6;

    html.dark & {
      border-top-color: #334155;
    }
  }
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.loading-container {
  padding: 40px 0;
}
</style>
