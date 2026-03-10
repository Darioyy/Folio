<template>
  <div class="user-avatar" :class="{ [`size-${size}`]: true }">
    <img
      v-if="shouldShowImage"
      :src="effectiveAvatarUrl"
      :alt="user?.username || 'Avatar'"
      @error="handleImageError"
    />
    <div v-else class="avatar-placeholder">
      <span>{{ displayLetter }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { User } from '@/types/models'
import { useUserStore } from '@/stores/user'

interface Props {
  user?: User | null
  src?: string
  size?: number
}

const props = withDefaults(defineProps<Props>(), {
  user: null,
  src: undefined,
  size: 40
})

const userStore = useUserStore()
const imageError = ref(false)

// 监听 src 和 user 变化，重置错误状态
watch(() => [props.src, props.user?.username], () => {
  imageError.value = false
})

// 有效的头像 URL - 统一使用后端 API
const effectiveAvatarUrl = computed(() => {
  // 优先使用传入的 src
  if (props.src) return props.src

  // 如果有用户对象，使用统一的头像端点
  if (props.user?.username) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    return `${baseUrl}/users/username/${props.user.username}/avatar/view`
  }

  return ''
})

// 是否应该显示图片
const shouldShowImage = computed(() => {
  return !imageError.value && !!effectiveAvatarUrl.value
})

// 显示的字母
const displayLetter = computed(() => {
  const name = props.user?.nickname || props.user?.username || '?'
  return name.charAt(0).toUpperCase()
})

// 图片加载失败处理
function handleImageError() {
  imageError.value = true
}
</script>

<style scoped lang="scss">
.user-avatar {
  border-radius: 50% !important;
  overflow: hidden;
  background: var(--el-fill-color-light);
  flex-shrink: 0;
  display: inline-block;
  position: relative;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .avatar-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
    font-weight: 600;
  }

  &.size-32 {
    width: 32px;
    height: 32px;
    .avatar-placeholder {
      font-size: 14px;
    }
  }

  &.size-36 {
    width: 36px;
    height: 36px;
    .avatar-placeholder {
      font-size: 15px;
    }
  }

  &.size-40 {
    width: 40px;
    height: 40px;
    .avatar-placeholder {
      font-size: 16px;
    }
  }

  &.size-48 {
    width: 48px;
    height: 48px;
    .avatar-placeholder {
      font-size: 18px;
    }
  }

  &.size-64 {
    width: 64px;
    height: 64px;
    .avatar-placeholder {
      font-size: 24px;
    }
  }

  &.size-80 {
    width: 80px;
    height: 80px;
    .avatar-placeholder {
      font-size: 32px;
    }
  }

  &.size-128 {
    width: 128px;
    height: 128px;
    .avatar-placeholder {
      font-size: 48px;
    }
  }
}
</style>
