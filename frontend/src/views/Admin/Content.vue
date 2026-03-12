<template>
  <div class="content-management">
    <!-- 搜索 + 筛选栏 -->
    <el-card class="filter-card">
      <div class="filter-row">
        <el-input
          v-model="searchUsername"
          placeholder="按用户名搜索"
          clearable
          style="width: 200px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filterCategory" placeholder="全部类型" clearable style="width: 140px" @change="handleSearch">
          <el-option label="图片" value="image" />
          <el-option label="视频" value="video" />
          <el-option label="文档" value="document" />
        </el-select>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>
    </el-card>

    <!-- 文件表格 -->
    <el-card v-loading="loading">
      <el-table :data="files" style="width: 100%">
        <el-table-column label="文件" min-width="200">
          <template #default="{ row }">
            <div class="file-cell">
              <el-tag :type="categoryTagType(row.file_category)" size="small" style="margin-right: 6px;">
                {{ categoryLabel(row.file_category) }}
              </el-tag>
              <span class="file-title">{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="上传者" width="130">
          <template #default="{ row }">
            <span>{{ row.username || row.nickname || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="90">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="上传时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="70" fixed="right">
          <template #default="{ row }">
            <el-popconfirm title="确定删除该文件？" confirm-button-text="删除" confirm-button-type="danger" @confirm="handleDeleteRow(row)">
              <template #reference>
                <el-button text :icon="DeleteIcon" class="danger-btn" />
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @change="loadFiles"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Delete as DeleteIcon } from '@element-plus/icons-vue'
import { systemApi } from '@/api/modules/system'
import { filesApi } from '@/api/modules/files'
import { formatDate } from '@/utils/format'
import type { FileItem } from '@/types/models'

const loading = ref(false)
const files = ref<FileItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterCategory = ref('')
const searchUsername = ref('')

function categoryLabel(cat: string) {
  return { image: '图片', video: '视频', document: '文档' }[cat] ?? cat
}
function categoryTagType(cat: string) {
  return { image: '', video: 'warning', document: 'info' }[cat] ?? ''
}
function formatSize(bytes?: number) {
  if (!bytes) return '-'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

async function loadFiles() {
  loading.value = true
  try {
    const res = await systemApi.getAdminFiles({
      page: page.value,
      page_size: pageSize.value,
      category: filterCategory.value || undefined,
      username: searchUsername.value || undefined,
    })
    if (res.success && res.data) {
      files.value = res.data.items
      total.value = res.data.total
    }
  } catch {
    ElMessage.error('获取文件列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadFiles()
}

async function handleDeleteRow(row: FileItem) {
  try {
    await filesApi.delete(row.id)
    ElMessage.success('文件已删除')
    loadFiles()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(loadFiles)
</script>

<style scoped lang="scss">
.content-management {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-card {
  :deep(.el-card__body) {
    padding: 16px;
  }
}

.filter-row {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.file-cell {
  display: flex;
  align-items: center;
}

.file-title {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 240px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.danger-btn {
  color: var(--el-color-danger) !important;
}
</style>
