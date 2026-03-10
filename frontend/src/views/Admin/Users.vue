<template>
  <div class="admin-users">
    <el-card shadow="never">
      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button
          type="primary"
          :icon="Plus"
          @click="showCreateDialog"
        >
          新增用户
        </el-button>
        <div style="flex: 1" />
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户名"
          :prefix-icon="Search"
          clearable
          style="width: 200px"
          @input="loadUsers"
        />
      </div>

      <!-- 用户列表 -->
      <el-table
        :data="users"
        v-loading="loading"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="nickname" label="昵称" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleType(getRole(row))">
              {{ getRoleText(getRole(row)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="180">
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
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="signature">
          <el-input v-model="formData.signature" placeholder="请输入邮箱地址" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" style="width: 100%">
            <el-option :value="0" label="普通用户" />
            <el-option :value="1" label="管理员" />
            <el-option :value="2" label="超级管理员" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            show-password
            placeholder="请输入密码"
          />
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
import { usersApi } from '@/api/modules/users'
import { useUserStore } from '@/stores/user'
import { formatDate } from '@/utils/format'

const userStore = useUserStore()

const users = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({
  id: 0,
  username: '',
  nickname: '',
  role: 0, // 用于表单选择：0=用户, 1=管理员, 2=ROOT
  password: '',
  signature: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }
  ]
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await usersApi.getList({ limit: 100 })
    users.value = (res.data || []).filter(u =>
      u.username.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  } finally {
    loading.value = false
  }
}

// 将 is_admin/is_root 转换为 role 值
function getRole(user: any): number {
  if (user.is_root) return 2
  if (user.is_admin) return 1
  return 0
}

// 将 role 值转换为 is_admin/is_root
function getAdminFlags(role: number): { is_admin: number; is_root: number } {
  if (role === 2) return { is_admin: 1, is_root: 1 }
  if (role === 1) return { is_admin: 1, is_root: 0 }
  return { is_admin: 0, is_root: 0 }
}

function getRoleText(role: number) {
  return { 0: '用户', 1: '管理员', 2: 'ROOT' }[role] || '未知'
}

function getRoleType(role: number) {
  return { 0: 'info', 1: 'warning', 2: 'danger' }[role] || 'info'
}

function canEdit(user: any): boolean {
  const currentUserId = userStore.currentUser?.id
  const currentUserIsRoot = userStore.currentUser?.is_root
  const currentUserIsAdmin = userStore.currentUser?.is_admin
  const userIsRoot = user.is_root
  const userIsAdmin = user.is_admin

  // 不能编辑自己
  if (user.id === currentUserId) return false

  // ROOT 可以编辑任何人（除自己）
  if (currentUserIsRoot) return true

  // ADMIN 只能编辑普通用户（不是 ADMIN 或 ROOT）
  return currentUserIsAdmin && !userIsAdmin && !userIsRoot
}

function canDelete(user: any): boolean {
  const currentUserId = userStore.currentUser?.id
  const currentUserIsRoot = userStore.currentUser?.is_root
  const currentUserIsAdmin = userStore.currentUser?.is_admin
  const userIsRoot = user.is_root
  const userIsAdmin = user.is_admin

  // 不能删除自己
  if (user.id === currentUserId) return false

  // ROOT 可以删除任何人（除自己）
  if (currentUserIsRoot) return true

  // ADMIN 只能删除普通用户（不是 ADMIN 或 ROOT）
  return currentUserIsAdmin && !userIsAdmin && !userIsRoot
}

function showCreateDialog() {
  isEdit.value = false
  Object.assign(formData, {
    id: 0,
    username: '',
    nickname: '',
    role: 0,
    password: '',
    signature: ''
  })
  dialogVisible.value = true
}

function showEditDialog(user: any) {
  isEdit.value = true
  Object.assign(formData, {
    id: user.id,
    username: user.username,
    nickname: user.nickname || '',
    role: getRole(user),
    password: '',
    signature: user.signature || ''
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      const { is_admin, is_root } = getAdminFlags(formData.role)

      if (isEdit.value) {
        // 构建更新数据，只包含非空字段
        const updateData: any = {
          is_admin,
          is_root
        }
        // 只有当邮箱非空时才添加到更新数据中
        if (formData.signature && formData.signature.trim()) {
          updateData.email = formData.signature
        }
        await usersApi.update(formData.id, updateData)
        ElMessage.success('更新成功')
      } else {
        await usersApi.create({
          username: formData.username,
          password: formData.password,
          // 只有当邮箱非空时才添加
          ...(formData.signature?.trim() ? { email: formData.signature } : {}),
          is_admin,
          is_root
        })
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadUsers()
    } catch {
      // 错误已在 API 层处理
    }
  })
}

async function handleDelete(user: any) {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${user.username}" 吗？`, '警告', {
      type: 'warning'
    })
    await usersApi.delete(user.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch {
    // 取消删除
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped lang="scss">
.admin-users {
  .toolbar {
    display: flex;
    align-items: center;
    margin-bottom: $spacing-md;
  }
}
</style>
