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
        <img :src="fileUrl" :alt="title" @load="handleLoad" @error="handleError" />
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
        <iframe :src="fileUrl" frameborder="0" @load="handleLoad" @error="handleError" />
        <el-skeleton v-if="loading" :rows="8" animated />
      </template>

      <!-- 不支持预览 / 文档 -->
      <template v-else>
        <div class="preview-unsupported">
          <div class="unsupported-icon">
            <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" width="52" height="52">
              <path d="M8 6h22l10 10v26a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2z"/>
              <polyline points="30,6 30,16 40,16"/>
              <line x1="16" y1="24" x2="32" y2="24"/>
              <line x1="16" y1="30" x2="26" y2="30"/>
            </svg>
          </div>
          <p class="unsupported-name">{{ props.file?.file_name || title }}</p>
          <p class="unsupported-hint">暂不支持预览此格式</p>
          <button v-if="props.file?.id" class="download-btn-inline" @click="confirmDownload">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
              <path d="M8 3v8M4 8l4 4 4-4"/>
              <path d="M2 13h12"/>
            </svg>
            下载文件
          </button>
        </div>
      </template>
    </div>

    <!-- 预览失败提示 -->
    <el-alert
      v-if="error"
      title="预览失败"
      type="error"
      :description="error"
      show-icon
      :closable="false"
      style="margin-top: 12px"
    />

    <!-- 底部操作栏（可预览时显示下载） -->
    <template v-if="fileType !== 'unsupported' && fileType !== '' && props.file?.id" #footer>
      <div class="preview-footer">
        <span class="file-info">{{ props.file?.file_name || '' }}</span>
        <button class="download-btn-footer" @click="confirmDownload">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="13" height="13">
            <path d="M8 3v8M4 8l4 4 4-4"/>
            <path d="M2 13h12"/>
          </svg>
          下载
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { FullScreen, Crop } from '@element-plus/icons-vue'
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
  type?: 'media' | 'document' | 'resource'
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  type: 'media'
})

const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const error = ref('')
const isFullscreen = ref(false)
const videoRef = ref<HTMLVideoElement>()

const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// 文件类型检测（从扩展名+category）
const fileType = computed(() => {
  if (!props.file) return ''
  const ext = (props.file.file_name || '').split('.').pop()?.toLowerCase() || ''
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'avif'].includes(ext)) return 'image'
  if (['mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv'].includes(ext)) return 'video'
  if (ext === 'pdf') return 'pdf'
  if (props.file.file_category === 'image') return 'image'
  if (props.file.file_category === 'video') return 'video'
  return 'unsupported'
})

const title = computed(() => props.file?.title || props.file?.file_name || '文件预览')

// 统一使用 files API
const fileUrl = computed(() => {
  if (!props.file?.id) return ''
  if (fileType.value === 'image' || fileType.value === 'pdf') {
    return `${apiBase}/files/${props.file.id}/download`
  }
  if (fileType.value === 'video') {
    return `${apiBase}/files/${props.file.id}/download`
  }
  return ''
})

const downloadUrl = computed(() =>
  props.file?.id ? `${apiBase}/files/${props.file.id}/download` : ''
)

function toggleFullscreen() { isFullscreen.value = !isFullscreen.value }

function confirmDownload() {
  if (!downloadUrl.value) return
  const link = document.createElement('a')
  link.href = downloadUrl.value
  link.download = props.file?.file_name || 'download'
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('开始下载')
}

function handleLoad() { loading.value = false; error.value = '' }
function handleError() { loading.value = false; error.value = '文件加载失败，请稍后重试' }

function handleClose() {
  if (videoRef.value) videoRef.value.pause()
  loading.value = false
  error.value = ''
}

watch(() => props.file, () => {
  error.value = ''
  // 仅可预览类型才显示 loading
  loading.value = ['image', 'video', 'pdf'].includes(fileType.value)
}, { immediate: true })
</script>

<style scoped lang="scss">
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;

  .preview-title {
    font-size: 15px;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.preview-container {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $radius-md;
  overflow: hidden;

  &.preview-image, &.preview-video {
    background: #000;
    min-height: 300px;
    html.dark & { background: #141720; }
  }

  &.preview-pdf {
    min-height: 70vh;
  }

  img { max-width: 100%; max-height: 70vh; object-fit: contain; }
  video { max-width: 100%; max-height: 70vh; }
  iframe { width: 100%; height: 70vh; border: none; }
}

// 不支持预览
.preview-unsupported {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 32px;
  min-height: 200px;
  justify-content: center;
}

.unsupported-icon {
  color: var(--color-text-muted);
  opacity: 0.5;
}

.unsupported-name {
  font-size: $font-sm;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0;
  max-width: 360px;
  text-align: center;
  word-break: break-all;
}

.unsupported-hint {
  font-size: $font-xs;
  color: var(--color-text-muted);
  margin: 0;
}

.download-btn-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  border-radius: $radius-md;
  font-size: $font-sm;
  cursor: pointer;
  transition: border-color $transition-fast, color $transition-fast, background $transition-fast;
  margin-top: 4px;

  &:hover {
    border-color: $color-primary;
    color: $color-primary;
    background: rgba(90, 103, 216, 0.05);
  }
}

// 底部操作栏
.preview-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-md;
}

.file-info {
  font-size: $font-xs;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  flex: 1;
}

.download-btn-footer {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  border-radius: $radius-md;
  font-size: $font-sm;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color $transition-fast, color $transition-fast;

  &:hover { border-color: $color-primary; color: $color-primary; }
}

:deep(.el-dialog.is-fullscreen) {
  .preview-container img, .preview-container video { max-height: calc(100vh - 120px); }
  .preview-container iframe { height: calc(100vh - 120px); }
}
</style>
