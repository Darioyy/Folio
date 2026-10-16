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
        <router-link to="/tools" class="nav-link" :class="{ active: isActive('/tools') }">工具</router-link>
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
        <NotificationPanel />

        <!-- Theme toggle -->
        <button class="icon-btn" :title="isDarkMode ? '切换亮色' : '切换暗色'" @click="toggleDarkMode">
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
        <button class="icon-btn mobile-menu-btn show-on-mobile" @click="mobileMenuOpen = !mobileMenuOpen">
          <span class="hamburger" :class="{ open: mobileMenuOpen }">
            <i></i><i></i><i></i>
          </span>
        </button>

        <!-- User dropdown / Login -->
        <template v-if="userStore.isLoggedIn">
          <UserMenu />
        </template>
        <template v-else>
          <el-button type="primary" size="small" class="login-btn" @click="goToLogin">登录</el-button>
        </template>
      </div>
    </div>

    <!-- Mobile menu -->
    <MobileMenu :open="mobileMenuOpen" @close="mobileMenuOpen = false" />
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import NotificationPanel from './header/NotificationPanel.vue'
import UserMenu from './header/UserMenu.vue'
import MobileMenu from './header/MobileMenu.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const mobileMenuOpen = ref(false)
const searchQuery = ref('')
const searchExpanded = ref(false)
const searchInputRef = ref<HTMLInputElement | null>(null)

const isDarkMode = computed(() => appStore.isDarkMode)

let reviewTimer: ReturnType<typeof setInterval> | null = null

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
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
  if (!searchQuery.value.trim()) searchExpanded.value = false
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

// ---------- Theme ----------
function toggleDarkMode() {
  appStore.toggleDarkMode()
}

// ---------- Navigation ----------
function goToLogin() {
  router.push({ name: 'Login', query: { redirect: route.fullPath } })
}

// ---------- Review badge polling (admin/root only) ----------
async function fetchReviewCount() {
  if (!userStore.isAdminOrRoot) return
  await appStore.refreshReviewCount()
}

onMounted(() => {
  if (userStore.isLoggedIn) {
    fetchReviewCount()
    reviewTimer = setInterval(fetchReviewCount, 30000)
  }
})

onUnmounted(() => {
  if (reviewTimer) clearInterval(reviewTimer)
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
    &::after { width: 100%; }
  }
  &:hover .brand-olio { letter-spacing: 0.04em; }
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
    bottom: 0; left: 0;
    width: 10px; height: 2px;
    background: $color-primary;
    border-radius: 1px;
    transition: width 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
}

.brand-F {
  font-size: 20px; font-weight: 800; letter-spacing: -0.5px;
  color: $color-primary;
}

.brand-olio {
  font-size: 20px; font-weight: 600; letter-spacing: -0.3px;
  color: var(--color-text-primary);
  transition: letter-spacing 0.25s ease;
}

// ---- Nav ----
.header-nav {
  display: flex; align-items: center; gap: 2px; flex: 1;
}

.nav-link {
  position: relative;
  display: inline-flex; align-items: center;
  padding: 0 12px; height: 52px;
  font-size: 14px; font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color $transition-base;

  &::after {
    content: '';
    position: absolute; bottom: 0; left: 12px; right: 12px;
    height: 2px; background: var(--color-primary);
    border-radius: 2px 2px 0 0;
    opacity: 0; transform: scaleX(0.6);
    transition: opacity $transition-base, transform $transition-base;
  }

  &:hover { color: var(--color-text-primary); }

  &.active {
    color: var(--color-primary);
    &::after { opacity: 1; transform: scaleX(1); }
  }
}

// ---- Actions ----
.header-actions {
  display: flex; align-items: center; gap: 8px; margin-left: auto;
}

.action-icon { width: 16px; height: 16px; display: block; }

// ---- Search ----
.search-box {
  display: flex; align-items: center; gap: 4px;
  width: 32px; height: 32px;
  background: transparent; border: 1px solid transparent;
  border-radius: $radius-md; padding: 0 6px; overflow: hidden;
  transition: width $transition-base, border-color $transition-base, background $transition-base;

  &.expanded {
    width: 200px;
    border-color: var(--color-primary);
    background: var(--color-surface);
    padding: 0 8px;
    html.dark & { background: var(--color-surface-hover); }
  }
}

.search-icon-btn {
  display: inline-flex; align-items: center; justify-content: center;
  background: none; border: none; padding: 0; cursor: pointer;
  color: var(--color-text-secondary); flex-shrink: 0;
  transition: color $transition-fast;
  &:hover { color: var(--color-text-primary); }
}

.search-input {
  flex: 1; border: none; outline: none; background: transparent;
  font-size: 13px; color: var(--color-text-primary); min-width: 0; width: 0;
  &::placeholder { color: var(--color-text-muted); }
}

// ---- Icon button ----
.icon-btn {
  position: relative;
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border: none; background: transparent;
  border-radius: $radius-md; color: var(--color-text-secondary);
  cursor: pointer; transition: color $transition-base, background $transition-base; padding: 0;

  &:hover { color: var(--color-text-primary); background: var(--color-surface-hover); }
  &.active { color: var(--color-primary); background: var(--color-primary-subtle); }
}

.login-btn { height: 30px; font-size: 13px; }

// ---- Mobile hamburger ----
.hamburger {
  display: flex; flex-direction: column; justify-content: center;
  gap: 4px; width: 16px; height: 16px;

  i {
    display: block; height: 1.5px;
    background: currentColor; border-radius: 1px;
    transform-origin: center;
    transition: transform $transition-base, opacity $transition-base;
  }

  &.open {
    i:nth-child(1) { transform: translateY(5.5px) rotate(45deg); }
    i:nth-child(2) { opacity: 0; transform: scaleX(0); }
    i:nth-child(3) { transform: translateY(-5.5px) rotate(-45deg); }
  }
}
</style>
