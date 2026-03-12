<template>
  <div>
    <!-- 修改密码 -->
    <div class="settings-card">
      <div class="card-title">
        <el-icon><Key /></el-icon>
        修改密码
      </div>
      <el-form :model="passwordForm" label-position="top" class="settings-form">
        <el-form-item label="当前密码">
          <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="输入当前密码" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="输入新密码（至少6位）" />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="再次输入新密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="passwordSaving" @click="savePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 内测码兑换（仅普通用户可见） -->
    <div v-if="!userStore.isAdminOrRoot" class="settings-card">
      <div class="card-title">
        <el-icon><Ticket /></el-icon>
        内测码兑换
      </div>
      <el-form label-position="top" class="settings-form">
        <el-form-item label="内测码">
          <el-input
            v-model="redeemCode"
            placeholder="输入 8 位内测码"
            maxlength="8"
            style="width: 200px"
            :disabled="redeemLoading"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="redeemLoading" @click="handleRedeemCode">兑换</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Key, Ticket } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { usersApi } from '@/api/modules/users'

const userStore = useUserStore()
const router = useRouter()

const passwordForm = reactive({ old_password: '', new_password: '', confirm_password: '' })
const passwordSaving = ref(false)
const redeemCode = ref('')
const redeemLoading = ref(false)

async function savePassword() {
  if (!passwordForm.old_password || !passwordForm.new_password) {
    ElMessage.warning('请填写完整密码信息')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }
  if (passwordForm.new_password.length < 6) {
    ElMessage.error('新密码不能少于6位')
    return
  }
  passwordSaving.value = true
  try {
    await usersApi.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    await userStore.logout()
    await router.push('/login')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '密码修改失败')
  } finally {
    passwordSaving.value = false
  }
}

async function handleRedeemCode() {
  const code = redeemCode.value.trim().toUpperCase()
  if (!code || code.length !== 8) {
    ElMessage.warning('请输入有效的 8 位内测码')
    return
  }
  redeemLoading.value = true
  try {
    await usersApi.redeemInviteCode(code)
    ElMessage.success('内测码兑换成功')
    redeemCode.value = ''
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '兑换失败，内测码无效或已被使用')
  } finally {
    redeemLoading.value = false
  }
}
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
</style>
