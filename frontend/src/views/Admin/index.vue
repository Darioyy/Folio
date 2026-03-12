<template>
  <div class="admin-layout">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside :width="collapsed ? '64px' : '200px'" class="admin-aside">
        <div class="admin-logo" @click="goToHome">
          <h1 v-if="!collapsed">Folio</h1>
          <span v-else class="logo-icon">F</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          :collapse="collapsed"
          router
        >
          <el-menu-item index="/admin/dashboard">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据概览</span>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/blog">
            <el-icon><Document /></el-icon>
            <span>博客管理</span>
          </el-menu-item>
          <el-menu-item v-if="userStore.isRoot" index="/admin/content">
            <el-icon><Files /></el-icon>
            <span>文件管理</span>
          </el-menu-item>
          <el-menu-item v-if="userStore.isRoot" index="/admin/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容 -->
      <el-container>
        <el-header>
          <div class="header-left">
            <el-button
              :icon="collapsed ? Expand : Fold"
              circle
              text
              @click="toggleCollapsed"
            />
            <el-breadcrumb separator="/">
              <el-breadcrumb-item>后台管理</el-breadcrumb-item>
              <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <!-- 暗黑模式切换 -->
            <el-button
              :icon="isDarkMode ? Sunny : Moon"
              circle
              text
              @click="toggleDarkMode"
              class="theme-toggle"
            />

            <el-dropdown trigger="hover" :show-timeout="60" :hide-timeout="200" :popper-options="{ modifiers: [{ name: 'offset', options: { offset: [0, 4] } }] }">
              <div class="user-dropdown-trigger">
                <UserAvatar :src="avatarUrl" :user="userStore.currentUser" :size="36" />
                <span class="user-name-display">{{ displayName }}</span>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="goToHome">
                    <el-icon><HomeFilled /></el-icon>
                    首页
                  </el-dropdown-item>
                  <el-dropdown-item @click="goToSettings">
                    <el-icon><Setting /></el-icon>
                    账户设置
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleLogout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  Setting, User, Document, Files, DataAnalysis,
  Expand, Fold, HomeFilled, UserFilled, SwitchButton,
  Sunny, Moon
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/modules/auth'
import UserAvatar from '@/components/common/UserAvatar.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

const collapsed = ref(false)
const isDarkMode = computed(() => appStore.isDarkMode)

const activeMenu = computed(() => route.path)

const currentTitle = computed(() => {
  const titles: Record<string, string> = {
    '/admin/dashboard': '数据概览',
    '/admin/users': '用户管理',
    '/admin/blog': '博客管理',
    '/admin/posts': '文章管理',
    '/admin/content': '文件管理',
    '/admin/settings': '系统设置',
  }
  return titles[route.path] || '后台管理'
})

// 显示名称（优先显示昵称）
const displayName = computed(() => {
  const user = userStore.currentUser
  return user?.nickname || user?.username || ''
})

// 头像 URL
const avatarUrl = computed(() => {
  const user = userStore.currentUser
  if (user?.avatar) {
    const baseUrl = authApi.getAvatarUrl()
    const timestamp = new Date(user.updated_at).getTime()
    return `${baseUrl}?uid=${user.id}&t=${timestamp}`
  }
  return undefined
})

function toggleCollapsed() {
  collapsed.value = !collapsed.value
}

function toggleDarkMode() {
  appStore.toggleDarkMode()
}

function goToHome() {
  router.push({ name: 'Home' })
}

function goToSettings() {
  router.push({ name: 'Settings' })
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userStore.logout()
    router.push({ name: 'Login' })
  } catch {
    // 取消退出
  }
}
</script>

<style scoped lang="scss">
.admin-layout {
  height: 100vh;

  :deep(.el-container) {
    height: 100%;
  }
}

.admin-aside {
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  transition: width 0.3s;

  html.dark & {
    background: #1e293b;
    border-right-color: #334155;
  }

  .admin-logo {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid var(--el-border-color);
    cursor: pointer;
    transition: all 0.2s;

    html.dark & {
      border-bottom-color: #334155;
    }

    &:hover {
      background: rgba(99, 102, 241, 0.05);
    }

    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 700;
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: -0.5px;
    }

    .logo-icon {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      font-weight: 700;
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      color: white;
      border-radius: 8px;
    }
  }

  .el-menu {
    border-right: none;
    background: transparent;

    .el-menu-item {
      &:hover {
        background: rgba(99, 102, 241, 0.05);
      }

      &.is-active {
        background: rgba(99, 102, 241, 0.1);
        color: #6366f1;
      }
    }
  }
}

.el-header {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $spacing-lg;
  height: 64px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.9);

  html.dark & {
    background: rgba(15, 23, 42, 0.9);
    border-bottom-color: #334155;
  }
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.theme-toggle {
  color: var(--el-text-color-secondary);

  &:hover {
    color: #6366f1;
    background: rgba(99, 102, 241, 0.08);
  }
}

.user-dropdown-trigger {
  cursor: pointer;
  padding: 6px 12px;
  border-radius: $radius-full;
  transition: all $transition-base;
  display: flex;
  align-items: center;
  gap: $spacing-sm;

  &:hover {
    background: var(--el-fill-color-light);
  }
}

.user-name-display {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  @media (max-width: $breakpoint-md) {
    display: none;
  }
}

.el-main {
  background: #f9fafb;
  padding: 24px;

  html.dark & {
    background: #0f172a;
  }
}

// 统一卡片和表格样式
:deep(.el-card),
:deep(.el-table) {
  html.dark & {
    --el-bg-color: #1e293b;
    --el-fill-color-blank: #1e293b;
    --el-border-color: #334155;
  }
}

// 表格行高和单元格样式
:deep(.el-table) {
  .el-table__body-wrapper {
    .el-table__body {
      .el-table__row {
        .el-table__cell {
          padding: 12px 0;
          min-height: 48px;
          height: auto;

          .cell {
            padding: 0 12px;
            min-height: 24px;
            line-height: 24px;
            word-break: break-word;
          }
        }
      }
    }
  }

  .el-table__header-wrapper {
    .el-table__header {
      .el-table__cell {
        padding: 12px 0;
        min-height: 48px;

        .cell {
          padding: 0 12px;
          min-height: 24px;
          line-height: 24px;
          font-weight: 600;
        }
      }
    }
  }

  // 确保固定宽度的列不会变化
  .el-table__cell.is-left,
  .el-table__cell.is-center,
  .el-table__cell.is-right {
    .cell {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }

  // 昵称列可能较长，允许换行
  .el-table__cell:nth-child(3) {
    .cell {
      white-space: normal;
      word-break: break-word;
    }
  }
}

// 统一操作按钮样式
:deep(.el-table) {
  // 表格单元格对齐
  .el-table__cell {
    .el-button {
      vertical-align: middle;
    }
  }

  // 操作列样式
  .el-table__body-wrapper {
    .el-table__body {
      .el-table__row {
        .el-table__cell:last-child {
          .cell {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 4px;
            height: 32px;
          }
        }
      }
    }
  }

  .el-button {
    &.is-link {
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

      html.dark &.el-button--primary {
        color: #a5b4fc;

        &:hover {
          color: #c7d2fe;
        }
      }

      html.dark &.el-button--danger {
        color: #fca5a5;

        &:hover {
          color: #fecaca;
        }
      }

      html.dark &.el-button--info {
        color: #94a3b8;

        &:hover {
          color: #cbd5e1;
        }
      }

      html:not(.dark) &.el-button--primary {
        color: #8b5cf6;

        &:hover {
          color: #7c3aed;
        }
      }

      html:not(.dark) &.el-button--danger {
        color: #f87171;

        &:hover {
          color: #ef4444;
        }
      }

      html:not(.dark) &.el-button--info {
        color: #6b7280;

        &:hover {
          color: #4b5563;
        }
      }

      .el-icon {
        margin-right: 4px;
        font-size: 14px;
      }
    }
  }
}

// 下拉菜单样式
:deep(.el-dropdown-menu) {
  .el-dropdown-menu__item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    min-height: 40px;

    .el-icon {
      font-size: 16px;
    }
  }

  // 移除分隔线的额外间距，确保所有选项高度一致
  .el-dropdown-menu__item--divided {
    position: relative;
    margin-top: 0;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      right: 0;
      top: 0;
      height: 1px;
      background: var(--el-border-color-lighter);
    }
  }
}
</style>
