<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { View } from '@element-plus/icons-vue'
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
  post.value?.content ? String(marked.parse(post.value.content)) : ''
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

async function init() {
  loading.value = true
  try {
    const res = await postsApi.getDetail(postId.value)
    if (!res.success || !res.data) return router.push('/blog')
    post.value = res.data
    likeCount.value = res.data.like_count
    collectCount.value = res.data.collect_count
    const statusRes = await interactionsApi.getPostStatus(postId.value).catch(() => null)
    if (statusRes?.data) {
      liked.value = statusRes.data.liked
      collected.value = statusRes.data.collected
    }
  } catch {
    router.push('/blog')
  } finally {
    loading.value = false
  }
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

onMounted(init)
</script>

<template>
  <div class="detail-page">
    <div v-if="loading" class="loading-box" v-loading="true" />

    <article v-else-if="post">
      <div v-if="post.cover_image_url" class="cover-wrap">
        <img :src="getFileUrl(post.cover_image_url)" :alt="post.title" class="cover-img" />
      </div>

      <div class="post-container">
        <header class="post-header">
          <span v-if="post.category_name" class="cat-badge">{{ post.category_name }}</span>
          <h1 class="post-title">{{ post.title }}</h1>
          <div class="post-meta">
            <el-avatar :size="28" :src="authorAvatarUrl" class="meta-avatar">
              {{ (post.author_nickname || post.author_name || '?')[0].toUpperCase() }}
            </el-avatar>
            <span class="meta-author" @click="router.push('/u/' + post.author_name)">
              {{ post.author_nickname || post.author_name }}
            </span>
            <span class="meta-sep">·</span>
            <span>{{ fromNow(post.published_at || post.created_at) }}</span>
            <span class="meta-sep">·</span>
            <span class="meta-views">
              <el-icon><View /></el-icon> {{ post.view_count }}
            </span>
          </div>
        </header>

        <div class="post-content" v-html="markdownHtml" />

        <div v-if="post.attachments?.length" class="attachments-wrap">
          <h3 class="sub-title">附件</h3>
          <div class="attachments-list">
            <AttachmentCard
              v-for="att in post.attachments"
              :key="att.file_id"
              :attachment="att"
              :post-id="post.id"
            />
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
  </div>
</template>

<style lang="scss" scoped>
.detail-page {
  max-width: 860px;
  margin: 0 auto;
  padding-bottom: $spacing-2xl;
}

.loading-box { height: 400px; }

.cover-wrap {
  width: 100%;
  max-height: 420px;
  overflow: hidden;

  .cover-img { width: 100%; height: 100%; object-fit: cover; display: block; }
}

.post-container {
  padding: $spacing-xl $spacing-lg;
}

.post-header {
  margin-bottom: $spacing-xl;

  .cat-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: $radius-full;
    font-size: $font-xs;
    font-weight: 500;
    background: rgba(99, 102, 241, 0.1);
    color: $color-primary;
    margin-bottom: $spacing-sm;
  }

  .post-title {
    font-size: 28px;
    font-weight: 700;
    line-height: 1.3;
    color: var(--el-text-color-primary);
    margin: 0 0 $spacing-md;
  }

  .post-meta {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    font-size: $font-sm;
    color: var(--el-text-color-secondary);

    .meta-avatar { flex-shrink: 0; }
    .meta-author {
      cursor: pointer;
      font-weight: 500;
      color: var(--el-text-color-primary);
      &:hover { color: $color-primary; }
    }
    .meta-sep { color: var(--el-text-color-placeholder); }
    .meta-views { display: flex; align-items: center; gap: 3px; margin-left: auto; }
  }
}

.post-content {
  line-height: 1.8;
  font-size: 15px;
  color: var(--el-text-color-regular);
  margin-bottom: $spacing-2xl;

  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    color: var(--el-text-color-primary);
    font-weight: 600;
    margin: 1.5em 0 0.5em;
  }
  :deep(h1) { font-size: 1.75em; }
  :deep(h2) { font-size: 1.4em; border-bottom: 1px solid var(--el-border-color-light); padding-bottom: 0.3em; }
  :deep(h3) { font-size: 1.2em; }
  :deep(p) { margin: 0.8em 0; }
  :deep(a) { color: $color-primary; text-decoration: none; &:hover { text-decoration: underline; } }
  :deep(code) {
    background: var(--el-fill-color);
    padding: 2px 6px;
    border-radius: $radius-sm;
    font-size: 0.9em;
    font-family: monospace;
  }
  :deep(pre) {
    border-radius: $radius-lg;
    overflow-x: auto;
    margin: 1em 0;
    code {
      background: none;
      padding: 0;
      font-size: 0.875em;
      line-height: 1.6;
    }
  }
  :deep(blockquote) {
    border-left: 4px solid $color-primary;
    margin: 1em 0;
    padding: $spacing-sm $spacing-md;
    background: var(--el-fill-color-light);
    color: var(--el-text-color-secondary);
  }
  :deep(ul), :deep(ol) { padding-left: 1.5em; margin: 0.8em 0; }
  :deep(img) { max-width: 100%; border-radius: $radius-lg; }
  :deep(hr) { border: none; border-top: 1px solid var(--el-border-color-light); margin: 1.5em 0; }
  :deep(table) { width: 100%; border-collapse: collapse; margin: 1em 0; }
  :deep(th), :deep(td) { border: 1px solid var(--el-border-color-light); padding: 8px 12px; }
  :deep(th) { background: var(--el-fill-color); font-weight: 600; }
}

.sub-title {
  font-size: $font-base;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 $spacing-md;
}

.attachments-wrap { margin-bottom: $spacing-xl; }
.attachments-list { display: flex; flex-direction: column; gap: $spacing-sm; }

.interact-bar {
  display: flex;
  gap: $spacing-md;
  padding: $spacing-lg 0;
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
  margin-bottom: $spacing-xl;
}

.interact-btn {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  padding: 8px 20px;
  border-radius: $radius-full;
  border: 1px solid var(--el-border-color);
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: $font-sm;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover { border-color: var(--el-border-color-dark); }
  &.active { border-color: transparent; background: transparent; }
}

@media (max-width: 560px) {
  .post-container { padding: $spacing-md; }
  .post-title { font-size: 22px; }
}
</style>
