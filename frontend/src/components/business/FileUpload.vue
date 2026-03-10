<template>
  <div class="file-upload">
    <!-- 上传区域 -->
    <div
      v-if="!disabled"
      class="upload-area"
      :class="{ 'is-dragover': isDragOver }"
      @click="selectFile"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragOver = true"
      @dragleave.prevent="isDragOver = false"
    >
      <el-icon :size="48" class="upload-icon">
        <UploadFilled />
      </el-icon>
      <p class="upload-text">点击或拖拽文件到此区域上传</p>
      <p class="upload-hint">支持 {{ allowedExtensions.join(', ') }} 格式</p>
      <p v-if="maxSize" class="upload-hint">单个文件不超过 {{ formatSize(maxSize) }}</p>
      <input
        ref="fileInputRef"
        type="file"
        :accept="acceptAttr"
        :multiple="multiple"
        style="display: none"
        @change="handleFileSelect"
      />
    </div>

    <!-- 文件列表 -->
    <div v-if="fileList.length > 0" class="file-list">
      <div
        v-for="file in fileList"
        :key="file.id"
        class="file-item"
        :class="{
          'is-uploading': file.status === 'uploading',
          'is-success': file.status === 'success',
          'is-error': file.status === 'error'
        }"
      >
        <!-- 文件图标 -->
        <div class="file-icon">
          <el-icon v-if="file.status === 'uploading'" :size="24" class="is-loading">
            <Loading />
          </el-icon>
          <el-icon v-else-if="file.status === 'success'" :size="24" color="#67c23a">
            <CircleCheck />
          </el-icon>
          <el-icon v-else-if="file.status === 'error'" :size="24" color="#f56c6c">
            <CircleClose />
          </el-icon>
          <el-icon v-else :size="24">
            <Document />
          </el-icon>
        </div>

        <!-- 文件信息 -->
        <div class="file-info">
          <div class="file-name" :title="file.name">
            {{ file.name }}
          </div>
          <div class="file-meta">
            <span v-if="file.size">{{ formatSize(file.size) }}</span>
            <span v-if="file.status === 'error'" class="error-text">
              {{ file.errorMessage || '上传失败' }}
            </span>
            <span v-else-if="file.status === 'success'" class="success-text">
              上传成功
            </span>
            <span v-else-if="file.status === 'uploading'" class="uploading-text">
              {{ file.progress }}%
            </span>
          </div>
          <!-- 进度条 -->
          <el-progress
            v-if="file.status === 'uploading'"
            :percentage="file.progress"
            :show-text="false"
            :stroke-width="3"
          />
        </div>

        <!-- 操作按钮 -->
        <div class="file-actions">
          <el-button
            v-if="file.status === 'error' || file.status === 'pending'"
            link
            type="primary"
            @click="retryUpload(file)"
          >
            重试
          </el-button>
          <el-button
            link
            type="danger"
            @click="removeFile(file)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 重复文件提示 -->
    <el-dialog
      v-model="duplicateDialogVisible"
      title="文件重复提示"
      width="400px"
    >
      <div class="duplicate-dialog">
        <el-icon :size="48" color="#e6a23c">
          <Warning />
        </el-icon>
        <p>以下文件已存在于上传列表：</p>
        <ul class="duplicate-list">
          <li v-for="name in duplicateFiles" :key="name">{{ name }}</li>
        </ul>
        <p class="duplicate-tip">是否仍要上传？</p>
      </div>
      <template #footer>
        <el-button @click="duplicateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmDuplicateUpload">继续上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UploadFilled,
  Document,
  Loading,
  CircleCheck,
  CircleClose,
  Warning
} from '@element-plus/icons-vue'
import type { UploadRequestOptions } from 'element-plus'

// 文件状态
type FileStatus = 'pending' | 'uploading' | 'success' | 'error'

interface UploadFile {
  id: string
  file: File
  name: string
  size: number
  status: FileStatus
  progress: number
  errorMessage?: string
  response?: any
}

interface Props {
  // 是否允许多选
  multiple?: boolean
  // 允许的文件扩展名（不含点）
  allowedExtensions?: string[]
  // 最大文件大小（字节）
  maxSize?: number
  // 最大文件数量
  maxCount?: number
  // 是否禁用
  disabled?: boolean
  // 自动上传
  autoUpload?: boolean
}

interface Emits {
  (e: 'change', files: UploadFile[]): void
  (e: 'success', file: UploadFile, response: any): void
  (e: 'error', file: UploadFile, error: any): void
  (e: 'progress', file: UploadFile, percent: number): void
}

const props = withDefaults(defineProps<Props>(), {
  multiple: true,
  allowedExtensions: () => ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'zip', 'rar'],
  maxSize: 100 * 1024 * 1024, // 100MB
  maxCount: 10,
  disabled: false,
  autoUpload: true
})

const emit = defineEmits<Emits>()

const fileInputRef = ref<HTMLInputElement>()
const isDragOver = ref(false)
const fileList = ref<UploadFile[]>([])
const duplicateDialogVisible = ref(false)
const duplicateFiles = ref<string[]>([])
const pendingFiles = ref<File[]>([])

// 接受属性
const acceptAttr = computed(() => {
  return props.allowedExtensions.map(ext => `.${ext}`).join(',')
})

// 选择文件
function selectFile() {
  fileInputRef.value?.click()
}

// 处理文件选择
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  handleFiles(files)
  target.value = ''
}

// 处理拖放
function handleDrop(event: DragEvent) {
  isDragOver.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  handleFiles(files)
}

// 处理文件
function handleFiles(files: File[]) {
  if (files.length === 0) return

  // 检查文件数量
  if (fileList.value.length + files.length > props.maxCount) {
    ElMessage.warning(`最多只能上传 ${props.maxCount} 个文件`)
    return
  }

  const validFiles: File[] = []
  const duplicates: string[] = []

  files.forEach(file => {
    // 检查文件扩展名
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (ext && !props.allowedExtensions.includes(ext)) {
      ElMessage.warning(`不支持的文件类型: ${file.name}`)
      return
    }

    // 检查文件大小
    if (file.size > props.maxSize) {
      ElMessage.warning(`文件 ${file.name} 超过大小限制 (${formatSize(props.maxSize)})`)
      return
    }

    // 检查重复
    const isDuplicate = fileList.value.some(f => f.name === file.name)
    if (isDuplicate) {
      duplicates.push(file.name)
    } else {
      validFiles.push(file)
    }
  })

  // 如果有重复文件，显示确认对话框
  if (duplicates.length > 0) {
    duplicateFiles.value = duplicates
    pendingFiles.value = validFiles
    duplicateDialogVisible.value = true
  } else {
    addFiles(validFiles)
  }
}

// 确认重复上传
function confirmDuplicateUpload() {
  duplicateDialogVisible.value = false
  const duplicates = duplicateFiles.value.map(name => {
    const ext = name.split('.').pop()
    return new File([], name, { type: ext ? `.${ext}` : '' })
  })
  addFiles([...pendingFiles.value, ...duplicates])
}

// 添加文件到列表
function addFiles(files: File[]) {
  const newFiles: UploadFile[] = files.map(file => ({
    id: `${file.name}_${Date.now()}_${Math.random()}`,
    file,
    name: file.name,
    size: file.size,
    status: 'pending',
    progress: 0
  }))

  fileList.value.push(...newFiles)
  emit('change', fileList.value)

  if (props.autoUpload) {
    newFiles.forEach(file => uploadFile(file))
  }
}

// 上传文件
async function uploadFile(uploadFile: UploadFile) {
  if (uploadFile.status === 'uploading' || uploadFile.status === 'success') {
    return
  }

  uploadFile.status = 'uploading'
  uploadFile.progress = 0

  try {
    // 创建 FormData
    const formData = new FormData()
    formData.append('file', uploadFile.file)

    // 模拟上传进度（实际应该使用真实API）
    const simulateProgress = () => {
      return new Promise((resolve, reject) => {
        const interval = setInterval(() => {
          if (uploadFile.progress < 90) {
            uploadFile.progress += 10
            emit('progress', uploadFile, uploadFile.progress)
          } else {
            clearInterval(interval)
            // 模拟上传完成
            setTimeout(() => {
              uploadFile.progress = 100
              uploadFile.status = 'success'
              emit('progress', uploadFile, 100)
              emit('success', uploadFile, { success: true })
              ElMessage.success(`${uploadFile.name} 上传成功`)
              resolve(true)
            }, 500)
          }
        }, 200)
      })
    }

    await simulateProgress()
  } catch (error) {
    uploadFile.status = 'error'
    uploadFile.errorMessage = '上传失败'
    emit('error', uploadFile, error)
    ElMessage.error(`${uploadFile.name} 上传失败`)
  }
}

// 重试上传
function retryUpload(file: UploadFile) {
  uploadFile(file)
}

// 移除文件
function removeFile(file: UploadFile) {
  const index = fileList.value.findIndex(f => f.id === file.id)
  if (index > -1) {
    fileList.value.splice(index, 1)
    emit('change', fileList.value)
  }
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// 暴露方法
defineExpose({
  uploadFile,
  clearFiles: () => {
    fileList.value = []
    emit('change', [])
  },
  getFiles: () => fileList.value
})
</script>

<style scoped lang="scss">
.file-upload {
  .upload-area {
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

    &:hover {
      border-color: #6366f1;
      background: rgba(99, 102, 241, 0.02);
    }

    &.is-dragover {
      border-color: #6366f1;
      background: rgba(99, 102, 241, 0.08);
    }

    html.dark & {
      border-color: #4b5563;
      background: rgba(255, 255, 255, 0.02);

      &:hover,
      &.is-dragover {
        border-color: #8b5cf6;
        background: rgba(139, 92, 246, 0.1);
      }
    }
  }

  .upload-icon {
    color: #6366f1;
    margin-bottom: 16px;

    html.dark & {
      color: #8b5cf6;
    }
  }

  .upload-text {
    font-size: 14px;
    color: var(--el-text-color-primary);
    margin: 0 0 8px 0;
  }

  .upload-hint {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin: 0 0 4px 0;
  }
}

.file-list {
  margin-top: 20px;
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
  transition: all 0.3s;

  html.dark & {
    background: #1e293b;
    border-color: #334155;
  }

  &.is-uploading {
    border-color: #6366f1;

    html.dark & {
      border-color: #8b5cf6;
    }
  }

  &.is-success {
    border-color: #67c23a;
  }

  &.is-error {
    border-color: #f56c6c;
  }
}

.file-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.file-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 8px;

  .error-text {
    color: #f56c6c;
  }

  .success-text {
    color: #67c23a;
  }

  .uploading-text {
    color: #6366f1;
  }
}

.file-actions {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
}

.duplicate-dialog {
  text-align: center;
  padding: 20px 0;

  .el-icon {
    margin-bottom: 16px;
  }

  p {
    margin: 8px 0;
    font-size: 14px;
    color: var(--el-text-color-primary);
  }

  .duplicate-list {
    text-align: left;
    margin: 16px 0;
    padding-left: 20px;

    li {
      font-size: 13px;
      color: var(--el-text-color-secondary);
      margin: 4px 0;
    }
  }

  .duplicate-tip {
    font-weight: 500;
    color: #e6a23c;
  }
}
</style>
