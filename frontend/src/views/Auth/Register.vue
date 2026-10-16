<template>
  <div class="register-page">
    <div class="register-container">
      <el-card class="register-card" shadow="always">
        <template #header>
          <div class="register-header">
            <h1>注册</h1>
            <p>创建新账号</p>
          </div>
        </template>

        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-position="top"
          size="large"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="formData.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
              clearable
              @input="onUsernameInput"
            />
            <div v-if="usernameStatus" :class="['username-status', usernameStatus.available ? 'available' : 'taken']">
              {{ usernameStatus.message }}
            </div>
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="formData.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="formData.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              :prefix-icon="Lock"
              show-password
              clearable
              @keyup.enter="handleRegister"
            />
          </el-form-item>

          <el-form-item label="昵称（可选）" prop="nickname">
            <el-input
              v-model="formData.nickname"
              placeholder="显示名称，不填则使用用户名"
              clearable
            />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="formData.email"
              placeholder="请输入邮箱地址"
              clearable
              @input="onEmailInput"
            />
            <div v-if="emailStatus" :class="['username-status', emailStatus.available ? 'available' : 'taken']">
              {{ emailStatus.message }}
            </div>
          </el-form-item>

          <el-form-item label="内测码（可选）" prop="invite_code">
            <el-input
              v-model="formData.invite_code"
              placeholder="如有内测码请输入"
              :prefix-icon="Key"
              clearable
              @keyup.enter="handleRegister"
            />
          </el-form-item>

          <el-form-item v-if="captchaEnabled" label="验证码" prop="captcha">
            <div class="captcha-row">
              <el-input
                v-model="formData.captcha"
                placeholder="请输入验证码"
                clearable
                style="flex: 1"
                @keyup.enter="handleRegister"
              />
              <img
                :src="captchaImg"
                class="captcha-img"
                title="点击刷新验证码"
                @click="refreshCaptcha"
              />
            </div>
            <div class="captcha-hint">不区分大小写 · 点击图片刷新</div>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              style="width: 100%"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form-item>
        </el-form>

        <div class="register-footer">
          <span>已有账号？</span>
          <el-link type="primary" @click="goToLogin">立即登录</el-link>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Key } from '@element-plus/icons-vue'
import { authApi } from '@/api/modules/auth'
import { usersApi } from '@/api/modules/users'
import { useUserStore } from '@/stores/user'
import { storage } from '@/utils/storage'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const captchaImg = ref('')
const captchaEnabled = ref(true)
const usernameStatus = ref<{ available: boolean; message: string } | null>(null)
const emailStatus = ref<{ available: boolean; message: string } | null>(null)
let usernameTimer: ReturnType<typeof setTimeout> | null = null
let emailTimer: ReturnType<typeof setTimeout> | null = null

const formData = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  nickname: '',
  email: '',
  invite_code: '',
  captcha: ''
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== formData.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validateEmail = (_rule: any, value: string, callback: any) => {
  if (!value) return callback(new Error('请输入邮箱地址'))
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(value)) {
    callback(new Error('邮箱格式不正确'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3-20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ],
  email: [
    { required: true, validator: validateEmail, trigger: 'blur' }
  ],
  captcha: [
    { required: () => captchaEnabled.value, message: '请输入验证码', trigger: 'blur' }
  ]
}

function onUsernameInput(val: string) {
  usernameStatus.value = null
  if (usernameTimer) clearTimeout(usernameTimer)
  const trimmed = val.trim()
  if (trimmed.length < 3) return
  usernameTimer = setTimeout(async () => {
    try {
      const res = await usersApi.checkUsername(trimmed)
      usernameStatus.value = res.data
    } catch {
      // ignore
    }
  }, 600)
}

function onEmailInput(val: string) {
  emailStatus.value = null
  if (emailTimer) clearTimeout(emailTimer)
  const trimmed = val.trim()
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) return
  emailTimer = setTimeout(async () => {
    try {
      const res = await usersApi.checkEmail(trimmed)
      emailStatus.value = res.data
    } catch {
      // ignore
    }
  }, 600)
}

async function refreshCaptcha() {
  try {
    const res = await authApi.getCaptcha()
    captchaEnabled.value = res.data.enabled
    captchaImg.value = res.data.image
  } catch {
    // ignore
  }
}

onMounted(refreshCaptcha)

async function handleRegister() {
  if (!formRef.value) return
  if (usernameStatus.value && !usernameStatus.value.available) {
    ElMessage.warning(usernameStatus.value.message || '该用户名已被使用，请更换')
    return
  }
  if (emailStatus.value && !emailStatus.value.available) {
    ElMessage.warning(emailStatus.value.message || '该邮箱已被注册，请更换')
    return
  }

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const res = await authApi.register({
        username: formData.username,
        password: formData.password,
        captcha: formData.captcha,
        invite_code: formData.invite_code || undefined,
        nickname: formData.nickname.trim() || undefined,
        email: formData.email.trim()
      })
      // 注册成功后自动登录
      const user = (res.data as any).user
      userStore.currentUser = user
      storage.setUser(user)
      const redirect = route.query.redirect as string
      router.replace(redirect || '/')
    } catch {
      // 错误已在 API 层处理；刷新验证码供下次使用
      refreshCaptcha()
      formData.captcha = ''
    } finally {
      loading.value = false
    }
  })
}

function goToLogin() {
  router.push({ name: 'Login', query: { redirect: route.query.redirect } })
}
</script>

<style scoped lang="scss">
.register-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 60px);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: $spacing-lg;
}

.register-container {
  width: 100%;
  max-width: 400px;
}

.register-card {
  :deep(.el-card__header) {
    padding: $spacing-lg $spacing-lg $spacing-md;
    text-align: center;
  }
}

.register-header {
  h1 {
    font-size: 28px;
    margin-bottom: $spacing-xs;
  }

  p {
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.captcha-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.captcha-img {
  height: 40px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid var(--el-border-color);
  flex-shrink: 0;
}

.captcha-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  line-height: 1.4;
}

.username-status {
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.4;

  &.available {
    color: #10b981;
  }

  &.taken {
    color: var(--el-color-danger);
  }
}


.register-footer {
  text-align: center;
  margin-top: $spacing-md;
  color: var(--el-text-color-secondary);

  .el-link {
    margin-left: $spacing-xs;
  }
}
</style>
