const USER_KEY = 'user_info'
const DARK_MODE_KEY = 'dark_mode'

/**
 * 存储工具
 */
export const storage = {
  // 用户信息相关
  getUser(): any {
    try {
      const user = localStorage.getItem(USER_KEY)
      return user ? JSON.parse(user) : null
    } catch {
      localStorage.removeItem(USER_KEY)
      return null
    }
  },

  setUser(user: any): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },

  removeUser(): void {
    localStorage.removeItem(USER_KEY)
  },

  // 暗黑模式
  getDarkMode(): boolean {
    const mode = localStorage.getItem(DARK_MODE_KEY)
    if (mode) return mode === 'true'
    // 默认跟随系统
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  },

  setDarkMode(isDark: boolean): void {
    localStorage.setItem(DARK_MODE_KEY, String(isDark))
  },

  // 清空所有
  clear(): void {
    localStorage.removeItem(USER_KEY)
  }
}
