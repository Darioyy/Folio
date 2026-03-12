<template>
  <div class="post-detail-page">
    <div class="container">
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>

      <el-card v-else-if="post" shadow="never">
        <!-- 文章标题 -->
        <h1 class="post-title">{{ post.title }}</h1>

        <!-- 文章元信息 -->
        <div class="post-meta">
          <el-tag>{{ post.category_name || '未分类' }}</el-tag>
          <span class="meta-item">
            <el-icon><User /></el-icon>
            {{ post.author_name || '匿名' }}
          </span>
          <span class="meta-item">
            <el-icon><View /></el-icon>
            {{ post.view_count }} 次浏览
          </span>
          <span class="meta-item">
            <el-icon><Clock /></el-icon>
            {{ formatDate(post.created_at) }}
          </span>
        </div>

        <el-divider />

        <!-- 文章内容 -->
        <div class="post-content" v-html="renderContent(post.content)" />

        <!-- 文章操作 -->
        <div class="post-actions">
          <el-button @click="goBack">返回列表</el-button>
        </div>
      </el-card>

      <el-empty v-else description="文章不存在或已被删除" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { User, View, Clock } from '@element-plus/icons-vue'
import { postsApi } from '@/api/modules/posts'
import { formatDate } from '@/utils/format'
import { escapeHtml } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const post = ref<any>(null)
const loading = ref(true)

async function loadPost() {
  loading.value = true
  try {
    const id = Number(route.params.id)
    const res = await postsApi.getDetail(id)
    post.value = res.data
  } catch {
    post.value = null
  } finally {
    loading.value = false
  }
}

function renderContent(content: string) {
  // 简单的 Markdown 转换（可以用 marked.js 替代）
  let html = escapeHtml(content)
  // 转换换行
  html = html.replace(/\n/g, '<br>')
  // 转换标题
  html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>')
  html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>')
  html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>')
  return html
}

function goBack() {
  router.push({ name: 'Posts' })
}

onMounted(() => {
  loadPost()
})
</script>

<style scoped lang="scss">
.post-detail-page {
  .container {
    max-width: 800px;
  }
}

.loading-container {
  padding: $spacing-lg;
}

.post-title {
  font-size: 32px;
  margin-bottom: $spacing-md;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  flex-wrap: wrap;
  color: var(--el-text-color-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.post-content {
  font-size: 16px;
  line-height: 1.8;
  color: var(--el-text-color-primary);

  :deep(h1) {
    font-size: 28px;
    margin-top: $spacing-lg;
    margin-bottom: $spacing-md;
  }

  :deep(h2) {
    font-size: 24px;
    margin-top: $spacing-lg;
    margin-bottom: $spacing-md;
  }

  :deep(h3) {
    font-size: 20px;
    margin-top: $spacing-md;
    margin-bottom: $spacing-sm;
  }

  :deep(p) {
    margin-bottom: $spacing-md;
  }

  :deep(code) {
    background: var(--el-fill-color-light);
    padding: 2px 6px;
    border-radius: $radius-sm;
    font-family: 'Courier New', monospace;
  }

  :deep(pre) {
    background: var(--el-fill-color-light);
    padding: $spacing-md;
    border-radius: $radius-md;
    overflow-x: auto;
    margin-bottom: $spacing-md;
  }
}

.post-actions {
  margin-top: $spacing-xl;
  padding-top: $spacing-lg;
  border-top: 1px solid var(--el-border-color);
}
</style>
