<template>
  <header class="app-header">
    <div class="container header-container">
      <!-- Logo -->
      <div class="header-brand">
        <router-link to="/" class="brand-link">
          <h1>VaultShare</h1>
        </router-link>
      </div>

      <!-- 桌面导航 -->
      <nav class="header-nav hide-on-mobile">
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="item.path"
          class="nav-link"
          :class="{ active: isActive(item.path) }"
        >
          <el-icon v-if="item.icon">
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 右侧操作区 -->
      <div class="header-actions">
        <!-- 暗黑模式切换 -->
        <el-button
          :icon="isDarkMode ? Sunny : Moon"
          circle
          text
          @click="toggleDarkMode"
          class="theme-toggle"
        />

        <!-- 用户菜单 -->
        <template v-if="userStore.isLoggedIn">
          <el-dropdown trigger="click">
            <div class="user-dropdown-trigger">
              <UserAvatar :src="avatarUrl" :user="userStore.currentUser" :size="36" />
              <span class="user-name-display">{{ displayName }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="goToDashboard">
                  <el-icon><FolderOpened /></el-icon>
                  工作台
                </el-dropdown-item>
                <el-dropdown-item @click="goToProfile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item v-if="userStore.isAdminOrRoot" @click="goToAdmin">
                  <el-icon><Setting /></el-icon>
                  后台管理
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" @click="goToLogin">登录</el-button>
        </template>

        <!-- 移动端菜单按钮 -->
        <el-button
          class="mobile-menu-btn show-on-mobile"
          :icon="mobileMenuOpen ? Close : Menu"
          circle
          text
          @click="toggleMobileMenu"
        />
      </div>
    </div>

    <!-- 移动端菜单 -->
    <transition name="slide">
      <div v-show="mobileMenuOpen" class="mobile-menu">
        <nav class="mobile-nav">
          <router-link
            v-for="item in navItems"
            :key="item.name"
            :to="item.path"
            class="mobile-nav-link"
            :class="{ active: isActive(item.path) }"
            @click="closeMobileMenu"
          >
            <el-icon v-if="item.icon">
              <component :is="item.icon" />
            </el-icon>
            <span>{{ item.label }}</span>
          </router-link>
          <div v-if="userStore.isLoggedIn" class="mobile-nav-section">
            <div class="mobile-user-info">
              <el-avatar :size="40" :icon="UserFilled" />
              <span>{{ displayName }}</span>
            </div>
            <el-button text block @click="goToDashboard">
              <el-icon><FolderOpened /></el-icon>
              工作台
            </el-button>
            <el-button text block @click="goToProfile">
              <el-icon><User /></el-icon>
              个人中心
            </el-button>
            <el-button v-if="userStore.isAdminOrRoot" text block @click="goToAdmin">
              <el-icon><Setting /></el-icon>
              后台管理
            </el-button>
            <el-button text block type="danger" @click="handleLogout">
              退出登录
            </el-button>
          </div>
          <el-button v-else text block type="primary" @click="goToLogin">
            登录 / 注册
          </el-button>
        </nav>
      </div>
    </transition>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  Menu, Close, Moon, Sunny, UserFilled, User, Setting, SwitchButton,
  House, Document, Grid
} from '@element-plus/icons-vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/modules/auth'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const mobileMenuOpen = ref(false)

const isDarkMode = computed(() => appStore.isDarkMode)

// 头像 URL（带时间戳避免缓存）
const avatarUrl = computed(() => {
  const user = userStore.currentUser
  if (user?.avatar) {
    const baseUrl = authApi.getAvatarUrl()
    const timestamp = new Date(user.updated_at).getTime()
    return `${baseUrl}?t=${timestamp}`
  }
  return undefined
})

// 显示名称（优先显示昵称）
const displayName = computed(() => {
  const user = userStore.currentUser
  return user?.nickname || user?.username || ''
})

const navItems = computed(() => [
  { name: 'Home', label: '首页', path: '/', icon: House },
  { name: 'Plaza', label: '公共大厅', path: '/plaza', icon: Grid }
])

function isActive(path: string): boolean {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

function toggleDarkMode() {
  appStore.toggleDarkMode()
}

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}

function goToLogin() {
  closeMobileMenu()
  router.push({ name: 'Login', query: { redirect: route.fullPath } })
}

function goToDashboard() {
  closeMobileMenu()
  router.push('/hub')
}

function goToAdmin() {
  closeMobileMenu()
  router.push({ name: 'Admin' })
}

function goToProfile() {
  closeMobileMenu()
  router.push({ name: 'Profile' })
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userStore.logout()
    closeMobileMenu()
    router.push({ name: 'Home' })
  } catch {
    // 取消退出
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/variables.scss';

.app-header {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.9);

  html.dark & {
    background: rgba(15, 23, 42, 0.9);
    border-bottom-color: #334155;
  }
}

.header-container {
  display: flex;
  align-items: center;
  height: 64px;
  gap: $spacing-lg;
}

.header-brand {
  .brand-link {
    text-decoration: none;
    color: var(--el-text-color-primary);

    h1 {
      font-size: 22px;
      font-weight: 700;
      margin: 0;
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: -0.5px;
    }
  }
}

.header-nav {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  flex: 1;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  padding: 10px 16px;
  border-radius: $radius-lg;
  text-decoration: none;
  color: var(--el-text-color-regular);
  transition: all $transition-base;
  font-weight: 500;
  font-size: 15px;

  &:hover {
    color: #6366f1;
    background: rgba(99, 102, 241, 0.08);
  }

  &.active {
    color: #6366f1;
    background: rgba(99, 102, 241, 0.1);
  }

  .el-icon {
    font-size: 18px;
  }
}

.header-actions {
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

.mobile-menu-btn {
  display: none !important;

  @media (max-width: $breakpoint-sm) {
    display: block !important;
  }
}

// 移动端菜单
.mobile-menu {
  position: fixed;
  top: 64px;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--el-bg-color);
  padding: $spacing-lg;
  overflow-y: auto;
  z-index: 99;

  @media (min-width: $breakpoint-sm + 1) {
    display: none !important;
  }
}

.mobile-nav {
  display: flex;
  flex-direction: column;
  gap: $spacing-xs;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: 14px 16px;
  border-radius: $radius-lg;
  text-decoration: none;
  color: var(--el-text-color-regular);
  font-size: 16px;
  transition: all $transition-base;

  &:hover,
  &.active {
    color: #6366f1;
    background: rgba(99, 102, 241, 0.1);
  }

  .el-icon {
    font-size: 20px;
  }
}

.mobile-nav-section {
  margin-top: $spacing-lg;
  padding-top: $spacing-lg;
  border-top: 1px solid var(--el-border-color);
}

.mobile-user-info {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  margin-bottom: $spacing-md;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: $radius-lg;
}

// 滑动动画
.slide-enter-active,
.slide-leave-active {
  transition: transform $transition-base;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}

// 修复下拉菜单间隔
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
