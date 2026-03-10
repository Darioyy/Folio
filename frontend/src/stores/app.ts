import { defineStore } from 'pinia'
import { ref } from 'vue'
import { storage } from '@/utils/storage'

export const useAppStore = defineStore('app', () => {
  // 状态
  const isDarkMode = ref(false)
  const isLoading = ref(false)
  const sidebarCollapsed = ref(false)

  // 初始化暗黑模式
  function initDarkMode() {
    const saved = storage.getDarkMode()
    isDarkMode.value = saved
    applyDarkMode(saved)

    // 监听系统主题变化
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!storage.getDarkMode()) {
        // 如果用户没有手动设置过，则跟随系统
        applyDarkMode(e.matches)
      }
    })
  }

  // 应用暗黑模式
  function applyDarkMode(isDark: boolean) {
    const html = document.documentElement
    if (isDark) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  // 切换暗黑模式
  function toggleDarkMode() {
    isDarkMode.value = !isDarkMode.value
    storage.setDarkMode(isDarkMode.value)
    applyDarkMode(isDarkMode.value)
  }

  // 设置加载状态
  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  // 切换侧边栏
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return {
    isDarkMode,
    isLoading,
    sidebarCollapsed,
    initDarkMode,
    toggleDarkMode,
    setLoading,
    toggleSidebar
  }
})
