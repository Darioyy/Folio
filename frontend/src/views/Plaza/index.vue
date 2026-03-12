<template>
  <div class="plaza-page">
    <div class="container">
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <!-- 分类 tabs -->
        <div class="content-tabs">
          <span
            v-for="tab in tabs"
            :key="tab.value"
            :class="['tab-item', { active: activeTab === tab.value }]"
            @click="handleTabChange(tab.value)"
          >
            {{ tab.label }}
          </span>
        </div>

        <!-- 右侧控件 -->
        <div class="bar-right">
          <button
            class="view-toggle-btn"
            :data-tip="viewMode === 'grid' ? '列表' : '网格'"
            @click="toggleViewMode"
          >
            <svg v-if="viewMode === 'list'" viewBox="0 0 16 16" width="15" height="15" fill="currentColor">
              <rect x="1" y="2" width="14" height="2" rx="1"/>
              <rect x="1" y="7" width="14" height="2" rx="1"/>
              <rect x="1" y="12" width="14" height="2" rx="1"/>
            </svg>
            <svg v-else viewBox="0 0 16 16" width="15" height="15" fill="currentColor">
              <rect x="1" y="1" width="6" height="6" rx="1"/>
              <rect x="9" y="1" width="6" height="6" rx="1"/>
              <rect x="1" y="9" width="6" height="6" rx="1"/>
              <rect x="9" y="9" width="6" height="6" rx="1"/>
            </svg>
          </button>
          <el-select v-model="sortBy" @change="loadFiles(true)" size="small" style="width: 90px">
            <el-option label="最新" value="latest" />
            <el-option label="最多下载" value="popular" />
          </el-select>
        </div>
      </div>

      <!-- 加载占位 -->
      <div v-if="loading" class="content-loading">
        <template v-if="viewMode === 'grid'">
          <div class="grid-skeleton">
            <el-skeleton v-for="i in 12" :key="i" animated>
              <template #template>
                <el-skeleton-item variant="image" style="height: 160px; border-radius: 8px;" />
                <div style="padding: 8px 4px;">
                  <el-skeleton-item variant="p" style="width: 80%" />
                  <el-skeleton-item variant="p" style="width: 50%; margin-top: 6px" />
                </div>
              </template>
            </el-skeleton>
          </div>
        </template>
        <el-skeleton v-else :rows="8" animated />
      </div>

      <!-- 网格视图 -->
      <div v-else-if="files.length && viewMode === 'grid'" class="content-grid">
        <FileCard
          v-for="item in files"
          :key="item.id"
          :file="item"
          :show-badge="false"
          @click="viewFile"
        />
      </div>

      <!-- 列表视图 -->
      <div v-else-if="files.length && viewMode === 'list'" class="content-list">
        <div class="list-header">
          <span class="col-icon"></span>
          <span class="col-name">文件名</span>
          <span class="col-author hide-mobile">上传者</span>
          <span class="col-size hide-mobile">大小</span>
          <span class="col-time">上传时间</span>
        </div>
        <div
          v-for="item in files"
          :key="item.id"
          class="list-row"
          @click="viewFile(item)"
        >
          <span class="col-icon">
            <div v-if="item.file_category === 'image'" class="list-thumb">
              <img
                :src="getFileUrl(item.thumbnail_path || item.file_path)"
                :alt="item.title"
                loading="lazy"
                @error="(e) => ((e.target as HTMLImageElement).style.display = 'none')"
              />
            </div>
            <div v-else-if="item.file_category === 'video'" class="list-video">
              <img
                v-if="item.thumbnail_path"
                :src="getFileUrl(item.thumbnail_path)"
                :alt="item.title"
                loading="lazy"
                @error="(e) => ((e.target as HTMLImageElement).style.display = 'none')"
              />
              <el-icon v-else :size="20" style="color: #6366f1"><VideoPlay /></el-icon>
            </div>
            <FileTypeIcon
              v-else
              :mime-type="item.mime_type"
              :file-name="item.file_name"
              size="sm"
            />
          </span>
          <div class="col-name">
            <span class="row-title">{{ item.title }}</span>
            <span v-if="item.description" class="row-desc">{{ item.description }}</span>
          </div>
          <div
            class="col-author hide-mobile"
            @click.stop="goToUser(item.username)"
          >
            <el-avatar :size="20" :src="getFileUrl(item.avatar ?? '')">
              {{ (item.nickname || item.username || '?')[0].toUpperCase() }}
            </el-avatar>
            <span class="author-name">{{ item.nickname || item.username }}</span>
          </div>
          <span class="col-size hide-mobile">{{ formatFileSize(item.file_size) }}</span>
          <span class="col-time" :title="formatDate(item.created_at)">{{ formatDate(item.created_at, 'MM-DD HH:mm') }}</span>
        </div>
      </div>

      <el-empty v-else-if="!loading" description="暂无公开内容" :image-size="80" />

      <!-- 加载更多 -->
      <div v-if="hasMore && !loading" class="load-more">
        <el-button @click="loadMore" :loading="loadingMore" plain>加载更多</el-button>
      </div>
    </div>

    <FilePreview
      v-model="previewVisible"
      :file="currentFile"
      :type="previewType"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import FileCard from '@/components/business/FileCard.vue'
import FileTypeIcon from '@/components/business/FileTypeIcon.vue'
import FilePreview from '@/components/business/FilePreview.vue'
import { filesApi } from '@/api/modules/files'
import type { FileItem } from '@/types/models'
import { fromNow, formatFileSize, getFileUrl, formatDate } from '@/utils/format'

const router = useRouter()

type TabType = 'all' | 'image' | 'video' | 'document'
type ViewMode = 'grid' | 'list'

const tabs: { value: TabType; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'document', label: '文档' },
  { value: 'image', label: '图片' },
  { value: 'video', label: '视频' },
]

const activeTab = ref<TabType>('all')
const _savedPlazaView = localStorage.getItem('vs-plaza-view') as ViewMode | null
const viewMode = ref<ViewMode>(_savedPlazaView || 'grid')

function toggleViewMode() {
  viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid'
}

watch(viewMode, (val) => {
  localStorage.setItem('vs-plaza-view', val)
})
const sortBy = ref<'latest' | 'popular'>('latest')

const loading = ref(false)
const loadingMore = ref(false)
const currentPage = ref(1)
const pageSize = 24
const files = ref<FileItem[]>([])
const totalCount = ref(0)

const previewVisible = ref(false)
const currentFile = ref<FileItem | null>(null)

const hasMore = computed(() => files.value.length < totalCount.value)

const previewType = computed<'media' | 'document'>(() => {
  if (!currentFile.value) return 'media'
  return currentFile.value.file_category === 'document' ? 'document' : 'media'
})

async function loadFiles(reset = true) {
  if (reset) {
    currentPage.value = 1
    files.value = []
    totalCount.value = 0
  }
  reset ? (loading.value = true) : (loadingMore.value = true)

  try {
    const category = activeTab.value === 'all'
      ? undefined
      : activeTab.value as 'image' | 'video' | 'document'
    const res = await filesApi.getPublicList({
      page: currentPage.value,
      page_size: pageSize,
      ...(category ? { category } : {}),
    })
    const newItems = res.items || []

    if (sortBy.value === 'popular') {
      newItems.sort((a, b) => (b.download_count || 0) - (a.download_count || 0))
    }

    reset ? (files.value = newItems) : files.value.push(...newItems)
    totalCount.value = res.pagination?.total ?? 0
  } catch {
    ElMessage.error('加载内容失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function handleTabChange(tab: TabType) {
  activeTab.value = tab
  // Auto-switch view per content type
  if (tab === 'document') viewMode.value = 'list'
  else viewMode.value = 'grid'
  loadFiles(true)
}

function loadMore() {
  currentPage.value++
  loadFiles(false)
}

function viewFile(file: FileItem) {
  router.push({ name: 'FileDetail', params: { id: file.id } })
}

function goToUser(username?: string) {
  if (username) router.push({ name: 'UserProfile', params: { username } })
}

onMounted(() => loadFiles())
</script>

<style scoped lang="scss">
.plaza-page {
  min-height: 100vh;
  background: var(--el-bg-color-page);
  padding-bottom: $spacing-3xl;
}

.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: $spacing-lg $spacing-md;
}

// 筛选栏
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
  flex-wrap: wrap;
}

// 下划线 tab 导航
.content-tabs {
  display: flex;
  align-items: center;
  gap: 2px;
  border-bottom: 1px solid var(--el-border-color-light);

  .tab-item {
    padding: $spacing-sm $spacing-md;
    font-size: $font-sm;
    color: var(--el-text-color-secondary);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: color $transition-fast, border-color $transition-fast;
    white-space: nowrap;
    user-select: none;

    &:hover {
      color: var(--el-text-color-primary);
    }

    &.active {
      color: $color-primary;
      border-bottom-color: $color-primary;
      font-weight: 500;
    }
  }
}

// 右侧控件组
.bar-right {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

// 视图切换单按钮
.view-toggle-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-md;
  transition: background $transition-fast, color $transition-fast, border-color $transition-fast;

  &:hover {
    border-color: $color-primary;
    color: $color-primary;
  }

  // CSS tooltip —— 按钮正下方居中浮出
  &[data-tip]::after {
    content: attr(data-tip);
    position: absolute;
    top: calc(100% + 6px);
    left: 50%;
    translate: -50% 0;
    z-index: 9999;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11.5px;
    font-weight: 450;
    line-height: 1.4;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transform: translateY(-4px) scale(0.96);
    transform-origin: top center;
    transition: opacity 0.12s ease, transform 0.12s ease;
    transition-delay: 0.06s;
    background: rgba(22, 24, 30, 0.82);
    color: rgba(255, 255, 255, 0.92);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.07);
  }

  &[data-tip]:hover::after {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

:global(html.dark) .view-toggle-btn[data-tip]::after {
  background: rgba(48, 51, 62, 0.90);
  color: rgba(222, 225, 232, 0.92);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.40);
  border-color: rgba(255, 255, 255, 0.10);
}

// 加载占位
.content-loading {
  padding: $spacing-xl 0;
}

.grid-skeleton {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: $spacing-md;
}

// 内容网格
.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
}

// 列表视图
.content-list {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  overflow: hidden;
  margin-bottom: $spacing-lg;
}

.list-header {
  display: grid;
  grid-template-columns: 44px 1fr 140px 80px 100px;
  gap: $spacing-md;
  align-items: center;
  padding: $spacing-sm $spacing-md;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
  font-size: $font-xs;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.list-row {
  display: grid;
  grid-template-columns: 44px 1fr 140px 80px 100px;
  gap: $spacing-md;
  align-items: center;
  padding: $spacing-sm $spacing-md;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background $transition-fast;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: var(--el-fill-color-light);
  }
}

.col-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .list-thumb,
  .list-video {
    width: 36px;
    height: 36px;
    border-radius: $radius-sm;
    overflow: hidden;
    background: var(--el-fill-color);
    display: flex;
    align-items: center;
    justify-content: center;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
}

.col-name {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;

  .row-title {
    font-size: $font-sm;
    font-weight: 500;
    color: var(--el-text-color-primary);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .row-desc {
    font-size: $font-xs;
    color: var(--el-text-color-secondary);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
}

.col-author {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  cursor: pointer;
  min-width: 0;
  transition: color $transition-fast;

  &:hover {
    color: $color-primary;

    .author-name {
      color: $color-primary;
    }
  }

  .author-name {
    font-size: $font-xs;
    color: var(--el-text-color-secondary);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    max-width: 90px;
    transition: color $transition-fast;
  }
}

.col-size,
.col-time {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.hide-mobile {
  @media (max-width: $breakpoint-md) {
    display: none;
  }
}

@media (max-width: $breakpoint-md) {
  .list-header,
  .list-row {
    grid-template-columns: 44px 1fr 100px;
  }
}

// 加载更多
.load-more {
  display: flex;
  justify-content: center;
  padding: $spacing-md 0;
}
</style>
