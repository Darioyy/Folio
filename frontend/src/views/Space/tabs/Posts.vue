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
      <el-tooltip content="写新博文" placement="top">
        <button class="new-post-btn" @click="router.push('/post/create')">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 2l3 3-9 9H2v-3L11 2z"/>
          </svg>
          写博文
        </button>
      </el-tooltip>
    </div>

    <div v-loading="loading" class="posts-list">
      <el-empty v-if="!loading && posts.length === 0" description="暂无博文" :image-size="60" />

      <div v-for="post in posts" :key="post.id" class="post-row" @click="router.push('/post/' + post.id)">
        <div class="post-main">
          <div class="post-title-row">
            <span class="post-title">{{ post.title }}</span>
            <template v-if="post.is_hidden">
              <el-tag type="danger" size="small" class="status-tag">已隐藏</el-tag>
              <el-tooltip content="查看隐藏原因" placement="top">
                <button class="hide-info-btn" @click.stop="openHideInfo(post)">
                  <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="8" cy="8" r="6"/>
                    <path d="M8 7v4M8 5.5v.5"/>
                  </svg>
                </button>
              </el-tooltip>
            </template>
            <el-tag v-else :type="post.status === 'published' ? 'success' : 'info'" size="small" class="status-tag">
              {{ post.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </div>
          <div class="post-meta">
            <span class="meta-date">{{ formatDate(post.published_at || post.created_at) }}</span>
            <span class="meta-sep">·</span>
            <span class="meta-stat">
              <svg viewBox="0 0 16 16" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 14s-6-3.8-6-8a4 4 0 018 0 4 4 0 018 0c0 4.2-6 8-6 8z"/></svg>
              {{ post.like_count }}
            </span>
            <span class="meta-stat">
              <svg viewBox="0 0 16 16" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H2a1 1 0 00-1 1v9a1 1 0 001 1h3l3 2 3-2h3a1 1 0 001-1V3a1 1 0 00-1-1z"/></svg>
              {{ post.comment_count }}
            </span>
          </div>
        </div>
        <div class="post-actions" @click.stop>
          <el-tooltip content="编辑" placement="top">
            <button class="action-btn" @click="router.push('/post/' + post.id + '/edit')">
              <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 2l3 3-9 9H2v-3L11 2z"/></svg>
            </button>
          </el-tooltip>
          <el-tooltip content="删除" placement="top">
            <button class="action-btn danger" @click="handleDelete(post)">
              <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h12M5 4V2h6v2M6 7v5M10 7v5M3 4l1 10h8l1-10"/></svg>
            </button>
          </el-tooltip>
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
  loadPosts()
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
      // 更新本地状态
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
}

.posts-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-light);
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
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color $transition-fast, border-color $transition-fast;

  &:hover { color: var(--el-text-color-primary); }
  &.active { color: $color-primary; border-bottom-color: $color-primary; }
}

.new-post-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 14px;
  font-size: $font-sm;
  font-weight: 500;
  color: $color-primary;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.22);
  border-radius: $radius-md;
  cursor: pointer;
  transition: background $transition-fast;
  flex-shrink: 0;
  margin-bottom: $spacing-xs;

  &:hover { background: rgba(99, 102, 241, 0.14); border-color: $color-primary; }
}

.posts-list { min-height: 200px; }

.post-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-xs;
  border-bottom: 1px solid var(--el-border-color-lighter);
  gap: $spacing-sm;
  cursor: pointer;
  border-radius: $radius-md;
  transition: background $transition-fast;

  &:last-child { border-bottom: none; }
  &:hover { background: var(--el-fill-color-light); }
}

.post-main { flex: 1; min-width: 0; }

.post-title-row {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: 4px;
}

.post-title {
  font-size: $font-sm;
  font-weight: 500;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;

  .post-row:hover & { color: $color-primary; }
}

.status-tag { flex-shrink: 0; }

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
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.meta-date { color: var(--el-text-color-secondary); }
.meta-sep { color: var(--el-border-color); }
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
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background $transition-fast, color $transition-fast;

  &:hover { background: var(--el-fill-color); color: var(--el-text-color-primary); }
  &.danger:hover { background: rgba(239, 68, 68, 0.1); color: var(--el-color-danger); }
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: $spacing-lg;
}

// 隐藏信息弹窗
.hide-info-body {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.hide-post-title {
  font-size: $font-sm;
  font-weight: 600;
  color: var(--el-text-color-primary);
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
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: $spacing-xs;
}

.reason-text {
  font-size: $font-sm;
  color: var(--el-text-color-regular);
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

  &.pending {
    background: rgba(234, 179, 8, 0.08);
    color: #b45309;
    border: 1px solid rgba(234, 179, 8, 0.25);
  }

  &.rejected {
    background: rgba(239, 68, 68, 0.06);
    color: #b91c1c;
    border: 1px solid rgba(239, 68, 68, 0.2);
  }
}

.appeal-section {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  padding-top: $spacing-sm;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
