<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { View } from '@element-plus/icons-vue'
import DOMPurify from 'dompurify'
import { marked } from '@/utils/markdown'
import type { Post } from '@/types/models'
import { postsApi } from '@/api/modules/posts'
import { interactionsApi } from '@/api/modules/interactions'
import { filesApi } from '@/api/modules/files'
import { useUserStore } from '@/stores/user'
import { fromNow } from '@/utils/format'
import AttachmentCard from '@/components/business/AttachmentCard.vue'
import CommentSection from './components/CommentSection.vue'
import PostMoreMenu from './components/PostMoreMenu.vue'
import PostActionDialogs from './components/PostActionDialogs.vue'

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
const coverPreviewVisible = ref(false)
const reportDialogVisible = ref(false)
const hideDialogVisible = ref(false)

const coverImageSrc = computed(() =>
  post.value?.cover_image_id ? filesApi.getViewUrl(post.value.cover_image_id) : ''
)

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

function onPinUpdated(isPinned: boolean | undefined) {
  if (post.value) (post.value as any).is_pinned = isPinned
}

function goBack() {
  if (window.history.state.back) {
    router.back()
  } else {
    router.push('/blog')
  }
}

onMounted(() => init())
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
      <div v-if="post.cover_image_id" class="cover-wrap" @click="coverPreviewVisible = true" title="点击查看大图">
        <img :src="coverImageSrc" :alt="post.title" class="cover-img" />
      </div>

      <div class="post-container">
        <header class="post-header">
          <span v-if="post.category_name" class="cat-badge">{{ post.category_name }}</span>

          <div class="title-row">
            <h1 class="post-title">{{ post.title }}</h1>
            <PostMoreMenu
              :post="post"
              @pin-updated="onPinUpdated"
              @open-report="reportDialogVisible = true"
              @open-hide="hideDialogVisible = true"
            />
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

    <PostActionDialogs
      v-model:report-visible="reportDialogVisible"
      v-model:hide-visible="hideDialogVisible"
      :post-id="postId"
      :post="post"
      @hidden="init"
    />

    <!-- 封面大图遮罩 -->
    <Teleport to="body">
      <Transition name="overlay-fade">
        <div v-if="coverPreviewVisible" class="cover-overlay" @click="coverPreviewVisible = false">
          <img :src="coverImageSrc" class="cover-overlay-img" @click.stop />
          <button class="cover-overlay-close" @click="coverPreviewVisible = false">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style lang="scss" scoped>
.detail-page { max-width: 860px; margin: 0 auto; padding-bottom: $spacing-2xl; }

.detail-back-btn {
  position: fixed;
  top: 94px;
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
  width: 100%;
  overflow: hidden;
  cursor: pointer;
  line-height: 0;
  .cover-img {
    width: 100%;
    height: auto;
    max-height: 420px;
    object-fit: cover;
    display: block;
    transition: transform 0.3s ease;
  }
  &:hover .cover-img { transform: scale(1.015); }
}

.cover-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(0, 0, 0, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
}

.cover-overlay-img {
  max-width: 92vw;
  max-height: 92vh;
  object-fit: contain;
  border-radius: 4px;
  cursor: default;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
}

.cover-overlay-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
  &:hover { background: rgba(255, 255, 255, 0.28); }
}

.overlay-fade-enter-active, .overlay-fade-leave-active { transition: opacity 0.2s; }
.overlay-fade-enter-from, .overlay-fade-leave-to { opacity: 0; }

.post-container { padding: $spacing-xl $spacing-lg; }
.post-header { margin-bottom: $spacing-xl; }

.cat-badge {
  display: inline-block; padding: 2px 10px; border-radius: $radius-full;
  font-size: $font-xs; font-weight: 500;
  background: var(--color-primary-subtle); color: var(--color-primary); margin-bottom: $spacing-sm;
}

.title-row {
  display: flex; align-items: flex-start; gap: 8px; margin: 0 0 $spacing-md;
}
.post-title {
  flex: 1; font-size: 28px; font-weight: 700; line-height: 1.3;
  color: var(--el-text-color-primary); margin: 0;
}

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
  background: var(--color-primary-subtle); color: var(--color-primary); flex-shrink: 0;
}

.post-content {
  line-height: 1.8; font-size: 15px; color: var(--el-text-color-regular); margin-bottom: $spacing-2xl;
  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) { color: var(--el-text-color-primary); font-weight: 600; margin: 1.5em 0 0.5em; }
  :deep(h1) { font-size: 1.75em; }
  :deep(h2) { font-size: 1.4em; border-bottom: 1px solid var(--el-border-color-light); padding-bottom: 0.3em; }
  :deep(h3) { font-size: 1.2em; }
  :deep(h4) { font-size: 1.1em; }
  :deep(h5), :deep(h6) { font-size: 1em; }
  :deep(p) { margin: 0.8em 0; }
  :deep(a) { color: $color-primary; text-decoration: underline; text-decoration-color: transparent; transition: text-decoration-color .2s; &:hover { text-decoration-color: $color-primary; } }
  :deep(code) { background: var(--el-fill-color); border: 1px solid var(--el-border-color-light); padding: 1px 5px; border-radius: $radius-sm; font-size: 0.875em; font-family: 'Cascadia Code', 'Fira Code', ui-monospace, monospace; }
  :deep(pre) { background: var(--el-fill-color); border: 1px solid var(--el-border-color-light); border-radius: $radius-lg; padding: 16px 20px; overflow-x: auto; margin: 1em 0; code { background: none; border: none; padding: 0; font-size: 0.875em; line-height: 1.6; } }
  :deep(blockquote) { border-left: 3px solid $color-primary; margin: 1em 0; padding: 10px 16px; background: rgba(90,103,216,.05); color: var(--el-text-color-secondary); border-radius: 0 6px 6px 0; font-style: italic; }
  :deep(ul), :deep(ol) { padding-left: 1.5em; margin: 0.8em 0; }
  :deep(li) { margin: 0.3em 0; }
  :deep(input[type="checkbox"]) { margin-right: 5px; accent-color: $color-primary; vertical-align: middle; }
  :deep(li:has(input[type="checkbox"]:checked)) { text-decoration: line-through; opacity: .6; }
  :deep(img) { max-width: 100%; border-radius: $radius-lg; display: block; margin: 0.75em 0; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
  :deep(hr) { border: none; height: 1px; background: linear-gradient(90deg, transparent, var(--el-border-color), transparent); margin: 1.5em 0; }
  :deep(.md-table-wrap) { overflow-x: auto; margin: 1em 0; }
  :deep(table) { border-collapse: collapse; width: max-content; max-width: 100%; margin: 0; }
  :deep(th), :deep(td) { border: 1px solid var(--el-border-color-light); padding: 8px 12px; white-space: nowrap; }
  :deep(th) { background: var(--el-fill-color); font-weight: 600; }
  :deep(tr:nth-child(even) td) { background: var(--el-fill-color-lighter); }
  :deep(del) { text-decoration: line-through; opacity: 0.65; }
  :deep(mark) { background: rgba(255, 213, 0, 0.35); padding: 0 2px; border-radius: 2px; }
  :deep(strong) { font-weight: 600; }
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
