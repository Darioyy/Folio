<template>
  <div class="published-files-page">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <div class="page-title">
        <h2>公共发布区</h2>
        <p class="page-subtitle">管理已发布到公共大厅的文件</p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon :size="28"><Picture /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ mediaItems.filter(item => item.file_type === 'image' || item.type === 'image').length }}</div>
          <div class="stat-label">图片</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon :size="28"><VideoPlay /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ mediaItems.filter(item => item.file_type === 'video' || item.type === 'video').length }}</div>
          <div class="stat-label">视频</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon :size="28"><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ resourceItems.length }}</div>
          <div class="stat-label">资源</div>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-radio-group v-model="fileType" size="small" @change="loadFiles">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="image">图片</el-radio-button>
        <el-radio-button value="video">视频</el-radio-button>
        <el-radio-button value="resource">资源</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 文件列表 -->
    <div v-else-if="displayItems.length > 0" class="file-list">
      <div class="file-grid">
        <div
          v-for="file in displayItems"
          :key="file.id"
          class="file-card"
          :class="getFileCardClass(file)"
        >
          <!-- 媒体预览 -->
          <div class="file-preview" @click="handlePreview(file)">
            <template v-if="file.file_type === 'image' || file.type === 'image'">
              <img :src="getFileUrl(file.file_path)" :alt="file.title" />
            </template>
            <template v-else-if="file.file_type === 'video' || file.type === 'video'">
              <video
                :src="getFileUrl(file.file_path)"
                :poster="file.thumbnail_path ? getFileUrl(file.thumbnail_path) : undefined"
                muted
              />
              <div class="play-overlay">
                <el-icon :size="32"><VideoPlay /></el-icon>
              </div>
            </template>
            <!-- 资源预览 -->
            <template v-else>
              <div class="file-preview document">
                <el-icon><Document /></el-icon>
              </div>
            </template>
            <div class="file-visibility public">
              <el-icon><View /></el-icon>
            </div>
          </div>

          <!-- 文件信息 -->
          <div class="file-info">
            <h4 class="file-title" :title="file.title">{{ file.title }}</h4>
            <p class="file-meta">
              <span>{{ getFileTypeLabel(file) }}</span>
              <span v-if="file.file_size">· {{ formatSize(file.file_size) }}</span>
            </p>
          </div>

          <!-- 文件操作 -->
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

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty description="还没有发布任何文件到公共大厅">
        <el-button type="primary" @click="goToPrivate">
          去发布文件
        </el-button>
      </el-empty>
    </div>

    <!-- 文件预览对话框 -->
    <FilePreview
      v-model="previewVisible"
      :file="currentFile"
      type="media"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Picture,
  VideoPlay,
  Document,
  View
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import FilePreview from '@/components/business/FilePreview.vue'
import { hubApi } from '@/api/modules/hub'
import type { HubMedia, HubResource } from '@/api/modules/hub'

const router = useRouter()

const fileType = ref<string>('')
const loading = ref(false)
const toggleLoading = ref<number | null>(null)

const mediaItems = ref<HubMedia[]>([])
const resourceItems = ref<HubResource[]>([])

// 预览相关
const previewVisible = ref(false)
const currentFile = ref<any>(null)

// 显示的文件列表（根据筛选条件）
const displayItems = computed(() => {
  let items: any[] = []

  if (fileType.value === '' || fileType.value === 'image' || fileType.value === 'video') {
    items.push(...mediaItems.value)
  }
  if (fileType.value === '' || fileType.value === 'resource') {
    items.push(...resourceItems.value)
  }

  return items
})

// 获取文件卡片样式类
function getFileCardClass(file: any): string {
  if (file.file_type === 'image' || file.type === 'image') return 'media-card'
  if (file.file_type === 'video' || file.type === 'video') return 'media-card'
  return 'resource-card'
}

// 加载文件列表
async function loadFiles() {
  loading.value = true
  try {
    const [mediaRes, resourceRes] = await Promise.all([
      hubApi.getUserMedia({
        page: 1,
        page_size: 100,
        visibility: 'public'
      }),
      hubApi.getUserResources({
        page: 1,
        page_size: 100,
        visibility: 'public'
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

// 获取文件类型标签
function getFileTypeLabel(file: any): string {
  if (file.file_type === 'image' || file.type === 'image') return '图片'
  if (file.file_type === 'video' || file.type === 'video') return '视频'
  if (file.file_name) return file.file_name.split('.').pop()?.toUpperCase() || '资源'
  return '资源'
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
async function handleToggleVisibility(file: any) {
  toggleLoading.value = file.id
  try {
    if (file.file_type === 'image' || file.file_type === 'video') {
      const res = await hubApi.toggleMediaVisibility(file.id)
      file.visibility = res.data.visibility
    } else {
      const res = await hubApi.toggleResourceVisibility(file.id)
      file.visibility = res.data.visibility
    }
    ElMessage.success('已撤回为私有')
    // 重新加载列表
    await loadFiles()
  } catch (error) {
    console.error('切换可见性失败:', error)
    ElMessage.error('切换可见性失败')
  } finally {
    toggleLoading.value = null
  }
}

// 预览文件
function handlePreview(file: any) {
  currentFile.value = file
  previewVisible.value = true
}

// 跳转到私有文件
function goToPrivate() {
  router.push('/hub/private')
}

onMounted(() => {
  loadFiles()
})
</script>

<style scoped lang="scss">
.published-files-page {
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
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;

  .stat-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

    html.dark & {
      background: #1e293b;
    }

    .stat-icon {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      border-radius: 10px;
      color: white;
      flex-shrink: 0;
    }

    .stat-content {
      .stat-value {
        font-size: 20px;
        font-weight: 700;
        color: var(--el-text-color-primary);
        line-height: 1;
      }

      .stat-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin-top: 2px;
      }
    }
  }
}

// 筛选栏
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding: 12px 16px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  html.dark & {
    background: #1e293b;
  }
}

// 文件列表
.file-list {
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

    .play-overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.3);
      color: white;
    }

    &.document {
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f9fafb;

      html.dark & {
        background: rgba(255, 255, 255, 0.05);
      }

      .el-icon {
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
      background: #10b981;
      color: #fff;
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
