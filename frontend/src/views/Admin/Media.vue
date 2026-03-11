<template>
  <div class="admin-media">
    <el-card shadow="never">
      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button
          type="primary"
          :icon="Plus"
          @click="showUploadDialog"
        >
          上传媒体
        </el-button>
        <div style="flex: 1" />
        <el-radio-group v-model="mediaType" @change="loadMedia">
          <el-radio-button value="image">图片</el-radio-button>
          <el-radio-button value="video">视频</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 媒体列表 -->
      <el-table
        :data="mediaList"
        v-loading="loading"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="预览" width="100">
          <template #default="{ row }">
            <el-image
              v-if="row.file_category === 'image'"
              :src="getMediaUrl(row.id)"
              style="width: 60px; height: 60px"
              fit="cover"
              :preview-src-list="[getMediaUrl(row.id)]"
            />
            <div v-else class="video-preview">
              <el-icon :size="32"><VideoCamera /></el-icon>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" />
        <el-table-column label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            {{ row.mime_type || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="时长" width="80">
          <template #default="{ row }">
            {{ row.duration ? formatDuration(row.duration) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              :icon="View"
              @click="viewMedia(row)"
            >
              查看
            </el-button>
            <el-button
              v-if="canDelete(row)"
              link
              type="danger"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传媒体"
      width="500px"
    >
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="媒体类型">
          <el-radio-group v-model="uploadForm.type">
            <el-radio value="image">图片</el-radio>
            <el-radio value="video">视频</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input
            v-model="uploadForm.title"
            placeholder="请输入标题"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="2"
            placeholder="请输入描述（可选）"
          />
        </el-form-item>
        <el-form-item label="文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="10"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            drag
            multiple
            accept="image/*,video/*"
          >
            <el-icon :size="60"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 jpg/png/gif 图片和 mp4 视频，单个文件不超过 100MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelUpload">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          :disabled="!canUpload"
          @click="handleUpload"
        >
          开始上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadInstance, UploadProps, UploadUserFile } from 'element-plus'
import {
  Plus, VideoCamera, View, Delete, UploadFilled
} from '@element-plus/icons-vue'
import { mediaApi } from '@/api/modules/media'
import { useUserStore } from '@/stores/user'
import { formatDate, formatFileSize, formatDuration } from '@/utils/format'

const userStore = useUserStore()

const mediaList = ref<any[]>([])
const loading = ref(false)
const mediaType = ref<'image' | 'video'>('image')
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadRef = ref<UploadInstance>()

// 上传表单
const uploadForm = ref({
  type: 'image' as 'image' | 'video',
  title: '',
  description: ''
})

// 选中的文件列表
const selectedFiles = ref<UploadUserFile[]>([])

// 是否可以上传
const canUpload = computed(() => {
  return uploadForm.value.title.trim() !== '' && selectedFiles.value.length > 0
})

async function loadMedia() {
  loading.value = true
  try {
    const res = await mediaApi.getList({
      limit: 100,
      type: mediaType.value
    })
    mediaList.value = res.data || []
  } finally {
    loading.value = false
  }
}

function getMediaUrl(id: number) {
  return mediaApi.getViewUrl(id)
}

function viewMedia(media: any) {
  if (media.file_category === 'image') {
    // 使用 el-image 的预览功能
  } else {
    window.open(getMediaUrl(media.id), '_blank')
  }
}

function showUploadDialog() {
  uploadDialogVisible.value = true
  resetUploadForm()
}

function resetUploadForm() {
  uploadForm.value = {
    type: mediaType.value,
    title: '',
    description: ''
  }
  selectedFiles.value = []
  uploadRef.value?.clearFiles()
}

function cancelUpload() {
  uploadDialogVisible.value = false
  resetUploadForm()
}

function handleFileChange(file: UploadUserFile, fileList: UploadUserFile[]) {
  selectedFiles.value = fileList
}

function handleExceed() {
  ElMessage.warning('最多只能上传 10 个文件')
}

async function handleUpload() {
  if (!canUpload.value) {
    ElMessage.warning('请先输入标题并选择文件')
    return
  }

  uploading.value = true
  let successCount = 0
  let failCount = 0

  try {
    for (const file of selectedFiles.value) {
      if (!file.raw) continue

      const formData = new FormData()
      formData.append('file', file.raw)
      formData.append('title', uploadForm.value.title)
      if (uploadForm.value.description) {
        formData.append('description', uploadForm.value.description)
      }
      formData.append('category', uploadForm.value.type)

      try {
        await mediaApi.upload(formData)
        successCount++
      } catch {
        failCount++
      }
    }

    if (successCount > 0) {
      ElMessage.success(`成功上传 ${successCount} 个文件`)
    }
    if (failCount > 0) {
      ElMessage.error(`${failCount} 个文件上传失败`)
    }

    uploadDialogVisible.value = false
    loadMedia()
  } finally {
    uploading.value = false
  }
}

function canDelete(media: any): boolean {
  const currentUserIsRoot = userStore.currentUser?.is_root
  const currentUserIsAdmin = userStore.currentUser?.is_admin

  // ROOT 和 ADMIN 可以删除任何媒体
  return currentUserIsRoot || currentUserIsAdmin
}

async function handleDelete(media: any) {
  try {
    await ElMessageBox.confirm(`确定要删除 "${media.title}" 吗？`, '警告', {
      type: 'warning'
    })
    await mediaApi.delete(media.id)
    ElMessage.success('删除成功')
    loadMedia()
  } catch {
    // 取消删除
  }
}

onMounted(() => {
  loadMedia()
})
</script>

<style scoped lang="scss">
.admin-media {
  .toolbar {
    display: flex;
    align-items: center;
    margin-bottom: $spacing-md;
  }
}

.video-preview {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-placeholder);
}
</style>
