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
            />
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

          <el-form-item label="内测码（可选）" prop="code">
            <el-input
              v-model="formData.code"
              placeholder="如有内测码请输入"
              :prefix-icon="Key"
              clearable
              @keyup.enter="handleRegister"
            />
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
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Key } from '@element-plus/icons-vue'
import { authApi } from '@/api/modules/auth'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)

const formData = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  code: ''
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
  ]
}

async function handleRegister() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await authApi.register({
        username: formData.username,
        password: formData.password,
        code: formData.code || undefined
      })
      ElMessage.success('注册成功，请登录')
      router.push({ name: 'Login', query: { redirect: route.query.redirect } })
    } catch {
      // 错误已在 API 层处理
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

.register-footer {
  text-align: center;
  margin-top: $spacing-md;
  color: var(--el-text-color-secondary);

  .el-link {
    margin-left: $spacing-xs;
  }
}
</style>
