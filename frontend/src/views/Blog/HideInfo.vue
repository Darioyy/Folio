<template>
  <div class="hide-info-page">
    <div v-if="loading" class="loading-box" v-loading="true" />

    <div v-else-if="post" class="page-container">
      <div class="page-header">
        <button class="back-btn" @click="router.push('/space')">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 3L5 8l5 5"/>
          </svg>
          返回我的空间
        </button>
      </div>

      <div class="notice-card">
        <div class="notice-icon">
          <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 8v4M12 16h.01"/>
          </svg>
        </div>
        <div class="notice-main">
          <h2 class="notice-title">博文已被管理员隐藏</h2>
          <p class="notice-subtitle">你的博文因违规内容已从公开列表撤下，仅你可见</p>
        </div>
      </div>

      <div class="content-card">
        <h3 class="card-title">博文信息</h3>
        <p class="post-title-text">{{ post.title }}</p>
        <p class="post-meta-text">发布于 {{ formatDate(post.published_at || post.created_at) }}</p>
      </div>

      <div class="reason-card">
        <h3 class="card-title">隐藏原因</h3>
        <p class="reason-text">{{ post.hide_reason || '违反社区规范' }}</p>
      </div>

      <!-- 审核中 -->
      <div v-if="post.review_status === 'pending'" class="status-card pending">
        <div class="status-icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
        </div>
        <div>
          <p class="status-title">申诉审核中</p>
          <p class="status-desc">你的申诉已提交，管理员正在处理，请耐心等待</p>
        </div>
      </div>

      <!-- 申诉被拒绝 -->
      <div v-else-if="post.review_status === 'rejected'" class="status-card rejected">
        <div class="status-icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M9 9l6 6M15 9l-6 6"/></svg>
        </div>
        <div>
          <p class="status-title">申诉已被拒绝</p>
          <p class="status-desc">你可以修改内容后重新申诉</p>
        </div>
      </div>

      <!-- 申诉表单 -->
      <div v-if="post.review_status !== 'pending'" class="appeal-card">
        <h3 class="card-title">
          {{ post.review_status === 'rejected' ? '重新申诉' : '提交申诉' }}
        </h3>
        <p class="appeal-desc">
          如果你认为博文内容符合社区规范，可以向管理员提交申诉。申诉通过后，博文将重新公开。
        </p>
        <el-input
          v-model="appealReason"
          type="textarea"
          :rows="4"
          placeholder="请详细说明申诉理由，例如：内容符合社区规范，原因如下..."
          maxlength="500"
          show-word-limit
          resize="none"
          class="appeal-input"
        />
        <el-button
          type="primary"
          :loading="appealing"
          :disabled="!appealReason.trim()"
          @click="submitAppeal"
        >提交申诉</el-button>
      </div>
    </div>

    <div v-else class="error-box">
      <el-empty description="博文不存在或无权访问" />
      <el-button @click="router.push('/space')">返回空间</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { postsApi } from '@/api/modules/posts'
import { useUserStore } from '@/stores/user'
import { formatDate } from '@/utils/format'
import type { Post } from '@/types/models'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const post = ref<Post | null>(null)
const loading = ref(true)
const appealReason = ref('')
const appealing = ref(false)

async function load() {
  loading.value = true
  try {
    const id = Number(route.params.id)
    const res = await postsApi.getDetail(id)
    if (!res.success || !res.data) {
      loading.value = false
      return
    }
    const p = res.data as any
    // 只允许作者访问
    if (!userStore.isLoggedIn || (userStore.currentUser?.id !== p.author_id && !userStore.isAdminOrRoot)) {
      router.push('/blog')
      return
    }
    post.value = p
  } catch {
    // not found
  } finally {
    loading.value = false
  }
}

async function submitAppeal() {
  if (!post.value || !appealReason.value.trim()) return
  appealing.value = true
  try {
    const res = await postsApi.appeal(post.value.id, appealReason.value.trim())
    if (res.success) {
      ElMessage.success('申诉已提交，管理员将尽快处理')
      ;(post.value as any).review_status = 'pending'
      appealReason.value = ''
    }
  } catch {
    ElMessage.error('申诉提交失败，请稍后重试')
  } finally {
    appealing.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
.hide-info-page {
  max-width: 640px;
  margin: 0 auto;
  padding: $spacing-xl $spacing-md $spacing-2xl;
}

.loading-box { height: 300px; }
.error-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-2xl 0;
}

.page-header { margin-bottom: $spacing-lg; }

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: none;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  font-size: $font-sm;
  padding: 0;
  &:hover { color: $color-primary; }
}

.notice-card {
  display: flex;
  align-items: flex-start;
  gap: $spacing-md;
  padding: $spacing-lg;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: $radius-lg;
  margin-bottom: $spacing-md;
}

.notice-icon { flex-shrink: 0; }

.notice-title {
  font-size: 18px;
  font-weight: 700;
  color: #b91c1c;
  margin: 0 0 4px;
}

.notice-subtitle {
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.content-card,
.reason-card,
.appeal-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
}

.card-title {
  font-size: $font-sm;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 $spacing-sm;
}

.post-title-text {
  font-size: $font-lg;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 4px;
}

.post-meta-text {
  font-size: $font-xs;
  color: var(--el-text-color-placeholder);
  margin: 0;
}

.reason-text {
  font-size: $font-sm;
  color: var(--el-text-color-regular);
  line-height: 1.7;
  margin: 0;
}

.status-card {
  display: flex;
  align-items: flex-start;
  gap: $spacing-md;
  padding: $spacing-md $spacing-lg;
  border-radius: $radius-lg;
  margin-bottom: $spacing-md;

  &.pending {
    background: rgba(234, 179, 8, 0.06);
    border: 1px solid rgba(234, 179, 8, 0.25);
    color: #92400e;
  }

  &.rejected {
    background: rgba(239, 68, 68, 0.05);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #991b1b;
  }
}

.status-icon { flex-shrink: 0; margin-top: 2px; }

.status-title {
  font-size: $font-sm;
  font-weight: 600;
  margin: 0 0 2px;
}

.status-desc {
  font-size: $font-xs;
  opacity: 0.8;
  margin: 0;
}

.appeal-desc {
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  margin: 0 0 $spacing-md;
  line-height: 1.6;
}

.appeal-input { margin-bottom: $spacing-md; }
</style>
