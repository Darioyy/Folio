import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/models'
import { authApi } from '@/api/modules/auth'
import { storage } from '@/utils/storage'

export const useUserStore = defineStore('user', () => {
  // 状态
  const currentUser = ref<User | null>(storage.getUser())
  const isLoggedIn = computed(() => !!currentUser.value)

  // 计算属性 - 基于 is_admin 和 is_root 字段
  const isAdmin = computed(() => currentUser.value?.is_admin === 1)
  const isRoot = computed(() => currentUser.value?.is_root === 1)
  const isAdminOrRoot = computed(() => isAdmin.value || isRoot.value)

  // 方法
  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    currentUser.value = res.data.user
    storage.setUser(res.data.user)
    return res.data
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      currentUser.value = null
      storage.clear()
    }
  }

  async function refreshUser() {
    try {
      const res = await authApi.getMe()
      currentUser.value = res.data
      storage.setUser(res.data)
      return res.data
    } catch {
      currentUser.value = null
      storage.clear()
      throw null
    }
  }

  return {
    currentUser,
    isLoggedIn,
    isAdmin,
    isRoot,
    isAdminOrRoot,
    login,
    logout,
    refreshUser
  }
})
