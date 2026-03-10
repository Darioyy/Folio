<template>
  <div class="posts-page">
    <div class="container">
      <div class="page-header">
        <h1>文章列表</h1>
      </div>

      <el-empty v-if="posts.length === 0 && !loading" description="暂无文章" />

      <div v-else class="posts-grid">
        <el-card
          v-for="post in posts"
          :key="post.id"
          class="post-card"
          shadow="hover"
          @click="goToDetail(post.id)"
        >
          <h3 class="post-title">{{ post.title }}</h3>
          <div class="post-meta">
            <el-tag size="small">{{ post.category_name || '未分类' }}</el-tag>
            <span class="meta-item">
              <el-icon><User /></el-icon>
              {{ post.author_name || '匿名' }}
            </span>
            <span class="meta-item">
              <el-icon><View /></el-icon>
              {{ post.view_count }}
            </span>
            <span class="meta-item">
              <el-icon><Clock /></el-icon>
              {{ formatDate(post.created_at) }}
            </span>
          </div>
          <p class="post-summary">{{ truncate(post.content, 100) }}...</p>
        </el-card>
      </div>

      <div v-if="posts.length > 0" class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadPosts"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, View, Clock } from '@element-plus/icons-vue'
import { postsApi } from '@/api/modules/posts'
import { formatDate, truncate } from '@/utils/format'

const router = useRouter()

const posts = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

async function loadPosts(page = 1) {
  loading.value = true
  try {
    const res = await postsApi.getList({
      page,
      limit: pageSize.value,
      status: 'published'
    })
    posts.value = res.data || []
    // 注意：后端当前返回格式不包含 total，这里需要根据实际调整
  } catch {
    posts.value = []
  } finally {
    loading.value = false
  }
}

function goToDetail(id: number) {
  router.push({ name: 'PostDetail', params: { id } })
}

onMounted(() => {
  loadPosts()
})
</script>

<style scoped lang="scss">
.posts-page {
  .page-header {
    margin-bottom: $spacing-lg;
  }
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: $spacing-lg;
  margin-bottom: $spacing-xl;
}

.post-card {
  cursor: pointer;
  transition: $transition-base;
  height: 100%;

  &:hover {
    transform: translateY(-4px);
  }

  :deep(.el-card__body) {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
}

.post-title {
  font-size: 18px;
  margin-bottom: $spacing-sm;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-wrap: wrap;
  margin-bottom: $spacing-md;
  color: var(--el-text-color-secondary);
  font-size: 14px;

  .meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

.post-summary {
  color: var(--el-text-color-secondary);
  line-height: 1.6;
  margin-top: auto;
}

.pagination-container {
  display: flex;
  justify-content: center;
}
</style>
