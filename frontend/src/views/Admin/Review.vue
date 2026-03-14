<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import ReportsPanel from './Reports.vue'
import FeedbackPanel from './Feedback.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 通过 hash 或 query 保持 tab 状态
const tab = ref<'reports' | 'feedback'>('reports')

function switchTab(t: 'reports' | 'feedback') {
  tab.value = t
  router.replace({ query: { tab: t } })
}

onMounted(() => {
  const q = route.query.tab
  if (q === 'feedback' && userStore.isRoot) tab.value = 'feedback'
})
</script>

<template>
  <div class="review-page">
    <!-- Tab 导航 -->
    <nav class="review-tabs">
      <button
        :class="['rtab', { active: tab === 'reports' }]"
        @click="switchTab('reports')"
      >
        举报审核
      </button>
      <button
        v-if="userStore.isRoot"
        :class="['rtab', { active: tab === 'feedback' }]"
        @click="switchTab('feedback')"
      >
        建议审核
      </button>
    </nav>

    <!-- Tab 内容 -->
    <div class="review-body">
      <ReportsPanel v-if="tab === 'reports'" />
      <FeedbackPanel v-else-if="tab === 'feedback' && userStore.isRoot" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.review-page {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.review-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border, #e8eaed);
  padding: 0 4px;
  background: var(--color-surface, #fff);
  flex-shrink: 0;
  margin-bottom: 20px;

  html.dark & { border-bottom-color: #2d3242; }
}

.rtab {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 11px 14px 10px;
  font-size: $font-sm;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  cursor: pointer;
  transition: color $transition-fast, border-color $transition-fast;

  &:hover { color: var(--color-text-primary); }

  &.active {
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
    font-weight: 600;
  }
}

// 子页面样式覆盖（去掉内部卡片/外边距）
.review-body {
  flex: 1;
  min-height: 0;

  :deep(.reports-page),
  :deep(.feedback-page) {
    max-width: none;
  }

  // Feedback page header 已有 margin-bottom，与 tab 会重复，调整一下
  :deep(.page-header) {
    margin-bottom: $spacing-md;
  }
}
</style>
