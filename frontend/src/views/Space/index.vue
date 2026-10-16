<template>
  <div class="space-page">
    <AppHeader />

    <div class="space-container">
      <SpaceProfileCard
        :user="user"
        :avatar-url="avatarUrl"
        :cover-style="(coverStyle as any)"
        :has-custom-cover="!!coverMeta.image"
        :active-zone="activeZone"
        :zone-tabs="zoneTabs"
        @avatar-file="onAvatarFile"
        @cover-file="onCoverFile"
        @zone-change="activeZone = $event"
        @open-preset="presetVisible = true"
        @go-followers="goToFollowers"
        @go-following="goToFollowing"
      />

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

  <CoverPresetPicker v-model="presetVisible" @select="onPresetSelected" />

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
import { ref, computed, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/common/AppHeader.vue'
import ImageCropper from '@/components/common/ImageCropper.vue'
import CoverPresetPicker from '@/components/business/CoverPresetPicker.vue'
import SpaceProfileCard from './components/SpaceProfileCard.vue'
import Overview from './tabs/Overview.vue'
import Files from './tabs/Files.vue'
import Posts from './tabs/Posts.vue'
import Favorites from './tabs/Favorites.vue'
import { useUserStore } from '@/stores/user'
import { usersApi } from '@/api/modules/users'
import { authApi } from '@/api/modules/auth'
import { useSpaceCover } from '@/composables/useSpaceCover'

type ZoneType = 'overview' | 'files' | 'posts' | 'favorites'

defineOptions({ name: 'SpaceView' })

const router = useRouter()
const userStore = useUserStore()

const userId = computed(() => userStore.currentUser?.id)

const {
  coverMeta,
  presetVisible,
  coverStyle,
  cropperVisible,
  cropperSrc,
  cropperMode,
  openCropper,
  onCoverCropped,
  onPresetSelected,
} = useSpaceCover(userId)

const zoneTabs = [
  { value: 'overview'  as ZoneType, label: '主页' },
  { value: 'files'     as ZoneType, label: '云盘' },
  { value: 'posts'     as ZoneType, label: '文章' },
  { value: 'favorites' as ZoneType, label: '收藏' },
]

const activeZone = ref<ZoneType>('overview')
const avatarTimestamp = ref(Date.now())
const user = computed(() => userStore.currentUser)

const avatarUrl = computed(() => {
  const u = userStore.currentUser
  if (u?.avatar) return `${authApi.getAvatarUrl()}?uid=${u.id}&t=${avatarTimestamp.value}`
  return undefined
})

function onAvatarFile(file: File) {
  openCropper(file, 'avatar')
}

function onCoverFile(file: File) {
  openCropper(file, 'cover')
}

async function handleCropConfirm(dataUrl: string) {
  if (cropperMode.value === 'avatar') {
    try {
      const res = await fetch(dataUrl)
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
    await onCoverCropped(dataUrl)
  }
  URL.revokeObjectURL(cropperSrc.value)
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

.tab-content-area { flex: 1; min-height: calc(100vh - 52px); }

.tab-fade-enter-active,
.tab-fade-leave-active { transition: opacity 0.15s ease; }
.tab-fade-enter-from,
.tab-fade-leave-to    { opacity: 0; }
</style>
