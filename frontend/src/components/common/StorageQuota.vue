<template>
  <div class="storage-quota">
    <div class="quota-header">
      <span class="label">存储空间</span>
      <span class="percentage">{{ storageInfo.storage_percentage }}%</span>
    </div>
    <el-progress
      :percentage="storageInfo.storage_percentage"
      :color="progressColor"
      :stroke-width="8"
      :show-text="false"
    />
    <div class="quota-footer">
      <span class="used">{{ formatSize(storageInfo.storage_used) }}</span>
      <span class="separator">/</span>
      <span class="total">{{ formatSize(storageInfo.storage_quota) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StorageInfo } from '@/api/modules/hub'

interface Props {
  storageInfo: StorageInfo
}

const props = defineProps<Props>()

// 进度条颜色（根据使用率变化）
const progressColor = computed(() => {
  const p = props.storageInfo.storage_percentage
  if (p >= 90) return '#f56c6c'  // 红色
  if (p >= 70) return '#e6a23c'  // 橙色
  return '#67c23a'               // 绿色
})

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped lang="scss">
.storage-quota {
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;

  .quota-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .label {
      font-size: 14px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }

    .percentage {
      font-size: 14px;
      font-weight: 600;
      color: var(--el-color-primary);
    }
  }

  .el-progress {
    margin-bottom: 8px;
  }

  .quota-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;

    .used {
      color: var(--el-text-color-regular);
    }

    .separator {
      color: var(--el-text-color-secondary);
    }

    .total {
      color: var(--el-text-color-secondary);
    }
  }
}
</style>
