<template>
  <div class="search-page">
    <AppHeader />

    <div class="search-container">
      <!-- 搜索头部 -->
      <div class="search-header">
        <h1 class="search-title">
          搜索结果
          <span v-if="query" class="search-query">「{{ query }}」</span>
        </h1>

        <!-- 类型 Tab -->
        <div class="type-tabs">
          <span
            v-for="tab in typeTabs"
            :key="tab.value"
            :class="['tab-item', { active: currentType === tab.value }]"
            @click="switchType(tab.value)"
          >{{ tab.label }}</span>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="loading-wrap">
        <el-skeleton :rows="6" animated />
      </div>

      <!-- 结果为空 -->
      <div v-else-if="!hasResults" class="empty-state">
        <el-empty
          :description="query ? `没有找到「${query}」的相关内容` : '请输入搜索关键词'"
          :image-size="80"
        />
        <router-link v-if="query" to="/blog" class="empty-discover-link">去发现页探索 →</router-link>
      </div>

      <template v-else>
        <!-- 文件结果 -->
        <div v-if="currentType !== 'user' && files.length > 0" class="result-section">
          <div v-if="currentType === 'all'" class="section-title">文件</div>
          <div class="files-grid">
            <FileCard
              v-for="file in files"
              :key="file.id"
              :file="file"
              :show-author="true"
            />
          </div>
        </div>
        <el-empty
          v-else-if="currentType === 'file' && files.length === 0"
          description="没有找到相关文件"
          class="empty-state"
        />

        <!-- 用户结果 -->
        <div v-if="currentType !== 'file' && users.length > 0" class="result-section">
          <div v-if="currentType === 'all'" class="section-title">用户</div>
          <div class="users-grid">
            <div
              v-for="u in users"
              :key="u.id"
              class="user-card"
              @click="router.push({ name: 'UserProfile', params: { username: u.username } })"
            >
              <el-avatar :src="getUserAvatarUrl(u.username)" :size="48" class="user-avatar">
                {{ u.nickname?.[0] || u.username?.[0] || '?' }}
              </el-avatar>
              <div class="user-info">
                <p class="user-name">{{ u.nickname || u.username }}</p>
                <p class="user-username">@{{ u.username }}</p>
              </div>
            </div>
          </div>
        </div>
        <el-empty
          v-else-if="currentType === 'user' && users.length === 0"
          description="没有找到相关用户"
          class="empty-state"
        />
      </template>

      <!-- 加载更多 -->
      <div v-if="hasMore && !loading" class="load-more">
        <el-button @click="loadMore" :loading="loadingMore">加载更多</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import FileCard from '@/components/business/FileCard.vue'
import { searchApi } from '@/api/modules/search'
import type { FileItem } from '@/types/models'

const route = useRoute()
const router = useRouter()

type SearchType = 'all' | 'file' | 'user'

interface UserResult {
  id: number
  username: string
  nickname: string
  avatar?: string
}

const typeTabs = [
  { value: 'all' as SearchType, label: '全部' },
  { value: 'file' as SearchType, label: '文件' },
  { value: 'user' as SearchType, label: '用户' },
]

const query = computed(() => (route.query.q as string) || '')
const currentType = ref<SearchType>((route.query.type as SearchType) || 'all')

const loading = ref(false)
const loadingMore = ref(false)
const files = ref<FileItem[]>([])
const users = ref<UserResult[]>([])
const page = ref(1)
const fileTotal = ref(0)
const userTotal = ref(0)

const hasResults = computed(() => files.value.length > 0 || users.value.length > 0)

const hasMore = computed(() => {
  if (currentType.value === 'file') return files.value.length < fileTotal.value
  if (currentType.value === 'user') return users.value.length < userTotal.value
  return files.value.length < fileTotal.value || users.value.length < userTotal.value
})

function getUserAvatarUrl(username: string) {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/users/username/${username}/avatar/view`
}

async function doSearch(reset = true) {
  if (!query.value.trim()) return

  if (reset) {
    page.value = 1
    files.value = []
    users.value = []
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    const res = await searchApi.search(query.value, currentType.value, page.value, 20)
    const data = res.data || {}

    if (reset) {
      files.value = data.files || []
      users.value = data.users || []
      fileTotal.value = data.file_total || 0
      userTotal.value = data.user_total || 0
    } else {
      files.value.push(...(data.files || []))
      users.value.push(...(data.users || []))
    }
  } catch {
    // 静默失败
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function switchType(type: SearchType) {
  currentType.value = type
  router.replace({ query: { ...route.query, type } })
  doSearch(true)
}

async function loadMore() {
  page.value++
  await doSearch(false)
}

watch(() => route.query.q, () => {
  doSearch(true)
})

onMounted(() => {
  doSearch(true)
})
</script>

<style scoped lang="scss">
.search-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.search-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-lg $spacing-md;
  width: 100%;
}

.search-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
}

.search-title {
  font-size: $font-xl;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0;
}

.search-query {
  color: $color-primary;
}

.type-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
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

.loading-wrap {
  padding: $spacing-xl 0;
}

.empty-state {
  padding: $spacing-xl 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-discover-link {
  margin-top: $spacing-sm;
  font-size: $font-sm;
  color: $color-primary;
  text-decoration: none;
  opacity: 0.8;
  transition: opacity $transition-fast;

  &:hover { opacity: 1; }
}

.result-section {
  margin-bottom: $spacing-xl;
}

.section-title {
  font-size: $font-base;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: $spacing-md;
  padding-bottom: $spacing-xs;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: $spacing-md;
}

.users-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: $spacing-md;
}

.user-card {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md;
  background: var(--el-bg-color);
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  cursor: pointer;
  transition: box-shadow $transition-fast, transform $transition-fast;

  &:hover {
    box-shadow: $shadow-md;
    transform: translateY(-2px);
  }
}

.user-avatar {
  flex-shrink: 0;
  background: linear-gradient(135deg, $color-primary, $color-secondary);
  color: white;
  font-weight: 600;
}

.user-info {
  min-width: 0;
}

.user-name {
  font-size: $font-sm;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-username {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.load-more {
  display: flex;
  justify-content: center;
  padding-top: $spacing-lg;
}

@media (max-width: $breakpoint-md) {
  .search-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .files-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: $spacing-sm;
  }

  .users-grid {
    grid-template-columns: 1fr;
  }
}
</style>
