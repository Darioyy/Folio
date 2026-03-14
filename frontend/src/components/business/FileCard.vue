<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { VideoPlay } from '@element-plus/icons-vue'
import type { FileItem } from '@/types/models'
import { fromNow, getFileUrl } from '@/utils/format'
import FileTypeIcon from './FileTypeIcon.vue'

interface Props {
  file: FileItem
  showAuthor?: boolean
  showThumbnail?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showAuthor: true,
  showThumbnail: true,
})

defineEmits<{
  click: [file: FileItem]
}>()

const imgError = ref(false)
const videoThumbError = ref(false)

const thumbnailSrc = computed(() => {
  if (imgError.value) return ''
  return getFileUrl(props.file.thumbnail_path || props.file.file_path)
})

const videoThumbSrc = computed(() => {
  if (videoThumbError.value || !props.file.thumbnail_path) return ''
  return getFileUrl(props.file.thumbnail_path)
})

const displayName = computed(() => props.file.nickname || props.file.username || '未知用户')

const authorAvatarUrl = computed(() => {
  if (!props.file.username) return ''
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/users/username/${props.file.username}/avatar/view`
})

const router = useRouter()

function handleAuthorClick(e: MouseEvent) {
  e.stopPropagation()
  if (props.file.username) {
    router.push({ name: 'UserProfile', params: { username: props.file.username } })
  }
}
</script>

<template>
  <div class="file-card" @click="$emit('click', file)">
    <!-- 缩略图区（固定 16:9） -->
    <div class="thumbnail-wrap">
      <!-- 统一图标模式（Space 云盘视图） -->
      <div v-if="!showThumbnail" class="icon-placeholder">
        <FileTypeIcon
          :mime-type="file.mime_type"
          :file-name="file.file_name"
          :file-category="file.file_category"
          size="md"
        />
      </div>
      <!-- 缩略图模式（搜索等场景） -->
      <template v-else>
        <!-- 图片 -->
        <img
          v-if="file.file_category === 'image' && thumbnailSrc && !imgError"
          :src="thumbnailSrc"
          :alt="file.file_name"
          class="thumbnail-img"
          loading="lazy"
          @error="imgError = true"
        />
        <!-- 视频 -->
        <template v-else-if="file.file_category === 'video'">
          <img
            v-if="videoThumbSrc"
            :src="videoThumbSrc"
            :alt="file.file_name"
            class="thumbnail-img"
            loading="lazy"
            @error="videoThumbError = true"
          />
          <div v-else class="icon-placeholder">
            <el-icon :size="40" class="placeholder-icon"><VideoPlay /></el-icon>
          </div>
          <div class="play-overlay">
            <el-icon :size="28"><VideoPlay /></el-icon>
          </div>
        </template>
        <!-- 文档 / 资源 -->
        <div v-else class="icon-placeholder">
          <FileTypeIcon
            :mime-type="file.mime_type"
            :file-name="file.file_name"
            size="md"
          />
        </div>
      </template>
    </div>

    <!-- 内容区 -->
    <div class="card-body">
      <p class="card-title">{{ file.file_name }}</p>
      <p v-if="file.description" class="card-desc">{{ file.description }}</p>
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
        <span class="meta-time">{{ fromNow(file.created_at) }}</span>
        <template v-if="file.like_count > 0">
          <span class="meta-sep">·</span>
          <span class="meta-likes">♥ {{ file.like_count }}</span>
        </template>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.file-card {
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

.thumbnail-wrap {
  position: relative;
  padding-top: 56.25%; // 16:9
  overflow: hidden;
  background: var(--el-fill-color);

  .thumbnail-img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .icon-placeholder {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: $spacing-xs;

  }

  .play-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.3);
    color: #fff;
  }

}

.card-body {
  padding: $spacing-md;

  .card-title {
    margin: 0 0 $spacing-xs;
    font-size: $font-sm;
    font-weight: 600;
    color: var(--el-text-color-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .card-desc {
    margin: 0 0 $spacing-sm;
    font-size: $font-xs;
    color: var(--el-text-color-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .card-meta {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    margin-top: $spacing-sm;
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
        background: rgba(90, 103, 216, 0.08);
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

    .meta-likes {
      flex-shrink: 0;
      color: var(--el-text-color-placeholder);
      font-size: 11px;
    }
  }
}
</style>
