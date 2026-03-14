<template>
  <div class="dashboard">
    <!-- 数字卡片 -->
    <div class="stat-cards" v-loading="loading">
      <div class="stat-card">
        <div class="stat-icon users"><el-icon><User /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ stats?.users_total ?? '-' }}</div>
          <div class="stat-label">用户总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon files"><el-icon><Files /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ stats?.files_total ?? '-' }}</div>
          <div class="stat-label">文件总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon storage"><el-icon><Coin /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ formatStorage(stats?.storage_total) }}</div>
          <div class="stat-label">全站存储</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon new-users"><el-icon><TrendCharts /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ stats?.new_users_7d ?? '-' }}</div>
          <div class="stat-label">近7天新增用户</div>
        </div>
      </div>
    </div>

    <!-- 文件分类统计 -->
    <el-card class="category-card" v-loading="loading">
      <template #header>
        <span>文件分类统计</span>
      </template>
      <div class="category-list">
        <div class="category-item" v-for="item in categoryItems" :key="item.label">
          <div class="category-header">
            <span class="category-dot-label">
              <span class="cat-dot" :style="{ background: item.color }"></span>
              <span class="category-label">{{ item.label }}</span>
            </span>
            <span class="category-count">{{ item.count }}</span>
          </div>
          <div class="category-bar">
            <div class="category-fill" :style="{ width: getPercentage(item.count) + '%', background: item.color }"></div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Files, Coin, TrendCharts } from '@element-plus/icons-vue'
import { systemApi } from '@/api/modules/system'
import type { AdminStats } from '@/types/models'

const loading = ref(false)
const stats = ref<AdminStats | null>(null)

const categoryItems = computed(() => {
  if (!stats.value) return []
  const cat = stats.value.files_by_category
  return [
    { label: '图片', count: cat.image, color: '#5a67d8' },
    { label: '视频', count: cat.video, color: '#8b5cf6' },
    { label: '资源', count: cat.resource, color: '#10b981' },
    { label: '文档', count: cat.document, color: '#f59e0b' },
  ]
})

function getPercentage(count: number): number {
  const total = stats.value?.files_total || 1
  return Math.round((count / total) * 100)
}

function formatStorage(bytes?: number): string {
  if (bytes == null) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

async function loadStats() {
  loading.value = true
  try {
    const res = await systemApi.getStats()
    if (res.success) {
      stats.value = res.data
    }
  } catch {
    ElMessage.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>

<style scoped lang="scss">
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: $radius-lg;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;

  .stat-icon {
    width: 44px;
    height: 44px;
    border-radius: $radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;

    &.users    { background: rgba(90, 103, 216, 0.10); color: #5a67d8; }
    &.files    { background: rgba(139, 92, 246, 0.10); color: #8b5cf6; }
    &.storage  { background: rgba(16, 185, 129, 0.10); color: #10b981; }
    &.new-users { background: rgba(245, 158, 11, 0.10); color: #f59e0b; }
  }

  .stat-info {
    min-width: 0;
    .stat-value {
      font-size: 24px;
      font-weight: 700;
      line-height: 1.2;
      color: var(--color-text-primary);
    }
    .stat-label {
      font-size: 12px;
      color: var(--color-text-muted);
      margin-top: 3px;
    }
  }
}

.category-card {
  :deep(.el-card__header) {
    font-weight: 600;
    font-size: $font-sm;
    color: var(--color-text-primary);
  }
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 20px;
}

.category-item {
  .category-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;

    .category-count {
      font-size: 13px;
      font-weight: 600;
      color: var(--color-text-primary);
      font-variant-numeric: tabular-nums;
    }
  }
}

.category-dot-label {
  display: flex;
  align-items: center;
  gap: 7px;

  .cat-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .category-label {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}

.category-bar {
  height: 6px;
  background: var(--color-surface-raised);
  border-radius: $radius-sm;
  overflow: hidden;
  border: 1px solid var(--color-border-subtle);

  .category-fill {
    height: 100%;
    border-radius: $radius-sm;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }
}
</style>
