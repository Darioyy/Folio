<template>
  <div class="space-page">
    <AppHeader />

    <div class="space-container">
      <!-- 用户卡片 -->
      <div class="user-card">
        <div class="user-cover"></div>
        <div class="user-info-section">
          <div class="avatar-wrapper">
            <div class="avatar-upload-area" @click="triggerAvatarUpload">
              <el-avatar :src="avatarUrl" :size="100" class="user-avatar">
                {{ avatarFallback }}
              </el-avatar>
              <div class="avatar-overlay">
                <el-icon><Camera /></el-icon>
                <span>更换头像</span>
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

          <div class="user-details">
            <div class="user-header">
              <h1 class="user-name">
                {{ displayName }}
                <el-tag v-if="user?.is_root === 1" type="danger" size="small" style="margin-left: 8px">ROOT</el-tag>
                <el-tag v-else-if="user?.is_admin === 1" type="warning" size="small" style="margin-left: 8px">ADMIN</el-tag>
              </h1>
              <p class="user-username">@{{ user?.username }}</p>
              <p class="user-signature">{{ user?.signature || '这个人很懒，什么都没留下' }}</p>
            </div>

            <div class="user-stats">
              <div class="stat-item clickable" @click="goToFollowing">
                <span class="stat-value">{{ user?.following_count || 0 }}</span>
                <span class="stat-label">关注</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item clickable" @click="goToFollowers">
                <span class="stat-value">{{ user?.followers_count || 0 }}</span>
                <span class="stat-label">粉丝</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <span class="stat-value">{{ (user as any)?.like_count || 0 }}</span>
                <span class="stat-label">获赞</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <span class="stat-value">{{ (user as any)?.collect_count || 0 }}</span>
                <span class="stat-label">收藏</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 区域 Tab -->
      <div class="zone-tabs" ref="zoneTabsRef">
        <span
          v-for="tab in zoneTabs"
          :key="tab.value"
          :class="['zone-tab', { active: activeZone === tab.value }]"
          @click="selectZone(tab.value)"
        >
          <el-icon><component :is="tab.icon" /></el-icon>
          {{ tab.label }}
        </span>
      </div>

      <!-- Tab 内容 -->
      <Overview v-if="activeZone === 'overview'" />
      <Files v-else-if="activeZone === 'files'" />
      <Posts v-else-if="activeZone === 'posts'" />
      <Favorites v-else-if="activeZone === 'favorites'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Camera, DataLine, FolderOpened, Document, Star } from '@element-plus/icons-vue'
import AppHeader from '@/components/common/AppHeader.vue'
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
  { value: 'overview' as ZoneType, label: '概况', icon: DataLine },
  { value: 'files' as ZoneType, label: '文件', icon: FolderOpened },
  { value: 'posts' as ZoneType, label: '博文', icon: Document },
  { value: 'favorites' as ZoneType, label: '收藏', icon: Star },
]

const activeZone = ref<ZoneType>('overview')
const zoneTabsRef = ref<HTMLElement | null>(null)

const user = computed(() => userStore.currentUser)

// 头像
const avatarInputRef = ref<HTMLInputElement | null>(null)
const avatarTimestamp = ref(Date.now())

const avatarUrl = computed(() => {
  const u = userStore.currentUser
  if (u?.avatar) {
    return `${authApi.getAvatarUrl()}?uid=${u.id}&t=${avatarTimestamp.value}`
  }
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

function selectZone(zone: ZoneType) {
  activeZone.value = zone
  nextTick(() => {
    if (!zoneTabsRef.value) return
    const el = zoneTabsRef.value
    const top = el.getBoundingClientRect().top + window.scrollY - 72
    window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' })
  })
}

function triggerAvatarUpload() {
  avatarInputRef.value?.click()
}

async function handleAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    await usersApi.uploadAvatar(formData)
    await userStore.refreshUser()
    avatarTimestamp.value = Date.now()
    ElMessage.success('头像上传成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '头像上传失败')
  } finally {
    input.value = ''
  }
}

function goToFollowers() {
  if (user.value?.username) {
    router.push({ name: 'FollowList', params: { type: 'followers', username: user.value.username } })
  }
}

function goToFollowing() {
  if (user.value?.username) {
    router.push({ name: 'FollowList', params: { type: 'following', username: user.value.username } })
  }
}

onMounted(() => userStore.refreshUser())
onActivated(() => userStore.refreshUser())
</script>

<style scoped lang="scss">
.space-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.space-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-lg $spacing-md 120px;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 64px);
}

// ==================== 用户卡片 ====================

.user-card {
  background: var(--el-bg-color);
  border-radius: $radius-xl;
  overflow: hidden;
  box-shadow: $shadow-md;
  margin-bottom: $spacing-lg;
}

.user-cover {
  height: 200px;
  background: linear-gradient(135deg, $color-primary 0%, $color-secondary 100%);
}

.user-info-section {
  padding: 0 $spacing-xl $spacing-lg;
  margin-top: -50px;
}

.avatar-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: $spacing-md;
}

.avatar-upload-area {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  display: inline-block;

  &:hover .avatar-overlay {
    opacity: 1;
  }
}

.user-avatar {
  border: 4px solid var(--el-bg-color);
  font-size: 40px;
  font-weight: bold;
  background: linear-gradient(135deg, $color-primary, $color-secondary);
  color: white;
  display: block;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: white;
  font-size: $font-xs;
  opacity: 0;
  transition: opacity $transition-base;
  border: 4px solid transparent;

  .el-icon {
    font-size: 20px;
  }
}

.user-details {
  text-align: center;
}

.user-header {
  margin-bottom: $spacing-sm;
}

.user-name {
  font-size: $font-2xl;
  font-weight: 700;
  margin: 0 0 4px;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-username {
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  margin: 0 0 $spacing-sm;
}

.user-signature {
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  margin: 0;
  line-height: 1.6;
}

.user-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-md;
  padding: $spacing-sm 0 $spacing-md;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;

  &.clickable {
    cursor: pointer;
    transition: color $transition-fast;

    &:hover .stat-value {
      color: $color-primary;
    }
  }
}

.stat-value {
  font-size: $font-xl;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stat-label {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  line-height: 1;
}

.stat-divider {
  width: 1px;
  height: 24px;
  background: var(--el-border-color-light);
}

// ==================== 区域 Tab ====================

.zone-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  border-bottom: 1px solid var(--el-border-color-light);
  margin-bottom: $spacing-lg;
  scroll-margin-top: 64px;
}

.zone-tab {
  display: inline-flex;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-sm $spacing-lg;
  font-size: $font-base;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color $transition-fast, border-color $transition-fast;

  &:hover {
    color: var(--el-text-color-primary);
  }

  &.active {
    color: $color-primary;
    border-bottom-color: $color-primary;
  }

  .el-icon {
    font-size: 16px;
  }
}
</style>
