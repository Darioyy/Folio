<template>
  <nav class="app-tabbar">
    <router-link to="/" :class="['tab-item', { active: isHome }]">
      <div class="tab-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
      </div>
      <span class="tab-label">首页</span>
    </router-link>

    <router-link to="/blog" :class="['tab-item', { active: isBlog }]">
      <div class="tab-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="2" y1="12" x2="22" y2="12"/>
          <path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
        </svg>
      </div>
      <span class="tab-label">发现</span>
    </router-link>

    <template v-if="userStore.isLoggedIn">
      <router-link to="/space" :class="['tab-item', { active: isSpace }]">
        <div class="tab-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
          </svg>
        </div>
        <span class="tab-label">空间</span>
      </router-link>

      <router-link to="/settings" :class="['tab-item', { active: isMe }]">
        <div class="tab-icon tab-avatar-wrap">
          <UserAvatar :src="avatarUrl" :user="userStore.currentUser" :size="22" />
        </div>
        <span class="tab-label">我</span>
      </router-link>
    </template>

    <template v-else>
      <div class="tab-item" @click="goToLogin">
        <div class="tab-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
          </svg>
        </div>
        <span class="tab-label">空间</span>
      </div>

      <div class="tab-item" @click="goToLogin">
        <div class="tab-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
        <span class="tab-label">登录</span>
      </div>
    </template>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { authApi } from '@/api/modules/auth'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isHome = computed(() => route.path === '/')
const isBlog = computed(() => route.path.startsWith('/blog') || (route.path.startsWith('/post') && !route.path.startsWith('/posts')))
const isSpace = computed(() => route.path.startsWith('/space'))
const isMe = computed(() => route.path.startsWith('/settings') || route.path.startsWith('/u/'))

const avatarUrl = computed(() => {
  const user = userStore.currentUser
  if (user?.avatar) {
    const baseUrl = authApi.getAvatarUrl()
    const timestamp = new Date(user.updated_at).getTime()
    return `${baseUrl}?uid=${user.id}&t=${timestamp}`
  }
  return undefined
})

function goToLogin() {
  router.push({ name: 'Login', query: { redirect: route.fullPath } })
}
</script>

<style scoped lang="scss">
.app-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 200;
  display: flex;
  align-items: stretch;
  background: rgba(255, 255, 255, 0.92);
  border-top: 1px solid var(--el-border-color-light);
  padding-bottom: env(safe-area-inset-bottom, 0);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);

  html.dark & {
    background: rgba(28, 31, 38, 0.92);
    border-top-color: #2d3242;
  }

  @media (min-width: 641px) {
    display: none;
  }
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 8px 4px 6px;
  text-decoration: none;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  transition: color $transition-fast;
  border: none;
  background: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;

  &.active {
    color: $color-primary;
  }
}

.tab-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;

  svg { width: 20px; height: 20px; }
}

.tab-avatar-wrap {
  :deep(.el-avatar),
  :deep(img) {
    width: 22px !important;
    height: 22px !important;
    min-width: 22px !important;
    border-radius: 50%;
    font-size: 10px;
  }
}

.tab-label {
  font-size: 10px;
  font-weight: 500;
  line-height: 1;
}
</style>
