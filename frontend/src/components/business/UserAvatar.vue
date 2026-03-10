<template>
  <el-avatar
    :size="size"
    :src="avatarUrl"
    :icon="icon"
    :alt="alt"
    @error="handleError"
  >
    <slot>{{ defaultText }}</slot>
  </el-avatar>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { UserFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

interface Props {
  src?: string
  size?: number | 'large' | 'default' | 'small'
  alt?: string
  icon?: any
}

const props = withDefaults(defineProps<Props>(), {
  size: 'default',
  icon: UserFilled
})

const emit = defineEmits<{
  error: []
}>()

const userStore = useUserStore()
const imgError = ref(false)

const avatarUrl = computed(() => {
  if (imgError.value || !props.src) return undefined
  return props.src
})

const defaultText = computed(() => {
  if (userStore.currentUser) {
    return userStore.currentUser.nickname?.[0] || userStore.currentUser.username[0]
  }
  return '?'
})

function handleError() {
  imgError.value = true
  emit('error')
}
</script>
