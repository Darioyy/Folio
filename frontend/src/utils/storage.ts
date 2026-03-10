const TOKEN_KEY = 'auth_token'
const USER_KEY = 'user_info'
const DARK_MODE_KEY = 'dark_mode'

/**
 * 存储工具
 */
export const storage = {
  // Token 相关
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },

  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
  },

  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY)
  },

  // 用户信息相关
  getUser(): any {
    const user = localStorage.getItem(USER_KEY)
    return user ? JSON.parse(user) : null
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
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }
}
