<template>
  <div class="media-page">
    <div class="container">
      <div class="page-header">
        <h1>游戏媒体</h1>
        <el-radio-group v-model="mediaType" @change="loadMedia">
          <el-radio-button value="image">截图</el-radio-button>
          <el-radio-button value="video">视频</el-radio-button>
        </el-radio-group>
      </div>

      <el-empty v-if="mediaList.length === 0 && !loading" description="暂无媒体" />

      <div v-else class="media-grid">
        <div
          v-for="media in mediaList"
          :key="media.id"
          class="media-item"
          @click="viewMedia(media)"
        >
          <div class="media-thumb">
            <el-image
              v-if="mediaType === 'image'"
              :src="getMediaUrl(media.id)"
              fit="cover"
              lazy
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <div v-else class="video-thumb">
              <el-image
                v-if="media.thumbnail_path"
                :src="getThumbnailUrl(media.id)"
                fit="cover"
                lazy
              />
              <div v-else class="video-placeholder">
                <el-icon><VideoCamera /></el-icon>
              </div>
              <div class="play-overlay">
                <el-icon :size="32"><VideoPlay /></el-icon>
              </div>
            </div>
          </div>
          <div class="media-info">
            <h4>{{ media.title }}</h4>
          </div>
        </div>
      </div>
    </div>

    <!-- 文件预览对话框 -->
    <FilePreview
      v-model="previewVisible"
      :file="currentMedia"
      type="media"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  Picture,
  VideoCamera,
  VideoPlay
} from '@element-plus/icons-vue'
import FilePreview from '@/components/business/FilePreview.vue'
import { mediaApi } from '@/api/modules/media'

const mediaType = ref<'image' | 'video'>('image')
const mediaList = ref<any[]>([])
const loading = ref(false)
const previewVisible = ref(false)
const currentMedia = ref<any>(null)

async function loadMedia() {
  loading.value = true
  try {
    const res = await mediaApi.getList({
      limit: 50,
      type: mediaType.value
    })
    mediaList.value = res.data || []
  } catch {
    mediaList.value = []
  } finally {
    loading.value = false
  }
}

function getMediaUrl(id?: number) {
  if (!id) return ''
  return mediaApi.getViewUrl(id)
}

function getThumbnailUrl(id?: number) {
  if (!id) return ''
  return mediaApi.getThumbnailUrl(id)
}

function viewMedia(media: any) {
  currentMedia.value = media
  previewVisible.value = true
}

onMounted(() => {
  loadMedia()
})
</script>

<style scoped lang="scss">
.media-page {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-lg;
  }
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: $spacing-lg;
}

.media-item {
  cursor: pointer;
  border-radius: $border-radius-base;
  overflow: hidden;
  transition: $transition-base;

  &:hover {
    transform: translateY(-4px);
    box-shadow: $box-shadow-base;
  }
}

.media-thumb {
  aspect-ratio: 16 / 9;
  background: var(--el-fill-color-light);
  border-radius: $border-radius-base;
  overflow: hidden;
  position: relative;

  :deep(.el-image) {
    width: 100%;
    height: 100%;
  }
}

.image-error,
.video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
  font-size: 48px;
}

.video-thumb {
  position: relative;

  :deep(.el-image) {
    width: 100%;
    height: 100%;
  }
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  color: white;
}

.media-info {
  padding-top: $spacing-sm;

  h4 {
    font-size: 14px;
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
