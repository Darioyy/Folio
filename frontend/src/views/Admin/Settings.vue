<template>
  <div class="settings-page" v-loading="loading">
    <!-- 系统开关 -->
    <el-card class="settings-card">
      <template #header><span>系统开关</span></template>
      <div class="settings-form">
        <div class="setting-item">
          <div class="setting-label">
            <div class="setting-title">开放注册</div>
            <div class="setting-desc">关闭后新用户无法注册</div>
          </div>
          <el-switch v-model="config.register_enabled" @change="saveConfig" />
        </div>
        <div class="setting-item">
          <div class="setting-label">
            <div class="setting-title">内测码验证</div>
            <div class="setting-desc">开启后注册必须填写内测码</div>
          </div>
          <el-switch v-model="config.invite_code_required" @change="saveConfig" />
        </div>
        <div class="setting-item">
          <div class="setting-label">
            <div class="setting-title">登录/注册验证码</div>
            <div class="setting-desc">关闭后无需输入图形验证码（开发调试用）</div>
          </div>
          <el-switch v-model="config.captcha_enabled" @change="saveConfig" />
        </div>
      </div>
    </el-card>

    <!-- 全局设置 -->
    <el-card class="settings-card">
      <template #header><span>全局设置</span></template>
      <el-form label-width="160px" class="quota-form">
        <el-form-item label="超级管理员存储配额">
          <el-input-number
            v-model="quotaRootMB"
            :min="1"
            :max="10485760"
            controls-position="right"
            style="width: 180px"
          />
          <span class="unit-label">MB</span>
          <span class="hint-text">（{{ formatStorage(config.storage_quota_root) }}）</span>
        </el-form-item>
        <el-form-item label="管理员存储配额">
          <el-input-number
            v-model="quotaAdminMB"
            :min="1"
            :max="10485760"
            controls-position="right"
            style="width: 180px"
          />
          <span class="unit-label">MB</span>
          <span class="hint-text">（{{ formatStorage(config.storage_quota_admin) }}）</span>
        </el-form-item>
        <el-form-item label="普通用户存储配额">
          <el-input-number
            v-model="quotaUserMB"
            :min="1"
            :max="10485760"
            controls-position="right"
            style="width: 180px"
          />
          <span class="unit-label">MB</span>
          <span class="hint-text">（{{ formatStorage(config.storage_quota_user) }}）</span>
        </el-form-item>
        <el-form-item label="单文件大小上限">
          <el-input-number
            v-model="maxFileMB"
            :min="1"
            :max="2048"
            controls-position="right"
            style="width: 180px"
          />
          <span class="unit-label">MB</span>
          <span class="hint-text">（{{ formatStorage(config.max_file_size) }}）</span>
        </el-form-item>
        <el-form-item label="允许上传后缀" class="ext-form-item">
          <el-input
            v-model="config.allowed_extensions"
            placeholder="png,jpg,mp4,pdf,..."
            class="ext-input"
          />
          <div class="ext-hint">留空表示不限制后缀类型</div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveQuotaConfig">保存设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 内测码管理 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header-row">
          <span>内测码管理</span>
          <el-button type="primary" size="small" @click="generateCode" :loading="generatingCode">
            生成新内测码
          </el-button>
        </div>
      </template>
      <div class="invite-table-wrap">
        <el-table :data="inviteCodes" style="width: 100%" v-loading="codesLoading">
          <el-table-column label="内测码" prop="code" min-width="130">
            <template #default="{ row }">
              <code class="code-text">{{ row.code }}</code>
            </template>
          </el-table-column>
          <el-table-column label="状态" min-width="80">
            <template #default="{ row }">
              <el-tag :type="row.used ? 'info' : 'success'" size="small">
                {{ row.used ? '已使用' : '未使用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="使用者" min-width="110" show-overflow-tooltip>
            <template #default="{ row }">{{ row.used_by || '-' }}</template>
          </el-table-column>
          <el-table-column label="创建时间" min-width="165">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="使用时间" min-width="165">
            <template #default="{ row }">{{ row.used_at ? formatDate(row.used_at) : '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" min-width="70" fixed="right">
            <template #default="{ row }">
              <el-popconfirm
                title="确定删除该内测码？"
                confirm-button-text="删除"
                confirm-button-type="danger"
                @confirm="deleteCode(row.code)"
              >
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-if="inviteCodes.length === 0 && !codesLoading" class="empty-tip">
        暂无内测码
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi } from '@/api/modules/system'
import type { SystemConfig, InviteCode } from '@/types/models'

const loading = ref(false)
const codesLoading = ref(false)
const generatingCode = ref(false)

const config = ref<SystemConfig>({
  register_enabled: true,
  invite_code_required: false,
  storage_quota_root: 10737418240,
  storage_quota_admin: 5368709120,
  storage_quota_user: 1073741824,
  max_file_size: 16777216,
  allowed_extensions: '',
})

const inviteCodes = ref<InviteCode[]>([])

// 编辑用的 MB 值（双向绑定方便用户输入）
const quotaRootMB = computed({
  get: () => Math.round(config.value.storage_quota_root / 1024 / 1024),
  set: (v: number) => { config.value.storage_quota_root = v * 1024 * 1024 }
})
const quotaAdminMB = computed({
  get: () => Math.round(config.value.storage_quota_admin / 1024 / 1024),
  set: (v: number) => { config.value.storage_quota_admin = v * 1024 * 1024 }
})
const quotaUserMB = computed({
  get: () => Math.round(config.value.storage_quota_user / 1024 / 1024),
  set: (v: number) => { config.value.storage_quota_user = v * 1024 * 1024 }
})
const maxFileMB = computed({
  get: () => Math.round(config.value.max_file_size / 1024 / 1024),
  set: (v: number) => { config.value.max_file_size = v * 1024 * 1024 }
})

function formatStorage(bytes: number) {
  if (!bytes) return '0 B'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(0)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}
function formatDate(iso: string) {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

async function loadConfig() {
  loading.value = true
  try {
    const res = await systemApi.getConfig()
    if (res.success && res.data) {
      config.value = { ...config.value, ...res.data }
    }
  } catch {
    ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

async function loadCodes() {
  codesLoading.value = true
  try {
    const res = await systemApi.getInviteCodes()
    if (res.success) inviteCodes.value = res.data ?? []
  } catch {
    // silent
  } finally {
    codesLoading.value = false
  }
}

async function saveConfig() {
  try {
    const res = await systemApi.updateConfig({
      register_enabled: config.value.register_enabled,
      invite_code_required: config.value.invite_code_required,
      captcha_enabled: config.value.captcha_enabled,
    })
    if (res.success) ElMessage.success('配置已保存')
    else ElMessage.error(res.message || '保存失败')
  } catch {
    ElMessage.error('保存配置失败')
  }
}

async function saveQuotaConfig() {
  try {
    const res = await systemApi.updateConfig({
      storage_quota_root: config.value.storage_quota_root,
      storage_quota_admin: config.value.storage_quota_admin,
      storage_quota_user: config.value.storage_quota_user,
      max_file_size: config.value.max_file_size,
      allowed_extensions: config.value.allowed_extensions,
    })
    if (res.success) ElMessage.success('设置已保存')
    else ElMessage.error(res.message || '保存失败')
  } catch {
    ElMessage.error('保存配额设置失败')
  }
}

async function generateCode() {
  generatingCode.value = true
  try {
    const res = await systemApi.createInviteCode()
    if (res.success) {
      ElMessage.success(`内测码已生成：${res.data?.code}`)
      await loadCodes()
    }
  } catch {
    ElMessage.error('生成内测码失败')
  } finally {
    generatingCode.value = false
  }
}

async function deleteCode(code: string) {
  try {
    const res = await systemApi.deleteInviteCode(code)
    if (res.success) {
      ElMessage.success('内测码已删除')
      inviteCodes.value = inviteCodes.value.filter(c => c.code !== code)
    }
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadConfig()
  loadCodes()
})
</script>

<style scoped lang="scss">
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-card {
  :deep(.el-card__header) {
    font-weight: 600;
    font-size: 15px;
  }
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;

  .setting-title {
    font-size: 14px;
    font-weight: 500;
    color: var(--el-text-color-primary);
  }
  .setting-desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 2px;
  }
}

.quota-form {
  .unit-label {
    margin-left: 8px;
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }
  .hint-text {
    margin-left: 8px;
    color: var(--el-text-color-placeholder);
    font-size: 12px;
  }
}

:deep(.ext-form-item) {
  .el-form-item__content {
    flex-direction: column;
    align-items: flex-start;
  }
}

.ext-input {
  width: 480px;
  max-width: 100%;
}

.ext-hint {
  margin-top: 6px;
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.invite-table-wrap {
  overflow-x: auto;
}

.code-text {
  font-family: monospace;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 1px;
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
}

.empty-tip {
  text-align: center;
  color: var(--el-text-color-secondary);
  padding: 20px 0;
  font-size: 14px;
}
</style>
