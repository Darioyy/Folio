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

        <p v-if="file.description" class="file-description">{{ file.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import FileTypeIcon from '@/components/business/FileTypeIcon.vue'
import { filesApi } from '@/api/modules/files'
import type { FileItem } from '@/types/models'
import { formatDate, formatFileSize } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const file = ref<FileItem | null>(null)
const loading = ref(true)
const errorCode = ref<number | null>(null)

const fileId = computed(() => Number(route.params.id))

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

async function loadFile() {
  loading.value = true
  errorCode.value = null
  try {
    const res = await filesApi.getDetail(fileId.value)
    file.value = res.data
    if (file.value?.title) {
      document.title = `${file.value.title} - Folio`
    }
  } catch (e: any) {
    errorCode.value = e.response?.status || 404
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFile()
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
