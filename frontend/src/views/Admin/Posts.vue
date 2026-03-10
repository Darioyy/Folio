<template>
  <div class="admin-posts">
    <el-card shadow="never">
      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button
          type="primary"
          :icon="Plus"
          @click="showCreateDialog"
        >
          新增文章
        </el-button>
        <div style="flex: 1" />
        <el-select
          v-model="filterStatus"
          placeholder="状态筛选"
          clearable
          style="width: 120px; margin-right: $spacing-sm"
          @change="loadPosts"
        >
          <el-option value="draft" label="草稿" />
          <el-option value="published" label="已发布" />
        </el-select>
        <el-input
          v-model="searchQuery"
          placeholder="搜索标题"
          :prefix-icon="Search"
          clearable
          style="width: 200px"
          @input="loadPosts"
        />
      </div>

      <!-- 文章列表 -->
      <el-table
        :data="posts"
        v-loading="loading"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" />
        <el-table-column label="分类" width="120">
          <template #default="{ row }">
            {{ row.category_name || '未分类' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="浏览" width="80">
          <template #default="{ row }">
            {{ row.view_count }}
          </template>
        </el-table-column>
        <el-table-column label="发布时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="canEdit(row)"
              link
              type="primary"
              :icon="Edit"
              @click="showEditDialog(row)"
            >
              编辑
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

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑文章' : '新增文章'"
      width="800px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入文章标题" />
        </el-form-item>
        <el-form-item label="摘要" prop="summary">
          <el-input
            v-model="formData.summary"
            type="textarea"
            :rows="2"
            placeholder="文章摘要（可选）"
          />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="12"
            placeholder="支持 Markdown 格式"
          />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="formData.category_id" placeholder="选择分类" clearable>
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio value="draft">草稿</el-radio>
            <el-radio value="published">发布</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus, Search, Edit, Delete
} from '@element-plus/icons-vue'
import { postsApi } from '@/api/modules/posts'
import { useUserStore } from '@/stores/user'
import { formatDate } from '@/utils/format'

const userStore = useUserStore()

const posts = ref<any[]>([])
const categories = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const filterStatus = ref<string>()
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({
  id: 0,
  title: '',
  summary: '',
  content: '',
  category_id: undefined as number | undefined,
  status: 'draft'
})

const rules: FormRules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入内容', trigger: 'blur' }
  ]
}

async function loadPosts() {
  loading.value = true
  try {
    const res = await postsApi.getList({
      limit: 100,
      status: filterStatus.value,
      q: searchQuery.value
    })
    posts.value = res.data || []
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    const res = await postsApi.getCategories()
    categories.value = res.data || []
  } catch {
    categories.value = []
  }
}

function showCreateDialog() {
  isEdit.value = false
  Object.assign(formData, {
    id: 0,
    title: '',
    summary: '',
    content: '',
    category_id: undefined,
    status: 'draft'
  })
  dialogVisible.value = true
}

function showEditDialog(post: any) {
  isEdit.value = true
  Object.assign(formData, {
    id: post.id,
    title: post.title,
    summary: post.summary || '',
    content: post.content,
    category_id: post.category_id,
    status: post.status
  })
  dialogVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      if (isEdit.value) {
        await postsApi.update(formData.id, formData)
        ElMessage.success('更新成功')
      } else {
        await postsApi.create(formData)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadPosts()
    } catch {
      // 错误已在 API 层处理
    }
  })
}

function canEdit(post: any): boolean {
  const currentUserId = userStore.currentUser?.id
  const currentUserIsRoot = userStore.currentUser?.is_root
  const currentUserIsAdmin = userStore.currentUser?.is_admin

  // ROOT 和 ADMIN 可以编辑任何文章
  if (currentUserIsRoot || currentUserIsAdmin) return true

  // 作者可以编辑自己的文章
  return post.author_id === currentUserId
}

function canDelete(post: any): boolean {
  const currentUserId = userStore.currentUser?.id
  const currentUserIsRoot = userStore.currentUser?.is_root
  const currentUserIsAdmin = userStore.currentUser?.is_admin

  // ROOT 可以删除任何文章
  if (currentUserIsRoot) return true

  // ADMIN 可以删除任何文章
  if (currentUserIsAdmin) return true

  // 作者只能删除自己的文章
  return post.author_id === currentUserId
}

async function handleDelete(post: any) {
  try {
    await ElMessageBox.confirm(`确定要删除文章 "${post.title}" 吗？`, '警告', {
      type: 'warning'
    })
    await postsApi.delete(post.id)
    ElMessage.success('删除成功')
    loadPosts()
  } catch {
    // 取消删除
  }
}

onMounted(() => {
  loadPosts()
  loadCategories()
})
</script>

<style scoped lang="scss">
.admin-posts {
  .toolbar {
    display: flex;
    align-items: center;
    margin-bottom: $spacing-md;
  }
}
</style>
