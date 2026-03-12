<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PostCard from '@/components/business/PostCard.vue'
import { postsApi } from '@/api/modules/posts'
import type { Post, Category } from '@/types/models'

const PAGE_SIZE = 12

type SortMode = 'latest' | 'hot'

const posts = ref<Post[]>([])
const categories = ref<Category[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(false)
const currentCategory = ref<number | null>(null)
const sortMode = ref<SortMode>('latest')

async function loadPosts(reset = false) {
  if (reset) {
    page.value = 1
    posts.value = []
    loading.value = true
  } else {
    loadingMore.value = true
  }
  try {
    const res = await postsApi.getPaginatedList({
      page: page.value,
      limit: PAGE_SIZE,
      category_id: currentCategory.value ?? undefined,
      sort: sortMode.value,
    })
    posts.value = reset ? res.items : [...posts.value, ...res.items]
    hasMore.value = page.value < (res.pagination as any).pages
  } catch {
    // 静默失败
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function loadMore() {
  page.value++
  await loadPosts()
}

function selectCategory(id: number | null) {
  if (currentCategory.value === id) return
  currentCategory.value = id
  loadPosts(true)
}

function selectSort(mode: SortMode) {
  if (sortMode.value === mode) return
  sortMode.value = mode
  loadPosts(true)
}

onMounted(async () => {
  try {
    const res = await postsApi.getCategories()
    if (res.data) categories.value = res.data
  } catch { /* 静默 */ }
  await loadPosts(true)
})
</script>

<template>
  <div class="blog-page">
    <div class="page-header">
      <h1 class="page-title">博客</h1>
    </div>

    <!-- 分类 + 排序 -->
    <div class="filter-bar">
      <div v-if="categories.length > 0" class="category-tabs">
        <button class="cat-tab" :class="{ active: currentCategory === null }" @click="selectCategory(null)">全部</button>
        <button
          v-for="cat in categories"
          :key="cat.id"
          class="cat-tab"
          :class="{ active: currentCategory === cat.id }"
          @click="selectCategory(cat.id)"
        >{{ cat.name }}</button>
      </div>
      <div class="sort-tabs">
        <button class="sort-tab" :class="{ active: sortMode === 'latest' }" @click="selectSort('latest')">最新</button>
        <button class="sort-tab" :class="{ active: sortMode === 'hot' }" @click="selectSort('hot')">最热</button>
      </div>
    </div>

    <!-- 加载骨架 -->
    <div v-if="loading" class="posts-grid">
      <el-skeleton v-for="i in PAGE_SIZE" :key="i" animated :rows="3" />
    </div>

    <!-- 文章网格 -->
    <div v-else-if="posts.length > 0" class="posts-grid">
      <PostCard v-for="post in posts" :key="post.id" :post="post" />
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无博文" />

    <!-- 加载更多 -->
    <div v-if="!loading && hasMore" class="load-more">
      <el-button :loading="loadingMore" @click="loadMore">加载更多</el-button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.blog-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-xl $spacing-lg;
}

.page-header {
  margin-bottom: $spacing-xl;

  .page-title {
    font-size: $font-2xl;
    font-weight: 700;
    color: var(--el-text-color-primary);
    margin: 0;
  }
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: $spacing-sm;
  margin-bottom: $spacing-xl;
}

.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;

  .cat-tab {
    padding: 6px 16px;
    border-radius: $radius-full;
    border: 1px solid var(--el-border-color);
    background: transparent;
    color: var(--el-text-color-secondary);
    font-size: $font-sm;
    cursor: pointer;
    transition: all $transition-fast;

    &:hover {
      border-color: $color-primary;
      color: $color-primary;
    }

    &.active {
      background: $color-primary;
      border-color: $color-primary;
      color: #fff;
    }
  }
}

.sort-tabs {
  display: flex;
  gap: 2px;
  background: var(--el-fill-color);
  border-radius: $radius-full;
  padding: 3px;

  .sort-tab {
    padding: 4px 14px;
    border-radius: $radius-full;
    border: none;
    background: transparent;
    color: var(--el-text-color-secondary);
    font-size: $font-sm;
    cursor: pointer;
    transition: all $transition-fast;

    &:hover { color: var(--el-text-color-primary); }

    &.active {
      background: var(--el-bg-color);
      color: $color-primary;
      font-weight: 500;
      box-shadow: $shadow-sm;
    }
  }
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-lg;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: $spacing-2xl;
}

@media (max-width: 900px) {
  .posts-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 560px) {
  .blog-page { padding: $spacing-md; }
  .posts-grid { grid-template-columns: 1fr; }
  .filter-bar { flex-direction: column; align-items: flex-start; }
}
</style>
