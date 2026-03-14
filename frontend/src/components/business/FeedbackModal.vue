<template>
  <el-dialog
    v-model="visible"
    width="420px"
    :close-on-click-modal="!submitting"
    @close="resetForm"
  >
    <template #header>
      <span class="dialog-title">提个建议</span>
    </template>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      :disabled="submitting"
      class="fb-form"
    >
      <!-- 类型分段选择 -->
      <el-form-item prop="type">
        <div class="type-seg">
          <button
            v-for="t in TYPES"
            :key="t.value"
            :class="['seg-btn', { active: form.type === t.value }]"
            type="button"
            @click="form.type = t.value"
          >{{ t.label }}</button>
        </div>
      </el-form-item>

      <el-form-item prop="title">
        <el-input
          v-model="form.title"
          placeholder="标题：用一句话概括..."
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="4"
          placeholder="请详细描述你的建议或遇到的问题..."
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-form-item>
        <el-input
          v-model="form.contact"
          placeholder="联系方式（选填，邮箱或其他）"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false" :disabled="submitting">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { feedbackApi, type FeedbackType } from '@/api/modules/feedback'

const visible = defineModel<boolean>({ required: true })

const TYPES = [
  { value: 'feature' as FeedbackType, label: '功能建议' },
  { value: 'bug'     as FeedbackType, label: 'Bug 反馈' },
  { value: 'other'   as FeedbackType, label: '其他'     },
]

const formRef    = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  type:    'feature' as FeedbackType,
  title:   '',
  content: '',
  contact: '',
})

const rules: FormRules = {
  title:   [
    { required: true, message: '请填写标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题 2–100 字', trigger: 'blur' },
  ],
  content: [
    { required: true, message: '请填写描述', trigger: 'blur' },
    { min: 5, max: 500, message: '描述 5–500 字', trigger: 'blur' },
  ],
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await feedbackApi.submit({
      type:    form.type,
      title:   form.title,
      content: form.content,
      contact: form.contact || undefined,
    })
    ElMessage.success('感谢你的反馈！')
    visible.value = false
    resetForm()
  } catch {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  form.type    = 'feature'
  form.title   = ''
  form.content = ''
  form.contact = ''
  formRef.value?.clearValidate()
}
</script>

<style scoped lang="scss">
// ── 弹窗标题 ─────────────────────────────────────────
.dialog-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

// ── 表单整体 ─────────────────────────────────────────
.fb-form {
  display: flex;
  flex-direction: column;
  gap: 2px;

  :deep(.el-form-item) {
    margin-bottom: 10px;
  }

  :deep(.el-form-item__label) {
    display: none;
  }

  :deep(.el-form-item__error) {
    font-size: 11px;
    padding-top: 3px;
  }
}

// ── 分段类型选择器 ───────────────────────────────────
.type-seg {
  display: flex;
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: $radius-md;
  overflow: hidden;
}

.seg-btn {
  flex: 1;
  padding: 8px 0;
  background: transparent;
  border: none;
  border-right: 1px solid var(--color-border);
  font-size: 13px;
  font-family: inherit;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background $transition-fast, color $transition-fast;

  &:last-child { border-right: none; }

  &:hover {
    background: var(--color-surface-hover);
  }

  &.active {
    background: var(--color-primary-subtle);
    color: var(--color-primary);
    font-weight: 500;
  }
}
</style>
