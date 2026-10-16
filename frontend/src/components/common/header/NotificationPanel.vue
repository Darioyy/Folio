<template>
  <div v-if="userStore.isLoggedIn" class="notif-wrap" ref="notifWrapRef">
    <button class="notif-btn" :class="{ active: panelOpen }" @click="togglePanel">
      <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
      <span v-if="unreadCount > 0" class="notif-badge">
        <span v-if="unreadCount >= 10" class="notif-badge-num">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
      </span>
    </button>

    <transition name="panel-pop">
      <div v-if="panelOpen" class="notif-panel" @click.stop>
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
            @click="onNotifClick(n)"
          >
            <div class="notif-avatar">{{ (n.actor_nickname || n.actor_username || '?')[0] }}</div>
            <div class="notif-content">
              <p class="notif-text">{{ formatNotif(n) }}</p>
              <span class="notif-time">{{ fromNow(n.created_at) }}</span>
            </div>
          </div>
        </div>

        <div v-if="notifications.length > 0" class="notif-foot">
          <button class="view-all-btn" @click="() => { panelOpen = false; router.push('/notifications') }">查看全部通知</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import type { Notification } from '@/types/models'
import { useUserStore } from '@/stores/user'
import { fromNow } from '@/utils/format'
import { useHeaderNotifications } from '@/composables/useHeaderNotifications'

const router = useRouter()
const userStore = useUserStore()

const { unreadCount, notifications, notifLoading, fetchUnreadCount, loadNotifications, clearAllNotifications, handleNotifClick, formatNotif } = useHeaderNotifications()

const panelOpen = ref(false)
const notifWrapRef = ref<HTMLElement | null>(null)
let timer: ReturnType<typeof setInterval> | null = null

function togglePanel() {
  panelOpen.value = !panelOpen.value
  if (panelOpen.value) loadNotifications()
}

function onNotifClick(n: Notification) {
  panelOpen.value = false
  handleNotifClick(n)
}

function handleOutside(e: MouseEvent) {
  if (notifWrapRef.value && !notifWrapRef.value.contains(e.target as Node)) panelOpen.value = false
}

onMounted(() => {
  if (userStore.isLoggedIn) {
    fetchUnreadCount()
    timer = setInterval(fetchUnreadCount, 30000)
  }
  document.addEventListener('click', handleOutside)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  document.removeEventListener('click', handleOutside)
})
</script>

<style scoped lang="scss">
.notif-wrap { position: relative; }

.notif-btn {
  position: relative;
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px;
  border: none; background: transparent; border-radius: $radius-md;
  color: var(--color-text-secondary); cursor: pointer; padding: 0;
  transition: color $transition-base, background $transition-base;
  &:hover { color: var(--color-text-primary); background: var(--color-surface-hover); }
  &.active { color: var(--color-primary); background: var(--color-primary-subtle); }
}

.action-icon { width: 16px; height: 16px; display: block; }

.notif-badge {
  position: absolute; top: 4px; right: 4px;
  min-width: 8px; height: 8px; padding: 0;
  background: #e05555; border: 1.5px solid var(--color-surface, #fff); border-radius: 8px;
  display: flex; align-items: center; justify-content: center; pointer-events: none;
  html.dark & { border-color: rgba(28, 31, 38, 0.92); }
}

.notif-badge-num { font-size: 9px; font-weight: 700; color: white; line-height: 1; padding: 0 3px; }

.notif-panel {
  position: absolute; top: calc(100% + 8px); right: 0;
  width: 300px; background: var(--color-surface);
  border: 1px solid var(--color-border); border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04);
  overflow: hidden; z-index: 200;
  html.dark & { box-shadow: 0 8px 24px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.06); }
}

.notif-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px 10px; border-bottom: 1px solid var(--color-border-subtle);
}

.notif-title { font-size: 13px; font-weight: 600; color: var(--color-text-primary); }

.clear-btn {
  font-size: 12px; color: var(--color-text-muted); background: none; border: none;
  cursor: pointer; padding: 2px 6px; border-radius: $radius-sm; transition: color $transition-base;
  &:hover { color: #ef4444; }
}

.notif-empty { padding: $spacing-lg $spacing-md; font-size: 13px; color: var(--color-text-muted); text-align: center; }

.notif-list { max-height: 320px; overflow-y: auto; }

.notif-item {
  display: flex; align-items: flex-start; gap: $spacing-sm;
  padding: 10px 14px; cursor: pointer; transition: background $transition-fast;
  &:hover { background: var(--color-surface-raised); }
}

.notif-avatar {
  flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%;
  background: var(--color-primary-subtle); color: var(--color-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600; position: relative;

  .notif-item.unread & {
    &::after {
      content: ''; position: absolute; top: 1px; right: 1px;
      width: 6px; height: 6px; border-radius: 50%;
      background: #f87171; border: 1px solid var(--color-surface);
    }
  }
}

.notif-content { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }

.notif-text { font-size: 12px; color: var(--color-text-primary); line-height: 1.45; word-break: break-word; margin: 0; }

.notif-time { font-size: 11px; color: var(--color-text-muted); text-align: right; align-self: flex-end; }

.notif-foot { padding: 8px 14px; border-top: 1px solid var(--color-border-subtle); text-align: center; }

.view-all-btn {
  font-size: 12px; color: var(--color-text-muted); background: none; border: none;
  cursor: pointer; padding: 4px 8px; border-radius: $radius-sm; transition: color $transition-base;
  &:hover { color: var(--color-primary); }
}

.panel-pop-enter-active { transition: opacity 0.15s ease, transform 0.18s cubic-bezier(0.34, 1.56, 0.64, 1); }
.panel-pop-leave-active { transition: opacity 0.1s ease, transform 0.1s ease; }
.panel-pop-enter-from { opacity: 0; transform: translateY(-6px) scale(0.97); }
.panel-pop-leave-to   { opacity: 0; transform: translateY(-4px) scale(0.98); }
</style>
