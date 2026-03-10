<template>
  <div class="profile-page" :class="{ 'is-dark': isDarkMode }">
    <AppHeader />

    <div class="profile-container">
      <!-- 侧边栏 -->
      <aside class="profile-sidebar">
        <div class="sidebar-card">
          <!-- 头像区域 -->
          <div class="avatar-section">
            <el-avatar :src="avatarUrl" :size="100" class="user-avatar">
              {{ displayName }}
            </el-avatar>
            <el-upload
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              :http-request="uploadAvatar"
              accept="image/*"
            >
              <div class="avatar-upload-btn">
                <el-icon><Camera /></el-icon>
                <span>更换头像</span>
              </div>
            </el-upload>
          </div>

          <!-- 用户名 -->
          <div class="user-name">
            {{ userStore.currentUser?.nickname || userStore.currentUser?.username }}
          </div>

          <!-- 用户角色标签 -->
          <div class="user-tags">
            <el-tag v-if="userStore.isRoot" type="danger" size="small">ROOT</el-tag>
            <el-tag v-else-if="userStore.isAdmin" type="warning" size="small">ADMIN</el-tag>
          </div>

          <!-- 个性签名 -->
          <div class="user-signature">
            {{ userStore.currentUser?.signature || '这个人很懒，什么都没留下' }}
          </div>

          <!-- 统计数据 -->
          <div class="stats-grid">
            <div class="stat-item" @click="goToPosts">
              <div class="stat-value">{{ stats.posts }}</div>
              <div class="stat-label">文章</div>
            </div>
            <div class="stat-item" @click="goToMedia">
              <div class="stat-value">{{ stats.media }}</div>
              <div class="stat-label">媒体</div>
            </div>
            <div class="stat-item" @click="goToResources">
              <div class="stat-value">{{ stats.resources }}</div>
              <div class="stat-label">资源</div>
            </div>
            <div class="stat-item" @click="showStorageDetail" style="cursor: pointer">
              <div class="stat-value">{{ formatSize(stats.total_size) }}</div>
              <div class="stat-label">存储</div>
            </div>
          </div>

          <!-- 社交数据 -->
          <div class="social-stats">
            <div class="social-item" @click="goToFollowers">
              <div class="social-value">{{ userStore.currentUser?.followers_count || 0 }}</div>
              <div class="social-label">粉丝</div>
            </div>
            <div class="social-item" @click="goToFollowing">
              <div class="social-value">{{ userStore.currentUser?.following_count || 0 }}</div>
              <div class="social-label">关注</div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 主内容区 -->
      <main class="profile-main">
        <!-- 标签页 -->
        <el-tabs v-model="activeTab" class="profile-tabs">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="basic">
            <el-card shadow="never">
              <el-form
                ref="formRef"
                :model="form"
                :rules="rules"
                label-width="80px"
                class="profile-form"
              >
                <el-form-item label="用户名">
                  <el-input v-model="userStore.currentUser!.username" disabled />
                </el-form-item>

                <el-form-item label="昵称" prop="nickname">
                  <el-input
                    v-model="form.nickname"
                    placeholder="请输入昵称"
                    maxlength="50"
                    show-word-limit
                  />
                </el-form-item>

                <el-form-item label="个性签名" prop="signature">
                  <el-input
                    v-model="form.signature"
                    type="textarea"
                    :rows="4"
                    placeholder="写点什么吧..."
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>

                <el-form-item label="邮箱" prop="email">
                  <el-input
                    v-model="form.email"
                    placeholder="请输入邮箱"
                  />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="submitForm" :loading="saving">
                    保存修改
                  </el-button>
                  <el-button @click="resetForm">重置</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>

          <!-- 账户信息 -->
          <el-tab-pane label="账户信息" name="account">
            <el-card shadow="never">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="用户ID">
                  {{ userStore.currentUser?.id }}
                </el-descriptions-item>
                <el-descriptions-item label="用户名">
                  {{ userStore.currentUser?.username }}
                </el-descriptions-item>
                <el-descriptions-item label="角色">
                  <el-tag v-if="userStore.isRoot" type="danger">超级管理员</el-tag>
                  <el-tag v-else-if="userStore.isAdmin" type="warning">管理员</el-tag>
                  <el-tag v-else type="info">普通用户</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="注册时间">
                  {{ formatDate(userStore.currentUser?.created_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="最后上线">
                  {{ formatDate(userStore.currentUser?.updated_at) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-tab-pane>

          <!-- 安全设置 -->
          <el-tab-pane label="安全设置" name="security">
            <el-card shadow="never">
              <el-form
                ref="passwordFormRef"
                :model="passwordForm"
                :rules="passwordRules"
                label-width="80px"
                class="password-form"
              >
                <el-form-item label="旧密码" prop="old_password">
                  <el-input
                    v-model="passwordForm.old_password"
                    type="password"
                    placeholder="请输入旧密码"
                    show-password
                  />
                </el-form-item>

                <el-form-item label="新密码" prop="new_password">
                  <el-input
                    v-model="passwordForm.new_password"
                    type="password"
                    placeholder="请输入新密码（至少6位）"
                    show-password
                  />
                </el-form-item>

                <el-form-item label="确认密码" prop="confirm_password">
                  <el-input
                    v-model="passwordForm.confirm_password"
                    type="password"
                    placeholder="请再次输入新密码"
                    show-password
                  />
                </el-form-item>

                <el-form-item>
                  <el-button
                    type="primary"
                    @click="submitPassword"
                    :loading="changingPassword"
                  >
                    修改密码
                  </el-button>
                  <el-button @click="resetPasswordForm">重置</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>

          <!-- 隐私设置 -->
          <el-tab-pane label="隐私设置" name="privacy">
            <el-card shadow="never">
              <el-form
                ref="privacyFormRef"
                :model="privacyForm"
                label-width="120px"
                class="privacy-form"
              >
                <el-form-item label="头像可见性">
                  <el-radio-group v-model="privacyForm.privacy_avatar">
                    <el-radio :value="1">公开</el-radio>
                    <el-radio :value="0">私密</el-radio>
                  </el-radio-group>
                  <div class="form-tip">设置头像是否对其他用户可见</div>
                </el-form-item>

                <el-form-item label="统计可见性">
                  <el-radio-group v-model="privacyForm.privacy_stats">
                    <el-radio :value="1">公开</el-radio>
                    <el-radio :value="0">私密</el-radio>
                  </el-radio-group>
                  <div class="form-tip">设置文章、媒体、资源等统计数据是否对其他用户可见</div>
                </el-form-item>

                <el-form-item label="内容可见性">
                  <el-radio-group v-model="privacyForm.privacy_content">
                    <el-radio :value="1">公开</el-radio>
                    <el-radio :value="0">私密</el-radio>
                  </el-radio-group>
                  <div class="form-tip">设置公共内容是否对其他用户可见</div>
                </el-form-item>

                <el-form-item label="允许关注">
                  <el-radio-group v-model="privacyForm.privacy_follow">
                    <el-radio :value="1">允许</el-radio>
                    <el-radio :value="0">不允许</el-radio>
                  </el-radio-group>
                  <div class="form-tip">设置是否允许其他用户关注你</div>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="submitPrivacy" :loading="savingPrivacy">
                    保存设置
                  </el-button>
                  <el-button @click="resetPrivacyForm">重置</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </main>
    </div>

    <!-- 存储详情弹窗 -->
    <StorageDetail
      v-model="storageDetailVisible"
      :storage-info="storageInfo"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules, type UploadRequestOptions } from 'element-plus'
import { Camera } from '@element-plus/icons-vue'
import AppHeader from '@/components/common/AppHeader.vue'
import StorageDetail from '@/components/common/StorageDetail.vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/modules/auth'
import { hubApi } from '@/api/modules/hub'
import type { StorageInfo } from '@/api/modules/hub'

const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()
const isDarkMode = computed(() => appStore.isDarkMode)

const activeTab = ref('basic')
const formRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const uploading = ref(false)
const saving = ref(false)
const changingPassword = ref(false)
const loadingStats = ref(false)

// 表单数据
const form = ref({
  nickname: '',
  signature: '',
  email: ''
})

// 密码表单
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 隐私设置表单
const privacyForm = ref({
  privacy_avatar: 1,
  privacy_stats: 1,
  privacy_content: 1,
  privacy_follow: 1
})

const savingPrivacy = ref(false)

// 统计数据
const stats = ref({
  posts: 0,
  media: 0,
  resources: 0,
  total_size: 0
})

// 存储信息
const storageInfo = ref<StorageInfo>({
  storage_used: 0,
  storage_quota: 0,
  storage_percentage: 0
})

const storageDetailVisible = ref(false)

// 显示名称（头像默认显示）
const displayName = computed(() => {
  const user = userStore.currentUser
  return user?.nickname?.[0] || user?.username[0] || '?'
})

// 头像URL（带时间戳避免缓存）
const avatarUrl = computed(() => {
  const user = userStore.currentUser
  if (user?.avatar) {
    // 使用 updated_at 作为缓存破坏参数
    const timestamp = new Date(user.updated_at).getTime()
    return `${authApi.getAvatarUrl()}?t=${timestamp}`
  }
  return undefined
})

// 表单验证规则
const rules: FormRules = {
  nickname: [
    { min: 1, max: 50, message: '昵称长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  signature: [
    { max: 200, message: '个性签名最多 200 个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

// 密码验证规则
const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, min: 6, max: 100, message: '密码长度至少 6 位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 初始化表单
function initForm() {
  const user = userStore.currentUser
  if (user) {
    form.value = {
      nickname: user.nickname || '',
      signature: user.signature || '',
      email: user.email || ''
    }
  }
}

// 上传头像前验证
function beforeAvatarUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  return true
}

// 上传头像
async function uploadAvatar(options: UploadRequestOptions) {
  uploading.value = true
  try {
    await authApi.uploadAvatar(options.file)
    await userStore.refreshUser()
    ElMessage.success('头像上传成功')
  } catch (error) {
    ElMessage.error('头像上传失败')
  } finally {
    uploading.value = false
  }
}

// 提交表单
async function submitForm() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      await authApi.updateProfile({
        nickname: form.value.nickname || undefined,
        signature: form.value.signature || undefined,
        email: form.value.email || undefined
      })
      await userStore.refreshUser()
      ElMessage.success('保存成功')
    } catch (error) {
      ElMessage.error('保存失败')
    } finally {
      saving.value = false
    }
  })
}

// 重置表单
function resetForm() {
  initForm()
  ElMessage.info('已重置')
}

// 修改密码
async function submitPassword() {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    changingPassword.value = true
    try {
      await authApi.changePassword({
        old_password: passwordForm.value.old_password,
        new_password: passwordForm.value.new_password
      })

      ElMessage.success('密码修改成功，请重新登录')
      passwordFormRef.value?.resetFields()

      // 修改密码成功后自动退出并跳转登录页
      await userStore.logout()
      setTimeout(() => {
        router.push({ name: 'Login' })
      }, 1000)
    } catch (error: any) {
      const message = error?.response?.data?.error?.message || '密码修改失败'
      if (message.includes('原密码错误')) {
        ElMessage.error('原密码错误，请重新输入')
      } else {
        ElMessage.error(message)
      }
    } finally {
      changingPassword.value = false
    }
  })
}

// 重置密码表单
function resetPasswordForm() {
  passwordFormRef.value?.resetFields()
}

// 初始化隐私设置表单
function initPrivacyForm() {
  const user = userStore.currentUser
  if (user) {
    privacyForm.value = {
      privacy_avatar: user.privacy_avatar ?? 1,
      privacy_stats: user.privacy_stats ?? 1,
      privacy_content: user.privacy_content ?? 1,
      privacy_follow: user.privacy_follow ?? 1
    }
  }
}

// 提交隐私设置
async function submitPrivacy() {
  savingPrivacy.value = true
  try {
    await authApi.updatePrivacy(privacyForm.value)
    await userStore.refreshUser()
    ElMessage.success('隐私设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    savingPrivacy.value = false
  }
}

// 重置隐私设置表单
function resetPrivacyForm() {
  initPrivacyForm()
  ElMessage.info('已重置')
}

// 跳转到粉丝列表
function goToFollowers() {
  if (userStore.currentUser?.username) {
    router.push({ name: 'FollowList', params: { username: userStore.currentUser.username, type: 'followers' } })
  }
}

// 跳转到关注列表
function goToFollowing() {
  if (userStore.currentUser?.username) {
    router.push({ name: 'FollowList', params: { username: userStore.currentUser.username, type: 'following' } })
  }
}

// 加载统计数据
async function loadStats() {
  loadingStats.value = true
  try {
    const [statsRes, storageRes] = await Promise.all([
      authApi.getStats(),
      hubApi.getStorageInfo()
    ])
    stats.value = statsRes.data
    storageInfo.value = storageRes.data
  } catch (error) {
    console.error('加载统计数据失败', error)
  } finally {
    loadingStats.value = false
  }
}

// 显示存储详情
function showStorageDetail() {
  storageDetailVisible.value = true
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 跳转到文章列表
function goToPosts() {
  router.push({ name: 'AdminPosts' })
}

// 跳转到媒体列表
function goToMedia() {
  router.push({ name: 'AdminMedia' })
}

// 跳转到资源列表
function goToResources() {
  router.push({ name: 'AdminResources' })
}

onMounted(() => {
  initForm()
  loadStats()
})
</script>

<style scoped lang="scss">
.profile-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f9fafb;

  html.dark & {
    background: #0f172a;
  }
}

.profile-container {
  flex: 1;
  display: flex;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 24px;
}

// 侧边栏
.profile-sidebar {
  width: 300px;
  flex-shrink: 0;
}

.sidebar-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 88px;

  html.dark & {
    background: #1e293b;
    border-color: #334155;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.user-avatar {
  border: 4px solid var(--el-border-color);
  font-size: 40px;
  font-weight: bold;
}

.avatar-upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
  user-select: none;

  &:hover {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  }

  &:active {
    transform: translateY(0);
  }

  .el-icon {
    font-size: 16px;
  }
}

.user-name {
  font-size: 20px;
  font-weight: 600;
  text-align: center;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.user-tags {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
}

.user-signature {
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;

  html.dark & {
    border-bottom-color: #334155;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 10px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
  padding: 12px;
  border-radius: 10px;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.3s;

  html.dark & {
    background: rgba(255, 255, 255, 0.05);
  }

  &:hover {
    background: rgba(99, 102, 241, 0.08);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
  }
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 4px;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1;
  font-weight: 500;
}

// 社交数据样式
.social-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid #e5e7eb;

  html.dark & {
    border-top-color: #334155;
  }
}

.social-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1.5;
  padding: 12px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05));
  cursor: pointer;
  transition: all 0.3s;

  html.dark & {
    background: rgba(99, 102, 241, 0.1);
  }

  &:hover {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
  }
}

.social-value {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 4px;
  line-height: 1.2;
}

.social-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1;
  font-weight: 500;
}

// 主内容区
.profile-main {
  flex: 1;
  min-width: 0;
}

.profile-tabs {
  :deep(.el-tabs__content) {
    padding-top: 16px;
  }

  :deep(.el-card) {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    background: #ffffff;

    html.dark & {
      background: #1e293b;
      border-color: #334155;
    }
  }

  // 账户信息表格样式
  :deep(.el-descriptions) {
    --el-descriptions-table-border: 1px solid #e5e7eb;
    --el-descriptions-border-color: #e5e7eb;

    .el-descriptions__body {
      background: #ffffff;
    }

    .el-descriptions__table {
      border: 1px solid #e5e7eb;
    }

    .el-descriptions__cell {
      border: 1px solid #e5e7eb;
    }

    .el-descriptions__label {
      background: #f9fafb;
      font-weight: 500;
    }

    .el-descriptions__content {
      color: var(--el-text-color-primary);
    }

    html.dark & {
      --el-descriptions-table-border: 1px solid #334155;
      --el-descriptions-border-color: #334155;

      .el-descriptions__body {
        background: #1e293b;
      }

      .el-descriptions__table,
      .el-descriptions__cell {
        border-color: #334155;
      }

      .el-descriptions__label {
        background: #0f172a;
      }
    }
  }
}

.profile-form,
.password-form {
  max-width: 600px;
}

// 响应式
@media (max-width: 768px) {
  .profile-container {
    flex-direction: column;
    padding: 12px;
  }

  .profile-sidebar {
    width: 100%;
  }

  .sidebar-card {
    position: static;
  }

  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }

  .stat-value {
    font-size: 18px;
  }
}
</style>
