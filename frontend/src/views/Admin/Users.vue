<template>
  <div class="admin-users">
    <el-card shadow="never">
      <!-- 操作栏 -->
      <div class="toolbar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户名"
          :prefix-icon="Search"
          clearable
          style="width: 240px"
          @input="loadUsers"
        />
      </div>

      <!-- 用户列表 -->
      <el-table
        :data="users"
        v-loading="loading"
        stripe
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="uid" label="UID" width="100" />
        <el-table-column label="用户名">
          <template #default="{ row }">
            <a
              :href="`/u/${row.username}`"
              target="_blank"
              class="username-link"
            >{{ row.username }}</a>
          </template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleType(getRole(row))">
              {{ getRoleText(getRole(row)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="110">
          <template #default="{ row }">
            <span class="date-cell">{{ formatDate(row.created_at, 'YYYY-MM-DD') }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="canEdit(row)"
              link
              type="primary"
              :icon="Edit"
              @click="showEditDialog(row)"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="编辑用户"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item v-if="userStore.isRoot" label="UID" prop="uid">
          <el-input v-model="formData.uid" placeholder="8位数字" maxlength="8" />
          <div class="field-hint">超级管理员可修改 UID（8位数字）</div>
        </el-form-item>
        <el-form-item v-else label="UID">
          <el-input :value="formData.uid" disabled />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            :disabled="!userStore.isRoot"
          />
          <div v-if="userStore.isRoot" class="field-hint">超级管理员可修改用户名</div>
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
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-popconfirm
            v-if="editingUser && canDelete(editingUser)"
            :title="`确定删除用户 &quot;${editingUser?.username}&quot; 吗？`"
            confirm-button-text="删除"
            confirm-button-type="danger"
            @confirm="handleDeleteFromDialog"
          >
            <template #reference>
              <el-button type="danger" plain>删除用户</el-button>
            </template>
          </el-popconfirm>
          <div style="flex: 1" />
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Search, Edit } from '@element-plus/icons-vue'
import { usersApi } from '@/api/modules/users'
import { useUserStore } from '@/stores/user'
import { formatDate } from '@/utils/format'

const userStore = useUserStore()

const users = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const dialogVisible = ref(false)
const editingUser = ref<any>(null)
const formRef = ref<FormInstance>()

const formData = reactive({
  id: 0,
  uid: '',
  username: '',
  role: 0,
  signature: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
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

function getRole(user: any): number {
  if (user.is_root) return 2
  if (user.is_admin) return 1
  return 0
}

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

  if (user.id === currentUserId) return false
  if (currentUserIsRoot) return true
  return currentUserIsAdmin && !userIsAdmin && !userIsRoot
}

function canDelete(user: any): boolean {
  const currentUserId = userStore.currentUser?.id
  const currentUserIsRoot = userStore.currentUser?.is_root
  const currentUserIsAdmin = userStore.currentUser?.is_admin
  const userIsRoot = user.is_root
  const userIsAdmin = user.is_admin

  if (user.id === currentUserId) return false
  if (currentUserIsRoot) return true
  return currentUserIsAdmin && !userIsAdmin && !userIsRoot
}

function showEditDialog(user: any) {
  editingUser.value = user
  Object.assign(formData, {
    id: user.id,
    uid: user.uid || '',
    username: user.username,
    role: getRole(user),
    signature: user.email || user.signature || ''
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      const { is_admin, is_root } = getAdminFlags(formData.role)
      const updateData: any = { is_admin, is_root }
      if (formData.signature && formData.signature.trim()) {
        updateData.email = formData.signature
      }
      if (userStore.isRoot && formData.username.trim()) {
        updateData.username = formData.username.trim()
      }
      if (userStore.isRoot && formData.uid.trim()) {
        updateData.uid = formData.uid.trim()
      }
      await usersApi.update(formData.id, updateData)
      ElMessage.success('更新成功')
      dialogVisible.value = false
      loadUsers()
    } catch {
      // 错误已在 API 层处理
    }
  })
}

async function handleDeleteFromDialog() {
  if (!editingUser.value) return
  try {
    await usersApi.delete(editingUser.value.id)
    ElMessage.success('删除成功')
    dialogVisible.value = false
    loadUsers()
  } catch {
    // 错误已在 API 层处理
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped lang="scss">
.admin-users { }

.username-link {
  color: #5a67d8;
  text-decoration: none;
  font-weight: 500;

  &:hover {
    text-decoration: underline;
  }
}

.date-cell {
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
}

.field-hint {
  font-size: 12px;
  color: var(--el-color-warning);
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  align-items: center;
  width: 100%;
}
</style>
