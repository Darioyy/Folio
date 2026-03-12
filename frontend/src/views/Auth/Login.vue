<template>
  <div class="login-page">
    <div class="login-background">
      <div class="background-shape shape-1"></div>
      <div class="background-shape shape-2"></div>
      <div class="background-shape shape-3"></div>
    </div>

    <div class="login-container">
      <div class="login-brand">
        <h1>Folio</h1>
        <p>欢迎回来</p>
      </div>

      <el-card class="login-card" shadow="never">
        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-position="top"
          size="large"
        >
          <el-form-item prop="username">
            <el-input
              v-model="formData.username"
              placeholder="用户名"
              :prefix-icon="User"
              clearable
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="formData.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              show-password
              clearable
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item v-if="captchaEnabled" prop="captcha">
            <div class="captcha-row">
              <el-input
                v-model="formData.captcha"
                placeholder="请输入验证码"
                clearable
                style="flex: 1"
                @keyup.enter="handleLogin"
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
              size="large"
              style="width: 100%"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <span>还没有账号？</span>
          <el-link type="primary" @click="goToRegister">立即注册</el-link>
        </div>
      </el-card>

      <div class="login-back">
        <el-link @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回首页
        </el-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, ArrowLeft } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/modules/auth'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const captchaImg = ref('')
const captchaEnabled = ref(true)

const formData = reactive({
  username: '',
  password: '',
  captcha: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }
  ],
  captcha: [
    { required: () => captchaEnabled.value, message: '请输入验证码', trigger: 'blur' }
  ]
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

async function handleLogin() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await userStore.login(formData.username, formData.password, formData.captcha)
      ElMessage.success('登录成功')

      const redirect = (route.query.redirect as string) || '/'
      router.push(redirect)
    } catch {
      // 错误已在 store 中处理；延迟刷新验证码，避免立即重绘影响错误提示的可读性
      formData.captcha = ''
      setTimeout(refreshCaptcha, 1200)
    } finally {
      loading.value = false
    }
  })
}

function goToRegister() {
  router.push({ name: 'Register', query: { redirect: route.query.redirect } })
}

function goBack() {
  router.push({ name: 'Home' })
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.background-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s ease-in-out infinite;
}

.shape-1 {
  width: 400px;
  height: 400px;
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}

.shape-2 {
  width: 300px;
  height: 300px;
  bottom: -50px;
  left: -50px;
  animation-delay: 5s;
}

.shape-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 50%;
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg);
  }
  33% {
    transform: translate(30px, -30px) rotate(120deg);
  }
  66% {
    transform: translate(-20px, 20px) rotate(240deg);
  }
}

.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 24px;
}

.login-brand {
  text-align: center;
  margin-bottom: 24px;
  color: white;

  h1 {
    font-size: 36px;
    font-weight: 800;
    margin: 0 0 8px 0;
    letter-spacing: -1px;
  }

  p {
    font-size: 16px;
    opacity: 0.9;
    margin: 0;
  }
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: none !important;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;

  html.dark & {
    background: rgba(30, 41, 59, 0.95) !important;
  }

  :deep(.el-card__body) {
    padding: 32px;
  }

  :deep(.el-input__wrapper) {
    border-radius: 10px;
    padding: 8px 16px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);

    &:hover,
    &.is-focus {
      box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }
  }

  .el-button {
    height: 48px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 10px;
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
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
  line-height: 1.4;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: var(--el-text-color-secondary);

  .el-link {
    font-weight: 600;
    margin-left: 4px;
  }
}

.login-back {
  text-align: center;
  margin-top: 16px;

  .el-link {
    color: rgba(255, 255, 255, 0.8);
    font-size: 14px;
    display: inline-flex;
    align-items: center;
    gap: 4px;

    &:hover {
      color: white;
    }
  }
}

@media (max-width: 640px) {
  .login-container {
    padding: 16px;
  }

  .login-brand {
    h1 {
      font-size: 28px !important;
    }

    p {
      font-size: 14px !important;
    }
  }

  .login-card {
    :deep(.el-card__body) {
      padding: 24px;
    }
  }
}
</style>
