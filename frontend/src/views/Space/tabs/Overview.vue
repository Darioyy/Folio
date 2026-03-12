<template>
  <div class="overview-zone">
    <!-- 存储卡片 -->
    <div class="settings-card">
      <div class="card-title">
        <el-icon><Coin /></el-icon>
        存储空间
      </div>
      <div v-if="storageInfo" class="storage-info">
        <div class="storage-bar-wrap">
          <div
            class="storage-bar"
            :style="{
              width: storageInfo.storage_percentage + '%',
              background: storageInfo.storage_percentage >= 90
                ? 'var(--el-color-danger)'
                : storageInfo.storage_percentage >= 70
                ? 'var(--el-color-warning)'
                : undefined
            }"
          ></div>
        </div>
        <p class="storage-text">
          已用 <strong>{{ formatSize(storageInfo.storage_used) }}</strong>
          &nbsp;/&nbsp;共 <strong>{{ formatSize(storageInfo.storage_quota) }}</strong>
          &nbsp;（{{ storageInfo.storage_percentage.toFixed(1) }}%）
        </p>
      </div>
      <el-skeleton v-else :rows="2" animated />
    </div>

    <!-- 文件统计 -->
    <div class="settings-card">
      <div class="card-title">
        <el-icon><FolderOpened /></el-icon>
        文件统计
      </div>
      <div class="stats-grid">
        <div class="stats-cell">
          <el-icon class="stats-icon image-icon"><Picture /></el-icon>
          <span class="stats-num">{{ myStats.media }}</span>
          <span class="stats-label">媒体</span>
        </div>
        <div class="stats-cell">
          <el-icon class="stats-icon resource-icon"><Folder /></el-icon>
          <span class="stats-num">{{ myStats.resources }}</span>
          <span class="stats-label">资源</span>
        </div>
        <div class="stats-cell">
          <el-icon class="stats-icon post-icon"><Document /></el-icon>
          <span class="stats-num">{{ myStats.posts }}</span>
          <span class="stats-label">文章</span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onActivated } from 'vue'
import { Coin, FolderOpened, Picture, Folder, Document } from '@element-plus/icons-vue'
import { hubApi } from '@/api/modules/hub'
import { usersApi } from '@/api/modules/users'
import type { StorageInfo } from '@/api/modules/hub'
import type { MyStats } from '@/api/modules/users'

const storageInfo = ref<StorageInfo | null>(null)
const myStats = reactive<MyStats>({ posts: 0, media: 0, resources: 0, total_size: 0 })

async function loadOverview() {
  try {
    const [storageRes, statsRes] = await Promise.all([
      hubApi.getStorageInfo(),
      usersApi.getMyStats(),
    ])
    if (storageRes.data) {
      storageInfo.value = {
        storage_used: storageRes.data.storage_used ?? 0,
        storage_quota: storageRes.data.storage_quota ?? 0,
        storage_percentage: Number(storageRes.data.storage_percentage ?? 0),
      }
    }
    if (statsRes.data) Object.assign(myStats, statsRes.data)
  } catch { /* 静默失败 */ }
}

onMounted(loadOverview)
onActivated(loadOverview)

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}
</script>

<style scoped lang="scss">
.settings-card {
  background: var(--el-bg-color);
  border-radius: $radius-lg;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
  margin-bottom: $spacing-md;
}

.card-title {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: $font-base;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: $spacing-md;

  .el-icon {
    font-size: 18px;
    color: $color-primary;
  }
}

.storage-info {
  .storage-bar-wrap {
    height: 8px;
    background: var(--el-fill-color);
    border-radius: $radius-full;
    overflow: hidden;
    margin-bottom: $spacing-sm;
  }

  .storage-bar {
    height: 100%;
    background: linear-gradient(90deg, $color-primary 0%, $color-secondary 100%);
    border-radius: $radius-full;
    transition: width 0.6s ease;
    min-width: 2px;
  }

  .storage-text {
    font-size: $font-sm;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-md;
  text-align: center;
}

.stats-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-md;
  background: var(--el-fill-color-light);
  border-radius: $radius-lg;
}

.stats-icon {
  font-size: 28px;
  &.image-icon { color: #6366f1; }
  &.resource-icon { color: #f59e0b; }
  &.post-icon { color: #10b981; }
}

.stats-num {
  font-size: $font-2xl;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stats-label {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
}

</style>
