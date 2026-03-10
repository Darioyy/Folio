<template>
  <div class="categories-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>分类管理</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">
        新建分类
      </el-button>
    </div>

    <!-- 分类列表 -->
    <el-card>
      <el-table :data="categories" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="分类名称" min-width="200" />
        <el-table-column label="文章数量" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="info">{{ row.post_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              :icon="Edit"
              @click="showEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              link
              type="danger"
              :icon="Delete"
              :disabled="row.post_count > 0"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? '编辑分类' : '新建分类'"
      width="500px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="分类名称" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="请输入分类名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEditMode ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { systemApi } from '@/api/modules/system'
import { formatDate } from '@/utils/format'

interface Category {
  id: number
  name: string
  post_count?: number
  created_at: string
}

const loading = ref(false)
const categories = ref<Category[]>([])

const dialogVisible = ref(false)
const isEditMode = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const formData = ref({
  id: 0,
  name: ''
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { min: 1, max: 100, message: '分类名称长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 加载分类列表
async function loadCategories() {
  loading.value = true
  try {
    const res = await systemApi.getCategories()
    categories.value = res.data || []
  } catch (error) {
    console.error('加载分类列表失败:', error)
    ElMessage.error('加载分类列表失败')
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
function showCreateDialog() {
  isEditMode.value = false
  formData.value = { id: 0, name: '' }
  dialogVisible.value = true
}

// 显示编辑对话框
function showEditDialog(category: Category) {
  isEditMode.value = true
  formData.value = { id: category.id, name: category.name }
  dialogVisible.value = true
}

// 重置表单
function resetForm() {
  formRef.value?.resetFields()
  formData.value = { id: 0, name: '' }
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEditMode.value) {
        await systemApi.updateCategory(formData.value.id, { name: formData.value.name })
        ElMessage.success('分类更新成功')
      } else {
        await systemApi.createCategory({ name: formData.value.name })
        ElMessage.success('分类创建成功')
      }

      dialogVisible.value = false
      await loadCategories()
    } catch (error: any) {
      console.error('操作失败:', error)
      const errorMsg = error?.response?.data?.error?.message || '操作失败'
      ElMessage.error(errorMsg)
    } finally {
      submitting.value = false
    }
  })
}

// 删除分类
async function handleDelete(category: Category) {
  if (category.post_count && category.post_count > 0) {
    ElMessage.warning('该分类下还有文章，无法删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除分类"${category.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await systemApi.deleteCategory(category.id)
    ElMessage.success('分类删除成功')
    await loadCategories()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      const errorMsg = error?.response?.data?.error?.message || '删除失败'
      ElMessage.error(errorMsg)
    }
  }
}

onMounted(() => {
  loadCategories()
})
</script>

<style scoped lang="scss">
.categories-page {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
  }

  h2 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
  }

  :deep(.el-card) {
    .el-table {
      .el-table__row {
        &:hover {
          background-color: var(--el-fill-color-light);
        }
      }
    }
  }
}
</style>
