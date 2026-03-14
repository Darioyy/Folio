<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Setting, User, Document, Files, DataAnalysis, EditPen, ArrowLeft, Tickets } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/modules/auth'

const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

const activeMenu = computed(() => route.path)
const avatarTs = ref(Date.now())
const avatarUrl = computed(() => {
  const u = userStore.currentUser
  if (u?.avatar) return `${authApi.getAvatarUrl()}?t=${avatarTs.value}`
  return undefined
})
const avatarFallback = computed(() => {
  const u = userStore.currentUser
  return (u?.nickname || u?.username || 'A')[0].toUpperCase()
})

// 审核待处理数量从全局 store 读取（AppHeader 负责轮询，此处只读）
const reviewCount = computed(() => appStore.reviewCount)
</script>

<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <aside class="admin-aside">
      <div class="sidebar-brand">
        <router-link to="/" class="brand-back" title="返回首页">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回首页</span>
        </router-link>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/admin/dashboard" :class="['nav-item', { active: activeMenu === '/admin/dashboard' }]">
          <el-icon><DataAnalysis /></el-icon><span>概览</span>
        </router-link>
        <router-link to="/admin/users" :class="['nav-item', { active: activeMenu === '/admin/users' }]">
          <el-icon><User /></el-icon><span>用户</span>
        </router-link>
        <router-link to="/admin/blog" :class="['nav-item', { active: activeMenu === '/admin/blog' }]">
          <el-icon><Document /></el-icon><span>博文</span>
        </router-link>
        <router-link v-if="userStore.isRoot" to="/admin/content" :class="['nav-item', { active: activeMenu === '/admin/content' }]">
          <el-icon><Files /></el-icon><span>云盘</span>
        </router-link>
        <router-link to="/admin/review" :class="['nav-item', { active: activeMenu.startsWith('/admin/review') }]">
          <el-icon><Tickets /></el-icon><span>审核</span>
          <span v-if="reviewCount > 0" class="nav-dot" />
        </router-link>
        <router-link v-if="userStore.isRoot" to="/admin/site" :class="['nav-item', { active: activeMenu === '/admin/site' }]">
          <el-icon><EditPen /></el-icon><span>站点</span>
        </router-link>
        <router-link v-if="userStore.isRoot" to="/admin/settings" :class="['nav-item', { active: activeMenu === '/admin/settings' }]">
          <el-icon><Setting /></el-icon><span>设置</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="sidebar-user">
          <el-avatar :size="28" :src="avatarUrl" class="user-avatar">{{ avatarFallback }}</el-avatar>
          <span class="user-name">{{ userStore.currentUser?.nickname || userStore.currentUser?.username }}</span>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="admin-main">
      <router-view v-slot="{ Component }">
        <Transition name="admin-fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped lang="scss">
.admin-layout { display: flex; height: 100vh; overflow: hidden; }

.admin-aside {
  width: 184px;
  flex-shrink: 0;
  background: var(--color-surface, #fff);
  border-right: 1px solid var(--color-border, #e8eaed);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow-y: auto;

  html.dark & { background: #1c1f26; border-right-color: #2d3242; }
}

.sidebar-brand {
  display: flex;
  align-items: center;
  padding: 0 14px;
  height: 52px;
  border-bottom: 1px solid var(--color-border, #e8eaed);
  flex-shrink: 0;

  html.dark & { border-bottom-color: #2d3242; }
}

.brand-back {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: $font-sm;
  font-weight: 500;
  transition: color $transition-fast;

  .el-icon { font-size: 14px; }
  &:hover { color: $color-primary; }
}

.sidebar-nav { padding: 10px 8px; flex: 1; overflow-y: auto; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 8px 10px;
  border-radius: $radius-sm;
  font-size: $font-sm;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  margin-bottom: 1px;
  border-left: 2px solid transparent;
  transition: background $transition-fast, color $transition-fast, border-color $transition-fast;

  .el-icon { font-size: 15px; flex-shrink: 0; }

  &:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
  }

  &.active {
    background: var(--color-primary-subtle);
    color: var(--color-primary);
    font-weight: 600;
    border-left-color: var(--color-primary);
  }
}

.nav-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ef4444;
  flex-shrink: 0;
  margin-left: auto;
}

.sidebar-footer {
  border-top: 1px solid var(--color-border, #e8eaed);
  padding: 10px 8px;
  flex-shrink: 0;

  html.dark & { border-top-color: #2d3242; }
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 4px;
}

.user-avatar {
  flex-shrink: 0;
  background: linear-gradient(135deg, $color-primary, #7c3aed);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

.user-name {
  font-size: $font-13;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}


.admin-main {
  flex: 1;
  min-width: 0;
  background: #f5f6fa;
  padding: 28px 28px 24px;
  overflow-y: auto;

  html.dark & { background: #141720; }

  // 顶部 title 与卡片统一边距
  :deep(.el-card) {
    border-radius: $radius-lg;
    border-color: var(--color-border);

    .el-card__header {
      padding: 14px 20px;
      font-size: $font-sm;
      font-weight: 600;
    }

    .el-card__body { padding: 0; }
  }

  // toolbar 区域统一
  :deep(.toolbar) {
    padding: 14px 20px;
    border-bottom: 1px solid var(--color-border);
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    flex-wrap: wrap;
  }
}

.admin-fade-enter-active {
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}
.admin-fade-leave-active {
  transition: opacity 0.13s ease, transform 0.13s ease;
}
.admin-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.admin-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

// 统一卡片和表格暗模式
:deep(.el-card),
:deep(.el-table) {
  html.dark & {
    --el-bg-color: #1c1f26;
    --el-fill-color-blank: #1c1f26;
    --el-border-color: #2d3242;
  }
}

// 表格行高
:deep(.el-table) {
  .el-table__body-wrapper .el-table__body .el-table__row .el-table__cell {
    padding: 8px 0;
    min-height: 40px;
    height: auto;
    .cell { padding: 0 12px; min-height: 24px; line-height: 24px; word-break: break-word; }
  }
  .el-table__header-wrapper .el-table__header .el-table__cell {
    padding: 12px 0;
    .cell { padding: 0 12px; line-height: 24px; font-weight: 600; }
  }
  .el-table__cell.is-left .cell,
  .el-table__cell.is-center .cell,
  .el-table__cell.is-right .cell { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .el-table__cell:nth-child(3) .cell { white-space: normal; word-break: break-word; }
}

// 操作列按钮对齐
:deep(.el-table) {
  .el-table__cell .el-button { vertical-align: middle; }
  .el-table__body-wrapper .el-table__body .el-table__row .el-table__cell:last-child .cell {
    display: flex; align-items: center; justify-content: flex-start; gap: 4px; height: 32px;
  }
  .el-button.is-link {
    padding: 6px 10px;
    font-size: 13px;
    font-weight: 500;
    border: none;
    background: transparent !important;
    transition: all 0.2s;
    height: auto;
    line-height: 1.5;
    display: inline-flex;
    align-items: center;

    html.dark &.el-button--primary { color: #a5b4fc; &:hover { color: #c7d2fe; } }
    html.dark &.el-button--danger  { color: #fca5a5; &:hover { color: #fecaca; } }
    html.dark &.el-button--info    { color: #94a3b8; &:hover { color: #cbd5e1; } }
    html:not(.dark) &.el-button--primary { color: #8b5cf6; &:hover { color: #7c3aed; } }
    html:not(.dark) &.el-button--danger  { color: #f87171; &:hover { color: #ef4444; } }
    html:not(.dark) &.el-button--info    { color: #6b7280; &:hover { color: #4b5563; } }

    .el-icon { margin-right: 4px; font-size: 14px; }
  }
}


// 下拉菜单
:deep(.el-dropdown-menu) {
  .el-dropdown-menu__item {
    display: flex; align-items: center; gap: 8px; padding: 10px 16px; min-height: 40px;
    .el-icon { font-size: 16px; }
  }
  .el-dropdown-menu__item--divided {
    position: relative; margin-top: 0;
    &::before { content: ''; position: absolute; left: 0; right: 0; top: 0; height: 1px; background: var(--el-border-color-lighter); }
  }
}
</style>
