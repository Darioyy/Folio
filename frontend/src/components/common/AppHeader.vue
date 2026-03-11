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
        <!-- 搜索框（桌面端） -->
        <div class="search-wrap hide-on-mobile">
          <div :class="['search-box', { focused: searchFocused }]">
            <el-icon class="search-icon"><Search /></el-icon>
            <input
              v-model="searchQuery"
              class="search-input"
              placeholder="搜索..."
              @focus="searchFocused = true"
              @blur="searchFocused = false"
              @keyup.enter="doSearch"
            />
          </div>
        </div>

        <!-- 暗黑模式切换 -->
        <el-button
          :icon="isDarkMode ? Sunny : Moon"
          circle
          text
          @click="toggleDarkMode"
          class="theme-toggle"
        />

        <!-- 通知铃铛（登录后显示） -->
        <el-popover
          v-if="userStore.isLoggedIn"
          placement="bottom-end"
          :width="320"
          trigger="click"
          popper-class="notif-popover"
          @show="loadNotifications"
        >
          <template #reference>
            <el-badge :value="unreadCount > 0 ? (unreadCount > 99 ? '99+' : unreadCount) : ''" :hidden="unreadCount === 0" class="notif-badge">
              <el-button :icon="Bell" circle text class="notif-btn" />
            </el-badge>
          </template>
          <div class="notif-panel">
            <div class="notif-panel-header">
              <span class="notif-panel-title">通知</span>
              <el-button v-if="unreadCount > 0" link size="small" @click="markAllRead">全部已读</el-button>
            </div>
            <div v-if="notifLoading" class="notif-loading">
              <el-skeleton :rows="3" animated />
            </div>
            <div v-else-if="notifications.length === 0" class="notif-empty">暂无通知</div>
            <div v-else class="notif-list">
              <div
                v-for="n in notifications"
                :key="n.id"
                :class="['notif-item', { unread: !n.is_read }]"
              >
                <el-avatar :size="32" class="notif-avatar">
                  {{ (n.actor_nickname || n.actor_username || '?')[0] }}
                </el-avatar>
                <div class="notif-content">
                  <p class="notif-text">{{ formatNotif(n) }}</p>
                  <span class="notif-time">{{ fromNow(n.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-popover>

        <!-- 用户菜单 -->
        <template v-if="userStore.isLoggedIn">
          <el-dropdown trigger="hover" :show-timeout="60" :hide-timeout="200" :popper-options="{ modifiers: [{ name: 'offset', options: { offset: [0, 4] } }] }">
            <div class="user-dropdown-trigger">
              <UserAvatar :src="avatarUrl" :user="userStore.currentUser" :size="36" />
              <span class="user-name-display">{{ displayName }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="goToSpace">
                  <el-icon><Grid /></el-icon>
                  我的空间
                </el-dropdown-item>
                <el-dropdown-item v-if="userStore.isAdminOrRoot" @click="goToAdmin">
                  <el-icon><Setting /></el-icon>
                  后台管理
                </el-dropdown-item>
                <el-dropdown-item @click="handleLogout">
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

        <!-- 移动端搜索图标 -->
        <el-button
          class="show-on-mobile"
          :icon="Search"
          circle
          text
          @click="goToSearchPage"
        />

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
            <el-button text block @click="goToSpace">
              <el-icon><Grid /></el-icon>
              我的空间
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  Menu, Close, Moon, Sunny, UserFilled, Setting, SwitchButton,
  House, Grid, Search, Bell
} from '@element-plus/icons-vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/modules/auth'
import { notificationsApi } from '@/api/modules/notifications'
import type { Notification } from '@/types/models'
import { fromNow } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const mobileMenuOpen = ref(false)
const searchQuery = ref('')
const searchFocused = ref(false)

// 通知
const unreadCount = ref(0)
const notifications = ref<Notification[]>([])
const notifLoading = ref(false)
let notifTimer: ReturnType<typeof setInterval> | null = null

const isDarkMode = computed(() => appStore.isDarkMode)

// 头像 URL（uid+时间戳双重缓存破坏：切换用户或更新头像时强制重新加载）
const avatarUrl = computed(() => {
  const user = userStore.currentUser
  if (user?.avatar) {
    const baseUrl = authApi.getAvatarUrl()
    const timestamp = new Date(user.updated_at).getTime()
    return `${baseUrl}?uid=${user.id}&t=${timestamp}`
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

function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  router.push({ name: 'Search', query: { q } })
  searchQuery.value = ''
}

function goToSearchPage() {
  router.push({ name: 'Search' })
}

async function fetchUnreadCount() {
  if (!userStore.isLoggedIn) return
  try {
    const res = await notificationsApi.getUnreadCount()
    unreadCount.value = res.data.count
  } catch { /* ignore */ }
}

async function loadNotifications() {
  notifLoading.value = true
  try {
    const res = await notificationsApi.getList(1, 10)
    notifications.value = res.items
  } catch { /* ignore */ } finally {
    notifLoading.value = false
  }
}

async function markAllRead() {
  try {
    await notificationsApi.readAll()
    notifications.value = notifications.value.map(n => ({ ...n, is_read: 1 }))
    unreadCount.value = 0
  } catch { /* ignore */ }
}

function formatNotif(n: Notification): string {
  const actor = n.actor_nickname || n.actor_username || '某用户'
  const fileTitle = n.extra?.file_title ? `《${n.extra.file_title}》` : '你的文件'
  const content = n.extra?.content ? `：${n.extra.content}` : ''
  switch (n.type) {
    case 'like': return `${actor} 赞了你的 ${fileTitle}`
    case 'comment': return `${actor} 评论了 ${fileTitle}${content}`
    case 'reply': return `${actor} 回复了你的评论${content}`
    case 'follow': return `${actor} 关注了你`
    default: return '新通知'
  }
}

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

function goToSpace() {
  closeMobileMenu()
  router.push({ name: 'Space' })
}

function goToAdmin() {
  closeMobileMenu()
  router.push({ name: 'Admin' })
}

onMounted(() => {
  if (userStore.isLoggedIn) {
    fetchUnreadCount()
    notifTimer = setInterval(fetchUnreadCount, 60000)
  }
})

onUnmounted(() => {
  if (notifTimer) clearInterval(notifTimer)
})

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

// 搜索框
.search-wrap {
  display: flex;
  align-items: center;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-full;
  padding: 6px 12px;
  width: 200px;
  transition: width $transition-base, border-color $transition-base;

  &.focused {
    width: 280px;
    border-color: $color-primary;
    background: var(--el-bg-color);
  }
}

.search-icon {
  color: var(--el-text-color-placeholder);
  font-size: 14px;
  flex-shrink: 0;
}

.search-input {
  border: none;
  outline: none;
  background: transparent;
  font-size: $font-sm;
  color: var(--el-text-color-primary);
  width: 100%;

  &::placeholder {
    color: var(--el-text-color-placeholder);
  }
}

// 通知
.notif-badge {
  line-height: 1;
}

.notif-btn {
  color: var(--el-text-color-secondary);

  &:hover {
    color: $color-primary;
    background: rgba(99, 102, 241, 0.08);
  }
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

// 通知面板
.notif-panel {
  padding: 4px 0;
}

.notif-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 4px;
}

.notif-panel-title {
  font-size: $font-sm;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.notif-loading,
.notif-empty {
  padding: $spacing-md;
  color: var(--el-text-color-secondary);
  font-size: $font-sm;
  text-align: center;
}

.notif-list {
  max-height: 320px;
  overflow-y: auto;
}

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: $spacing-sm;
  padding: 10px 12px;
  transition: background $transition-fast;

  &.unread {
    background: rgba(99, 102, 241, 0.04);
  }

  &:hover {
    background: var(--el-fill-color-lighter);
  }
}

.notif-avatar {
  flex-shrink: 0;
  font-size: 12px;
  background: linear-gradient(135deg, $color-primary, $color-secondary);
  color: white;
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-text {
  margin: 0 0 2px;
  font-size: $font-xs;
  color: var(--el-text-color-regular);
  line-height: 1.4;
  word-break: break-word;
}

.notif-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
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
