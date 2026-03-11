<template>
  <div class="file-detail-page">
    <AppHeader />

    <div v-if="loading" class="state-wrap">
      <el-skeleton :rows="8" animated style="max-width: 960px; margin: 40px auto; padding: 0 24px" />
    </div>

    <div v-else-if="errorCode" class="state-wrap">
      <el-result
        :icon="errorCode === 403 ? 'warning' : 'error'"
        :title="errorCode === 403 ? '无权访问' : '文件不存在'"
        :sub-title="errorCode === 403 ? '该文件为私密文件，仅所有者可查看' : '文件可能已被删除或链接有误'"
      >
        <template #extra>
          <el-button type="primary" @click="router.back()">返回</el-button>
        </template>
      </el-result>
    </div>

    <div v-else-if="file" class="detail-container">
      <!-- 预览区 -->
      <div class="preview-section">
        <img
          v-if="file.file_category === 'image'"
          :src="viewUrl"
          :alt="file.title"
          class="preview-image"
        />
        <video
          v-else-if="file.file_category === 'video'"
          :src="viewUrl"
          controls
          class="preview-video"
        />
        <div v-else class="preview-download">
          <FileTypeIcon :mime-type="file.mime_type" :file-name="file.file_name" size="lg" />
          <p class="download-filename">{{ file.file_name }}</p>
          <a :href="downloadUrl" :download="file.file_name">
            <el-button type="primary" size="large">下载文件</el-button>
          </a>
        </div>
      </div>

      <!-- 文件信息 -->
      <div class="info-section">
        <h1 class="file-title">{{ file.title }}</h1>

        <div class="file-meta">
          <div class="meta-author">
            <el-avatar :src="authorAvatarUrl" :size="28" class="author-avatar">
              {{ authorInitial }}
            </el-avatar>
            <router-link
              v-if="file.username"
              :to="`/u/${file.username}`"
              class="author-name"
            >{{ file.nickname || file.username }}</router-link>
          </div>
          <span class="meta-sep">·</span>
          <span class="meta-item">{{ formatDate(file.created_at, 'YYYY-MM-DD') }}</span>
          <span class="meta-sep">·</span>
          <span class="meta-item">{{ formatFileSize(file.file_size) }}</span>
          <span class="meta-sep">·</span>
          <span class="meta-item">{{ file.mime_type || file.file_category }}</span>
        </div>

        <!-- 点赞 / 收藏按钮 -->
        <div class="interact-btns">
          <button
            :class="['interact-btn', { active: liked }]"
            :disabled="interactLoading"
            @click="handleLike"
            :title="liked ? '取消点赞' : '点赞'"
          >
            <svg v-if="liked" viewBox="0 0 16 16" width="15" height="15" fill="currentColor">
              <path d="M8 14s-6-3.9-6-8a4 4 0 018 0 4 4 0 018 0c0 4.1-6 8-6 8z"/>
            </svg>
            <svg v-else viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M8 14s-6-3.9-6-8a4 4 0 018 0 4 4 0 018 0c0 4.1-6 8-6 8z"/>
            </svg>
            <span class="interact-count">{{ likeCount }}</span>
          </button>
          <button
            :class="['interact-btn', { active: collected }]"
            :disabled="interactLoading"
            @click="handleCollect"
            :title="collected ? '取消收藏' : '收藏'"
          >
            <svg v-if="collected" viewBox="0 0 16 16" width="15" height="15" fill="currentColor">
              <path d="M8 1l1.85 3.75 4.15.6-3 2.93.71 4.13L8 10.4l-3.71 1.95.71-4.13-3-2.93 4.15-.6z"/>
            </svg>
            <svg v-else viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M8 1l1.85 3.75 4.15.6-3 2.93.71 4.13L8 10.4l-3.71 1.95.71-4.13-3-2.93 4.15-.6z"/>
            </svg>
            <span class="interact-count">{{ collectCount }}</span>
          </button>
        </div>

        <p v-if="file.description" class="file-description">{{ file.description }}</p>
      </div>

      <!-- 评论区 -->
      <div class="comments-section">
        <h3 class="comments-title">评论 <span class="comments-count">{{ commentTotal }}</span></h3>

        <!-- 评论输入框 -->
        <template v-if="userStore.isLoggedIn">
          <div class="comment-input-wrap">
            <el-input
              v-model="commentInput"
              type="textarea"
              :rows="2"
              placeholder="写下你的评论..."
              :maxlength="500"
              show-word-limit
              resize="none"
            />
            <div class="comment-input-actions">
              <el-button
                type="primary"
                size="small"
                :disabled="!commentInput.trim()"
                :loading="commentSubmitting"
                @click="submitComment(null)"
              >发表</el-button>
            </div>
          </div>
        </template>
        <div v-else class="comment-login-tip">
          <el-link type="primary" @click="router.push({ name: 'Login', query: { redirect: route.fullPath } })">
            登录后发表评论
          </el-link>
        </div>

        <!-- 评论列表 -->
        <div v-if="commentsLoading" class="comments-loading">
          <el-skeleton :rows="3" animated />
        </div>
        <div v-else-if="comments.length > 0" class="comments-list">
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-header">
              <el-avatar :size="32" :src="getCommentAvatarUrl(comment)" class="comment-avatar">
                {{ (comment.nickname || comment.username || '?')[0] }}
              </el-avatar>
              <div class="comment-meta">
                <span class="comment-author">{{ comment.nickname || comment.username }}</span>
                <span class="comment-time">{{ fromNow(comment.created_at) }}</span>
              </div>
              <button
                v-if="canDeleteComment(comment)"
                class="comment-delete-btn"
                @click="deleteComment(comment.id)"
                title="删除"
              >×</button>
            </div>
            <p class="comment-content">{{ comment.content }}</p>

            <!-- 回复按钮 -->
            <div class="comment-actions">
              <button
                v-if="userStore.isLoggedIn"
                class="reply-btn"
                @click="toggleReplyInput(comment.id)"
              >回复</button>
            </div>

            <!-- 回复输入框 -->
            <div v-if="replyingTo === comment.id" class="reply-input-wrap">
              <el-input
                v-model="replyInput"
                type="textarea"
                :rows="2"
                :placeholder="`回复 @${comment.nickname || comment.username}...`"
                :maxlength="500"
                show-word-limit
                resize="none"
              />
              <div class="reply-input-actions">
                <el-button size="small" @click="replyingTo = null">取消</el-button>
                <el-button
                  type="primary"
                  size="small"
                  :disabled="!replyInput.trim()"
                  :loading="commentSubmitting"
                  @click="submitComment(comment.id)"
                >回复</el-button>
              </div>
            </div>

            <!-- 二级回复 -->
            <div v-if="comment.replies && comment.replies.length > 0" class="replies-list">
              <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                <div class="comment-header">
                  <el-avatar :size="24" :src="getCommentAvatarUrl(reply)" class="comment-avatar">
                    {{ (reply.nickname || reply.username || '?')[0] }}
                  </el-avatar>
                  <div class="comment-meta">
                    <span class="comment-author">{{ reply.nickname || reply.username }}</span>
                    <span class="comment-time">{{ fromNow(reply.created_at) }}</span>
                  </div>
                  <button
                    v-if="canDeleteComment(reply)"
                    class="comment-delete-btn"
                    @click="deleteComment(reply.id)"
                    title="删除"
                  >×</button>
                </div>
                <p class="comment-content">{{ reply.content }}</p>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else-if="!commentsLoading" description="暂无评论" :image-size="80" />

        <!-- 加载更多 -->
        <div v-if="commentHasMore" class="load-more">
          <el-button @click="loadMoreComments" :loading="commentsLoadingMore" size="small">加载更多评论</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/common/AppHeader.vue'
import FileTypeIcon from '@/components/business/FileTypeIcon.vue'
import { filesApi } from '@/api/modules/files'
import { interactionsApi } from '@/api/modules/interactions'
import { get, post, del } from '@/api/request'
import { useUserStore } from '@/stores/user'
import type { FileItem, Comment } from '@/types/models'
import { formatDate, formatFileSize, fromNow } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const file = ref<FileItem | null>(null)
const loading = ref(true)
const errorCode = ref<number | null>(null)

// 互动状态
const liked = ref(false)
const collected = ref(false)
const likeCount = ref(0)
const collectCount = ref(0)
const interactLoading = ref(false)

// 评论
const comments = ref<Comment[]>([])
const commentsLoading = ref(false)
const commentsLoadingMore = ref(false)
const commentTotal = ref(0)
const commentPage = ref(1)
const commentInput = ref('')
const replyInput = ref('')
const replyingTo = ref<number | null>(null)
const commentSubmitting = ref(false)

const fileId = computed(() => Number(route.params.id))
const commentHasMore = computed(() => comments.value.length < commentTotal.value)

const viewUrl = computed(() => {
  if (!file.value) return ''
  return filesApi.getViewUrl(file.value.id)
})

const downloadUrl = computed(() => {
  if (!file.value) return ''
  return filesApi.getDownloadUrl(file.value.id)
})

const authorAvatarUrl = computed(() => {
  if (!file.value?.username) return undefined
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/users/username/${file.value.username}/avatar/view`
})

const authorInitial = computed(() => {
  const f = file.value
  return f?.nickname?.[0] || f?.username?.[0] || '?'
})

function getCommentAvatarUrl(comment: Comment) {
  if (!comment.username) return undefined
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/users/username/${comment.username}/avatar/view`
}

function canDeleteComment(comment: Comment) {
  if (!userStore.isLoggedIn) return false
  const u = userStore.currentUser
  if (!u) return false
  return u.id === comment.user_id || u.is_admin === 1 || u.is_root === 1
}

async function loadFile() {
  loading.value = true
  errorCode.value = null
  try {
    const res = await filesApi.getDetail(fileId.value)
    file.value = res.data
    likeCount.value = res.data.like_count || 0
    collectCount.value = res.data.collect_count || 0
    if (file.value?.title) {
      document.title = `${file.value.title} - VaultShare`
    }
    // 查询互动状态
    if (userStore.isLoggedIn) {
      try {
        const statusRes = await interactionsApi.batchStatus([fileId.value])
        const s = statusRes.data[fileId.value]
        if (s) {
          liked.value = s.liked
          collected.value = s.collected
        }
      } catch { /* ignore */ }
    }
  } catch (e: any) {
    errorCode.value = e.response?.status || 404
  } finally {
    loading.value = false
  }
}

async function loadComments(reset = true) {
  if (reset) {
    commentsLoading.value = true
    commentPage.value = 1
  } else {
    commentsLoadingMore.value = true
    commentPage.value++
  }
  try {
    const res = await get(`/files/${fileId.value}/comments`, { page: commentPage.value, page_size: 20 })
    const data = res.data as any
    const items: Comment[] = data?.items || []
    commentTotal.value = data?.pagination?.total || 0
    reset ? (comments.value = items) : comments.value.push(...items)
  } catch { /* ignore */ } finally {
    commentsLoading.value = false
    commentsLoadingMore.value = false
  }
}

function loadMoreComments() {
  loadComments(false)
}

async function handleLike() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  interactLoading.value = true
  try {
    const res = await interactionsApi.toggleLike(fileId.value)
    liked.value = res.data.liked
    likeCount.value = res.data.like_count
  } catch { /* ignore */ } finally {
    interactLoading.value = false
  }
}

async function handleCollect() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  interactLoading.value = true
  try {
    const res = await interactionsApi.toggleCollect(fileId.value)
    collected.value = res.data.collected
    collectCount.value = res.data.collect_count
  } catch { /* ignore */ } finally {
    interactLoading.value = false
  }
}

function toggleReplyInput(commentId: number) {
  replyingTo.value = replyingTo.value === commentId ? null : commentId
  replyInput.value = ''
}

async function submitComment(parentId: number | null) {
  const content = parentId === null ? commentInput.value.trim() : replyInput.value.trim()
  if (!content) return
  commentSubmitting.value = true
  try {
    await post(`/files/${fileId.value}/comments`, { content, parent_id: parentId })
    if (parentId === null) {
      commentInput.value = ''
    } else {
      replyInput.value = ''
      replyingTo.value = null
    }
    ElMessage.success('评论成功')
    await loadComments(true)
  } catch { /* handled by interceptor */ } finally {
    commentSubmitting.value = false
  }
}

async function deleteComment(commentId: number) {
  try {
    await del(`/comments/${commentId}`)
    ElMessage.success('删除成功')
    await loadComments(true)
  } catch { /* handled */ }
}

onMounted(() => {
  loadFile()
  loadComments()
})
</script>

<style scoped lang="scss">
.file-detail-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.state-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-xl;
}

.detail-container {
  max-width: 960px;
  margin: 0 auto;
  padding: $spacing-lg $spacing-md;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
}

// 预览区
.preview-section {
  background: var(--el-bg-color);
  border-radius: $radius-xl;
  overflow: hidden;
  box-shadow: $shadow-md;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.preview-image {
  width: 100%;
  max-height: 600px;
  object-fit: contain;
  display: block;
}

.preview-video {
  width: 100%;
  max-height: 540px;
  display: block;
  background: #000;
}

.preview-download {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-2xl;

  .download-filename {
    font-size: $font-sm;
    color: var(--el-text-color-secondary);
    word-break: break-all;
    text-align: center;
  }
}

// 文件信息
.info-section {
  background: var(--el-bg-color);
  border-radius: $radius-xl;
  padding: $spacing-lg;
  box-shadow: $shadow-md;
}

.file-title {
  font-size: $font-2xl;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 $spacing-md;
  line-height: 1.3;
}

.file-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: $spacing-xs;
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
}

.meta-author {
  display: flex;
  align-items: center;
  gap: 6px;
}

.author-avatar {
  font-size: 12px;
  background: linear-gradient(135deg, $color-primary, $color-secondary);
  color: white;
  flex-shrink: 0;
}

.author-name {
  color: $color-primary;
  text-decoration: none;
  font-weight: 500;

  &:hover {
    text-decoration: underline;
  }
}

.meta-sep {
  color: var(--el-text-color-placeholder);
}

.meta-item {
  color: var(--el-text-color-secondary);
}

.file-description {
  margin: $spacing-md 0 0;
  font-size: $font-sm;
  color: var(--el-text-color-regular);
  line-height: 1.7;
  white-space: pre-wrap;
}

// 互动按钮
.interact-btns {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-top: $spacing-md;
  padding-top: $spacing-md;
  border-top: 1px solid var(--el-border-color-lighter);
}

.interact-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: $radius-full;
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  cursor: pointer;
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  transition: all $transition-fast;

  &:hover:not(:disabled) {
    border-color: $color-primary;
    color: $color-primary;
  }

  &.active {
    border-color: $color-primary;
    color: $color-primary;
    background: rgba(99, 102, 241, 0.06);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .interact-count {
    font-size: $font-xs;
  }
}

// 评论区
.comments-section {
  background: var(--el-bg-color);
  border-radius: $radius-xl;
  padding: $spacing-lg;
  box-shadow: $shadow-md;
}

.comments-title {
  font-size: $font-lg;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 $spacing-lg;

  .comments-count {
    font-size: $font-sm;
    color: var(--el-text-color-secondary);
    font-weight: 400;
    margin-left: 4px;
  }
}

.comment-input-wrap {
  margin-bottom: $spacing-lg;

  .comment-input-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: $spacing-sm;
  }
}

.comment-login-tip {
  margin-bottom: $spacing-lg;
  padding: $spacing-md;
  background: var(--el-fill-color-lighter);
  border-radius: $radius-lg;
  text-align: center;
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
}

.comments-loading {
  padding: $spacing-md 0;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.comment-item {
  padding-bottom: $spacing-md;
  border-bottom: 1px solid var(--el-border-color-lighter);

  &:last-child {
    border-bottom: none;
  }
}

.comment-header {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: $spacing-sm;
}

.comment-avatar {
  flex-shrink: 0;
  font-size: 12px;
  background: linear-gradient(135deg, $color-primary, $color-secondary);
  color: white;
}

.comment-meta {
  flex: 1;
  display: flex;
  align-items: baseline;
  gap: $spacing-sm;
}

.comment-author {
  font-size: $font-sm;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.comment-time {
  font-size: $font-xs;
  color: var(--el-text-color-placeholder);
}

.comment-delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--el-text-color-placeholder);
  font-size: 16px;
  padding: 0 4px;
  line-height: 1;
  transition: color $transition-fast;

  &:hover {
    color: var(--el-color-danger);
  }
}

.comment-content {
  margin: 0 0 $spacing-xs 40px;
  font-size: $font-sm;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-actions {
  margin-left: 40px;
  margin-bottom: $spacing-xs;
}

.reply-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  padding: 2px 6px;
  border-radius: $radius-sm;
  transition: color $transition-fast, background $transition-fast;

  &:hover {
    color: $color-primary;
    background: rgba(99, 102, 241, 0.08);
  }
}

.reply-input-wrap {
  margin-left: 40px;
  margin-top: $spacing-sm;

  .reply-input-actions {
    display: flex;
    justify-content: flex-end;
    gap: $spacing-sm;
    margin-top: $spacing-sm;
  }
}

.replies-list {
  margin-left: 40px;
  margin-top: $spacing-sm;
  padding: $spacing-sm;
  background: var(--el-fill-color-lighter);
  border-radius: $radius-lg;
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.reply-item {
  .comment-content {
    margin-left: 32px;
  }

  .comment-header {
    margin-bottom: 4px;
  }
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: $spacing-md;
}

// 响应式
@media (max-width: $breakpoint-md) {
  .detail-container {
    padding: $spacing-sm;
  }

  .file-title {
    font-size: $font-xl;
  }
}
</style>
