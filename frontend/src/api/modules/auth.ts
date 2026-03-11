import { get, post, put } from '../request'
import type { LoginRequest, RegisterRequest, User } from '@/types/models'
import type { ApiResponse } from '@/types/api'

export const authApi = {
  /**
   * 获取验证码图片（服务端生成，答案存 session）
   */
  getCaptcha(): Promise<ApiResponse<{ enabled: boolean; image: string }>> {
    return get('/users/captcha')
  },

  /**
   * 登录
   */
  login(data: LoginRequest): Promise<ApiResponse<{ user: User }>> {
    return post('/users/login', data)
  },

  /**
   * 登出
   */
  logout(): Promise<ApiResponse> {
    return post('/users/logout')
  },

  /**
   * 获取当前用户信息
   */
  getMe(): Promise<ApiResponse<User>> {
    return get('/users/me')
  },

  /**
   * 注册
   */
  register(data: RegisterRequest): Promise<ApiResponse<User>> {
    return post('/users/register', data)
  },

  /**
   * 更新个人资料
   */
  updateProfile(data: {
    nickname?: string
    signature?: string
    email?: string
  }): Promise<ApiResponse<User>> {
    return put('/users/me/profile', data)
  },

  /**
   * 上传头像
   */
  uploadAvatar(file: File): Promise<ApiResponse<User>> {
    const formData = new FormData()
    formData.append('file', file)
    return post('/users/me/avatar', formData)
  },

  /**
   * 获取用户统计数据
   */
  getStats(): Promise<ApiResponse<{
    posts: number
    media: number
    resources: number
    total_size: number
  }>> {
    return get('/users/me/stats')
  },

  /**
   * 获取头像 URL
   */
  getAvatarUrl(): string {
    return `${import.meta.env.VITE_API_BASE_URL}/users/me/avatar/view`
  },

  /**
   * 修改密码
   */
  changePassword(data: {
    old_password: string
    new_password: string
  }): Promise<ApiResponse> {
    return put('/users/me/password', data)
  },

  /**
   * 更新隐私设置
   */
  updatePrivacy(data: {
    privacy_avatar?: number
    privacy_stats?: number
    privacy_content?: number
    privacy_follow?: number
  }): Promise<ApiResponse<User>> {
    return put('/users/me/privacy', data)
  },

  /**
   * 获取存储分类统计
   */
  getStorageCategories(): Promise<ApiResponse<{
    type: string
    name: string
    count: number
    size: number
  }[]>> {
    return get('/users/me/storage/categories')
  }
}
