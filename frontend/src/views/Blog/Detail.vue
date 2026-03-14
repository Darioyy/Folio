<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DOMPurify from 'dompurify'
import { marked } from '@/utils/markdown'
import type { Post } from '@/types/models'
import { postsApi } from '@/api/modules/posts'
import { interactionsApi } from '@/api/modules/interactions'
import { useUserStore } from '@/stores/user'
import { fromNow, getFileUrl } from '@/utils/format'
import AttachmentCard from '@/components/business/AttachmentCard.vue'
import CommentSection from './components/CommentSection.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const postId = computed(() => Number(route.params.id))
const post = ref<Post | null>(null)
const loading = ref(true)

const markdownHtml = computed(() =>
  post.value?.content ? DOMPurify.sanitize(String(marked.parse(post.value.content))) : ''
)
const authorAvatarUrl = computed(() => {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return post.value?.author_name
    ? `${base}/users/username/${post.value.author_name}/avatar/view`
    : ''
})

const liked = ref(false)
const likeCount = ref(0)
const collected = ref(false)
const collectCount = ref(0)

// ── 三点菜单 ──────────────────────────────────────────
const moreOpen = ref(false)
const moreWrapRef = ref<HTMLElement | null>(null)
const isAuthor = computed(() => !!userStore.currentUser && userStore.currentUser.id === post.value?.author_id)
const isAdminOrRoot = computed(() => !!(userStore.currentUser?.is_admin || userStore.currentUser?.is_root))
// Admin 不能操作 Root 的博文；Root 无限制
const canHidePost = computed(() => {
  if (!isAdminOrRoot.value) return false
  if (userStore.isRoot) return true
  return !(post.value as any)?.author_is_root
})
// 作者/管理员/Root 可删除（管理员不能删 Root 的博文）
const canDeletePost = computed(() => {
  if (!userStore.isLoggedIn) return false
  if (isAuthor.value) return true
  if (!isAdminOrRoot.value) return false
  if (userStore.isRoot) return true
  return !(post.value as any)?.author_is_root
})

// ── 菜单项可见性 & 分隔线 ──────────────────────────────
const showEdit   = computed(() => isAuthor.value)
const showPin    = computed(() => userStore.isRoot)
const showHide   = computed(() => canHidePost.value)
// 举报：登录用户且非作者、非管理员（管理员用隐藏代替举报）
const showReport = computed(() => userStore.isLoggedIn && !isAuthor.value && !isAdminOrRoot.value)
const showDelete = computed(() => canDeletePost.value)

const hasG1 = computed(() => showEdit.value || showPin.value)
const hasG2 = computed(() => showHide.value)
const hasG3 = computed(() => showReport.value)
const hasG4 = computed(() => showDelete.value)

// 三点按钮仅在至少有一项可操作时显示
const showMoreMenu = computed(() => hasG1.value || hasG2.value || hasG3.value || hasG4.value)
// 组间分隔线
const sep1 = computed(() => hasG1.value && (hasG2.value || hasG3.value || hasG4.value))
const sep2 = computed(() => hasG2.value && (hasG3.value || hasG4.value))
const sep3 = computed(() => hasG3.value && hasG4.value)

// ── 举报 ──────────────────────────────────────────────
const reportDialogVisible = ref(false)
const reportReason = ref('')
const reportSaving = ref(false)

// ── 隐藏（管理员） ────────────────────────────────────
const hideDialogVisible = ref(false)
const hideReason = ref('')
const hideSaving = ref(false)

// ── 删除 ──────────────────────────────────────────────
const deleteLoading = ref(false)

async function init() {
  loading.value = true
  try {
    const res = await postsApi.getDetail(postId.value)
    if (!res.success || !res.data) return router.push('/blog')
    post.value = res.data
    if (res.data.is_hidden === 1) {
      const uid = userStore.currentUser?.id
      const isAuthorCheck = uid && uid === res.data.author_id
      const isAdmin = userStore.currentUser?.is_admin || userStore.currentUser?.is_root
      if (!isAuthorCheck && !isAdmin) { loading.value = false; return }
    }
    likeCount.value = res.data.like_count
    collectCount.value = res.data.collect_count
    const statusRes = await interactionsApi.getPostStatus(postId.value).catch(() => null)
    if (statusRes?.data) { liked.value = statusRes.data.liked; collected.value = statusRes.data.collected }
  } catch { router.push('/blog') } finally { loading.value = false }
}

async function toggleLike() {
  if (!userStore.isLoggedIn) return router.push('/login')
  const res = await interactionsApi.togglePostLike(postId.value).catch(() => null)
  if (res?.data) { liked.value = res.data.liked; likeCount.value = res.data.like_count }
}
async function toggleCollect() {
  if (!userStore.isLoggedIn) return router.push('/login')
  const res = await interactionsApi.togglePostCollect(postId.value).catch(() => null)
  if (res?.data) { collected.value = res.data.collected; collectCount.value = res.data.collect_count }
}

async function handlePin() {
  if (!post.value) return
  moreOpen.value = false
  const newPinned = !post.value.is_pinned
  try {
    const res = await postsApi.togglePin(post.value.id, newPinned)
    if (res.success) {
      post.value.is_pinned = res.data?.is_pinned
      ElMessage.success(newPinned ? '已置顶，已通知所有成员' : '已取消置顶')
    }
  } catch { /* 拦截器已处理 */ }
}

function openReport() {
  if (!userStore.isLoggedIn) return router.push('/login')
  moreOpen.value = false
  reportReason.value = ''
  reportDialogVisible.value = true
}
async function submitReport() {
  if (!reportReason.value.trim()) { ElMessage.warning('请填写举报原因'); return }
  reportSaving.value = true
  try {
    await postsApi.reportPost(postId.value, reportReason.value.trim())
    ElMessage.success('举报已提交，管理员将尽快处理')
    reportDialogVisible.value = false
  } catch { /* 拦截器已处理 */ } finally { reportSaving.value = false }
}

function openHide() {
  moreOpen.value = false
  hideReason.value = ''
  hideDialogVisible.value = true
}
async function submitHide() {
  const isHiding = !post.value?.is_hidden
  if (isHiding && !hideReason.value.trim()) { ElMessage.warning('请填写隐藏原因'); return }
  hideSaving.value = true
  try {
    await postsApi.setVisibility(postId.value, isHiding, isHiding ? hideReason.value.trim() : undefined)
    ElMessage.success(isHiding ? '博文已隐藏' : '已取消隐藏')
    hideDialogVisible.value = false
    await init()
  } catch { /* 拦截器已处理 */ } finally { hideSaving.value = false }
}

async function handleDelete() {
  moreOpen.value = false
  try {
    await ElMessageBox.confirm(
      `确定要永久删除「${post.value?.title}」吗？此操作不可恢复。`,
      '删除博文',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning', confirmButtonClass: 'el-button--danger' }
    )
  } catch { return }
  deleteLoading.value = true
  try {
    await postsApi.delete(postId.value)
    ElMessage.success('博文已删除')
    router.push('/blog')
  } catch { /* 拦截器已处理 */ } finally { deleteLoading.value = false }
}

function handleOutside(e: MouseEvent) {
  if (moreWrapRef.value && !moreWrapRef.value.contains(e.target as Node)) moreOpen.value = false
}

function goBack() {
  if (window.history.state.back) {
    router.back()
  } else {
    router.push('/blog')
  }
}

onMounted(() => { init(); document.addEventListener('click', handleOutside) })
onUnmounted(() => document.removeEventListener('click', handleOutside))
</script>

<template>
  <div class="detail-page">
    <button class="detail-back-btn" @click="goBack" title="返回发现">
      <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="10 3 5 8 10 13"/>
      </svg>
    </button>

    <div v-if="loading" class="loading-box" v-loading="true" />

    <div v-else-if="post?.is_hidden === 1" class="hidden-post-notice">
      <div class="notice-icon">
        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/>
          <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
          <line x1="1" y1="1" x2="23" y2="23"/>
        </svg>
      </div>
      <h3>此博文暂时无法查看</h3>
      <p>该内容因违反相关社区规范已被暂时隐藏，如有疑问请联系管理员。</p>
      <el-button @click="router.push('/blog')">返回发现</el-button>
    </div>

    <article v-else-if="post">
      <div v-if="post.cover_image_url" class="cover-wrap">
        <img :src="getFileUrl(post.cover_image_url)" :alt="post.title" class="cover-img" />
      </div>

      <div class="post-container">
        <header class="post-header">
          <span v-if="post.category_name" class="cat-badge">{{ post.category_name }}</span>

          <!-- 标题行 + 三点菜单 -->
          <div class="title-row">
            <h1 class="post-title">{{ post.title }}</h1>
            <div v-if="showMoreMenu" class="more-wrap" ref="moreWrapRef">
              <button class="more-btn" :class="{ active: moreOpen }" @click.stop="moreOpen = !moreOpen" title="更多操作">
                <svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor">
                  <circle cx="3" cy="8" r="1.3"/><circle cx="8" cy="8" r="1.3"/><circle cx="13" cy="8" r="1.3"/>
                </svg>
              </button>
              <Transition name="menu-pop">
                <div v-if="moreOpen" class="more-menu" @click.stop>

                  <!-- ① 编辑 / 置顶 — 作者与 Root 的内容管理 -->
                  <button v-if="showEdit" class="more-item"
                    @click="() => { moreOpen=false; router.push({ name:'PostEdit', params:{id:post!.id} }) }">
                    <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M11.5 2.5a1.414 1.414 0 0 1 2 2L5 13 2 14l1-3 8.5-8.5z"/>
                    </svg>
                    编辑
                  </button>
                  <button v-if="showPin" class="more-item pin-item" @click="handlePin">
                    <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M9.5 1.5L14.5 6.5L11 10L10 13L3 6L6 5Z"/><line x1="1.5" y1="14.5" x2="5.5" y2="10.5"/>
                    </svg>
                    {{ post.is_pinned ? '取消置顶' : '置顶' }}
                  </button>

                  <div v-if="sep1" class="more-sep" />

                  <!-- ② 隐藏 / 取消隐藏 — 管理员审核操作 -->
                  <button v-if="showHide" class="more-item hide-item" @click="openHide">
                    <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M13.5 13.5L2.5 2.5"/><path d="M6.3 3.2A6.6 6.6 0 018 3c4 0 6.5 5 6.5 5a13 13 0 01-2.1 2.8M4.6 4.6A13 13 0 001.5 8s2.5 5 6.5 5a6.5 6.5 0 003.4-1"/>
                      <circle cx="8" cy="8" r="2" stroke-dasharray="3 1.4"/>
                    </svg>
                    {{ post?.is_hidden ? '取消隐藏' : '隐藏博文' }}
                  </button>

                  <div v-if="sep2" class="more-sep" />

                  <!-- ③ 举报 — 普通用户对他人内容的反馈 -->
                  <button v-if="showReport" class="more-item report-item" @click="openReport">
                    <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M3 2h10l-3 5 3 5H3V2z"/>
                    </svg>
                    举报
                  </button>

                  <div v-if="sep3" class="more-sep" />

                  <!-- ④ 删除 — 不可逆操作，置于最末 -->
                  <button v-if="showDelete" class="more-item delete-item" :disabled="deleteLoading" @click="handleDelete">
                    <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="2 4 14 4"/><path d="M5 4V2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 .5.5V4"/><path d="M13 4l-.8 8.5a1 1 0 0 1-1 .9H4.8a1 1 0 0 1-1-.9L3 4"/>
                    </svg>
                    删除
                  </button>

                </div>
              </Transition>
            </div>
          </div>

          <div class="post-meta">
            <el-avatar :size="28" :src="authorAvatarUrl" class="meta-avatar">
              {{ (post.author_nickname || post.author_name || '?')[0].toUpperCase() }}
            </el-avatar>
            <span class="meta-author" @click="router.push('/u/' + post.author_name)">
              {{ post.author_nickname || post.author_name }}
            </span>
            <span v-if="post.is_pinned" class="pin-badge">置顶</span>
            <span class="meta-sep">·</span>
            <span>{{ fromNow(post.published_at || post.created_at) }}</span>
            <span class="meta-sep">·</span>
            <span class="meta-views"><el-icon><View /></el-icon> {{ post.view_count }}</span>
          </div>
        </header>

        <div class="post-content" v-html="markdownHtml" />

        <div v-if="post.attachments?.length" class="attachments-wrap">
          <h3 class="sub-title">附件</h3>
          <div class="attachments-list">
            <AttachmentCard v-for="att in post.attachments" :key="att.file_id" :attachment="att" :post-id="post.id" />
          </div>
        </div>

        <div class="interact-bar">
          <button class="interact-btn" :class="{ active: liked }" @click="toggleLike">
            <svg viewBox="0 0 24 24" width="18" height="18" :fill="liked ? '#ef4444' : 'none'" :stroke="liked ? '#ef4444' : 'currentColor'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            <span>{{ likeCount }}</span>
          </button>
          <button class="interact-btn" :class="{ active: collected }" @click="toggleCollect">
            <svg viewBox="0 0 24 24" width="18" height="18" :fill="collected ? '#f59e0b' : 'none'" :stroke="collected ? '#f59e0b' : 'currentColor'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            <span>{{ collectCount }}</span>
          </button>
        </div>

        <CommentSection :post-id="post.id" />
      </div>
    </article>

    <!-- 举报对话框 -->
    <el-dialog v-model="reportDialogVisible" title="举报博文" width="400px" :append-to-body="true">
      <p class="report-target">「{{ post?.title }}」</p>
      <el-input v-model="reportReason" type="textarea" :rows="4"
        placeholder="请描述举报原因（违规内容、虚假信息等）" maxlength="500" show-word-limit />
      <template #footer>
        <el-button @click="reportDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="reportSaving" @click="submitReport">提交举报</el-button>
      </template>
    </el-dialog>

    <!-- 隐藏博文对话框（管理员） -->
    <el-dialog v-model="hideDialogVisible" :title="post?.is_hidden ? '取消隐藏' : '隐藏博文'" width="400px" :append-to-body="true">
      <p class="report-target">「{{ post?.title }}」</p>
      <el-input v-if="!post?.is_hidden" v-model="hideReason" type="textarea" :rows="4"
        placeholder="请填写隐藏原因（必填，将通知作者）" maxlength="500" show-word-limit />
      <p v-else style="font-size:13px;color:var(--el-text-color-secondary);margin:0">确定要取消隐藏该博文吗？博文将重新公开。</p>
      <template #footer>
        <el-button @click="hideDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="hideSaving" @click="submitHide">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.detail-page { max-width: 860px; margin: 0 auto; padding-bottom: $spacing-2xl; }

.detail-back-btn {
  position: fixed;
  // 垂直：与博文标题齐平（header 52px + container padding-top 32px + title 行高一半 ≈ 94px）
  top: 94px;
  // 水平：与 header 中 Folio 品牌名对齐（header-inner: max-width 1200px + padding 32px）
  left: max(32px, calc(50vw - 568px));
  z-index: 40;
  width: 30px; height: 30px;
  border-radius: 50%;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0.75;
  transition: opacity 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  &:hover {
    opacity: 1;
    color: $color-primary;
    border-color: $color-primary;
    box-shadow: 0 2px 8px rgba(90,103,216,0.15);
  }
  @media (max-width: 999px) { display: none; }
}
.loading-box { height: 400px; }

.cover-wrap {
  width: 100%; max-height: 420px; overflow: hidden;
  .cover-img { width: 100%; height: 100%; object-fit: cover; display: block; }
}

.post-container { padding: $spacing-xl $spacing-lg; }

.post-header { margin-bottom: $spacing-xl; }

.cat-badge {
  display: inline-block; padding: 2px 10px; border-radius: $radius-full;
  font-size: $font-xs; font-weight: 500;
  background: rgba(90, 103, 216, 0.1); color: $color-primary; margin-bottom: $spacing-sm;
}

// 标题行
.title-row {
  display: flex; align-items: flex-start; gap: 8px; margin: 0 0 $spacing-md;
}
.post-title {
  flex: 1; font-size: 28px; font-weight: 700; line-height: 1.3;
  color: var(--el-text-color-primary); margin: 0;
}

// 三点菜单
.more-wrap { position: relative; flex-shrink: 0; margin-top: 6px; }
.more-btn {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border: none; background: transparent;
  border-radius: $radius-sm; color: var(--el-text-color-placeholder);
  cursor: pointer; transition: color $transition-fast, background $transition-fast;
  &:hover, &.active { color: var(--el-text-color-primary); background: var(--el-fill-color-light); }
}
.more-menu {
  position: absolute; top: calc(100% + 4px); right: 0;
  min-width: 124px; background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.09);
  padding: 4px; z-index: 50;
}
.more-sep { height: 1px; background: var(--el-border-color-lighter); margin: 4px 0; }
.more-item {
  display: flex; align-items: center; gap: 8px;
  width: 100%; padding: 7px 10px; border: none; background: transparent;
  border-radius: 5px; font-size: 13px; color: var(--el-text-color-primary);
  cursor: pointer; text-align: left; white-space: nowrap; font-family: inherit;
  transition: background $transition-fast;
  &:hover { background: var(--el-fill-color-light); }
  svg { flex-shrink: 0; color: var(--el-text-color-secondary); }
  &.pin-item    { color: $color-primary; svg { color: $color-primary; } &:hover { background: var(--color-primary-subtle); } }
  &.hide-item   { color: #d97706; svg { color: #d97706; } &:hover { background: rgba(217,119,6,0.06); } }
  &.report-item { color: #f97316; svg { color: #f97316; } &:hover { background: rgba(249,115,22,0.06); } }
  &.delete-item { color: #ef4444; svg { color: #ef4444; } &:hover { background: rgba(239,68,68,0.06); } &:disabled { opacity: 0.5; cursor: not-allowed; } }
}
.menu-pop-enter-active { transition: opacity 0.12s ease, transform 0.14s cubic-bezier(0.34,1.56,0.64,1); }
.menu-pop-leave-active { transition: opacity 0.08s ease; }
.menu-pop-enter-from { opacity: 0; transform: translateY(-4px) scale(0.96); }
.menu-pop-leave-to { opacity: 0; }

.post-meta {
  display: flex; align-items: center; gap: $spacing-xs;
  font-size: $font-sm; color: var(--el-text-color-secondary);
  .meta-avatar { flex-shrink: 0; }
  .meta-author { cursor: pointer; font-weight: 500; color: var(--el-text-color-primary); &:hover { color: $color-primary; } }
  .meta-sep { color: var(--el-text-color-placeholder); }
  .meta-views { display: flex; align-items: center; gap: 3px; margin-left: auto; }
}
.pin-badge {
  font-size: 10px; font-weight: 600; letter-spacing: 0.04em;
  padding: 1px 5px; border-radius: 3px;
  background: rgba(90,103,216,0.1); color: $color-primary; flex-shrink: 0;
}

.post-content {
  line-height: 1.8; font-size: 15px; color: var(--el-text-color-regular); margin-bottom: $spacing-2xl;
  :deep(h1), :deep(h2), :deep(h3), :deep(h4) { color: var(--el-text-color-primary); font-weight: 600; margin: 1.5em 0 0.5em; }
  :deep(h1) { font-size: 1.75em; }
  :deep(h2) { font-size: 1.4em; border-bottom: 1px solid var(--el-border-color-light); padding-bottom: 0.3em; }
  :deep(h3) { font-size: 1.2em; }
  :deep(p) { margin: 0.8em 0; }
  :deep(a) { color: $color-primary; text-decoration: none; &:hover { text-decoration: underline; } }
  :deep(code) { background: var(--el-fill-color); padding: 2px 6px; border-radius: $radius-sm; font-size: 0.9em; font-family: monospace; }
  :deep(pre) { border-radius: $radius-lg; overflow-x: auto; margin: 1em 0; code { background: none; padding: 0; font-size: 0.875em; line-height: 1.6; } }
  :deep(blockquote) { border-left: 4px solid $color-primary; margin: 1em 0; padding: $spacing-sm $spacing-md; background: var(--el-fill-color-light); color: var(--el-text-color-secondary); }
  :deep(ul), :deep(ol) { padding-left: 1.5em; margin: 0.8em 0; }
  :deep(img) { max-width: 100%; border-radius: $radius-lg; }
  :deep(hr) { border: none; border-top: 1px solid var(--el-border-color-light); margin: 1.5em 0; }
  :deep(table) { width: 100%; border-collapse: collapse; margin: 1em 0; }
  :deep(th), :deep(td) { border: 1px solid var(--el-border-color-light); padding: 8px 12px; }
  :deep(th) { background: var(--el-fill-color); font-weight: 600; }
}

.sub-title { font-size: $font-base; font-weight: 600; color: var(--el-text-color-primary); margin: 0 0 $spacing-md; }
.attachments-wrap { margin-bottom: $spacing-xl; }
.attachments-list { display: flex; flex-direction: column; gap: $spacing-sm; }

.interact-bar {
  display: flex; gap: $spacing-md; padding: $spacing-lg 0;
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
  margin-bottom: $spacing-xl;
}
.interact-btn {
  display: flex; align-items: center; gap: $spacing-xs;
  padding: 8px 20px; border-radius: $radius-full;
  border: 1px solid var(--el-border-color); background: transparent;
  color: var(--el-text-color-secondary); font-size: $font-sm;
  cursor: pointer; transition: all $transition-fast;
  &:hover { border-color: var(--el-border-color-dark); }
  &.active { border-color: transparent; background: transparent; }
}

// 举报对话框
.report-target { font-size: 13px; font-weight: 500; color: var(--el-text-color-primary); margin: 0 0 12px; }

@media (max-width: 560px) {
  .post-container { padding: $spacing-md; }
  .post-title { font-size: 22px; }
}

.hidden-post-notice {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 80px 24px; text-align: center; color: var(--el-text-color-secondary);
  .notice-icon { margin-bottom: 16px; opacity: 0.4; }
  h3 { font-size: 18px; font-weight: 600; color: var(--el-text-color-primary); margin: 0 0 8px; }
  p { margin: 0 0 24px; font-size: 14px; line-height: 1.6; max-width: 400px; }
}
</style>
