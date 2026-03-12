<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChatLineRound, Star, View } from '@element-plus/icons-vue'
import type { Post } from '@/types/models'
import { fromNow, getFileUrl } from '@/utils/format'

interface Props {
  post: Post
  showAuthor?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showAuthor: true
})

const router = useRouter()

const imgError = ref(false)

const coverSrc = computed(() => {
  if (imgError.value || !props.post.cover_image_url) return ''
  return getFileUrl(props.post.cover_image_url)
})

const authorAvatarUrl = computed(() => {
  if (!props.post.author_name) return ''
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/users/username/${props.post.author_name}/avatar/view`
})

const displayName = computed(() =>
  props.post.author_nickname || props.post.author_name || '未知用户'
)

const timeStr = computed(() => {
  const t = props.post.published_at || props.post.created_at
  return t ? fromNow(t) : ''
})

function handleClick() {
  router.push(`/post/${props.post.id}`)
}

function handleAuthorClick(e: MouseEvent) {
  e.stopPropagation()
  if (props.post.author_name) {
    router.push({ name: 'UserProfile', params: { username: props.post.author_name } })
  }
}
</script>

<template>
  <div class="post-card" @click="handleClick">
    <!-- 封面图区（16:9） -->
    <div class="cover-wrap">
      <img
        v-if="coverSrc"
        :src="coverSrc"
        :alt="post.title"
        class="cover-img"
        loading="lazy"
        @error="imgError = true"
      />
      <div v-else class="cover-placeholder">
        <span class="cover-initial">{{ post.title[0] }}</span>
      </div>
      <span v-if="post.category_name" class="category-badge">{{ post.category_name }}</span>
    </div>

    <!-- 内容区 -->
    <div class="card-body">
      <p class="card-title">{{ post.title }}</p>
      <p v-if="post.summary" class="card-summary">{{ post.summary }}</p>

      <div class="card-meta">
        <template v-if="showAuthor">
          <span class="meta-author-link" @click="handleAuthorClick">
            <el-avatar :size="18" :src="authorAvatarUrl" class="meta-avatar">
              {{ displayName[0].toUpperCase() }}
            </el-avatar>
            <span class="meta-author">{{ displayName }}</span>
          </span>
          <span class="meta-sep">·</span>
        </template>
        <span class="meta-time">{{ timeStr }}</span>
      </div>

      <div class="card-stats">
        <span class="stat-item">
          <el-icon :size="12"><Star /></el-icon>
          {{ post.like_count }}
        </span>
        <span class="stat-item">
          <el-icon :size="12"><ChatLineRound /></el-icon>
          {{ post.comment_count }}
        </span>
        <span class="stat-item stat-views">
          <el-icon :size="12"><View /></el-icon>
          {{ post.view_count }}
        </span>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.post-card {
  background: var(--el-bg-color);
  border-radius: $radius-lg;
  overflow: hidden;
  border: 1px solid var(--el-border-color-light);
  box-shadow: $shadow-sm;
  cursor: pointer;
  transition: transform $transition-base, box-shadow $transition-base;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
  }
}

.cover-wrap {
  position: relative;
  padding-top: 56.25%; // 16:9
  overflow: hidden;
  background: var(--el-fill-color);

  .cover-img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .cover-placeholder {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--el-fill-color) 0%, var(--el-fill-color-dark) 100%);

    .cover-initial {
      font-size: 36px;
      font-weight: 700;
      color: var(--el-text-color-placeholder);
      text-transform: uppercase;
      line-height: 1;
      user-select: none;
    }
  }

  .category-badge {
    position: absolute;
    top: $spacing-sm;
    left: $spacing-sm;
    padding: 2px 8px;
    border-radius: $radius-full;
    font-size: $font-xs;
    font-weight: 500;
    background: rgba(99, 102, 241, 0.85);
    color: #fff;
    backdrop-filter: blur(4px);
  }
}

.card-body {
  padding: $spacing-md;

  .card-title {
    margin: 0 0 $spacing-xs;
    font-size: $font-sm;
    font-weight: 600;
    color: var(--el-text-color-primary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .card-summary {
    margin: 0 0 $spacing-sm;
    font-size: $font-xs;
    color: var(--el-text-color-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: 1.5;
  }

  .card-meta {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    font-size: $font-xs;
    color: var(--el-text-color-secondary);

    .meta-author-link {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      cursor: pointer;
      border-radius: $radius-sm;
      padding: 1px 3px;
      margin: -1px -3px;
      transition: color $transition-fast, background $transition-fast;

      &:hover {
        color: $color-primary;
        background: rgba(99, 102, 241, 0.08);
      }
    }

    .meta-avatar {
      flex-shrink: 0;
    }

    .meta-author {
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      max-width: 90px;
    }

    .meta-sep {
      flex-shrink: 0;
      color: var(--el-text-color-placeholder);
    }

    .meta-time {
      margin-left: auto;
      flex-shrink: 0;
    }
  }

  .card-stats {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-top: $spacing-sm;
    font-size: 11px;
    color: var(--el-text-color-placeholder);

    .stat-item {
      display: flex;
      align-items: center;
      gap: 3px;
    }

    .stat-views {
      margin-left: auto;
    }
  }
}
</style>
