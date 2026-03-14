<template>
  <div class="space-page">
    <AppHeader />

    <div class="space-container">
      <!-- 用户名片 -->
      <div class="profile-card">

        <!-- 封面 -->
        <div
          class="profile-cover"
          :class="{ 'has-custom': !!coverMeta.image }"
          :style="coverStyle"
          @click="triggerCoverUpload"
        >
          <div class="cover-edit-hint">
            <button class="cover-act" @click.stop="triggerCoverUpload">
              <svg viewBox="0 0 14 14" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="1" y="4" width="12" height="8" rx="1.5"/>
                <circle cx="7" cy="8" r="2"/>
                <path d="M4.5 4l.8-2h3.4l.8 2"/>
              </svg>
              上传图片
            </button>
            <button class="cover-act" @click.stop="presetVisible = true">
              <svg viewBox="0 0 14 14" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="1" y="1" width="5" height="5" rx="1"/>
                <rect x="8" y="1" width="5" height="5" rx="1"/>
                <rect x="1" y="8" width="5" height="5" rx="1"/>
                <rect x="8" y="8" width="5" height="5" rx="1"/>
              </svg>
              预设背景
            </button>
          </div>
          <input
            ref="coverInputRef"
            type="file"
            accept="image/*"
            style="display:none"
            @click.stop
            @change="handleCoverChange"
          />
        </div>

        <!-- 名片主体 -->
        <div class="profile-body">
          <!-- 头像 -->
          <div class="avatar-section">
            <div class="avatar-upload" @click="triggerAvatarUpload">
              <el-avatar :src="avatarUrl" :size="72" class="profile-avatar">
                {{ avatarFallback }}
              </el-avatar>
              <div class="avatar-hover">
                <el-icon><Camera /></el-icon>
              </div>
            </div>
            <input
              ref="avatarInputRef"
              type="file"
              accept="image/*"
              style="display: none"
              @change="handleAvatarChange"
            />
          </div>

          <!-- 身份信息 -->
          <div class="name-row">
            <h1 class="profile-name">{{ displayName }}</h1>
            <span v-if="user?.is_root === 1" class="role-tag root">ROOT</span>
            <span v-else-if="user?.is_admin === 1" class="role-tag admin">ADMIN</span>
          </div>
          <p class="profile-handle">@{{ user?.username }}</p>
          <p class="profile-bio">{{ user?.signature || '这个人很懒，什么都没留下' }}</p>

          <!-- 统计数据 -->
          <div class="profile-stats">
            <div class="stat-item clickable" @click="goToFollowing">
              <span class="stat-num">{{ user?.following_count || 0 }}</span>
              <span class="stat-label">关注</span>
            </div>
            <span class="stat-sep">·</span>
            <div class="stat-item clickable" @click="goToFollowers">
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
        <div ref="zoneTabsRef" class="zone-tabs">
          <span
            v-for="tab in zoneTabs" :key="tab.value"
            :class="['zone-tab', { active: activeZone === tab.value }]"
            @click="selectZone(tab.value)"
          >{{ tab.label }}</span>
        </div>
      </div>

      <!-- Tab 内容区 -->
      <div class="tab-content-area">
        <Transition name="tab-fade">
          <Overview  v-if="activeZone === 'overview'"  key="overview" />
          <Files     v-else-if="activeZone === 'files'"     key="files" />
          <Posts     v-else-if="activeZone === 'posts'"     key="posts" />
          <Favorites v-else-if="activeZone === 'favorites'" key="favorites" />
        </Transition>
      </div>
    </div>
  </div>

  <!-- 封面预设选择器 -->
  <CoverPresetPicker v-model="presetVisible" @select="handlePresetSelect" />

  <!-- 图片裁剪器 -->
  <ImageCropper
    v-model="cropperVisible"
    :src="cropperSrc"
    :circular="cropperMode === 'avatar'"
    :aspect-ratio="cropperMode === 'cover' ? undefined : 1"
    :output-width="cropperMode === 'cover' ? 1200 : 320"
    :display-hint="cropperMode === 'cover' ? '封面显示区 全宽×132px' : ''"
    @confirm="handleCropConfirm"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onActivated, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Camera } from '@element-plus/icons-vue'
import AppHeader from '@/components/common/AppHeader.vue'
import ImageCropper from '@/components/common/ImageCropper.vue'
import CoverPresetPicker from '@/components/business/CoverPresetPicker.vue'
import Overview from './tabs/Overview.vue'
import Files from './tabs/Files.vue'
import Posts from './tabs/Posts.vue'
import Favorites from './tabs/Favorites.vue'
import { useUserStore } from '@/stores/user'
import { usersApi } from '@/api/modules/users'
import { authApi } from '@/api/modules/auth'

type ZoneType = 'overview' | 'files' | 'posts' | 'favorites'

defineOptions({ name: 'SpaceView' })

const router = useRouter()
const userStore = useUserStore()

const zoneTabs = [
  { value: 'overview'  as ZoneType, label: '主页' },
  { value: 'files'     as ZoneType, label: '云盘' },
  { value: 'posts'     as ZoneType, label: '文章' },
  { value: 'favorites' as ZoneType, label: '收藏' },
]

const activeZone     = ref<ZoneType>('overview')
const user           = computed(() => userStore.currentUser)
const avatarInputRef   = ref<HTMLInputElement | null>(null)
const coverInputRef    = ref<HTMLInputElement | null>(null)
const avatarTimestamp  = ref(Date.now())
const coverMeta = reactive({ image: '', size: 'cover' })
const presetVisible = ref(false)

function coverStorageKey(uid: number) { return `space_cover_${uid}` }

function loadCustomCover() {
  const uid = userStore.currentUser?.id
  if (!uid) return
  const stored = localStorage.getItem(coverStorageKey(uid))
  if (!stored) { coverMeta.image = ''; return }
  try {
    const parsed = JSON.parse(stored)
    if (parsed.image) { coverMeta.image = parsed.image; coverMeta.size = parsed.size || 'cover'; return }
  } catch { /* legacy */ }
  // 兼容旧格式：裸 data URL
  coverMeta.image = `url(${stored})`
  coverMeta.size = 'cover'
}

const coverStyle = computed(() => {
  if (!coverMeta.image) return {}
  return {
    backgroundImage: coverMeta.image,
    backgroundSize: coverMeta.size,
    backgroundPosition: 'center',
    backgroundRepeat: coverMeta.size !== 'cover' ? 'repeat' : 'no-repeat',
  }
})

watch(() => userStore.currentUser?.id, (uid) => { if (uid) loadCustomCover() }, { immediate: true })

const avatarUrl = computed(() => {
  const u = userStore.currentUser
  if (u?.avatar) return `${authApi.getAvatarUrl()}?uid=${u.id}&t=${avatarTimestamp.value}`
  return undefined
})

const avatarFallback = computed(() => {
  const u = userStore.currentUser
  return u?.nickname?.[0] || u?.username?.[0] || '?'
})

const displayName = computed(() => {
  const u = userStore.currentUser
  return u?.nickname || u?.username || ''
})

const zoneTabsRef = ref<HTMLElement | null>(null)

function selectZone(zone: ZoneType) {
  activeZone.value = zone
  nextTick(() => {
    const el = zoneTabsRef.value
    if (el) {
      // 滚到 tab 栏顶部，留 52px 给 header
      const top = el.getBoundingClientRect().top + window.scrollY - 52
      window.scrollTo({ top, behavior: 'smooth' })
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  })
}
function triggerAvatarUpload() { avatarInputRef.value?.click() }
function triggerCoverUpload() { coverInputRef.value?.click() }

// ── 裁剪器状态 ───────────────────────────────────────
const cropperVisible = ref(false)
const cropperSrc     = ref('')
const cropperMode    = ref<'avatar' | 'cover'>('avatar')

function openCropper(file: File, mode: 'avatar' | 'cover') {
  cropperSrc.value  = URL.createObjectURL(file)
  cropperMode.value = mode
  cropperVisible.value = true
}

function handleAvatarChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  openCropper(file, 'avatar')
  ;(event.target as HTMLInputElement).value = ''
}

function handleCoverChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  openCropper(file, 'cover')
  ;(event.target as HTMLInputElement).value = ''
}

async function handleCropConfirm(dataUrl: string) {
  if (cropperMode.value === 'avatar') {
    try {
      const res  = await fetch(dataUrl)
      const blob = await res.blob()
      const formData = new FormData()
      formData.append('file', blob, 'avatar.png')
      await usersApi.uploadAvatar(formData)
      await userStore.refreshUser()
      avatarTimestamp.value = Date.now()
      ElMessage.success('头像更新成功')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.error?.message || '头像上传失败')
    }
  } else {
    const imgValue = `url(${dataUrl})`
    coverMeta.image = imgValue
    coverMeta.size = 'cover'
    const uid = userStore.currentUser?.id
    if (uid) localStorage.setItem(coverStorageKey(uid), JSON.stringify({ image: imgValue, size: 'cover' }))
  }
  URL.revokeObjectURL(cropperSrc.value)
}

function handlePresetSelect(value: { image: string; size: string }) {
  coverMeta.image = value.image
  coverMeta.size = value.size
  const uid = userStore.currentUser?.id
  if (uid) localStorage.setItem(coverStorageKey(uid), JSON.stringify(value))
}

function goToFollowers() {
  if (user.value?.username)
    router.push({ name: 'FollowList', params: { type: 'followers', username: user.value.username } })
}
function goToFollowing() {
  if (user.value?.username)
    router.push({ name: 'FollowList', params: { type: 'following', username: user.value.username } })
}

onMounted(() => userStore.refreshUser())
onActivated(() => userStore.refreshUser())
</script>

<style scoped lang="scss">
// ── 页面骨架 ─────────────────────────────────────────
.space-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface-raised);
}

.space-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-lg $spacing-md 120px;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 52px);
}

// ── 名片卡 ───────────────────────────────────────────
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

  // 装饰圆 — 大
  &::before {
    content: '';
    position: absolute;
    width: 240px; height: 240px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.06);
    bottom: -96px; right: 48px;
    pointer-events: none;
  }

  // 装饰圆 — 小
  &::after {
    content: '';
    position: absolute;
    width: 110px; height: 110px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.05);
    top: -36px; right: 200px;
    pointer-events: none;
  }

  // 有自定义封面时隐藏装饰圆
  &.has-custom::before,
  &.has-custom::after { display: none; }

  &:hover .cover-edit-hint { opacity: 1; }
}

.cover-edit-hint {
  position: absolute;
  bottom: 8px;
  right: 10px;
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity $transition-fast;
  pointer-events: none;
}

.profile-cover:hover .cover-edit-hint {
  opacity: 1;
  pointer-events: auto;
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

  &:hover {
    background: rgba(0, 0, 0, 0.52);
  }
}


// ── 名片主体 ─────────────────────────────────────────
.profile-body {
  padding: 0 $spacing-xl $spacing-md;
}

// 头像
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

// 姓名行
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

// 统计行
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

.stat-label {
  font-size: $font-xs; color: var(--color-text-muted);
}

.stat-sep {
  font-size: 14px; color: var(--color-border);
  user-select: none;
}

// ── Tab 栏 ───────────────────────────────────────────
.zone-tabs {
  display: flex; align-items: stretch;
  border-top: 1px solid var(--color-border-subtle);
  padding: 0 $spacing-lg;
  gap: 0;
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

  // 底部指示线（内嵌缩进，更精致）
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

// ── 内容区 ───────────────────────────────────────────
.tab-content-area { flex: 1; min-height: calc(100vh - 52px); }

.tab-fade-enter-active,
.tab-fade-leave-active { transition: opacity 0.15s ease; }
.tab-fade-enter-from,
.tab-fade-leave-to    { opacity: 0; }

// ── 响应式 ───────────────────────────────────────────
@media (max-width: $breakpoint-sm) {
  .profile-body { padding: 0 $spacing-md $spacing-md; }
  .zone-tabs    { padding: 0 $spacing-md; }
  .profile-name { font-size: $font-lg; }
}
</style>
