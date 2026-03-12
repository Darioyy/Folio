<template>
  <div>
    <!-- 资料设置 -->
    <div class="settings-card">
      <div class="card-title">
        <el-icon><Edit /></el-icon>
        资料设置
      </div>
      <el-form :model="profileForm" label-position="top" class="settings-form">
        <el-form-item label="用户名">
          <el-input v-if="userStore.isRoot" v-model="profileForm.username" placeholder="修改登录用户名" maxlength="50" />
          <el-input v-else :value="user?.username || '--'" disabled />
          <div v-if="userStore.isRoot" class="field-hint">修改用户名将影响登录凭据和个人主页链接</div>
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="profileForm.nickname" placeholder="设置昵称" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item label="个性签名">
          <el-input
            v-model="profileForm.signature"
            type="textarea"
            placeholder="写下你的个性签名"
            :rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="profileForm.email" type="email" placeholder="your@email.com" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="profileSaving" @click="saveProfile">保存资料</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 隐私设置 -->
    <div class="settings-card">
      <div class="card-title">
        <el-icon><Lock /></el-icon>
        隐私设置
      </div>
      <div class="privacy-list">
        <div class="privacy-item">
          <div class="privacy-label">
            <span>展示统计</span>
            <span class="privacy-hint">是否公开博文数量等统计信息</span>
          </div>
          <el-switch
            v-model="privacyForm.privacy_stats"
            :active-value="1"
            :inactive-value="0"
            @change="savePrivacy"
          />
        </div>
        <div class="privacy-item">
          <div class="privacy-label">
            <span>展示内容</span>
            <span class="privacy-hint">是否在主页显示你的公开作品</span>
          </div>
          <el-switch
            v-model="privacyForm.privacy_content"
            :active-value="1"
            :inactive-value="0"
            @change="savePrivacy"
          />
        </div>
        <div class="privacy-item">
          <div class="privacy-label">
            <span>展示关注关系</span>
            <span class="privacy-hint">是否公开粉丝和关注列表</span>
          </div>
          <el-switch
            v-model="privacyForm.privacy_follow"
            :active-value="1"
            :inactive-value="0"
            @change="savePrivacy"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { usersApi } from '@/api/modules/users'

const userStore = useUserStore()
const user = computed(() => userStore.currentUser)

const profileForm = reactive({ nickname: '', signature: '', email: '', username: '' })
const profileSaving = ref(false)

const privacyForm = reactive<{ privacy_stats: 0|1, privacy_content: 0|1, privacy_follow: 0|1 }>({
  privacy_stats: 1,
  privacy_content: 1,
  privacy_follow: 1,
})

function initForms() {
  const u = userStore.currentUser
  if (!u) return
  profileForm.nickname = u.nickname || ''
  profileForm.signature = (u as any).signature || ''
  profileForm.email = u.email || ''
  profileForm.username = u.username || ''
  privacyForm.privacy_stats = (u as any).privacy_stats ?? 1
  privacyForm.privacy_content = (u as any).privacy_content ?? 1
  privacyForm.privacy_follow = (u as any).privacy_follow ?? 1
}

async function saveProfile() {
  profileSaving.value = true
  try {
    const u = userStore.currentUser
    if (userStore.isRoot && u && profileForm.username.trim() && profileForm.username.trim() !== u.username) {
      await usersApi.update(u.id, { username: profileForm.username.trim() } as any)
    }
    await usersApi.updateProfile({
      nickname: profileForm.nickname,
      signature: profileForm.signature,
      email: profileForm.email,
    })
    await userStore.refreshUser()
    profileForm.username = userStore.currentUser?.username || ''
    ElMessage.success('资料保存成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '保存失败')
  } finally {
    profileSaving.value = false
  }
}

async function savePrivacy() {
  try {
    await usersApi.updatePrivacy({ ...privacyForm })
    ElMessage.success('隐私设置已保存')
  } catch {
    ElMessage.error('保存隐私设置失败')
  }
}

onMounted(initForms)
</script>

<style scoped lang="scss">
.settings-card {
  background: var(--el-bg-color);
  border-radius: $radius-lg;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
  margin-bottom: $spacing-md;
}

.card-title {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: $font-base;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: $spacing-md;

  .el-icon {
    font-size: 18px;
    color: $color-primary;
  }
}

.settings-form {
  max-width: 480px;
}

.field-hint {
  font-size: 12px;
  color: var(--el-color-warning);
  margin-top: 4px;
}

.privacy-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.privacy-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm 0;
  border-bottom: 1px solid var(--el-border-color-lighter);

  &:last-child {
    border-bottom: none;
  }
}

.privacy-label {
  display: flex;
  flex-direction: column;
  gap: 2px;

  span:first-child {
    font-size: $font-sm;
    font-weight: 500;
    color: var(--el-text-color-primary);
  }
}

.privacy-hint {
  font-size: $font-xs !important;
  color: var(--el-text-color-secondary) !important;
  font-weight: 400 !important;
}
</style>
