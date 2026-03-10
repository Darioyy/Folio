<template>
  <div class="admin-resources">
    <el-card shadow="never">
      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button
          type="primary"
          :icon="Plus"
          @click="showUploadDialog"
        >
          上传资源
        </el-button>
        <div style="flex: 1" />
        <el-input
          v-model="searchQuery"
          placeholder="搜索标题"
          :prefix-icon="Search"
          clearable
          style="width: 200px"
          @input="loadResources"
        />
      </div>

      <!-- 资源列表 -->
      <el-table
        :data="resources"
        v-loading="loading"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="文件名" prop="file_name" />
        <el-table-column label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column label="下载次数" width="100">
          <template #default="{ row }">
            {{ row.download_count }}
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
              :icon="Download"
              @click="downloadResource(row)"
            >
              下载
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
      title="上传资源"
      width="500px"
    >
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="uploadForm.title" placeholder="请输入资源标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="资源描述（可选）"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="uploadForm.category" placeholder="分类（可选）" />
        </el-form-item>
        <el-form-item label="文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            drag
          >
            <el-icon :size="60"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、DOC、DOCX、TXT 等文档格式，单个文件不超过 100MB
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadInstance, UploadUserFile } from 'element-plus'
import {
  Plus, Search, Download, Delete, UploadFilled
} from '@element-plus/icons-vue'
import { resourcesApi } from '@/api/modules/resources'
import { useUserStore } from '@/stores/user'
import { formatDate, formatFileSize } from '@/utils/format'

const userStore = useUserStore()

const resources = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadRef = ref<UploadInstance>()

const uploadForm = reactive({
  title: '',
  description: '',
  category: ''
})

// 选中的文件
const selectedFile = ref<UploadUserFile | null>(null)

// 是否可以上传
const canUpload = computed(() => {
  return uploadForm.title.trim() !== '' && selectedFile.value !== null
})

async function loadResources() {
  loading.value = true
  try {
    const res = await resourcesApi.getList({ limit: 100 })
    resources.value = (res.data || []).filter(r =>
      r.title.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  } finally {
    loading.value = false
  }
}

function downloadResource(resource: any) {
  window.open(resourcesApi.getDownloadUrl(resource.id), '_blank')
}

function showUploadDialog() {
  uploadForm.title = ''
  uploadForm.description = ''
  uploadForm.category = ''
  selectedFile.value = null
  uploadRef.value?.clearFiles()
  uploadDialogVisible.value = true
}

function cancelUpload() {
  uploadDialogVisible.value = false
  showUploadDialog()
}

function handleFileChange(file: UploadUserFile) {
  selectedFile.value = file
}

function handleExceed() {
  ElMessage.warning('只能上传一个文件')
}

async function handleUpload() {
  if (!canUpload.value) {
    ElMessage.warning('请先输入标题并选择文件')
    return
  }

  if (!selectedFile.value?.raw) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value.raw)
    formData.append('title', uploadForm.title)
    if (uploadForm.description) {
      formData.append('description', uploadForm.description)
    }

    await resourcesApi.upload(formData)
    ElMessage.success('上传成功')
    uploadDialogVisible.value = false
    loadResources()
  } catch {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

function canDelete(resource: any): boolean {
  const currentUserIsRoot = userStore.currentUser?.is_root
  const currentUserIsAdmin = userStore.currentUser?.is_admin

  // ROOT 和 ADMIN 可以删除任何资源
  return currentUserIsRoot || currentUserIsAdmin
}

async function handleDelete(resource: any) {
  try {
    await ElMessageBox.confirm(`确定要删除 "${resource.title}" 吗？`, '警告', {
      type: 'warning'
    })
    await resourcesApi.delete(resource.id)
    ElMessage.success('删除成功')
    loadResources()
  } catch {
    // 取消删除
  }
}

onMounted(() => {
  loadResources()
})
</script>

<style scoped lang="scss">
.admin-resources {
  .toolbar {
    display: flex;
    align-items: center;
    margin-bottom: $spacing-md;
  }
}
</style>
