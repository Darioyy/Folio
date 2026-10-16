<template>
  <div class="notif-page">
    <AppHeader />

    <main class="notif-main">
      <div class="notif-wrap">

        <!-- Page header -->
        <header class="page-head">
          <div class="page-head-left">
            <h1 class="page-title">通知</h1>
            <transition name="badge-pop">
              <span v-if="unreadCount > 0" class="unread-badge">
                {{ unreadCount > 99 ? '99+' : unreadCount }}
              </span>
            </transition>
          </div>
          <transition name="fade">
            <button
              v-if="unreadCount > 0"
              class="mark-all-btn"
              :disabled="marking"
              @click="markAllRead"
            >
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 8l4 4 8-8"/>
              </svg>
              全部已读
            </button>
          </transition>
        </header>

        <!-- Loading skeleton -->
        <div v-if="loading && !notifications.length" class="skeleton-wrap">
          <div v-for="i in 5" :key="i" class="skeleton-item" :style="{ animationDelay: `${i * 0.06}s` }">
            <div class="sk-avatar"></div>
            <div class="sk-lines">
              <div class="sk-line" :style="{ width: `${55 + (i % 3) * 15}%` }"></div>
              <div class="sk-line short"></div>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else-if="!loading && !notifications.length" class="empty-state">
          <svg class="empty-svg" viewBox="0 0 120 100" fill="none">
            <ellipse cx="60" cy="88" rx="28" ry="5" fill="var(--color-border-subtle)"/>
            <rect x="38" y="18" width="44" height="56" rx="6" fill="var(--color-surface-raised)" stroke="var(--color-border)" stroke-width="1.5"/>
            <path d="M48 34h24M48 42h18M48 50h20M48 58h12" stroke="var(--color-border)" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="84" cy="28" r="14" fill="var(--color-surface)" stroke="var(--color-border)" stroke-width="1.5"/>
            <path d="M84 21v8l4 3" stroke="var(--color-text-muted)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p class="empty-title">暂无通知</p>
          <router-link to="/blog" class="empty-link">去发现页看看 →</router-link>
        </div>

        <!-- Grouped notifications -->
        <template v-else>
          <section
            v-for="group in groupedNotifications"
            :key="group.label"
            class="notif-group"
          >
            <div class="group-header">
              <span class="group-label">{{ group.label }}</span>
            </div>

            <div class="notif-list">
              <div
                v-for="n in group.items"
                :key="n.id"
                class="notif-item"
                :class="{ unread: !n.is_read }"
                @click="handleClick(n)"
              >
                <div class="notif-avatar" :style="{ '--avatar-bg': typeColor(n.type) }">
                  {{ actorInitial(n) }}
                </div>
                <div class="notif-body">
                  <p class="notif-text">{{ formatNotif(n) }}</p>
                  <time class="notif-time">{{ fromNow(n.created_at) }}</time>
                </div>
                <span v-if="!n.is_read" class="unread-dot" />
              </div>
            </div>
          </section>

          <!-- Load more -->
          <div v-if="hasMore" class="load-more-wrap">
            <button class="load-more-btn" :disabled="loadingMore" @click="loadMore">
              <span v-if="loadingMore" class="spinner" />
              <span v-else>加载更多</span>
            </button>
          </div>
        </template>

      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import { notificationsApi } from '@/api/modules/notifications'
import type { Notification } from '@/types/models'
import { fromNow } from '@/utils/format'

const router = useRouter()

const notifications = ref<Notification[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const marking = ref(false)
const page = ref(1)
const total = ref(0)
const PAGE_SIZE = 20

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)
const hasMore = computed(() => notifications.value.length < total.value)

// ── Date grouping ──────────────────────────────────────────────
interface NotifGroup { label: string; items: Notification[] }

const groupedNotifications = computed<NotifGroup[]>(() => {
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const yesterdayStart = todayStart - 86400000

  const buckets: { today: Notification[]; yesterday: Notification[]; earlier: Notification[] } = {
    today: [], yesterday: [], earlier: []
  }

  for (const n of notifications.value) {
    const t = new Date(n.created_at).getTime()
    if (t >= todayStart) buckets.today.push(n)
    else if (t >= yesterdayStart) buckets.yesterday.push(n)
    else buckets.earlier.push(n)
  }

  const result: NotifGroup[] = []
  if (buckets.today.length)     result.push({ label: '今天',  items: buckets.today })
  if (buckets.yesterday.length) result.push({ label: '昨天',  items: buckets.yesterday })
  if (buckets.earlier.length)   result.push({ label: '更早',  items: buckets.earlier })
  return result
})

function actorInitial(n: Notification): string {
  return (n.actor_nickname || n.actor_username || '?')[0].toUpperCase()
}

function typeColor(type: string): string {
  const map: Record<string, string> = {
    like:          'rgba(251, 113, 133, 0.18)',
    collect:       'rgba(251, 191, 36, 0.18)',
    comment:       'rgba(59, 130, 246, 0.16)',
    reply:         'rgba(59, 130, 246, 0.16)',
    follow:        'rgba(16, 185, 129, 0.16)',
    new_post:      'rgba(90, 103, 216, 0.14)',
    admin:         'rgba(107, 114, 128, 0.15)',
    review_result: 'rgba(107, 114, 128, 0.15)',
    appeal:        'rgba(249, 115, 22, 0.16)',
    report:        'rgba(249, 115, 22, 0.16)',
    pinned:        'rgba(245, 158, 11, 0.18)',
  }
  return map[type] ?? 'rgba(90, 103, 216, 0.12)'
}

function formatNotif(n: Notification): string {
  const actor = n.actor_nickname || n.actor_username || '管理员'
  const postTitle = n.extra?.post_title ? `《${n.extra.post_title}》` : '你的博文'
  const content = n.extra?.content ? `：${n.extra.content}` : ''
  const reason = n.extra?.reason || ''

  switch (n.type) {
    case 'like':    return `${actor} 赞了 ${postTitle}`
    case 'collect': return `${actor} 收藏了 ${postTitle}`
    case 'comment': return `${actor} 评论了 ${postTitle}${content}`
    case 'reply':   return `${actor} 回复了你的评论${content}`
    case 'follow':  return `${actor} 关注了你`
    case 'new_post': return `您关注的 ${actor} 发布了新博文 ${postTitle}`
    case 'admin': {
      const action = n.extra?.action
      if (action === 'report_valid')   return `您举报的 ${postTitle} 经审核已被隐藏`
      if (action === 'report_invalid') return `您举报的 ${postTitle} 经审核暂不违规`
      return `你的博文 ${postTitle} 已被隐藏${reason ? '，原因：' + reason : ''}`
    }
    case 'appeal': {
      const ap = n.extra?.post_title ? `《${n.extra.post_title}》` : '某博文'
      return `${actor} 对 ${ap} 提交了申诉`
    }
    case 'review_result': {
      const ok = n.extra?.action === 'approved'
      return ok
        ? `你对 ${postTitle} 的申诉已通过，博文已恢复`
        : `你对 ${postTitle} 的申诉被拒绝${reason ? '，原因：' + reason : ''}`
    }
    case 'report': {
      const rp = n.extra?.post_title ? `《${n.extra.post_title}》` : '某博文'
      return `${actor} 对 ${rp} 提交了举报${n.extra?.reason ? '，理由：' + n.extra.reason : ''}`
    }
    case 'pinned': return `博文 ${postTitle} 已被置顶推荐`
    default: return '新通知'
  }
}

function handleClick(n: Notification) {
  if (!n.is_read) {
    n.is_read = 1
    notificationsApi.readOne(n.id).catch(() => {})
  }
  if (n.type === 'follow') {
    router.push(`/u/${n.actor_username}`)
  } else if (n.type === 'admin') {
    const action = n.extra?.action
    if (action === 'report_invalid') {
      if (n.target_id) router.push(`/post/${n.target_id}`)
    } else if (action !== 'report_valid') {
      if (n.target_id) router.push(`/post/${n.target_id}/moderation`)
    }
  } else if (n.type === 'review_result') {
    if (n.target_id) {
      router.push(n.extra?.action === 'approved'
        ? `/post/${n.target_id}`
        : `/post/${n.target_id}/moderation`)
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

async function loadNotifications(reset = true) {
  if (reset) {
    loading.value = true
    page.value = 1
  } else {
    loadingMore.value = true
    page.value++
  }
  try {
    const res = await notificationsApi.getList(page.value, PAGE_SIZE)
    if (reset) {
      notifications.value = res.items ?? []
    } else {
      notifications.value.push(...(res.items ?? []))
    }
    total.value = (res as any).total ?? notifications.value.length
  } catch { /* silent */ } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function loadMore() {
  await loadNotifications(false)
}

async function markAllRead() {
  marking.value = true
  try {
    await notificationsApi.readAll()
    notifications.value.forEach(n => { n.is_read = 1 })
  } catch { /* silent */ } finally {
    marking.value = false
  }
}

onMounted(() => loadNotifications())
</script>

<style scoped lang="scss">
.notif-page {
  min-height: 100vh;
  background: var(--color-surface-raised);
  display: flex;
  flex-direction: column;
}

.notif-main {
  flex: 1;
  padding: $spacing-xl $spacing-md;

  @media (max-width: $breakpoint-sm) {
    padding: $spacing-lg $spacing-sm;
  }
}

.notif-wrap { max-width: 680px; margin: 0 auto; }

// ── Page header ────────────────────────────────────────────────
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-xl;
  padding-bottom: $spacing-lg;
  border-bottom: 1px solid var(--color-border);
}

.page-head-left { display: flex; align-items: center; gap: $spacing-sm; }

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: -0.4px;
}

.unread-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: $color-primary;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.mark-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-size: $font-sm;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: $radius-md;
  cursor: pointer;
  transition: color $transition-fast, border-color $transition-fast, background $transition-fast;

  &:hover:not(:disabled) {
    color: $color-primary;
    border-color: $color-primary;
    background: rgba(90, 103, 216, 0.05);
  }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}

// ── Skeleton ───────────────────────────────────────────────────
.skeleton-wrap { display: flex; flex-direction: column; }

.skeleton-item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: 14px 0;
  border-bottom: 1px solid var(--color-border-subtle);
  opacity: 0;
  animation: sk-fade-in 0.3s ease forwards;

  &:last-child { border-bottom: none; }
}

@keyframes sk-fade-in { to { opacity: 1; } }

.sk-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
  background: linear-gradient(90deg,
    var(--color-surface-raised) 0%, var(--color-surface-hover) 50%,
    var(--color-surface-raised) 100%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.sk-lines { flex: 1; display: flex; flex-direction: column; gap: 7px; }

.sk-line {
  height: 11px;
  border-radius: 6px;
  background: linear-gradient(90deg,
    var(--color-surface-raised) 0%, var(--color-surface-hover) 50%,
    var(--color-surface-raised) 100%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;

  &.short { width: 28%; }
}

@keyframes shimmer { to { background-position: -200% 0; } }

// ── Empty state ────────────────────────────────────────────────
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 0 40px;
  gap: $spacing-sm;
}

.empty-svg { width: 120px; height: 100px; margin-bottom: $spacing-sm; opacity: 0.7; }

.empty-title {
  font-size: $font-base;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin: 0;
}

.empty-link {
  font-size: $font-sm;
  color: $color-primary;
  text-decoration: none;
  opacity: 0.8;
  transition: opacity $transition-fast;

  &:hover { opacity: 1; }
}

// ── Groups ─────────────────────────────────────────────────────
.notif-group { & + & { margin-top: $spacing-lg; } }

.group-header {
  position: sticky;
  top: 52px;
  z-index: 10;
  background: var(--color-surface-raised);
  padding: $spacing-xs 0;
  margin-bottom: 2px;
}

.group-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.notif-list {
  border: 1px solid var(--color-border);
  border-radius: $radius-lg;
  overflow: hidden;
  background: var(--color-surface);
}

// ── Item ───────────────────────────────────────────────────────
.notif-item {
  display: flex;
  align-items: flex-start;
  gap: $spacing-sm;
  padding: 14px $spacing-md;
  border-bottom: 1px solid var(--color-border-subtle);
  cursor: pointer;
  position: relative;
  transition: background $transition-fast;

  &:last-child { border-bottom: none; }
  &:hover { background: var(--color-surface-hover); }

  &.unread {
    background: rgba(90, 103, 216, 0.04);

    html.dark & { background: rgba(107, 121, 224, 0.08); }

    &::before {
      content: '';
      position: absolute;
      left: 0; top: 0; bottom: 0;
      width: 2px;
      background: $color-primary;
      border-radius: 0 2px 2px 0;
    }

    &:hover { background: rgba(90, 103, 216, 0.07); }
  }
}

.notif-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--avatar-bg, rgba(90, 103, 216, 0.12));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-top: 1px;
}

.notif-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }

.notif-text {
  font-size: $font-sm;
  color: var(--color-text-primary);
  line-height: 1.5;
  margin: 0;
  word-break: break-word;
}

.notif-time { font-size: 11px; color: var(--color-text-muted); }

.unread-dot {
  flex-shrink: 0;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: $color-primary;
  margin-top: 6px;
  opacity: 0.7;
}

// ── Load more ──────────────────────────────────────────────────
.load-more-wrap { display: flex; justify-content: center; padding: $spacing-xl 0 $spacing-md; }

.load-more-btn {
  display: inline-flex;
  align-items: center;
  gap: $spacing-xs;
  padding: 7px 20px;
  font-size: $font-sm;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: $radius-md;
  cursor: pointer;
  min-width: 100px;
  justify-content: center;
  transition: color $transition-fast, border-color $transition-fast;

  &:hover:not(:disabled) { color: $color-primary; border-color: $color-primary; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}

.spinner {
  width: 13px;
  height: 13px;
  border: 1.5px solid var(--color-border);
  border-top-color: $color-primary;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}

@keyframes spin { to { transform: rotate(360deg); } }

.fade-enter-active, .fade-leave-active { transition: opacity $transition-fast; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.badge-pop-enter-active { transition: opacity 0.2s ease, transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1); }
.badge-pop-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.badge-pop-enter-from, .badge-pop-leave-to { opacity: 0; transform: scale(0.6); }
</style>
