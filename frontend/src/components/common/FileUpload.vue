<template>
  <div class="file-upload">
    <!-- 拖拽上传区域 -->
    <el-upload
      ref="uploadRef"
      :action="uploadUrl"
      :http-request="handleUpload"
      :before-upload="beforeUpload"
      :on-change="handleChange"
      :on-progress="handleProgress"
      :on-success="handleSuccess"
      :on-error="handleError"
      :on-remove="handleRemove"
      :file-list="fileList"
      :multiple="multiple"
      :accept="accept"
      :drag="drag"
      :limit="limit"
      :disabled="disabled"
      :auto-upload="false"
      class="upload-container"
    >
      <template #trigger>
        <div class="upload-trigger" :class="{ 'is-disabled': disabled }">
          <el-icon class="upload-icon" :size="48">
            <UploadFilled />
          </el-icon>
          <div class="upload-text">
            <p class="upload-tip">{{ dragText }}</p>
            <p class="upload-hint">{{ acceptText }}</p>
          </div>
        </div>
      </template>
    </el-upload>

    <!-- 文件列表 -->
    <div v-if="showFileList && fileList.length > 0" class="file-list">
      <div
        v-for="file in fileList"
        :key="file.uid"
        class="file-item"
        :class="{
          'is-duplicate': file.status === 'duplicate',
          'is-uploading': file.status === 'uploading',
          'is-success': file.status === 'success',
          'is-error': file.status === 'error'
        }"
      >
        <div class="file-info">
          <el-icon class="file-icon" :size="20">
            <Document v-if="isDocument(file.name)" />
            <Picture v-else-if="isImage(file.name)" />
            <VideoPlay v-else-if="isVideo(file.name)" />
            <Folder v-else />
          </el-icon>
          <div class="file-details">
            <span class="file-name" :title="file.name">{{ file.name }}</span>
            <span class="file-size">{{ formatSize(file.size) }}</span>
          </div>
        </div>

        <!-- 上传进度 -->
        <div v-if="file.status === 'uploading'" class="file-progress">
          <el-progress
            :percentage="file.percentage || 0"
            :stroke-width="4"
            :show-text="false"
          />
          <span class="progress-text">{{ file.percentage || 0 }}%</span>
        </div>

        <!-- 状态标签 -->
        <div v-else class="file-status">
          <el-tag v-if="file.status === 'duplicate'" type="warning" size="small">
            文件重复
          </el-tag>
          <el-tag v-else-if="file.status === 'success'" type="success" size="small">
            上传成功
          </el-tag>
          <el-tag v-else-if="file.status === 'error'" type="danger" size="small">
            上传失败
          </el-tag>
          <el-tag v-else-if="file.status === 'pending'" type="info" size="small">
            等待上传
          </el-tag>
        </div>

        <!-- 操作按钮 -->
        <div class="file-actions">
          <el-button
            v-if="file.status === 'duplicate'"
            link
            type="primary"
            size="small"
            @click="handleReupload(file)"
          >
            重新上传
          </el-button>
          <el-button
            link
            type="danger"
            size="small"
            @click="handleRemove(file)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="showActions && fileList.length > 0" class="upload-actions">
      <span class="upload-summary">
        已选择 {{ fileList.length }} 个文件
        <span v-if="duplicateCount > 0" class="duplicate-text">
          （{{ duplicateCount }} 个重复）
        </span>
      </span>
      <div class="action-buttons">
        <el-button size="small" @click="clearFiles">清空</el-button>
        <el-button
          type="primary"
          size="small"
          :loading="uploading"
          :disabled="canUpload"
          @click="startUpload"
        >
          {{ uploading ? '上传中...' : '开始上传' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, type UploadInstance, type UploadProps, type UploadRawFile, type UploadUserFile } from 'element-plus'
import {
  UploadFilled,
  Document,
  Picture,
  VideoPlay,
  Folder,
  Delete
} from '@element-plus/icons-vue'
import SparkMD5 from 'spark-md5'

export interface FileUploadOptions {
  multiple?: boolean
  accept?: string
  limit?: number
  drag?: boolean
  maxSize?: number // MB
  dragText?: string
  acceptText?: string
  uploadUrl?: string
  checkDuplicate?: (file: UploadRawFile) => Promise<boolean>
  onUpload?: (file: UploadRawFile, formData: FormData) => Promise<any>
  showFileList?: boolean
  showActions?: boolean
}

const props = withDefaults(defineProps<FileUploadOptions>(), {
  multiple: true,
  accept: '*',
  limit: 10,
  drag: true,
  maxSize: 100,
  dragText: '拖拽文件到此处或点击上传',
  acceptText: '支持所有文件格式',
  showFileList: true,
  showActions: true
})

const emit = defineEmits<{
  'update:file-list': [files: UploadUserFile[]]
  'upload-success': [response: any, file: UploadUserFile]
  'upload-error': [error: Error, file: UploadUserFile]
  'duplicate-detected': [file: UploadUserFile]
}>()

const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadUserFile[]>([])
const uploading = ref(false)
const existingFileHashes = ref<Set<string>>(new Set())

// 上传URL
const uploadUrl = computed(() => props.uploadUrl || '')

// 是否禁用
const disabled = computed(() => uploading.value || fileList.value.length >= props.limit)

// 可以上传
const canUpload = computed(() => {
  return fileList.value.length === 0 ||
         fileList.value.every(f => f.status === 'duplicate' || f.status === 'error')
})

// 重复文件数量
const duplicateCount = computed(() => {
  return fileList.value.filter(f => f.status === 'duplicate').length
})

// 计算文件hash
async function calculateHash(file: File): Promise<string> {
  return new Promise((resolve) => {
    const spark = new SparkMD5.ArrayBuffer()
    const fileReader = new FileReader()
    const chunkSize = 2 * 1024 * 1024 // 2MB
    let offset = 0

    fileReader.onload = (e) => {
      spark.append(e.target?.result as ArrayBuffer)
      offset += chunkSize

      if (offset < file.size) {
        readNextChunk()
      } else {
        resolve(spark.end())
      }
    }

    const readNextChunk = () => {
      const slice = file.slice(offset, offset + chunkSize)
      fileReader.readAsArrayBuffer(slice)
    }

    readNextChunk()
  })
}

// 文件上传前验证
async function beforeUpload(file: UploadRawFile) {
  // 检查文件大小
  const isLtMaxSize = file.size / 1024 / 1024 < props.maxSize
  if (!isLtMaxSize) {
    ElMessage.error(`文件大小不能超过 ${props.maxSize}MB!`)
    return false
  }

  // 检查重复
  if (props.checkDuplicate) {
    try {
      const isDuplicate = await props.checkDuplicate(file)
      if (isDuplicate) {
        ElMessage.warning(`文件 "${file.name}" 已存在!`)
        return false
      }
    } catch (error) {
      console.error('检查文件重复失败:', error)
    }
  }

  return true
}

// 文件状态改变
async function handleChange(file: UploadUserFile, uploadFiles: UploadUserFile[]) {
  // 检查是否重复（基于文件名和大小）
  const isDuplicate = uploadFiles.some(
    f => f.uid !== file.uid &&
         f.name === file.name &&
         f.size === file.size &&
         f.status !== 'duplicate'
  )

  if (isDuplicate) {
    file.status = 'duplicate' as any
    emit('duplicate-detected', file)
  }

  fileList.value = uploadFiles
  emit('update:file-list', uploadFiles)
}

// 上传进度
function handleProgress(event: any, file: UploadUserFile) {
  file.percentage = Math.floor(event.percent)
}

// 上传成功
function handleSuccess(response: any, file: UploadUserFile) {
  file.status = 'success'
  ElMessage.success(`"${file.name}" 上传成功`)
  emit('upload-success', response, file)
}

// 上传失败
function handleError(error: Error, file: UploadUserFile) {
  file.status = 'error'
  ElMessage.error(`"${file.name}" 上传失败`)
  emit('upload-error', error, file)
}

// 移除文件
function handleRemove(file: UploadUserFile) {
  const index = fileList.value.findIndex(f => f.uid === file.uid)
  if (index > -1) {
    fileList.value.splice(index, 1)
  }
  emit('update:file-list', fileList.value)
}

// 自定义上传处理
async function handleUpload(options: any) {
  const { file, onProgress, onSuccess, onError } = options

  if (props.onUpload) {
    try {
      const formData = new FormData()
      formData.append('file', file)

      // 模拟进度
      let progress = 0
      const progressInterval = setInterval(() => {
        progress += 10
        if (progress <= 100) {
          onProgress({ percent: progress })
        }
      }, 200)

      const response = await props.onUpload(file, formData)

      clearInterval(progressInterval)
      onProgress({ percent: 100 })
      onSuccess(response)
    } catch (error) {
      onError(error)
    }
  } else {
    // 默认行为 - 实际上不会走到这里因为http-request被覆盖了
    onSuccess({})
  }
}

// 重新上传
function handleReupload(file: UploadUserFile) {
  file.status = 'ready'
}

// 开始上传
async function startUpload() {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }

  const validFiles = fileList.value.filter(
    f => f.status !== 'duplicate' && f.status !== 'success'
  )

  if (validFiles.length === 0) {
    ElMessage.warning('没有可上传的文件')
    return
  }

  uploading.value = true

  // 逐个上传文件
  for (const file of validFiles) {
    if (file.raw) {
      try {
        if (props.onUpload) {
          const formData = new FormData()
          formData.append('file', file.raw)
          await props.onUpload(file.raw, formData)
          handleSuccess({}, file)
        }
      } catch (error) {
        handleError(error as Error, file)
      }
    }
  }

  uploading.value = false
}

// 清空文件列表
function clearFiles() {
  fileList.value = []
  emit('update:file-list', [])
}

// 判断文件类型
function isImage(filename: string): boolean {
  return /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(filename)
}

function isVideo(filename: string): boolean {
  return /\.(mp4|avi|mov|wmv|flv|mkv)$/i.test(filename)
}

function isDocument(filename: string): boolean {
  return /\.(pdf|doc|docx|xls|xlsx|ppt|pptx|txt)$/i.test(filename)
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 暴露方法给父组件
defineExpose({
  clearFiles,
  startUpload,
  uploadRef
})
</script>

<style scoped lang="scss">
.file-upload {
  .upload-container {
    :deep(.el-upload) {
      width: 100%;
    }

    :deep(.el-upload-dragger) {
      padding: 0;
      background: transparent;
      border: none;

      &.is-dragover {
        background: transparent;
      }
    }
  }

  .upload-trigger {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    border: 2px dashed #dcdfe6;
    border-radius: 12px;
    background: #fafafa;
    cursor: pointer;
    transition: all 0.3s;

    html.dark & {
      background: rgba(255, 255, 255, 0.05);
      border-color: #4b5563;
    }

    &:hover:not(.is-disabled) {
      border-color: #6366f1;
      background: rgba(99, 102, 241, 0.05);

      .upload-icon {
        color: #6366f1;
      }
    }

    &.is-disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }

    .upload-icon {
      color: #9ca3af;
      transition: color 0.3s;
    }

    .upload-text {
      margin-top: 16px;
      text-align: center;

      .upload-tip {
        font-size: 14px;
        color: var(--el-text-color-primary);
        margin: 0 0 4px 0;
      }

      .upload-hint {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin: 0;
      }
    }
  }

  .file-list {
    margin-top: 16px;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 8px;
    transition: all 0.2s;

    html.dark & {
      background: #1e293b;
      border-color: #334155;
    }

    &.is-duplicate {
      border-color: #f59e0b;
      background: #fef3c7;

      html.dark & {
        background: rgba(245, 158, 11, 0.1);
        border-color: #f59e0b;
      }
    }

    &.is-success {
      border-color: #10b981;
      background: #d1fae5;

      html.dark & {
        background: rgba(16, 185, 129, 0.1);
        border-color: #10b981;
      }
    }

    &.is-error {
      border-color: #ef4444;
      background: #fee2e2;

      html.dark & {
        background: rgba(239, 68, 68, 0.1);
        border-color: #ef4444;
      }
    }

    .file-info {
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1;
      min-width: 0;

      .file-icon {
        color: #6366f1;
        flex-shrink: 0;
      }

      .file-details {
        display: flex;
        flex-direction: column;
        min-width: 0;
        flex: 1;

        .file-name {
          font-size: 13px;
          color: var(--el-text-color-primary);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .file-size {
          font-size: 11px;
          color: var(--el-text-color-secondary);
        }
      }
    }

    .file-progress {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 120px;

      :deep(.el-progress) {
        flex: 1;
      }

      .progress-text {
        font-size: 11px;
        color: var(--el-text-color-secondary);
        min-width: 35px;
        text-align: right;
      }
    }

    .file-actions {
      display: flex;
      gap: 4px;
      flex-shrink: 0;
    }
  }

  .upload-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 16px;
    padding: 12px 16px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;

    html.dark & {
      background: #1e293b;
      border-color: #334155;
    }

    .upload-summary {
      font-size: 13px;
      color: var(--el-text-color-secondary);

      .duplicate-text {
        color: #f59e0b;
      }
    }

    .action-buttons {
      display: flex;
      gap: 8px;
    }
  }
}
</style>
