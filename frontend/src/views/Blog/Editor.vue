<template>
  <div class="editor-page">
    <header class="top-bar">
      <button class="back-btn" @click="router.push('/blog')" title="返回博客">
        <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="10 3 5 8 10 13"/></svg>
      </button>
      <input v-model="title" class="title-input" placeholder="无标题文章" maxlength="120" />
      <div class="top-actions">
        <div class="save-status" v-show="saving || lastSaved">
          <span class="save-dot" :class="{ pulsing: saving }"></span>
          <span class="save-text">{{ saveHint }}</span>
        </div>
        <span :class="['status-badge', status === 'published' ? 'published' : 'draft']">
          {{ status === 'published' ? '已发布' : '草稿' }}
        </span>
        <button class="icon-btn" title="文章设置" @click="drawerVisible = true"><el-icon><Setting /></el-icon></button>
        <button class="action-btn ghost" :disabled="saving" @click="handleSaveDraft">存草稿</button>
        <button class="action-btn primary" :disabled="publishing" @click="handlePublish">
          {{ publishing ? '…' : (status === 'published' ? '更新' : '发布') }}
        </button>
      </div>
    </header>

    <div class="editor-body">
      <div class="editor-pane">
        <div class="md-toolbar">
          <div class="tb-group">
            <button class="tb-btn tb-bold"   title="粗体"   @click="wrapSelection('**','**','粗体文字')">B</button>
            <button class="tb-btn tb-italic" title="斜体"   @click="wrapSelection('*','*','斜体文字')">I</button>
            <button class="tb-btn tb-strike" title="删除线" @click="wrapSelection('~~','~~','文字')">S</button>
          </div>
          <div class="tb-group">
            <button class="tb-btn" title="二级标题" @click="insertAtCursor('\n## ')">H<sub>2</sub></button>
            <button class="tb-btn" title="三级标题" @click="insertAtCursor('\n### ')">H<sub>3</sub></button>
          </div>
          <div class="tb-group">
            <button class="tb-btn tb-mono" title="行内代码" @click="wrapSelection('`','`','code')">`c`</button>
            <button class="tb-btn tb-mono" title="代码块"   @click="insertAtCursor('\n```\n\n```')">{}</button>
          </div>
          <div class="tb-group">
            <button class="tb-btn" title="链接"             @click="wrapSelection('[','](url)','链接文字')"><el-icon><Link /></el-icon></button>
            <button class="tb-btn" title="插入图片（云盘）" @click="showContentImagePicker = true"><el-icon><Picture /></el-icon></button>
          </div>
          <div class="tb-group">
            <button class="tb-btn" title="无序列表" @click="insertAtCursor('\n- ')">≡</button>
            <button class="tb-btn tb-mono" title="有序列表" @click="insertAtCursor('\n1. ')">1.</button>
            <button class="tb-btn" title="任务列表" @click="insertAtCursor('\n- [ ] ')">☐</button>
            <button class="tb-btn" title="引用块"   @click="insertAtCursor('\n> ')">❝</button>
          </div>
          <div class="tb-group">
            <button class="tb-btn" title="插入表格" @click="insertAtCursor('\n| 列1 | 列2 | 列3 |\n|---|---|---|\n| 内容 | 内容 | 内容 |\n')">⊞</button>
            <button class="tb-btn tb-mono" title="分割线" @click="insertAtCursor('\n---\n')">—</button>
          </div>
        </div>
        <textarea ref="textareaRef" v-model="content" class="md-textarea"
          placeholder="开始写作…" spellcheck="false" @keydown="handleKeydown" />
        <div class="editor-footer">
          <span class="footer-stat">{{ charCount }} 字符 · {{ lineCount }} 行</span>
          <span class="footer-hint">Tab 缩进 · Enter 延续列表</span>
        </div>
      </div>

      <div class="preview-pane">
        <div class="preview-label-row"><span class="preview-label">预览</span></div>
        <div class="preview-scroll">
          <div class="preview-content post-content" v-html="markdownHtml" />
        </div>
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
          <el-select v-model="categoryId" placeholder="选择专栏" clearable style="width:100%">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </div>
        <div class="drawer-section">
          <label class="section-label">封面图 <span class="optional-tag">可选</span></label>
          <div v-if="coverImageUrl" class="cover-preview">
            <img :src="coverImageUrl" alt="封面" class="cover-thumb" />
            <el-button size="small" type="danger" plain @click="coverImageId = null; coverImageUrl = ''">移除</el-button>
          </div>
          <div v-else class="cover-pick-row">
            <el-button size="small" @click="showImagePicker = true"><el-icon><Picture /></el-icon> 从云盘选择</el-button>
            <el-button size="small" :loading="coverUploading" @click="coverFileInputRef?.click()"><el-icon v-if="!coverUploading"><Upload /></el-icon> 本地上传</el-button>
          </div>
          <input ref="coverFileInputRef" type="file" accept="image/*" style="display:none" @change="onLocalCoverChange" />
        </div>
        <div class="drawer-section">
          <label class="section-label">附件 <span class="optional-tag">可选</span></label>
          <div v-if="attachments.length" class="attachment-list">
            <div v-for="att in attachments" :key="att.file_id" class="att-item">
              <span class="att-name">{{ att.file_name }}</span>
              <el-button link type="danger" size="small" @click="removeAttachment(att.file_id)">移除</el-button>
            </div>
          </div>
          <div class="attach-pick-row">
            <el-button size="small" :disabled="!postId" @click="showFilePicker = true"><el-icon><Paperclip /></el-icon> 从云盘选择</el-button>
            <el-button size="small" :disabled="!postId" :loading="attachUploading" @click="attachFileInputRef?.click()"><el-icon v-if="!attachUploading"><Upload /></el-icon> 本地上传</el-button>
          </div>
          <input ref="attachFileInputRef" type="file" multiple style="display:none" @change="onLocalAttachChange" />
          <p v-if="!postId" class="attach-hint">请先存草稿后再添加附件</p>
        </div>
      </div>
    </el-drawer>

    <FilePicker v-model="showImagePicker" filter="image" @select="onCoverSelect" />
    <FilePicker v-model="showFilePicker" filter="all" @select="onAttachmentSelect" />
    <FilePicker v-model="showContentImagePicker" filter="image" @select="onContentImageSelect" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting, Picture, Paperclip, Upload, Link } from '@element-plus/icons-vue'
import DOMPurify from 'dompurify'
import { marked } from '@/utils/markdown'
import { usePostEditor } from '@/composables/usePostEditor'
import { useMarkdownEditor } from '@/composables/useMarkdownEditor'
import { filesApi } from '@/api/modules/files'
import FilePicker from '@/components/business/FilePicker.vue'
import type { FileItem } from '@/types/models'

const route = useRoute()
const router = useRouter()

const {
  postId, title, content, summary, categoryId,
  coverImageId, coverImageUrl, attachments, status, saving, categories,
  initNew, initEdit, saveDraft, publish, addAttachment, removeAttachment, setCoverImage, flushLocalDraft
} = usePostEditor()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const { insertAtCursor, wrapSelection, handleKeydown } = useMarkdownEditor(content, textareaRef)

const drawerVisible     = ref(false)
const showImagePicker   = ref(false)
const showFilePicker    = ref(false)
const showContentImagePicker = ref(false)
const publishing        = ref(false)
const lastSaved         = ref<Date | null>(null)
const coverFileInputRef = ref<HTMLInputElement | null>(null)
const attachFileInputRef = ref<HTMLInputElement | null>(null)
const coverUploading    = ref(false)
const attachUploading   = ref(false)

const markdownHtml = computed(() =>
  content.value
    ? DOMPurify.sanitize(String(marked.parse(content.value)))
    : '<p class="preview-placeholder">预览将在这里显示…</p>'
)
const charCount  = computed(() => content.value.replace(/\s/g, '').length)
const lineCount  = computed(() => content.value ? content.value.split('\n').length : 0)
const saveHint   = computed(() => {
  if (saving.value) return '保存中…'
  if (lastSaved.value) return `已保存 ${lastSaved.value.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  return ''
})

async function handleSaveDraft() {
  if (!title.value.trim()) { ElMessage.warning('请先填写标题'); return }
  try {
    const id = await saveDraft()
    if (id) { lastSaved.value = new Date(); ElMessage.success('草稿已保存') }
    else ElMessage.error('保存失败，请重试')
  } catch { /* 拦截器已处理 */ }
}

async function handlePublish() {
  if (!title.value.trim()) { ElMessage.warning('请填写标题'); return }
  if (!content.value.trim()) { ElMessage.warning('请填写正文内容'); return }
  const isAlreadyPublished = status.value === 'published'
  try {
    await ElMessageBox.confirm(
      isAlreadyPublished ? '确认更新已发布的博文？' : '确认发布博文？发布后将对所有人可见。',
      isAlreadyPublished ? '更新博文' : '发布博文',
      { confirmButtonText: isAlreadyPublished ? '更新' : '发布', cancelButtonText: '取消', type: 'info' }
    )
  } catch { return }
  publishing.value = true
  try {
    const id = await publish()
    if (id) { ElMessage.success(isAlreadyPublished ? '更新成功' : '发布成功'); router.push(`/post/${id}`) }
    else ElMessage.error('操作失败，请重试')
  } catch { /* 拦截器已处理 */ } finally { publishing.value = false }
}

function onCoverSelect(file: FileItem) {
  if (file.file_category !== 'image') { ElMessage.warning('封面图请选择图片格式文件'); return }
  setCoverImage(file.id)
}
async function onAttachmentSelect(file: FileItem) { await addAttachment(file.id) }
function onContentImageSelect(file: FileItem) {
  insertAtCursor(`\n![${file.file_name}](${filesApi.getViewUrl(file.id)})\n`)
}

async function onLocalCoverChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]; input.value = ''
  if (!file || !file.type.startsWith('image/')) { if (file) ElMessage.warning('请选择图片格式'); return }
  coverUploading.value = true
  try {
    const fd = new FormData(); fd.append('file', file)
    const res = await filesApi.upload(fd)
    if (res.success && res.data) setCoverImage(res.data.id)
    else ElMessage.error('上传失败')
  } catch { /* 拦截器已处理 */ } finally { coverUploading.value = false }
}

async function onLocalAttachChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files ? [...input.files] : []; input.value = ''
  if (!files.length || !postId.value) { if (!postId.value) ElMessage.warning('请先存草稿后再添加附件'); return }
  attachUploading.value = true
  try {
    for (const file of files) {
      const fd = new FormData(); fd.append('file', file)
      const res = await filesApi.upload(fd)
      if (res.success && res.data) await addAttachment(res.data.id)
    }
    ElMessage.success('附件已添加')
  } catch { /* 拦截器已处理 */ } finally { attachUploading.value = false }
}

onBeforeRouteLeave((to, from, next) => {
  if (postId.value || (!title.value.trim() && !content.value.trim())) { next(); return }
  ElMessageBox.confirm('草稿尚未保存到服务器，是否先保存再离开？', '离开前保存', {
    confirmButtonText: '保存草稿', cancelButtonText: '直接离开', distinguishCancelAndClose: true, type: 'info',
  })
    .then(async () => { if (title.value.trim()) await saveDraft().catch(() => {}); next() })
    .catch((a: any) => (a === 'cancel' ? next() : next(false)))
})

onMounted(() => {
  const id = route.params.id
  if (id) initEdit(Number(id)); else initNew()
  window.addEventListener('beforeunload', flushLocalDraft)
})
onUnmounted(() => { window.removeEventListener('beforeunload', flushLocalDraft) })
</script>

<style lang="scss" scoped>
// ── CSS 变量：白天 / 暗夜双模式 ──────────────────────────────────
.editor-page {
  --ep-editor-bg:   #f5f5f2;
  --ep-preview-bg:  #ffffff;
  --ep-toolbar-bg:  #eeeeeb;
  --ep-border:      #e2e2de;
  --ep-footer-mute: #b8b8b0;
  --ep-pane-label:  #c8c8c0;
  --ep-code-color:  #2d2d2a;
  --ep-ghost-bd:    #d4d4ce;
  --ep-ghost-fg:    #4a4a44;
  --ep-ghost-hover: #e8e8e4;
}
:global(html.dark) .editor-page {
  --ep-editor-bg:   #1a1b1d;
  --ep-preview-bg:  #141516;
  --ep-toolbar-bg:  #1f2023;
  --ep-border:      #2a2b2f;
  --ep-footer-mute: #3e3f44;
  --ep-pane-label:  #38393e;
  --ep-code-color:  #d0d0ca;
  --ep-ghost-bd:    #2e2f34;
  --ep-ghost-fg:    #96968f;
  --ep-ghost-hover: #242528;
}

.editor-page { display: flex; flex-direction: column; height: 100vh; overflow: hidden; background: var(--ep-editor-bg); }

// ── 顶栏 ─────────────────────────────────────────────────────────
.top-bar {
  display: flex; align-items: center; gap: 10px; padding: 0 16px; height: 52px;
  background: var(--el-bg-color); border-bottom: 1px solid var(--ep-border); flex-shrink: 0; z-index: 10;
}
.back-btn {
  display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px;
  border: none; background: none; cursor: pointer; color: var(--el-text-color-placeholder);
  border-radius: 6px; transition: color 0.15s, background 0.15s; flex-shrink: 0;
  &:hover { color: var(--el-text-color-primary); background: var(--el-fill-color); }
}
.title-input {
  flex: 1; border: none; outline: none; background: transparent; min-width: 0;
  font-size: 17px; font-weight: 600; color: var(--el-text-color-primary); letter-spacing: -0.01em;
  &::placeholder { color: var(--el-text-color-placeholder); font-weight: 400; }
}
.top-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.save-status { display: flex; align-items: center; gap: 5px; }
.save-dot {
  width: 6px; height: 6px; border-radius: 50%; background: #10b981; flex-shrink: 0;
  &.pulsing { background: $color-primary; animation: dot-pulse 1.2s ease-in-out infinite; }
}
.save-text { font-size: 12px; color: var(--el-text-color-placeholder); white-space: nowrap; }
@keyframes dot-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(0.65); }
}
.status-badge {
  display: inline-flex; align-items: center; height: 22px; padding: 0 8px;
  border-radius: 11px; font-size: 11px; font-weight: 500; white-space: nowrap;
  &.published { background: rgba(16,185,129,.1); color: #059669; border: 1px solid rgba(16,185,129,.2); }
  &.draft { background: var(--el-fill-color-light); color: var(--el-text-color-placeholder); border: 1px solid var(--el-border-color-lighter); }
}
.icon-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px; border: none; background: none; cursor: pointer;
  color: var(--el-text-color-secondary); border-radius: 6px; transition: color .15s, background .15s;
  .el-icon { font-size: 15px; }
  &:hover { color: var(--el-text-color-primary); background: var(--el-fill-color); }
}
.action-btn {
  display: inline-flex; align-items: center; justify-content: center;
  height: 30px; padding: 0 14px; border-radius: 6px; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all .15s; border: 1px solid; font-family: inherit;
  &:disabled { opacity: 0.5; cursor: not-allowed; }
  &.ghost {
    background: transparent; border-color: var(--ep-ghost-bd); color: var(--ep-ghost-fg);
    &:hover:not(:disabled) { background: var(--ep-ghost-hover); }
  }
  &.primary {
    background: $color-primary; border-color: $color-primary; color: #fff;
    &:hover:not(:disabled) { filter: brightness(1.08); }
  }
}

// ── 双栏主体 ─────────────────────────────────────────────────────
.editor-body { display: flex; flex: 1; overflow: hidden; }
.editor-pane {
  flex: 1; min-width: 0; display: flex; flex-direction: column;
  background: var(--ep-editor-bg); border-right: 1px solid var(--ep-border);
}

// ── Markdown 工具栏 ──────────────────────────────────────────────
.md-toolbar {
  display: flex; align-items: center; gap: 2px; padding: 5px 14px;
  background: var(--ep-toolbar-bg); border-bottom: 1px solid var(--ep-border);
  flex-shrink: 0; flex-wrap: wrap;
}
.tb-group {
  display: flex; align-items: center; gap: 1px;
  &:not(:last-child) { margin-right: 5px; padding-right: 5px; border-right: 1px solid var(--ep-border); }
}
.tb-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 24px; border: none; background: none; border-radius: 4px;
  font-size: 11.5px; color: var(--el-text-color-secondary); cursor: pointer; font-family: inherit;
  transition: background .12s, color .12s;
  .el-icon { font-size: 12px; }
  sub { font-size: 8px; line-height: 1; }
  &:hover { background: rgba(90,103,216,.1); color: $color-primary; }
  &.tb-bold   { font-weight: 700; font-size: 13px; }
  &.tb-italic { font-style: italic; font-size: 13px; }
  &.tb-strike { text-decoration: line-through; font-size: 13px; }
  &.tb-mono   { font-family: monospace; font-size: 10.5px; }
}

// ── 编辑器 textarea ──────────────────────────────────────────────
.md-textarea {
  flex: 1; width: 100%; border: none; outline: none; resize: none; box-sizing: border-box;
  padding: 28px 36px; font-size: 14.5px; line-height: 1.85;
  font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
  color: var(--ep-code-color); background: var(--ep-editor-bg); caret-color: $color-primary;
  &::placeholder { color: var(--el-text-color-placeholder); }
}

// ── 编辑器底栏 ───────────────────────────────────────────────────
.editor-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 36px 6px; border-top: 1px solid var(--ep-border);
  background: var(--ep-toolbar-bg); flex-shrink: 0;
}
.footer-stat  { font-size: 11px; color: var(--ep-footer-mute); font-variant-numeric: tabular-nums; }
.footer-hint  { font-size: 11px; color: var(--ep-footer-mute); }

// ── 预览区 ───────────────────────────────────────────────────────
.preview-pane {
  flex: 1; min-width: 0; display: flex; flex-direction: column;
  background: var(--ep-preview-bg); overflow: hidden;
}
.preview-label-row {
  display: flex; align-items: center; padding: 5px 14px;
  border-bottom: 1px solid var(--ep-border); background: var(--ep-toolbar-bg); flex-shrink: 0;
}
.preview-label {
  font-size: 10px; font-weight: 600; letter-spacing: .1em;
  text-transform: uppercase; color: var(--ep-pane-label);
}
.preview-scroll { flex: 1; overflow-y: auto; }
.preview-content {
  max-width: 680px; margin: 0 auto; padding: 32px 40px 64px;
  font-size: 15px; line-height: 1.85; color: var(--el-text-color-regular);

  :deep(.preview-placeholder) { color: var(--el-text-color-placeholder); font-style: italic; }
  :deep(h1),:deep(h2),:deep(h3),:deep(h4),:deep(h5),:deep(h6) { color: var(--el-text-color-primary); font-weight: 650; margin: 1.6em 0 .5em; letter-spacing: -.01em; }
  :deep(h1) { font-size: 1.75em; }
  :deep(h2) { font-size: 1.4em; border-bottom: 1px solid var(--el-border-color-light); padding-bottom: .35em; }
  :deep(h3) { font-size: 1.2em; }
  :deep(h4) { font-size: 1.1em; }
  :deep(h5),:deep(h6) { font-size: 1em; }
  :deep(p) { margin: .9em 0; }
  :deep(a) { color: $color-primary; text-decoration: underline; text-decoration-color: transparent; transition: text-decoration-color .2s; &:hover { text-decoration-color: $color-primary; } }
  :deep(strong) { font-weight: 650; }
  :deep(del) { text-decoration: line-through; opacity: .6; }
  :deep(mark) { background: rgba(255,213,0,.35); padding: 0 2px; border-radius: 2px; }
  :deep(code) { background: var(--el-fill-color); border: 1px solid var(--el-border-color-light); padding: 1px 5px; border-radius: 4px; font-size: .875em; font-family: 'Cascadia Code', 'Fira Code', ui-monospace, monospace; }
  :deep(pre) { background: var(--el-fill-color); border: 1px solid var(--el-border-color-light); border-radius: 8px; padding: 16px 20px; overflow-x: auto; margin: 1.2em 0; line-height: 1.6; code { background: none; border: none; padding: 0; font-size: .875em; } }
  :deep(blockquote) { border-left: 3px solid $color-primary; margin: 1.2em 0; padding: 10px 16px; background: rgba(90,103,216,.05); color: var(--el-text-color-secondary); border-radius: 0 6px 6px 0; font-style: italic; }
  :deep(ul),:deep(ol) { padding-left: 1.5em; margin: .9em 0; }
  :deep(li) { margin: .35em 0; }
  :deep(input[type="checkbox"]) { margin-right: 5px; accent-color: $color-primary; vertical-align: middle; }
  :deep(li:has(input[type="checkbox"]:checked)) { text-decoration: line-through; opacity: .6; }
  :deep(img) { max-width: 100%; border-radius: 8px; display: block; margin: 1em 0; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
  :deep(hr) { border: none; height: 1px; background: linear-gradient(90deg, transparent, var(--el-border-color), transparent); margin: 1.8em 0; }
  :deep(.md-table-wrap) { overflow-x: auto; margin: 1.2em 0; }
  :deep(table) { border-collapse: collapse; width: max-content; max-width: 100%; margin: 0; }
  :deep(th),:deep(td) { border: 1px solid var(--el-border-color-light); padding: 7px 14px; white-space: nowrap; }
  :deep(th) { background: var(--el-fill-color); font-weight: 600; }
  :deep(tr:nth-child(even) td) { background: var(--el-fill-color-lighter); }
}

// ── 设置抽屉 ────────────────────────────────────────────────────
.drawer-body { padding: 12px 0; display: flex; flex-direction: column; gap: 20px; }
.drawer-section { display: flex; flex-direction: column; gap: 8px; }
.section-label { font-size: 13px; font-weight: 500; color: var(--el-text-color-primary); }
.optional-tag  { font-size: 11px; font-weight: 400; color: var(--el-text-color-placeholder); margin-left: 4px; }
.cover-preview {
  display: flex; flex-direction: column; gap: 8px; align-items: flex-start;
  .cover-thumb { width: 100%; max-height: 160px; object-fit: cover; border-radius: 8px; }
}
.cover-pick-row,.attach-pick-row { display: flex; gap: 8px; flex-wrap: wrap; }
.attachment-list { display: flex; flex-direction: column; gap: 4px; margin-bottom: 4px; }
.att-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 4px 10px; background: var(--el-fill-color-light); border-radius: 6px;
  .att-name { font-size: 13px; color: var(--el-text-color-regular); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; margin-right: 8px; }
}
.attach-hint { font-size: 12px; color: var(--el-text-color-placeholder); margin: 0; }
</style>
