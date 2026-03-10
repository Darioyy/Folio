<template>
  <el-dialog
    v-model="visible"
    title="存储空间详情"
    width="500px"
    @close="handleClose"
  >
    <div class="storage-detail">
      <!-- 总览 -->
      <div class="storage-overview">
        <div class="overview-item">
          <span class="overview-label">已用空间</span>
          <span class="overview-value used">{{ formatSize(storageInfo.storage_used) }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">总空间</span>
          <span class="overview-value">{{ formatSize(storageInfo.storage_quota) }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">使用率</span>
          <span class="overview-value" :class="getUsageClass()">
            {{ storageInfo.storage_percentage }}%
          </span>
        </div>
      </div>

      <!-- 分类统计 -->
      <div class="storage-categories">
        <h4 class="categories-title">分类统计</h4>
        <div v-loading="loading" class="categories-list">
          <div
            v-for="item in sortedCategories"
            :key="item.type"
            class="category-item"
          >
            <div class="category-icon">
              <el-icon :size="24">
                <component :is="getIcon(item.type)" />
              </el-icon>
            </div>
            <div class="category-info">
              <span class="category-name">{{ item.name }}</span>
              <span class="category-count">{{ item.count }} 个</span>
            </div>
            <div class="category-size">
              <span class="size-value">{{ formatSize(item.size) }}</span>
              <span class="size-percent">占用 {{ getPercent(item.size) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="storage-progress">
        <el-progress
          :percentage="Number(storageInfo.storage_percentage)"
          :color="progressColor"
          :stroke-width="12"
        />
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button type="primary" @click="goToCleanup">清理文件</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { Document, Picture, VideoPlay, Folder } from '@element-plus/icons-vue'
import type { StorageInfo } from '@/api/modules/hub'
import { hubApi } from '@/api/modules/hub'
import { authApi } from '@/api/modules/auth'

interface Props {
  modelValue: boolean
  storageInfo: StorageInfo
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const router = useRouter()
const loading = ref(false)

// 分类数据
const categories = ref([
  { type: 'image', name: '图片', size: 0, count: 0, icon: markRaw(Picture) },
  { type: 'video', name: '视频', size: 0, count: 0, icon: markRaw(VideoPlay) },
  { type: 'document', name: '文章', size: 0, count: 0, icon: markRaw(Document) },
  { type: 'resource', name: '资源', size: 0, count: 0, icon: markRaw(Folder) }
])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 按大小排序的分类
const sortedCategories = computed(() => {
  return [...categories.value].sort((a, b) => b.size - a.size)
})

// 进度条颜色
const progressColor = computed(() => {
  const p = props.storageInfo.storage_percentage
  if (p >= 90) return '#ef4444'
  if (p >= 70) return '#f59e0b'
  return '#10b981'
})

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// 获取百分比（占总存储空间）
function getPercent(size: number): number {
  if (props.storageInfo.storage_quota === 0) return 0
  return Math.round((size / props.storageInfo.storage_quota) * 100)
}

// 获取使用率样式类
function getUsageClass(): string {
  const p = props.storageInfo.storage_percentage
  if (p >= 90) return 'danger'
  if (p >= 70) return 'warning'
  return 'normal'
}

// 获取图标
function getIcon(type: string) {
  const item = categories.value.find(c => c.type === type)
  return item?.icon || markRaw(Document)
}

// 加载分类统计数据
async function loadCategories() {
  loading.value = true
  try {
    const res = await authApi.getStorageCategories()
    const iconMap: Record<string, any> = {
      image: markRaw(Picture),
      video: markRaw(VideoPlay),
      document: markRaw(Document),
      resource: markRaw(Folder)
    }
    categories.value = res.data.map(item => ({
      ...item,
      icon: iconMap[item.type] || markRaw(Document)
    }))
  } catch (error) {
    console.error('加载分类统计失败', error)
  } finally {
    loading.value = false
  }
}

// 关闭对话框
function handleClose() {
  visible.value = false
}

// 跳转到清理页面
function goToCleanup() {
  visible.value = false
  router.push({ name: 'HubPrivate' })
}

// 监听对话框打开
import { watch } from 'vue'
watch(() => props.modelValue, (val) => {
  if (val) {
    loadCategories()
  }
})
</script>

<style scoped lang="scss">
.storage-detail {
  padding: 8px 0;
}

.storage-overview {
  display: flex;
  justify-content: space-around;
  padding: 16px 0;
  background: var(--el-fill-color-light);
  border-radius: 12px;
  margin-bottom: 24px;

  .overview-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .overview-label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }

  .overview-value {
    font-size: 20px;
    font-weight: 600;

    &.used {
      color: #6366f1;
    }

    &.normal {
      color: #10b981;
    }

    &.warning {
      color: #f59e0b;
    }

    &.danger {
      color: #ef4444;
    }

    html.dark & {
      &.used {
        color: #818cf8;
      }
    }
  }
}

.storage-categories {
  .categories-title {
    font-size: 15px;
    font-weight: 600;
    margin: 0 0 16px 0;
    color: var(--el-text-color-primary);
  }

  .categories-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
}

.category-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 10px;
  transition: all 0.2s;

  &:hover {
    background: var(--el-fill-color-light);
  }

  .category-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 10px;
    color: white;
    flex-shrink: 0;
  }

  .category-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;

    .category-name {
      font-size: 14px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }

    .category-count {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }

  .category-size {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;

    .size-value {
      font-size: 14px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .size-percent {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.storage-progress {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
