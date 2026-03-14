<template>
  <header class="app-header">
    <div class="header-inner">
      <!-- Brand -->
      <router-link to="/" class="brand">
        <span class="brand-word">
          <span class="brand-F">F</span><span class="brand-olio">olio</span>
        </span>
      </router-link>

      <!-- Desktop Nav -->
      <nav class="header-nav hide-on-mobile">
        <router-link to="/blog" class="nav-link" :class="{ active: isActive('/blog') }">发现</router-link>
        <router-link v-if="userStore.isLoggedIn" to="/space" class="nav-link" :class="{ active: isActive('/space') }">空间</router-link>
      </nav>

      <!-- Right Actions -->
      <div class="header-actions">
        <!-- Search (desktop, icon-only → expand on click) -->
        <div :class="['search-box', 'hide-on-mobile', { expanded: searchExpanded }]">
          <button class="search-icon-btn" @click="toggleSearch">
            <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
          </button>
          <input
            v-if="searchExpanded"
            ref="searchInputRef"
            v-model="searchQuery"
            class="search-input"
            placeholder="搜索..."
            @keyup.enter="doSearch"
            @keyup.esc="closeSearch"
            @blur="onSearchBlur"
          />
        </div>

        <!-- Notifications -->
        <div v-if="userStore.isLoggedIn" class="notif-wrap" ref="notifWrapRef">
          <button class="icon-btn" @click="toggleNotifPanel" :class="{ active: notifPanelOpen }">
            <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <span v-if="unreadCount > 0" class="notif-badge">
              <span v-if="unreadCount >= 10" class="notif-badge-num">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
            </span>
          </button>

          <transition name="panel-pop">
            <div v-if="notifPanelOpen" class="notif-panel" @click.stop>
              <div class="notif-head">
                <span class="notif-title">通知</span>
                <button class="clear-btn" @click="clearAllNotifications">清除全部</button>
              </div>

              <div v-if="notifLoading" class="notif-body">
                <el-skeleton :rows="3" animated style="padding: 12px 14px" />
              </div>
              <div v-else-if="notifications.length === 0" class="notif-empty">暂无通知</div>
              <div v-else class="notif-list">
                <div
                  v-for="n in notifications"
                  :key="n.id"
                  class="notif-item"
                  :class="{ unread: !n.is_read }"
                  @click="handleNotifClick(n)"
                >
                  <div class="notif-avatar">{{ (n.actor_nickname || n.actor_username || '?')[0] }}</div>
                  <div class="notif-content">
                    <p class="notif-text">{{ formatNotif(n) }}</p>
                    <span class="notif-time">{{ fromNow(n.created_at) }}</span>
                  </div>
                </div>
              </div>

              <div v-if="notifications.length >= 5" class="notif-foot">
                <button class="view-all-btn" @click="closeNotifPanel">查看全部通知</button>
              </div>
            </div>
          </transition>
        </div>

        <!-- Theme toggle -->
        <button class="icon-btn" @click="toggleDarkMode" :title="isDarkMode ? '切换亮色' : '切换暗色'">
          <svg v-if="isDarkMode" class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="4"/>
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
          </svg>
          <svg v-else class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>

        <!-- Mobile: search -->
        <button class="icon-btn show-on-mobile" @click="goToSearchPage">
          <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
        </button>

        <!-- Mobile: hamburger -->
        <button class="icon-btn mobile-menu-btn show-on-mobile" @click="toggleMobileMenu">
          <span class="hamburger" :class="{ open: mobileMenuOpen }">
            <i></i><i></i><i></i>
          </span>
        </button>

        <!-- User dropdown -->
        <template v-if="userStore.isLoggedIn">
          <div class="user-wrap" ref="userWrapRef">
            <button class="user-trigger" @click="toggleUserMenu" :class="{ active: userMenuOpen, 'has-review': hasReviewBadge }">
              <UserAvatar :src="avatarUrl" :user="userStore.currentUser" :size="28" />
            </button>

            <transition name="panel-pop">
              <div v-if="userMenuOpen" class="user-menu" @click.stop>
                <div class="user-menu-header">
                  <UserAvatar :src="avatarUrl" :user="userStore.currentUser" :size="34" class="user-menu-avatar" />
                  <div class="user-menu-info">
                    <span class="user-menu-name">{{ userStore.currentUser?.nickname || userStore.currentUser?.username }}</span>
                    <span class="user-menu-username">@{{ userStore.currentUser?.username }}</span>
                  </div>
                </div>
                <div class="user-menu-body">
                  <button class="menu-item" @click="goToSettings">
                    <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="3"/>
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                    </svg>
                    <span>账户设置</span>
                  </button>
                  <button v-if="userStore.isAdminOrRoot" class="menu-item" @click="goToAdmin">
                    <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="3" width="7" height="7" rx="1.5"/>
                      <rect x="14" y="3" width="7" height="7" rx="1.5"/>
                      <rect x="14" y="14" width="7" height="7" rx="1.5"/>
                      <rect x="3" y="14" width="7" height="7" rx="1.5"/>
                    </svg>
                    <span>管理台</span>
                    <span v-if="hasReviewBadge" class="menu-review-dot" />
                  </button>
                  <button class="menu-item menu-item--danger" @click="handleLogout">
                    <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                      <polyline points="16 17 21 12 16 7"/>
                      <line x1="21" y1="12" x2="9" y2="12"/>
                    </svg>
                    <span>退出登录</span>
                  </button>
                </div>
              </div>
            </transition>
          </div>
        </template>
        <template v-else>
          <el-button type="primary" size="small" @click="goToLogin" class="login-btn">登录</el-button>
        </template>
      </div>
    </div>

    <!-- Mobile menu -->
    <transition name="slide-down">
      <div v-show="mobileMenuOpen" class="mobile-menu">
        <router-link to="/blog" class="mobile-link" @click="closeMobileMenu">发现</router-link>
        <router-link v-if="userStore.isLoggedIn" to="/space" class="mobile-link" @click="closeMobileMenu">空间</router-link>
        <template v-if="userStore.isLoggedIn">
          <div class="mobile-sep"></div>
          <button class="mobile-link" @click="goToSettings">账户设置</button>
          <button v-if="userStore.isAdminOrRoot" class="mobile-link" @click="goToAdmin">管理台</button>
          <button class="mobile-link mobile-link--danger" @click="handleLogout">退出登录</button>
        </template>
        <template v-else>
          <div class="mobile-sep"></div>
          <button class="mobile-link mobile-link--primary" @click="goToLogin">登录 / 注册</button>
        </template>
      </div>
    </transition>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/modules/auth'
import { notificationsApi } from '@/api/modules/notifications'
import { postsApi } from '@/api/modules/posts'
import type { Notification } from '@/types/models'
import { fromNow } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const mobileMenuOpen = ref(false)
const searchQuery = ref('')
const searchExpanded = ref(false)
const searchInputRef = ref<HTMLInputElement | null>(null)
const notifPanelOpen = ref(false)
const userMenuOpen = ref(false)
const notifWrapRef = ref<HTMLElement | null>(null)
const userWrapRef = ref<HTMLElement | null>(null)

// Notifications
const unreadCount = ref(0)
const notifications = ref<Notification[]>([])
const notifLoading = ref(false)
let notifTimer: ReturnType<typeof setInterval> | null = null

// 管理员审核待处理数量（从全局 store 读取，所有组件共享同一数据源）
const hasReviewBadge = computed(() => userStore.isAdminOrRoot && appStore.reviewCount > 0)

async function fetchReviewCount() {
  if (!userStore.isAdminOrRoot) return
  await appStore.refreshReviewCount()
}

const isDarkMode = computed(() => appStore.isDarkMode)

const avatarUrl = computed(() => {
  const user = userStore.currentUser
  if (user?.avatar) {
    const baseUrl = authApi.getAvatarUrl()
    const timestamp = new Date(user.updated_at).getTime()
    return `${baseUrl}?uid=${user.id}&t=${timestamp}`
  }
  return undefined
})

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

// ---------- Notification panel ----------
function toggleNotifPanel() {
  notifPanelOpen.value = !notifPanelOpen.value
  userMenuOpen.value = false
  if (notifPanelOpen.value) loadNotifications()
}

function closeNotifPanel() {
  notifPanelOpen.value = false
}

// ---------- User menu ----------
function toggleUserMenu() {
  userMenuOpen.value = !userMenuOpen.value
  notifPanelOpen.value = false
}

function closeUserMenu() {
  userMenuOpen.value = false
}

// ---------- Click outside ----------
function handleOutsideClick(e: MouseEvent) {
  if (notifWrapRef.value && !notifWrapRef.value.contains(e.target as Node)) {
    notifPanelOpen.value = false
  }
  if (userWrapRef.value && !userWrapRef.value.contains(e.target as Node)) {
    userMenuOpen.value = false
  }
}

// ---------- Search ----------
function toggleSearch() {
  searchExpanded.value = !searchExpanded.value
  if (searchExpanded.value) {
    nextTick(() => searchInputRef.value?.focus())
  } else {
    searchQuery.value = ''
  }
}

function closeSearch() {
  searchExpanded.value = false
  searchQuery.value = ''
}

function onSearchBlur() {
  if (!searchQuery.value.trim()) {
    searchExpanded.value = false
  }
}

function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  router.push({ name: 'Search', query: { q } })
  searchQuery.value = ''
  searchExpanded.value = false
}

function goToSearchPage() {
  router.push({ name: 'Search' })
}

// ---------- Notifications API ----------
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

async function clearAllNotifications() {
  try {
    await notificationsApi.clearAll()
    notifications.value = []
    unreadCount.value = 0
  } catch {
    ElMessage.error('清除失败')
  }
}

function handleNotifClick(n: Notification) {
  closeNotifPanel()
  if (!n.is_read) {
    n.is_read = 1
    if (unreadCount.value > 0) unreadCount.value--
    notificationsApi.readOne(n.id).catch(() => {})
  }
  if (n.type === 'follow') {
    router.push(`/u/${n.actor_username}`)
  } else if (n.type === 'admin') {
    const action = n.extra?.action
    if (action === 'report_invalid') {
      // 举报者：举报被驳回，博文仍可见，跳博文详情
      if (n.target_id) router.push(`/post/${n.target_id}`)
    } else if (action !== 'report_valid') {
      // 作者：博文被隐藏，跳隐藏说明页（report_valid 举报者收到此通知，博文已隐藏，不跳转）
      if (n.target_id) router.push(`/post/${n.target_id}/moderation`)
    }
  } else if (n.type === 'review_result') {
    if (n.target_id) {
      const action = n.extra?.action
      if (action === 'approved') router.push(`/post/${n.target_id}`)
      else router.push(`/post/${n.target_id}/moderation`)
    }
  } else if (n.type === 'appeal' || n.type === 'report') {
    router.push('/admin/review')
  } else if (n.type === 'pinned' && n.target_id) {
    router.push(`/post/${n.target_id}`)
  } else if (n.target_id) {
    const hash = (n.type === 'comment' || n.type === 'reply') ? '#comments' : ''
    router.push(`/post/${n.target_id}${hash}`)
  }
}

function formatNotif(n: Notification): string {
  const actor = n.actor_nickname || n.actor_username || '管理员'
  const postTitle = n.extra?.post_title ? `《${n.extra.post_title}》` : '你的博文'
  const content = n.extra?.content ? `：${n.extra.content}` : ''
  const reason = n.extra?.reason || ''
  switch (n.type) {
    case 'like': return `${actor} 赞了 ${postTitle}`
    case 'collect': return `${actor} 收藏了 ${postTitle}`
    case 'comment': return `${actor} 评论了 ${postTitle}${content}`
    case 'reply': return `${actor} 回复了你的评论${content}`
    case 'follow': return `${actor} 关注了你`
    case 'new_post': return `您关注的 ${actor} 发布了新博文 ${postTitle}`
    case 'admin': {
      const action = n.extra?.action
      if (action === 'report_valid')   return `您举报的博文 ${postTitle} 经审核已被隐藏，感谢您维护社区环境`
      if (action === 'report_invalid') return `您举报的博文 ${postTitle} 经审核暂不违规，感谢您对社区的贡献`
      return `你的博文 ${postTitle} 已被隐藏${reason ? '，原因：' + reason : ''}`
    }
    case 'appeal': {
      const appealPost = n.extra?.post_title ? `《${n.extra.post_title}》` : '某博文'
      return `${actor} 对 ${appealPost} 提交了申诉`
    }
    case 'review_result': {
      const approved = n.extra?.action === 'approved'
      return approved
        ? `你对 ${postTitle} 的申诉已通过，博文已恢复`
        : `你对 ${postTitle} 的申诉被拒绝${reason ? '，原因：' + reason : ''}`
    }
    case 'report': {
      const reportPost = n.extra?.post_title ? `《${n.extra.post_title}》` : '某博文'
      return `${actor} 对 ${reportPost} 提交了举报${reason ? '，理由：' + n.extra?.reason : ''}`
    }
    case 'pinned': return `博文 ${postTitle} 已被置顶推荐`
    default: return '新通知'
  }
}

// ---------- Dark mode ----------
function toggleDarkMode() {
  appStore.toggleDarkMode()
}

// ---------- Mobile menu ----------
function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}

// ---------- Navigation ----------
function goToLogin() {
  closeMobileMenu()
  router.push({ name: 'Login', query: { redirect: route.fullPath } })
}

function goToSettings() {
  closeUserMenu()
  closeMobileMenu()
  router.push({ name: 'Settings' })
}

function goToAdmin() {
  closeUserMenu()
  closeMobileMenu()
  // 有待处理审核时直接进审核页，否则进管理台概览
  router.push(hasReviewBadge.value ? '/admin/review' : { name: 'Admin' })
}

async function handleLogout() {
  closeUserMenu()
  closeMobileMenu()
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userStore.logout()
    router.push({ name: 'Home' })
  } catch { /* cancelled */ }
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  if (userStore.isLoggedIn) {
    fetchUnreadCount()
    fetchReviewCount()
    notifTimer = setInterval(() => {
      fetchUnreadCount()
      fetchReviewCount()
    }, 30000)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  if (notifTimer) clearInterval(notifTimer)
})
</script>

<style scoped lang="scss">
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 52px;
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(12px);
  background: rgba(255, 255, 255, 0.92);

  html.dark & {
    background: rgba(28, 31, 38, 0.92);
    border-bottom-color: var(--color-border);
  }
}

.header-inner {
  display: flex;
  align-items: center;
  height: 52px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 $spacing-xl;
  gap: 20px;

  @media (max-width: $breakpoint-lg) {
    max-width: 100%;
    padding: 0 $spacing-lg;
  }

  @media (max-width: $breakpoint-sm) {
    padding: 0 $spacing-md;
    gap: $spacing-sm;
  }
}

// ---- Brand ----
.brand {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  line-height: 1;
  margin-top: 3px;

  &:hover .brand-word {
    transform: translateY(-2px);

    &::after {
      width: 100%;
    }
  }
  &:hover .brand-olio {
    letter-spacing: 0.04em;
  }
}

.brand-word {
  display: inline-flex;
  align-items: baseline;
  line-height: 1;
  position: relative;
  padding-bottom: 3px;
  transform: translateY(0);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);

  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 10px;
    height: 2px;
    background: $color-primary;
    border-radius: 1px;
    transition: width 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
}

.brand-F {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: $color-primary;
}

.brand-olio {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: var(--color-text-primary);
  transition: letter-spacing 0.25s ease;
}

// ---- Nav ----
.header-nav {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: 1;
}

.nav-link {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 0 12px;
  height: 52px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color $transition-base;

  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 12px;
    right: 12px;
    height: 2px;
    background: var(--color-primary);
    border-radius: 2px 2px 0 0;
    opacity: 0;
    transform: scaleX(0.6);
    transition: opacity $transition-base, transform $transition-base;
  }

  &:hover {
    color: var(--color-text-primary);
  }

  &.active {
    color: var(--color-primary);

    &::after {
      opacity: 1;
      transform: scaleX(1);
    }
  }
}

// ---- Actions ----
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

// ---- Action icons (SVG) ----
.action-icon {
  width: 16px;
  height: 16px;
  display: block;
}

.menu-icon {
  width: 14px;
  height: 14px;
  display: block;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

// ---- Search ----
.search-box {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: $radius-md;
  padding: 0 6px;
  overflow: hidden;
  transition: width $transition-base, border-color $transition-base, background $transition-base;

  &.expanded {
    width: 200px;
    border-color: var(--color-primary);
    background: var(--color-surface);
    padding: 0 8px;

    html.dark & {
      background: var(--color-surface-hover);
    }
  }
}

.search-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: var(--color-text-secondary);
  flex-shrink: 0;
  transition: color $transition-fast;

  &:hover { color: var(--color-text-primary); }
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--color-text-primary);
  min-width: 0;
  width: 0;

  &::placeholder {
    color: var(--color-text-muted);
  }
}

// ---- Icon button ----
.icon-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: $radius-md;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: color $transition-base, background $transition-base;
  padding: 0;

  &:hover {
    color: var(--color-text-primary);
    background: var(--color-surface-hover);
  }

  &.active {
    color: var(--color-primary);
    background: var(--color-primary-subtle);
  }
}

// ---- Notification badge ----
.notif-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 8px;
  height: 8px;
  padding: 0;
  background: #e05555;
  border: 1.5px solid var(--color-surface, #fff);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;

  html.dark & {
    border-color: rgba(28, 31, 38, 0.92);
  }
}

.notif-badge-num {
  font-size: 9px;
  font-weight: 700;
  color: white;
  line-height: 1;
  padding: 0 3px;
}

// ---- Notification panel ----
.notif-wrap {
  position: relative;
}

.notif-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 300px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  z-index: 200;

  html.dark & {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.06);
  }
}

.notif-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px 10px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.notif-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.clear-btn {
  font-size: 12px;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: $radius-sm;
  transition: color $transition-base;

  &:hover {
    color: #ef4444;
  }
}

.notif-empty {
  padding: $spacing-lg $spacing-md;
  font-size: 13px;
  color: var(--color-text-muted);
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
  padding: 10px 14px;
  cursor: pointer;
  position: relative;
  transition: background $transition-fast;

  &:hover {
    background: var(--color-surface-raised);
  }
}

.notif-avatar {
  flex-shrink: 0;
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary-subtle);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;

  // 未读小红点：叠在头像右上角
  .notif-item.unread & {
    &::after {
      content: '';
      position: absolute;
      top: 1px;
      right: 1px;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #f87171;
      border: 1px solid var(--color-surface);
    }
  }
}

.notif-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.notif-text {
  font-size: 12px;
  color: var(--color-text-primary);
  line-height: 1.45;
  word-break: break-word;
  margin: 0;
}

.notif-time {
  font-size: 11px;
  color: var(--color-text-muted);
  text-align: right;
  align-self: flex-end;
}

.notif-foot {
  padding: 8px 14px;
  border-top: 1px solid var(--color-border-subtle);
  text-align: center;
}

.view-all-btn {
  font-size: 12px;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: $radius-sm;
  transition: color $transition-base;

  &:hover {
    color: var(--color-primary);
  }
}

// ---- User dropdown ----
.user-wrap {
  position: relative;
}

.user-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  padding: 0;
  transition: opacity $transition-base;

  &:hover,
  &.active {
    opacity: 0.8;
  }

  // 审核待处理小红点（带脉冲动画）
  &.has-review::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #f87171;
    border: 1.5px solid rgba(255, 255, 255, 0.92);
    z-index: 1;
    pointer-events: none;
    animation: review-pulse 2.2s ease-in-out infinite;

    html.dark & { border-color: rgba(28, 31, 38, 0.92); }
  }
}

// "管理台" 菜单项右侧小红点
.menu-review-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ef4444;
  margin-left: auto;
  flex-shrink: 0;
}

.user-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 148px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  z-index: 200;

  // 1280px+ 宽屏：将下拉框中心对齐到头像中心左移 14px
  // Avatar center = user-wrap.right - 16px
  // Dropdown center = user-wrap.right + 44 - 74 = user-wrap.right - 30px → 14px 偏左 ✓
  @media (min-width: $breakpoint-xl) {
    right: -44px;
  }

  html.dark & {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.06);
  }
}

.user-menu-header {
  padding: 12px 12px 10px;
  border-bottom: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: center;
  gap: 9px;
}

.user-menu-avatar {
  flex-shrink: 0;
}

.user-menu-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-menu-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-menu-username {
  font-size: 11px;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-menu-body {
  padding: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border: none;
  background: transparent;
  border-radius: $radius-sm;
  font-size: 13px;
  color: var(--color-text-primary);
  cursor: pointer;
  text-align: left;
  transition: background $transition-fast;

  &:hover {
    background: var(--color-surface-hover);
  }

  &--danger {
    color: #ef4444;

    .menu-icon {
      color: #ef4444;
    }

    &:hover {
      background: rgba(239, 68, 68, 0.06);
    }
  }
}

.login-btn {
  height: 30px;
  font-size: 13px;
}

// ---- Mobile hamburger ----
.hamburger {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  width: 16px;
  height: 16px;

  i {
    display: block;
    height: 1.5px;
    background: currentColor;
    border-radius: 1px;
    transform-origin: center;
    transition: transform $transition-base, opacity $transition-base;
  }

  &.open {
    i:nth-child(1) { transform: translateY(5.5px) rotate(45deg); }
    i:nth-child(2) { opacity: 0; transform: scaleX(0); }
    i:nth-child(3) { transform: translateY(-5.5px) rotate(-45deg); }
  }
}

// ---- Mobile menu ----
.mobile-menu {
  position: fixed;
  top: 52px;
  left: 0;
  right: 0;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: $spacing-sm $spacing-md $spacing-md;
  z-index: 99;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);

  @media (min-width: $breakpoint-sm + 1) {
    display: none !important;
  }
}

.mobile-link {
  display: block;
  width: 100%;
  padding: 12px $spacing-sm;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
  text-decoration: none;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  border-radius: $radius-md;
  transition: background $transition-fast, color $transition-fast;

  &:hover {
    background: var(--color-surface-hover);
  }

  &.active {
    color: var(--color-primary);
  }

  &--danger {
    color: #ef4444;
  }

  &--primary {
    color: var(--color-primary);
  }
}

.mobile-sep {
  height: 1px;
  background: var(--color-border-subtle);
  margin: $spacing-xs 0;
}

// ---- Review dot pulse ----
@keyframes review-pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(248, 113, 113, 0.5);
  }
  50% {
    transform: scale(1.3);
    box-shadow: 0 0 0 4px rgba(248, 113, 113, 0);
  }
}

// ---- Panel pop animation ----
.panel-pop-enter-active {
  transition: opacity 0.15s ease, transform 0.18s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.panel-pop-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}

.panel-pop-enter-from {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}

.panel-pop-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}

// ---- Slide-down transition ----
.slide-down-enter-active,
.slide-down-leave-active {
  transition: opacity $transition-base, transform $transition-base;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
