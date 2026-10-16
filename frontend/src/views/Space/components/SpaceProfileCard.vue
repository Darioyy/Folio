<template>
  <div class="profile-card">

    <!-- 封面 -->
    <div
      class="profile-cover"
      :class="{ 'has-custom': hasCustomCover }"
      :style="coverStyle"
      @click="coverFileRef?.click()"
    >
      <div class="cover-edit-hint">
        <button class="cover-act" @click.stop="coverFileRef?.click()">
          <svg viewBox="0 0 14 14" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="1" y="4" width="12" height="8" rx="1.5"/><circle cx="7" cy="8" r="2"/><path d="M4.5 4l.8-2h3.4l.8 2"/>
          </svg>
          上传图片
        </button>
        <button class="cover-act" @click.stop="$emit('open-preset')">
          <svg viewBox="0 0 14 14" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="1" y="1" width="5" height="5" rx="1"/><rect x="8" y="1" width="5" height="5" rx="1"/>
            <rect x="1" y="8" width="5" height="5" rx="1"/><rect x="8" y="8" width="5" height="5" rx="1"/>
          </svg>
          预设背景
        </button>
      </div>
      <input
        ref="coverFileRef"
        type="file"
        accept="image/*"
        style="display:none"
        @click.stop
        @change="onCoverChange"
      />
    </div>

    <!-- 名片主体 -->
    <div class="profile-body">
      <div class="avatar-section">
        <div class="avatar-upload" @click="avatarFileRef?.click()">
          <el-avatar :src="avatarUrl" :size="72" class="profile-avatar">
            {{ avatarFallback }}
          </el-avatar>
          <div class="avatar-hover">
            <el-icon><Camera /></el-icon>
          </div>
        </div>
        <input
          ref="avatarFileRef"
          type="file"
          accept="image/*"
          style="display:none"
          @change="onAvatarChange"
        />
      </div>

      <div class="name-row">
        <h1 class="profile-name">{{ displayName }}</h1>
        <span v-if="user?.is_root === 1" class="role-tag root">ROOT</span>
        <span v-else-if="user?.is_admin === 1" class="role-tag admin">ADMIN</span>
      </div>
      <p class="profile-handle">@{{ user?.username }}</p>
      <p class="profile-bio">{{ user?.signature || '这个人很懒，什么都没留下' }}</p>

      <div class="profile-stats">
        <div class="stat-item clickable" @click="$emit('go-following')">
          <span class="stat-num">{{ user?.following_count || 0 }}</span>
          <span class="stat-label">关注</span>
        </div>
        <span class="stat-sep">·</span>
        <div class="stat-item clickable" @click="$emit('go-followers')">
          <span class="stat-num">{{ user?.followers_count || 0 }}</span>
          <span class="stat-label">粉丝</span>
        </div>
        <span class="stat-sep">·</span>
        <div class="stat-item">
          <span class="stat-num">{{ (user as any)?.like_count || 0 }}</span>
          <span class="stat-label">获赞</span>
        </div>
      </div>
    </div>

    <!-- Tab 栏 -->
    <div ref="zoneTabsEl" class="zone-tabs">
      <span
        v-for="tab in zoneTabs"
        :key="tab.value"
        :class="['zone-tab', { active: activeZone === tab.value }]"
        @click="handleZoneClick(tab.value)"
      >{{ tab.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { Camera } from '@element-plus/icons-vue'
import type { User } from '@/types/models'

type ZoneType = 'overview' | 'files' | 'posts' | 'favorites'

const props = defineProps<{
  user: User | null
  avatarUrl: string | undefined
  coverStyle: Record<string, string>
  hasCustomCover: boolean
  activeZone: ZoneType
  zoneTabs: Array<{ value: ZoneType; label: string }>
}>()

const emit = defineEmits<{
  'avatar-file': [file: File]
  'cover-file': [file: File]
  'zone-change': [zone: ZoneType]
  'open-preset': []
  'go-followers': []
  'go-following': []
}>()

const coverFileRef = ref<HTMLInputElement | null>(null)
const avatarFileRef = ref<HTMLInputElement | null>(null)
const zoneTabsEl = ref<HTMLElement | null>(null)

const displayName = computed(() => props.user?.nickname || props.user?.username || '')
const avatarFallback = computed(() => props.user?.nickname?.[0] || props.user?.username?.[0] || '?')

function onCoverChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  emit('cover-file', file)
  ;(e.target as HTMLInputElement).value = ''
}

function onAvatarChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  emit('avatar-file', file)
  ;(e.target as HTMLInputElement).value = ''
}

function handleZoneClick(zone: ZoneType) {
  emit('zone-change', zone)
  nextTick(() => {
    const el = zoneTabsEl.value
    if (el) {
      window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 52, behavior: 'smooth' })
    }
  })
}
</script>

<style scoped lang="scss">
.profile-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: $radius-xl;
  overflow: hidden;
  margin-bottom: $spacing-lg;
}

// ── 封面 ─────────────────────────────────────────────
.profile-cover {
  height: 132px;
  background: linear-gradient(140deg, $color-primary 0%, $color-primary-dark 100%);
  background-size: cover;
  background-position: center;
  position: relative;
  overflow: hidden;
  cursor: pointer;

  &::before {
    content: '';
    position: absolute;
    width: 240px; height: 240px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.06);
    bottom: -96px; right: 48px;
    pointer-events: none;
  }

  &::after {
    content: '';
    position: absolute;
    width: 110px; height: 110px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.05);
    top: -36px; right: 200px;
    pointer-events: none;
  }

  &.has-custom::before,
  &.has-custom::after { display: none; }

  &:hover .cover-edit-hint { opacity: 1; pointer-events: auto; }
}

.cover-edit-hint {
  position: absolute;
  bottom: 8px; right: 10px;
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity $transition-fast;
  pointer-events: none;
}

.cover-act {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: $radius-full;
  background: rgba(0, 0, 0, 0.36);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.9);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.12s;
  user-select: none;

  &:hover { background: rgba(0, 0, 0, 0.52); }
}

// ── 名片主体 ─────────────────────────────────────────
.profile-body {
  padding: 0 $spacing-xl $spacing-md;
}

.avatar-section {
  margin-top: -38px;
  margin-bottom: $spacing-sm;
}

.avatar-upload {
  position: relative;
  display: inline-block;
  cursor: pointer;
  border-radius: 50%;

  &:hover .avatar-hover { opacity: 1; }
}

.profile-avatar {
  border: 3px solid var(--color-surface);
  font-size: 26px; font-weight: 700;
  background: linear-gradient(135deg, $color-primary, $color-secondary);
  color: #fff;
  line-height: 1;
}

.avatar-hover {
  position: absolute; inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.42);
  display: flex; align-items: center; justify-content: center;
  color: #fff; opacity: 0;
  transition: opacity $transition-base;
  border: 3px solid transparent;

  .el-icon { font-size: 18px; }
}

.name-row {
  display: flex; align-items: center; gap: 7px;
  margin-bottom: 3px;
}

.profile-name {
  font-size: $font-xl; font-weight: 700;
  font-family: $font-heading;
  color: var(--color-text-primary);
  margin: 0; line-height: 1.2;
}

.role-tag {
  font-size: 10px; font-weight: 600;
  font-family: $font-mono;
  letter-spacing: 0.06em;
  padding: 1px 6px;
  border-radius: $radius-sm;
  flex-shrink: 0;

  &.root  { background: rgba(239,68,68,.08); color: #ef4444; border: 1px solid rgba(239,68,68,.22); }
  &.admin { background: rgba(245,158,11,.08); color: #d97706; border: 1px solid rgba(245,158,11,.22); }
}

.profile-handle {
  font-size: $font-xs; color: var(--color-text-muted); margin: 0 0 6px;
}

.profile-bio {
  font-size: $font-13; color: var(--color-text-secondary);
  margin: 0; line-height: 1.55;
  overflow: hidden; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}

.profile-stats {
  display: flex; align-items: center; gap: 10px;
  margin-top: 14px; padding-top: 14px;
  border-top: 1px solid var(--color-border-subtle);
}

.stat-item {
  display: flex; align-items: baseline; gap: 4px;

  &.clickable {
    cursor: pointer;
    &:hover .stat-num { color: $color-primary; }
  }
}

.stat-num {
  font-size: 15px; font-weight: 600;
  color: var(--color-text-primary);
  transition: color $transition-fast;
  font-variant-numeric: tabular-nums;
}

.stat-label { font-size: $font-xs; color: var(--color-text-muted); }

.stat-sep { font-size: 14px; color: var(--color-border); user-select: none; }

// ── Tab 栏 ───────────────────────────────────────────
.zone-tabs {
  display: flex; align-items: stretch;
  border-top: 1px solid var(--color-border-subtle);
  padding: 0 $spacing-lg;
}

.zone-tab {
  position: relative;
  flex: 1;
  display: flex; align-items: center; justify-content: center;
  padding: 12px 8px 11px;
  font-size: 13px; font-weight: 500;
  letter-spacing: 0.04em;
  color: var(--color-text-muted);
  cursor: pointer; user-select: none;
  transition: color $transition-fast;

  &::after {
    content: '';
    position: absolute;
    bottom: 0; left: 22%; right: 22%;
    height: 2px;
    background: $color-primary;
    border-radius: 2px 2px 0 0;
    opacity: 0;
    transform: scaleX(0.3);
    transition: opacity 0.18s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  &:hover { color: var(--color-text-secondary); }

  &.active {
    color: $color-primary;
    font-weight: 600;
    letter-spacing: 0.02em;
    &::after { opacity: 1; transform: scaleX(1); }
  }
}

@media (max-width: $breakpoint-sm) {
  .profile-body { padding: 0 $spacing-md $spacing-md; }
  .zone-tabs    { padding: 0 $spacing-md; }
  .profile-name { font-size: $font-lg; }
}
</style>
