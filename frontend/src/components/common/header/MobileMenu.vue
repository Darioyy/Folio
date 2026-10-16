<template>
  <transition name="slide-down">
    <div v-show="open" class="mobile-menu">
      <router-link to="/blog" class="mobile-link" @click="emit('close')">发现</router-link>
      <router-link v-if="userStore.isLoggedIn" to="/space" class="mobile-link" @click="emit('close')">空间</router-link>
      <router-link to="/tools" class="mobile-link" @click="emit('close')">工具</router-link>
      <template v-if="userStore.isLoggedIn">
        <div class="mobile-sep"></div>
        <button class="mobile-link" @click="goToSettings">账户设置</button>
        <button v-if="userStore.isAdminOrRoot" class="mobile-link" @click="goToAdmin">管理台</button>
        <button class="mobile-link mobile-link--danger" @click="handleLogout">退出登录</button>
      </template>
      <template v-else>
        <div class="mobile-sep"></div>
        <button class="mobile-link mobile-link--primary" @click="goToLogin">登录 / 注册</button>
      </template>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const hasReviewBadge = computed(() => userStore.isAdminOrRoot && appStore.reviewCount > 0)

function goToSettings() { emit('close'); router.push({ name: 'Settings' }) }

function goToAdmin() {
  emit('close')
  router.push(hasReviewBadge.value ? '/admin/review' : { name: 'Admin' })
}

function goToLogin() {
  emit('close')
  router.push({ name: 'Login', query: { redirect: route.fullPath } })
}

async function handleLogout() {
  emit('close')
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
    })
    await userStore.logout()
    router.push({ name: 'Home' })
  } catch { /* cancelled */ }
}
</script>

<style scoped lang="scss">
.mobile-menu {
  position: fixed; top: 52px; left: 0; right: 0;
  background: var(--color-surface); border-bottom: 1px solid var(--color-border);
  padding: $spacing-sm $spacing-md $spacing-md; z-index: 99;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  @media (min-width: $breakpoint-sm + 1) { display: none !important; }
}

.mobile-link {
  display: block; width: 100%; padding: 12px $spacing-sm;
  font-size: 15px; font-weight: 500; color: var(--color-text-primary);
  text-decoration: none; background: none; border: none; text-align: left;
  cursor: pointer; border-radius: $radius-md;
  transition: background $transition-fast, color $transition-fast;
  &:hover { background: var(--color-surface-hover); }
  &.active    { color: var(--color-primary); }
  &--danger   { color: #ef4444; }
  &--primary  { color: var(--color-primary); }
}

.mobile-sep { height: 1px; background: var(--color-border-subtle); margin: $spacing-xs 0; }

.slide-down-enter-active,
.slide-down-leave-active { transition: opacity $transition-base, transform $transition-base; }
.slide-down-enter-from,
.slide-down-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
