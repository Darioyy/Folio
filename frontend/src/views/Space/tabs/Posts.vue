<template>
  <div class="posts-tab">
    <div class="posts-header">
      <div class="status-tabs">
        <span
          v-for="tab in statusTabs"
          :key="tab.value"
          :class="['status-tab', { active: activeTab === tab.value }]"
          @click="switchTab(tab.value)"
        >{{ tab.label }}</span>
      </div>
      <div class="header-right">
        <button :class="['icon-action-btn', { active: batchMode }]" data-tip="批量操作" @click="toggleBatchMode">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="1" y="3" width="5" height="5" rx="1"/>
            <rect x="1" y="10" width="5" height="5" rx="1"/>
            <line x1="9" y1="5.5" x2="15" y2="5.5"/>
            <line x1="9" y1="12.5" x2="15" y2="12.5"/>
          </svg>
        </button>
        <button class="icon-action-btn primary" data-tip="写博文" @click="router.push('/post/create')">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 2l3 3-9 9H2v-3L11 2z"/>
          </svg>
        </button>
      </div>
    </div>

    <div v-loading="loading" class="posts-list">
      <el-empty v-if="!loading && posts.length === 0" description="暂无博文" :image-size="60" />

      <div
        v-for="post in posts"
        :key="post.id"
        :class="['post-row', { selected: selectedIds.includes(post.id) }]"
        @click="batchMode ? toggleSelect(post.id) : router.push('/post/' + post.id)"
      >
        <!-- 批量模式复选框 -->
        <input
          v-if="batchMode"
          type="checkbox"
          class="row-check"
          :checked="selectedIds.includes(post.id)"
          @click.stop="toggleSelect(post.id)"
        />

        <!-- 左：标题 + 状态标签（flex:1 负责截断）-->
        <div class="post-left">
          <span class="post-title">{{ post.title }}</span>
          <template v-if="post.is_hidden">
            <span class="status-badge hidden">已隐藏</span>
            <el-tooltip content="查看隐藏原因" placement="top">
              <button class="hide-info-btn" @click.stop="openHideInfo(post)">
                <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="8" cy="8" r="6"/>
                  <path d="M8 7v4M8 5.5v.5"/>
                </svg>
              </button>
            </el-tooltip>
          </template>
          <span v-else :class="['status-badge', post.status === 'published' ? 'published' : 'draft']">
            {{ post.status === 'published' ? '已发布' : '草稿' }}
          </span>
        </div>
        <!-- 右：meta 统计（flex-shrink:0 不被压缩）+ 操作按钮 -->
        <div class="post-meta">
          <span class="meta-date">{{ formatDate(post.published_at || post.created_at) }}</span>
          <span class="meta-sep">·</span>
          <span class="meta-stat">
            <svg viewBox="0 0 16 16" width="11" height="11" style="overflow:visible"><path d="M8 14s-6-3.8-6-8a4 4 0 018 0 4 4 0 018 0c0 4.2-6 8-6 8z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            {{ post.like_count }}
          </span>
          <span class="meta-stat">
            <svg viewBox="0 0 16 16" width="11" height="11"><path d="M14 2H2a1 1 0 00-1 1v9a1 1 0 001 1h3l3 2 3-2h3a1 1 0 001-1V3a1 1 0 00-1-1z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
            {{ post.comment_count }}
          </span>
        </div>
        <div v-if="!batchMode" class="post-actions" @click.stop>
          <button class="action-btn" @click="router.push('/post/' + post.id + '/edit')">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 2l3 3-9 9H2v-3L11 2z"/></svg>
          </button>
          <button class="action-btn danger" @click="handleDelete(post)">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h12M5 4V2h6v2M6 7v5M10 7v5M3 4l1 10h8l1-10"/></svg>
          </button>
        </div>
      </div>

      <div v-if="total > pageSize" class="pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadPosts"
        />
      </div>
    </div>

    <!-- 批量操作栏 -->
    <Transition name="batch-bar">
      <div v-if="batchMode && selectedIds.length > 0" class="batch-bar">
        <span class="batch-count">已选 <b>{{ selectedIds.length }}</b> 篇</span>
        <button class="batch-sel-all" @click="selectAll">
          {{ selectedIds.length === posts.length ? '取消全选' : '全选' }}
        </button>
        <div class="batch-actions">
          <button v-if="activeTab === 'draft'" class="batch-btn" :disabled="batchLoading" @click="batchAction('publish')">发布</button>
          <button v-if="activeTab === 'published'" class="batch-btn" :disabled="batchLoading" @click="batchAction('draft')">转草稿</button>
          <button class="batch-btn danger" :disabled="batchLoading" @click="batchAction('delete')">删除</button>
        </div>
        <button class="batch-cancel" @click="toggleBatchMode">取消</button>
      </div>
    </Transition>

    <!-- 隐藏信息 & 申诉 Dialog -->
    <el-dialog v-model="hideInfoVisible" title="博文隐藏详情" width="460px" :close-on-click-modal="true">
      <div v-if="targetPost" class="hide-info-body">
        <p class="hide-post-title">「{{ targetPost.title }}」</p>

        <div class="hide-reason-block">
          <div class="info-label">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="#ef4444" stroke-width="1.5"><circle cx="8" cy="8" r="6"/><path d="M8 5v3M8 10.5v.5"/></svg>
            管理员隐藏原因
          </div>
          <p class="reason-text">{{ targetPost.hide_reason || '违反社区规范' }}</p>
        </div>

        <!-- 审核中状态 -->
        <div v-if="targetPost.review_status === 'pending'" class="review-status pending">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/><path d="M8 4v4l2 2"/></svg>
          申诉已提交，等待管理员审核
        </div>

        <!-- 申诉被拒绝 -->
        <div v-else-if="targetPost.review_status === 'rejected'" class="review-status rejected">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/><path d="M5 5l6 6M11 5l-6 6"/></svg>
          申诉被拒绝：{{ targetPost.hide_reason || '请查看原因' }}
        </div>

        <!-- 申诉表单 -->
        <template v-if="targetPost.review_status !== 'pending'">
          <div class="appeal-section">
            <div class="info-label">
              {{ targetPost.review_status === 'rejected' ? '重新申诉' : '提交申诉' }}
            </div>
            <el-input
              v-model="appealReason"
              type="textarea"
              :rows="3"
              placeholder="请说明申诉理由，例如：内容符合社区规范，希望重新审核..."
              maxlength="500"
              show-word-limit
              resize="none"
            />
            <el-button
              type="primary"
              size="small"
              :loading="appealing"
              :disabled="!appealReason.trim()"
              @click="submitAppeal"
            >提交申诉</el-button>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { postsApi } from '@/api/modules/posts'
import type { Post } from '@/types/models'
import { formatDate } from '@/utils/format'

const router = useRouter()

const posts = ref<Post[]>([])
const loading = ref(false)
const activeTab = ref<'published' | 'draft'>('published')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const hideInfoVisible = ref(false)
const targetPost = ref<Post | null>(null)
const appealReason = ref('')
const appealing = ref(false)

// 批量操作状态
const batchMode = ref(false)
const selectedIds = ref<number[]>([])
const batchLoading = ref(false)

const statusTabs = [
  { value: 'published' as const, label: '已发布' },
  { value: 'draft' as const, label: '草稿箱' },
]

async function loadPosts() {
  loading.value = true
  try {
    const res = await postsApi.getMyPosts({
      status: activeTab.value,
      page: page.value,
      page_size: pageSize
    })
    if (res.success && res.data) {
      posts.value = res.data.items
      total.value = res.data.total
    }
  } catch { /* 静默 */ } finally {
    loading.value = false
  }
}

function switchTab(tab: 'published' | 'draft') {
  activeTab.value = tab
  page.value = 1
  selectedIds.value = []
  loadPosts()
}

// 批量操作
function toggleBatchMode() {
  batchMode.value = !batchMode.value
  selectedIds.value = []
}
function toggleSelect(id: number) {
  const i = selectedIds.value.indexOf(id)
  if (i === -1) selectedIds.value.push(id)
  else selectedIds.value.splice(i, 1)
}
function selectAll() {
  if (selectedIds.value.length === posts.value.length) selectedIds.value = []
  else selectedIds.value = posts.value.map(p => p.id)
}
async function batchAction(action: 'publish' | 'draft' | 'delete') {
  const ids = [...selectedIds.value]
  if (!ids.length) return
  const label = action === 'publish' ? '发布' : action === 'draft' ? '转为草稿' : '删除'
  try {
    await ElMessageBox.confirm(
      `确认${label} ${ids.length} 篇博文？${action === 'delete' ? '此操作不可撤销。' : ''}`,
      '批量操作',
      { confirmButtonText: label, cancelButtonText: '取消', type: action === 'delete' ? 'warning' : 'info' }
    )
  } catch { return }
  batchLoading.value = true
  try {
    const calls = ids.map(id =>
      action === 'publish' ? postsApi.publish(id)
      : action === 'draft'  ? postsApi.update(id, { status: 'draft' } as Partial<Post>)
      : postsApi.delete(id)
    )
    const results = await Promise.allSettled(calls)
    const failed = results.filter(r => r.status === 'rejected').length
    if (failed) ElMessage.warning(`${ids.length - failed} 篇成功，${failed} 篇失败`)
    else ElMessage.success(`${label}成功`)
    selectedIds.value = []
    batchMode.value = false
    loadPosts()
  } finally {
    batchLoading.value = false
  }
}

function openHideInfo(post: Post) {
  targetPost.value = post
  appealReason.value = ''
  hideInfoVisible.value = true
}

async function submitAppeal() {
  if (!targetPost.value || !appealReason.value.trim()) return
  appealing.value = true
  try {
    const res = await postsApi.appeal(targetPost.value.id, appealReason.value.trim())
    if (res.success) {
      ElMessage.success('申诉已提交，等待管理员审核')
      const p = posts.value.find(p => p.id === targetPost.value!.id)
      if (p) (p as any).review_status = 'pending'
      targetPost.value = { ...targetPost.value, review_status: 'pending' } as any
      appealReason.value = ''
    }
  } catch {
    ElMessage.error('申诉提交失败')
  } finally {
    appealing.value = false
  }
}

async function handleDelete(post: Post) {
  await ElMessageBox.confirm(`确认删除《${post.title}》？此操作不可撤销。`, '删除博文', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
    confirmButtonClass: 'el-button--danger'
  }).catch(() => { throw new Error('cancel') })

  try {
    const res = await postsApi.delete(post.id)
    if (res.success) {
      ElMessage.success('删除成功')
      loadPosts()
    }
  } catch (e: any) {
    if (e?.message !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(loadPosts)
onActivated(loadPosts)
</script>

<style scoped lang="scss">
.posts-tab {
  padding: $spacing-lg 0;
  min-height: calc(100vh - 52px);
  position: relative;
}

.posts-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: $spacing-lg;
}

.status-tabs {
  display: flex;
  align-items: center;
}

.status-tab {
  padding: $spacing-sm $spacing-lg;
  font-size: $font-sm;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color $transition-fast, border-color $transition-fast;

  &:hover { color: var(--color-text-primary); }
  &.active { color: $color-primary; border-bottom-color: $color-primary; }
}

.header-right {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: $spacing-xs;
}

.icon-action-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: $radius-md;
  transition: background $transition-fast, color $transition-fast, border-color $transition-fast;
  flex-shrink: 0;

  &:hover {
    border-color: $color-primary;
    color: $color-primary;
  }
  &.active {
    border-color: rgba(90, 103, 216, 0.4);
    background: rgba(90, 103, 216, 0.06);
    color: $color-primary;
  }
  &.primary {
    background: $color-primary;
    border-color: $color-primary;
    color: #fff;
    &:hover { background: rgba(90, 103, 216, 0.82); }
  }

  // tooltip
  &[data-tip]::after {
    content: attr(data-tip);
    position: absolute;
    top: calc(100% + 6px);
    left: 50%;
    translate: -50% 0;
    z-index: 9999;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11.5px;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transform: translateY(-4px) scale(0.96);
    transform-origin: top center;
    transition: opacity 0.12s ease, transform 0.12s ease;
    transition-delay: 0.06s;
    background: rgba(22, 24, 30, 0.82);
    color: rgba(255, 255, 255, 0.92);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.07);
  }
  &[data-tip]:hover::after { opacity: 1; transform: translateY(0) scale(1); }
}

.posts-list { min-height: 200px; }

.post-row {
  display: flex;
  align-items: center;
  padding: 12px $spacing-xs;
  border-bottom: 1px solid var(--color-border-subtle);
  gap: $spacing-sm;
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background $transition-fast;

  &:last-child { border-bottom: none; }
  &:hover { background: var(--color-surface-hover); }
  &.selected { background: rgba(90, 103, 216, 0.05); }
}

.row-check {
  flex-shrink: 0;
  width: 15px;
  height: 15px;
  cursor: pointer;
  accent-color: $color-primary;
}

// 左侧：标题 + 状态标签，flex:1 截断
.post-left {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  overflow: hidden;
}

.post-title {
  font-size: $font-sm;
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 1;
  min-width: 0;

  .post-row:hover & { color: $color-primary; }
}

.status-badge {
  font-size: 10px;
  font-weight: 600;
  font-family: $font-mono;
  letter-spacing: 0.03em;
  padding: 1px 6px;
  border-radius: $radius-sm;
  flex-shrink: 0;
  white-space: nowrap;

  &.published { background: rgba(16, 185, 129, 0.08); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); }
  &.draft     { background: rgba(107, 114, 128, 0.08); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.18); }
  &.hidden    { background: rgba(239, 68, 68, 0.08);  color: #ef4444;  border: 1px solid rgba(239, 68, 68, 0.2); }
}

.hide-info-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: rgba(239, 68, 68, 0.1);
  border: none;
  border-radius: 50%;
  color: #ef4444;
  cursor: pointer;
  flex-shrink: 0;
  padding: 0;
  transition: background $transition-fast;

  &:hover { background: rgba(239, 68, 68, 0.2); }
}

.post-meta {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: 11px;
  color: var(--color-text-muted);
}

.meta-date { color: var(--color-text-secondary); }
.meta-sep { color: var(--color-border); }
.meta-stat { display: flex; align-items: center; gap: 3px; }

.post-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity $transition-fast;

  .post-row:hover & { opacity: 1; }
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background $transition-fast, color $transition-fast;

  &:hover { background: var(--color-surface-hover); color: var(--color-text-primary); }
  &.danger:hover { background: rgba(239, 68, 68, 0.08); color: #ef4444; }
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: $spacing-lg;
}

// 批量操作栏
.batch-bar {
  position: sticky;
  bottom: $spacing-md;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-top: $spacing-md;
  padding: 10px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: $radius-lg;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  z-index: 10;
}

.batch-count {
  font-size: $font-sm;
  color: var(--color-text-secondary);
  flex-shrink: 0;
  b { color: $color-primary; font-weight: 600; }
}

.batch-sel-all {
  font-size: $font-xs;
  color: var(--color-text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
  flex-shrink: 0;
  &:hover { color: $color-primary; }
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  margin-left: auto;
}

.batch-btn {
  padding: 4px 12px;
  font-size: $font-sm;
  font-weight: 500;
  background: rgba(90, 103, 216, 0.08);
  color: $color-primary;
  border: 1px solid rgba(90, 103, 216, 0.22);
  border-radius: $radius-md;
  cursor: pointer;
  transition: background $transition-fast;
  &:hover:not(:disabled) { background: rgba(90, 103, 216, 0.15); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
  &.danger {
    background: rgba(239, 68, 68, 0.07);
    color: #ef4444;
    border-color: rgba(239, 68, 68, 0.2);
    &:hover:not(:disabled) { background: rgba(239, 68, 68, 0.14); }
  }
}

.batch-cancel {
  font-size: $font-sm;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: $radius-sm;
  flex-shrink: 0;
  &:hover { color: var(--color-text-secondary); background: var(--color-surface-hover); }
}

.batch-bar-enter-active, .batch-bar-leave-active { transition: opacity $transition-fast, transform $transition-fast; }
.batch-bar-enter-from, .batch-bar-leave-to { opacity: 0; transform: translateY(8px); }

// 隐藏信息弹窗
.hide-info-body {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.hide-post-title {
  font-size: $font-sm;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.hide-reason-block {
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: $radius-md;
  padding: $spacing-sm $spacing-md;
}

.info-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: $font-xs;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: $spacing-xs;
}

.reason-text {
  font-size: $font-sm;
  color: var(--color-text-primary);
  margin: 0;
  line-height: 1.6;
}

.review-status {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-xs $spacing-md;
  border-radius: $radius-md;
  font-size: $font-sm;

  &.pending  { background: rgba(234, 179, 8, 0.08); color: #b45309; border: 1px solid rgba(234, 179, 8, 0.25); }
  &.rejected { background: rgba(239, 68, 68, 0.06); color: #b91c1c; border: 1px solid rgba(239, 68, 68, 0.2); }
}

.appeal-section {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  padding-top: $spacing-sm;
  border-top: 1px solid var(--color-border);
}
</style>
