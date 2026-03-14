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
      <div class="stats-row">
        <div class="stats-item">
          <span class="stats-num image-num">{{ myStats.media }}</span>
          <span class="stats-label">媒体文件</span>
        </div>
        <div class="stats-item">
          <span class="stats-num resource-num">{{ myStats.resources }}</span>
          <span class="stats-label">其他资源</span>
        </div>
        <div class="stats-item">
          <span class="stats-num post-num">{{ myStats.posts }}</span>
          <span class="stats-label">发布文章</span>
        </div>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="settings-card">
      <div class="card-title">
        <el-icon><Clock /></el-icon>
        最近活动
      </div>
      <div v-if="activityLoading" class="activity-skeleton">
        <el-skeleton v-for="i in 3" :key="i" :rows="1" animated style="margin-bottom: 10px" />
      </div>
      <div v-else-if="recentActivity.length === 0" class="activity-empty">
        暂无最近活动
      </div>
      <div v-else class="activity-list">
        <div
          v-for="item in recentActivity"
          :key="item.id + item.type"
          class="activity-item"
          @click="goToActivity(item)"
        >
          <div class="activity-dot" :class="item.type"></div>
          <div class="activity-body">
            <span class="activity-action">{{ item.action }}</span>
            <span class="activity-name">{{ item.name }}</span>
          </div>
          <span class="activity-time">{{ item.timeStr }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { Coin, FolderOpened, Picture, Folder, Document, Clock } from '@element-plus/icons-vue'
import { hubApi } from '@/api/modules/hub'
import { usersApi } from '@/api/modules/users'
import { postsApi } from '@/api/modules/posts'
import type { StorageInfo } from '@/api/modules/hub'
import type { MyStats } from '@/api/modules/users'
import { fromNow } from '@/utils/format'

interface ActivityItem {
  id: number
  type: 'post' | 'file'
  name: string
  action: string
  timeStr: string
  path: string
}

const router = useRouter()
const storageInfo = ref<StorageInfo | null>(null)
const myStats = reactive<MyStats>({ posts: 0, media: 0, resources: 0, total_size: 0 })
const recentActivity = ref<ActivityItem[]>([])
const activityLoading = ref(false)

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

async function loadRecentActivity() {
  activityLoading.value = true
  try {
    const [postsRes, filesRes] = await Promise.allSettled([
      postsApi.getMyPosts({ page: 1, page_size: 5 }),
      hubApi.getUserMedia({ page: 1, page_size: 5 }),
    ])

    const activities: ActivityItem[] = []

    if (postsRes.status === 'fulfilled' && postsRes.value.data?.items) {
      for (const p of postsRes.value.data.items) {
        activities.push({
          id: p.id,
          type: 'post',
          name: p.title,
          action: p.status === 'published' ? '发布了文章' : '创建了草稿',
          timeStr: fromNow(p.published_at || p.created_at),
          path: `/post/${p.id}`,
        })
      }
    }

    if (filesRes.status === 'fulfilled') {
      for (const f of filesRes.value.items || []) {
        activities.push({
          id: f.id,
          type: 'file',
          name: f.name,
          action: '上传了文件',
          timeStr: fromNow(f.created_at),
          path: `/file/${f.id}`,
        })
      }
    }

    // 按时间倒序取最新 3 条
    activities.sort((a, b) => b.id - a.id)
    recentActivity.value = activities.slice(0, 3)
  } catch { /* 静默失败 */ } finally {
    activityLoading.value = false
  }
}

function goToActivity(item: ActivityItem) {
  router.push(item.path)
}

onMounted(() => {
  loadOverview()
  loadRecentActivity()
})
onActivated(() => {
  loadOverview()
  loadRecentActivity()
})

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
  font-size: $font-sm;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: $spacing-md;

  .el-icon {
    font-size: 15px;
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

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px $spacing-sm 14px;
  background: var(--el-bg-color);
  border: 1px solid var(--color-border);
  border-radius: $radius-md;
  transition: border-color $transition-fast, background $transition-fast;

  &:hover {
    border-color: var(--color-text-muted);
    background: var(--el-fill-color-extra-light);
  }
}

.stats-num {
  font-size: $font-xl;
  font-weight: 700;
  line-height: 1;
  font-variant-numeric: tabular-nums;

  &.image-num { color: $color-primary; }
  &.resource-num { color: $color-warning; }
  &.post-num { color: $color-success; }
}

.stats-label {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  white-space: nowrap;
}

// 最近活动
.activity-skeleton { padding: 4px 0; }

.activity-empty {
  font-size: $font-sm;
  color: var(--el-text-color-placeholder);
  text-align: center;
  padding: $spacing-md 0;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: 9px 0;
  cursor: pointer;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  transition: background $transition-fast;

  &:last-child { border-bottom: none; }

  &:hover .activity-name { color: $color-primary; }
}

.activity-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;

  &.post { background: $color-primary; }
  &.file { background: $color-warning; }
}

.activity-body {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  overflow: hidden;
}

.activity-action {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.activity-name {
  font-size: $font-sm;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color $transition-fast;
}

.activity-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
}

.overview-zone {
  padding: $spacing-lg 0;
  min-height: calc(100vh - 52px);
}
</style>
