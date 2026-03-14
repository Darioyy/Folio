<template>
  <div class="editor-page">
    <header class="top-bar">
      <button class="back-btn" @click="router.push('/blog')">
        <el-icon><ArrowLeft /></el-icon>
        <span>博客</span>
      </button>
      <input v-model="title" class="title-input" placeholder="请输入标题..." maxlength="120" />
      <div class="top-actions">
        <span class="save-hint">{{ saveHint }}</span>
        <span :class="['status-tag', status === 'published' ? 'status-published' : 'status-draft']">
          {{ status === 'published' ? '已发布' : '草稿' }}
        </span>
        <button class="top-icon-btn" title="文章设置" @click="drawerVisible = true">
          <el-icon><Setting /></el-icon>
        </button>
        <el-button size="small" :loading="saving" @click="handleSaveDraft">存草稿</el-button>
        <el-button size="small" type="primary" :loading="publishing" @click="handlePublish">{{ status === 'published' ? '更新' : '发布' }}</el-button>
      </div>
    </header>

    <div class="editor-body">
      <div class="editor-pane">
        <textarea v-model="content" class="md-textarea" placeholder="开始写作... (支持 Markdown)" spellcheck="false" />
      </div>
      <div class="preview-pane">
        <div class="preview-content post-content" v-html="markdownHtml" />
      </div>
    </div>

    <el-drawer v-model="drawerVisible" title="文章设置" direction="rtl" size="360px">
      <div class="drawer-body">
        <div class="drawer-section">
          <label class="section-label">摘要</label>
          <el-input v-model="summary" type="textarea" :rows="3" placeholder="留空则自动提取正文前 120 字" maxlength="300" show-word-limit />
        </div>
        <div class="drawer-section">
          <label class="section-label">专栏</label>
          <el-select v-model="categoryId" placeholder="选择专栏" clearable style="width: 100%">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </div>
        <div class="drawer-section">
          <label class="section-label">封面图 <span class="optional-tag">可选</span></label>
          <div v-if="coverImageUrl" class="cover-preview">
            <img :src="coverImageUrl" alt="封面" class="cover-thumb" />
            <el-button size="small" type="danger" plain @click="coverImageId = null; coverImageUrl = ''">移除</el-button>
          </div>
          <el-button v-else size="small" @click="showImagePicker = true">
            <el-icon><Picture /></el-icon> 选择封面
          </el-button>
        </div>
        <div class="drawer-section">
          <label class="section-label">附件 <span class="optional-tag">可选</span></label>
          <div v-if="attachments.length" class="attachment-list">
            <div v-for="att in attachments" :key="att.file_id" class="att-item">
              <span class="att-name">{{ att.file_name }}</span>
              <el-button link type="danger" size="small" @click="removeAttachment(att.file_id)">移除</el-button>
            </div>
          </div>
          <el-button size="small" :disabled="!postId" @click="showFilePicker = true">
            <el-icon><Paperclip /></el-icon> 添加附件
          </el-button>
          <p v-if="!postId" class="attach-hint">请先存草稿后再添加附件</p>
        </div>
      </div>
    </el-drawer>

    <FilePicker v-model="showImagePicker" filter="image" @select="onCoverSelect" />
    <FilePicker v-model="showFilePicker" filter="all" @select="onAttachmentSelect" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Setting, Picture, Paperclip } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { usePostEditor } from '@/composables/usePostEditor'
import FilePicker from '@/components/business/FilePicker.vue'
import type { FileItem } from '@/types/models'

const route = useRoute()
const router = useRouter()

const {
  postId, title, content, summary, categoryId,
  coverImageId, coverImageUrl, attachments, status, saving, categories,
  initNew, initEdit, saveDraft, publish, addAttachment, removeAttachment, setCoverImage
} = usePostEditor()

const drawerVisible = ref(false)
const showImagePicker = ref(false)
const showFilePicker = ref(false)
const publishing = ref(false)
const lastSaved = ref<Date | null>(null)

const markdownHtml = computed(() =>
  content.value ? String(marked.parse(content.value)) : '<p class="preview-placeholder">预览将在这里显示...</p>'
)

const saveHint = computed(() => {
  if (saving.value) return '保存中...'
  if (lastSaved.value) return `已保存 ${lastSaved.value.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  return ''
})

async function handleSaveDraft() {
  if (!title.value.trim()) { ElMessage.warning('请先填写标题'); return }
  try {
    const id = await saveDraft()
    if (id) { lastSaved.value = new Date(); ElMessage.success('草稿已保存') }
    else ElMessage.error('保存失败，请重试')
  } catch { /* axios 拦截器已弹出错误提示 */ }
}

async function handlePublish() {
  if (!title.value.trim()) { ElMessage.warning('请填写标题'); return }
  if (!content.value.trim()) { ElMessage.warning('请填写正文内容'); return }

  const isAlreadyPublished = status.value === 'published'
  const confirmMsg = isAlreadyPublished
    ? '确认更新已发布的博文？'
    : '确认发布博文？发布后将对所有人可见。'
  const confirmTitle = isAlreadyPublished ? '更新博文' : '发布博文'

  try {
    await ElMessageBox.confirm(confirmMsg, confirmTitle, {
      confirmButtonText: isAlreadyPublished ? '更新' : '发布',
      cancelButtonText: '取消',
      type: 'info'
    })
  } catch { return }
  publishing.value = true
  try {
    const id = await publish()
    if (id) {
      ElMessage.success(isAlreadyPublished ? '更新成功' : '发布成功')
      router.push(`/post/${id}`)
    } else ElMessage.error('操作失败，请重试')
  } catch { /* 拦截器已弹出错误提示 */ } finally { publishing.value = false }
}

function onCoverSelect(file: FileItem) {
  if (file.file_category !== 'image') {
    ElMessage.warning('封面图请选择图片格式文件')
    return
  }
  setCoverImage(file.id)
}
async function onAttachmentSelect(file: FileItem) { await addAttachment(file.id) }

onMounted(() => {
  const id = route.params.id
  if (id) initEdit(Number(id))
  else initNew()
})
</script>

<style lang="scss" scoped>
.editor-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--el-bg-color);
}

.top-bar {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: 0 $spacing-lg;
  height: 56px;
  border-bottom: 1px solid var(--el-border-color-light);
  flex-shrink: 0;
  background: var(--el-bg-color);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  background: none;
  border: none;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  font-size: $font-sm;
  padding: 0;
  flex-shrink: 0;
  &:hover { color: $color-primary; }
}

.title-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: $font-lg;
  font-weight: 600;
  color: var(--el-text-color-primary);
  background: transparent;
  min-width: 0;
  &::placeholder { color: var(--el-text-color-placeholder); font-weight: 400; }
}

.top-actions {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-shrink: 0;
  .save-hint { font-size: $font-xs; color: var(--el-text-color-placeholder); white-space: nowrap; }
}

.top-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background $transition-fast, color $transition-fast;
  flex-shrink: 0;

  .el-icon { font-size: 16px; }
  &:hover { background: var(--el-fill-color); color: var(--el-text-color-primary); }
}

.status-tag {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;

  &.status-published {
    background: rgba(16, 185, 129, 0.1);
    color: #059669;
    border: 1px solid rgba(16, 185, 129, 0.25);
  }

  &.status-draft {
    background: var(--el-fill-color-light);
    color: var(--el-text-color-secondary);
    border: 1px solid var(--el-border-color-lighter);
  }
}

.editor-body { display: flex; flex: 1; overflow: hidden; }

.editor-pane, .preview-pane { flex: 1; overflow-y: auto; height: 100%; }
.editor-pane { border-right: 1px solid var(--el-border-color-light); }

.md-textarea {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  resize: none;
  padding: $spacing-xl;
  font-size: $font-sm;
  font-family: 'Cascadia Code', 'JetBrains Mono', monospace;
  line-height: 1.7;
  color: var(--el-text-color-regular);
  background: var(--el-bg-color);
  box-sizing: border-box;
}

.preview-content {
  padding: $spacing-xl;
  font-size: 15px;
  line-height: 1.8;
  color: var(--el-text-color-regular);

  :deep(.preview-placeholder) { color: var(--el-text-color-placeholder); font-style: italic; }
  :deep(h1), :deep(h2), :deep(h3) { color: var(--el-text-color-primary); font-weight: 600; margin: 1.5em 0 0.5em; }
  :deep(h1) { font-size: 1.75em; }
  :deep(h2) { font-size: 1.4em; border-bottom: 1px solid var(--el-border-color-light); padding-bottom: 0.3em; }
  :deep(h3) { font-size: 1.2em; }
  :deep(p) { margin: 0.8em 0; }
  :deep(a) { color: $color-primary; text-decoration: none; }
  :deep(code) { background: var(--el-fill-color); padding: 2px 6px; border-radius: $radius-sm; font-size: 0.9em; font-family: monospace; }
  :deep(pre) { background: var(--el-fill-color); border-radius: $radius-lg; padding: $spacing-md; overflow-x: auto; margin: 1em 0; code { background: none; padding: 0; } }
  :deep(blockquote) { border-left: 4px solid $color-primary; margin: 1em 0; padding: $spacing-sm $spacing-md; background: var(--el-fill-color-light); color: var(--el-text-color-secondary); }
  :deep(ul), :deep(ol) { padding-left: 1.5em; margin: 0.8em 0; }
  :deep(img) { max-width: 100%; border-radius: $radius-lg; }
  :deep(table) { width: 100%; border-collapse: collapse; margin: 1em 0; }
  :deep(th), :deep(td) { border: 1px solid var(--el-border-color-light); padding: 8px 12px; }
  :deep(th) { background: var(--el-fill-color); font-weight: 600; }
}

.drawer-body { padding: $spacing-md 0; display: flex; flex-direction: column; gap: $spacing-lg; }
.drawer-section { display: flex; flex-direction: column; gap: $spacing-sm; }
.section-label { font-size: $font-sm; font-weight: 500; color: var(--el-text-color-primary); }

.cover-preview {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  align-items: flex-start;
  .cover-thumb { width: 100%; max-height: 160px; object-fit: cover; border-radius: $radius-lg; }
}

.attachment-list { display: flex; flex-direction: column; gap: $spacing-xs; margin-bottom: $spacing-xs; }
.att-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px $spacing-sm;
  background: var(--el-fill-color-light);
  border-radius: $radius-md;
  .att-name { font-size: $font-sm; color: var(--el-text-color-regular); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; margin-right: $spacing-sm; }
}

.attach-hint { font-size: $font-xs; color: var(--el-text-color-placeholder); margin: 0; }

.optional-tag {
  font-size: 11px;
  font-weight: 400;
  color: var(--el-text-color-placeholder);
  margin-left: 4px;
}
</style>
