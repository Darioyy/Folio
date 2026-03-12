<script setup lang="ts">
import { computed } from 'vue'
import { Download } from '@element-plus/icons-vue'
import type { PostAttachment } from '@/types/models'
import { formatFileSize } from '@/utils/format'
import FileTypeIcon from './FileTypeIcon.vue'

interface Props {
  attachment: PostAttachment
  postId: number
}

const props = defineProps<Props>()

const downloadUrl = computed(() => {
  const base = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  return `${base}/posts/${props.postId}/attachments/${props.attachment.file_id}/download`
})

const displayName = computed(() => props.attachment.title || props.attachment.file_name)
</script>

<template>
  <div class="attachment-card">
    <div class="att-icon">
      <FileTypeIcon
        :mime-type="attachment.mime_type"
        :file-name="attachment.file_name"
        size="sm"
      />
    </div>
    <div class="att-info">
      <span class="att-name">{{ displayName }}</span>
      <span class="att-size">{{ formatFileSize(attachment.file_size) }}</span>
    </div>
    <a :href="downloadUrl" download class="att-download">
      <el-button :icon="Download" size="small" text>下载</el-button>
    </a>
  </div>
</template>

<style lang="scss" scoped>
.attachment-card {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-sm $spacing-md;
  border-radius: $radius-lg;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-fill-color-light);
  transition: border-color $transition-fast;

  &:hover {
    border-color: $color-primary;
  }
}

.att-icon {
  flex-shrink: 0;
}

.att-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.att-name {
  font-size: $font-sm;
  color: var(--el-text-color-primary);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.att-size {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
}

.att-download {
  flex-shrink: 0;
  text-decoration: none;
}
</style>
