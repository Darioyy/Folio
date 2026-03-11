<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="90%"
    :fullscreen="isFullscreen"
    destroy-on-close
    @close="handleClose"
  >
    <template #header>
      <div class="preview-header">
        <span class="preview-title">{{ title }}</span>
        <div class="preview-actions">
          <el-button
            :icon="isFullscreen ? Crop : FullScreen"
            circle
            text
            @click="toggleFullscreen"
          />
        </div>
      </div>
    </template>

    <div class="preview-container" :class="`preview-${fileType}`">
      <!-- 图片预览 -->
      <template v-if="fileType === 'image' && fileUrl">
        <img
          :src="fileUrl"
          :alt="title"
          @load="handleLoad"
          @error="handleError"
        />
        <el-skeleton v-if="loading" :rows="1" animated />
      </template>

      <!-- 视频预览 -->
      <template v-else-if="fileType === 'video' && fileUrl">
        <video
          ref="videoRef"
          :src="fileUrl"
          controls
          autoplay
          @loadstart="loading = true"
          @canplay="loading = false"
          @error="handleError"
        />
        <el-skeleton v-if="loading" :rows="1" animated />
      </template>

      <!-- PDF 预览 -->
      <template v-else-if="fileType === 'pdf' && fileUrl">
        <iframe
          :src="fileUrl"
          frameborder="0"
          @load="handleLoad"
          @error="handleError"
        />
        <el-skeleton v-if="loading" :rows="8" animated />
      </template>

      <!-- 资源文件预览（不支持直接预览，显示信息） -->
      <template v-else-if="fileType === 'resource'">
        <div class="preview-resource">
          <el-icon :size="80"><Folder /></el-icon>
          <h3>{{ title }}</h3>
          <p v-if="props.file?.file_name" class="file-name">{{ props.file.file_name }}</p>
          <p v-if="props.file?.description" class="file-description">{{ props.file.description }}</p>
          <p v-if="props.file?.file_size" class="file-size">文件大小: {{ formatFileSize(props.file.file_size) }}</p>
        </div>
      </template>

      <!-- 不支持的文件类型 -->
      <template v-else>
        <div class="preview-unsupported">
          <el-icon :size="64"><Document /></el-icon>
          <p>此文件类型不支持预览</p>
        </div>
      </template>

      <!-- 加载状态 -->
      <el-skeleton v-if="loading && fileType !== 'image'" :rows="6" animated />
    </div>

    <!-- 预览失败提示 -->
    <el-alert
      v-if="error"
      title="预览失败"
      type="error"
      :description="error"
      show-icon
      :closable="false"
    />

    <!-- 底部操作栏 -->
    <template #footer v-if="canDownload">
      <div class="preview-footer">
        <span class="file-info">{{ props.file?.file_name || '' }}</span>
        <el-button type="primary" :icon="Download" @click="showDownloadConfirm = true">
          下载文件
        </el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 下载确认对话框 -->
  <el-dialog
    v-model="showDownloadConfirm"
    title="确认下载"
    width="400px"
  >
    <p>确定要下载文件 <strong>{{ props.file?.file_name || title }}</strong> 吗？</p>
    <template #footer>
      <el-button @click="showDownloadConfirm = false">取消</el-button>
      <el-button type="primary" @click="confirmDownload">
        确认下载
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Document, Download, FullScreen, Crop, Folder } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  modelValue: boolean
  file?: {
    id: number
    title: string
    file_category?: string
    file_name?: string
    file_path?: string
    file_size?: number
    description?: string
  }
  type?: 'media' | 'resource'
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  type: 'media'
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(true)
const error = ref('')
const isFullscreen = ref(false)
const videoRef = ref<HTMLVideoElement>()

// 下载确认对话框
const showDownloadConfirm = ref(false)

// 文件类型
const fileType = computed(() => {
  if (!props.file) return ''

  // 资源文件类型
  if (props.type === 'resource') {
    const fileName = props.file.file_name || ''
    const ext = fileName.split('.').pop()?.toLowerCase() || ''

    // PDF 可以预览
    if (ext === 'pdf') return 'pdf'

    // 图片可以预览
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) {
      return 'image'
    }

    // 其他资源文件显示信息
    return 'resource'
  }

  const fileName = props.file.file_name || ''
  const ext = fileName.split('.').pop()?.toLowerCase() || ''

  // 图片类型
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) {
    return 'image'
  }

  // 视频类型
  if (['mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv'].includes(ext)) {
    return 'video'
  }

  // PDF 类型
  if (ext === 'pdf') {
    return 'pdf'
  }

  // 根据文件类型判断
  if (props.file.file_category === 'image') return 'image'
  if (props.file.file_category === 'video') return 'video'

  return 'unsupported'
})

// 文件标题
const title = computed(() => props.file?.title || '文件预览')

// 是否可下载
const canDownload = computed(() => {
  return fileType.value !== 'unsupported' && props.file?.id
})

// 文件 URL
const fileUrl = computed(() => {
  if (!props.file?.id) return ''

  const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1'

  if (props.type === 'media') {
    return `${apiBase}/media/${props.file.id}/view`
  }

  // 资源文件 - 支持预览的格式
  if (props.type === 'resource') {
    const fileName = props.file.file_name || ''
    const ext = fileName.split('.').pop()?.toLowerCase() || ''

    // PDF 和图片可以直接预览
    if (ext === 'pdf' || ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)) {
      return `${apiBase}/resources/${props.file.id}/download`
    }
  }

  return ''
})

// 下载 URL
const downloadUrl = computed(() => {
  if (!props.file?.id) return ''
  const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1'

  if (props.type === 'resource') {
    return `${apiBase}/resources/${props.file.id}/download`
  }

  // 媒体文件也可以下载
  return `${apiBase}/media/${props.file.id}/view`
})

// 切换全屏
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (!bytes || bytes === 0) return '未知大小'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 下载文件
function handleDownload() {
  showDownloadConfirm.value = true
}

// 确认下载
function confirmDownload() {
  if (!downloadUrl.value) return

  showDownloadConfirm.value = false

  // 创建隐藏的 a 标签来触发下载
  const link = document.createElement('a')
  link.href = downloadUrl.value
  link.download = props.file?.file_name || 'download'
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  ElMessage.success('开始下载')
}

// 加载完成
function handleLoad() {
  loading.value = false
  error.value = ''
}

// 加载失败
function handleError() {
  loading.value = false
  error.value = '文件加载失败，请稍后重试'
}

// 关闭对话框
function handleClose() {
  // 停止视频播放
  if (videoRef.value) {
    videoRef.value.pause()
  }
  loading.value = true
  error.value = ''
}

// 监听文件变化
watch(() => props.file, () => {
  if (props.file) {
    loading.value = true
    error.value = ''
  }
}, { immediate: true })
</script>

<style scoped lang="scss">
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;

  .preview-title {
    font-size: 16px;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .preview-actions {
    display: flex;
    gap: 8px;
    margin-left: 16px;
  }
}

.preview-container {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  border-radius: 8px;
  overflow: hidden;

  html.dark & {
    background: #0f172a;
  }

  // 图片预览
  &.preview-image {
    img {
      max-width: 100%;
      max-height: 70vh;
      object-fit: contain;
    }
  }

  // 视频预览
  &.preview-video {
    video {
      max-width: 100%;
      max-height: 70vh;
    }
  }

  // PDF 预览
  &.preview-pdf {
    iframe {
      width: 100%;
      height: 70vh;
      border: none;
    }
  }

  // 资源文件预览
  &.preview-resource {
    min-height: 400px;

    .preview-resource {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 16px;
      padding: 40px;

      .el-icon {
        color: #10b981;
      }

      h3 {
        font-size: 24px;
        margin: 0;
      }

      .file-name {
        font-size: 16px;
        color: var(--el-text-color-regular);
        margin: 0;
      }

      .file-description {
        font-size: 14px;
        color: var(--el-text-color-secondary);
        margin: 0;
        max-width: 500px;
        text-align: center;
      }

      .file-size {
        font-size: 14px;
        color: var(--el-text-color-secondary);
        margin: 0;
      }
    }
  }

  // 不支持的文件类型
  .preview-unsupported {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    padding: 40px;
    color: var(--el-text-color-secondary);

    .el-icon {
      color: var(--el-text-color-placeholder);
    }

    p {
      font-size: 16px;
      margin: 0;
    }
  }
}

// 底部操作栏
.preview-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .file-info {
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

// 全屏模式
:deep(.el-dialog.is-fullscreen) {
  .preview-container {
    min-height: calc(100vh - 120px);

    img,
    video {
      max-height: calc(100vh - 120px);
    }

    iframe {
      height: calc(100vh - 120px);
    }
  }
}
</style>
