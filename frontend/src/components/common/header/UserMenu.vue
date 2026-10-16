<template>
  <div class="user-wrap" ref="userWrapRef">
    <button class="user-trigger" :class="{ active: menuOpen, 'has-review': hasReviewBadge }" @click="toggleMenu">
      <UserAvatar :src="avatarUrl" :user="userStore.currentUser" :size="28" />
    </button>

    <transition name="panel-pop">
      <div v-if="menuOpen" class="user-menu" @click.stop>
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
              <rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>
              <rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>
            </svg>
            <span>管理台</span>
            <span v-if="hasReviewBadge" class="menu-review-dot" />
          </button>
          <button class="menu-item menu-item--danger" @click="handleLogout">
            <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            <span>退出登录</span>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/modules/auth'

const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const menuOpen = ref(false)
const userWrapRef = ref<HTMLElement | null>(null)

const hasReviewBadge = computed(() => userStore.isAdminOrRoot && appStore.reviewCount > 0)

const avatarUrl = computed(() => {
  const user = userStore.currentUser
  if (user?.avatar) {
    const baseUrl = authApi.getAvatarUrl()
    const timestamp = new Date(user.updated_at).getTime()
    return `${baseUrl}?uid=${user.id}&t=${timestamp}`
  }
  return undefined
})

function toggleMenu() { menuOpen.value = !menuOpen.value }

function goToSettings() {
  menuOpen.value = false
  router.push({ name: 'Settings' })
}

function goToAdmin() {
  menuOpen.value = false
  router.push(hasReviewBadge.value ? '/admin/review' : { name: 'Admin' })
}

async function handleLogout() {
  menuOpen.value = false
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
    })
    await userStore.logout()
    router.push({ name: 'Home' })
  } catch { /* cancelled */ }
}

function handleOutside(e: MouseEvent) {
  if (userWrapRef.value && !userWrapRef.value.contains(e.target as Node)) menuOpen.value = false
}

onMounted(() => document.addEventListener('click', handleOutside))
onUnmounted(() => document.removeEventListener('click', handleOutside))
</script>

<style scoped lang="scss">
.user-wrap { position: relative; }

.user-trigger {
  position: relative; display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border: none; background: transparent;
  border-radius: 50%; cursor: pointer; padding: 0;
  transition: opacity $transition-base;
  &:hover, &.active { opacity: 0.8; }

  &.has-review::after {
    content: ''; position: absolute; top: 0; right: 0;
    width: 7px; height: 7px; border-radius: 50%;
    background: #f87171; border: 1.5px solid rgba(255, 255, 255, 0.92); z-index: 1;
    pointer-events: none; animation: review-pulse 2.2s ease-in-out infinite;
    html.dark & { border-color: rgba(28, 31, 38, 0.92); }
  }
}

.menu-review-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #ef4444; margin-left: auto; flex-shrink: 0;
}

.user-menu {
  position: absolute; top: calc(100% + 8px); right: 0;
  width: 148px; background: var(--color-surface);
  border: 1px solid var(--color-border); border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04);
  overflow: hidden; z-index: 200;
  @media (min-width: $breakpoint-xl) { right: -44px; }
  html.dark & { box-shadow: 0 8px 24px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.06); }
}

.user-menu-header {
  padding: 12px 12px 10px; border-bottom: 1px solid var(--color-border-subtle);
  display: flex; align-items: center; gap: 9px;
}

.user-menu-avatar { flex-shrink: 0; }

.user-menu-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }

.user-menu-name {
  font-size: 13px; font-weight: 600; color: var(--color-text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.user-menu-username {
  font-size: 11px; color: var(--color-text-muted);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.user-menu-body { padding: 4px; }

.menu-item {
  display: flex; align-items: center; gap: 8px;
  width: 100%; padding: 7px 10px; border: none; background: transparent;
  border-radius: $radius-sm; font-size: 13px; color: var(--color-text-primary);
  cursor: pointer; text-align: left; transition: background $transition-fast;
  &:hover { background: var(--color-surface-hover); }
  &--danger { color: #ef4444; .menu-icon { color: #ef4444; } &:hover { background: rgba(239,68,68,0.06); } }
}

.menu-icon { width: 14px; height: 14px; display: block; color: var(--color-text-muted); flex-shrink: 0; }

@keyframes review-pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(248, 113, 113, 0.5); }
  50%       { transform: scale(1.3); box-shadow: 0 0 0 4px rgba(248, 113, 113, 0); }
}

.panel-pop-enter-active { transition: opacity 0.15s ease, transform 0.18s cubic-bezier(0.34, 1.56, 0.64, 1); }
.panel-pop-leave-active { transition: opacity 0.1s ease, transform 0.1s ease; }
.panel-pop-enter-from { opacity: 0; transform: translateY(-6px) scale(0.97); }
.panel-pop-leave-to   { opacity: 0; transform: translateY(-4px) scale(0.98); }
</style>
