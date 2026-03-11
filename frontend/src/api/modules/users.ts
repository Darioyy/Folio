import { get, getList, post, put, del } from '../request'
import type { User } from '@/types/models'
import type { ApiResponse, PaginationParams } from '@/types/api'

// 个人资料更新
export interface ProfileUpdateData {
  nickname?: string
  signature?: string
  email?: string
}

// 修改密码
export interface ChangePasswordData {
  old_password: string
  new_password: string
}

// 隐私设置
export interface PrivacySettings {
  privacy_avatar?: 0 | 1
  privacy_stats?: 0 | 1
  privacy_content?: 0 | 1
  privacy_follow?: 0 | 1
}

// 我的统计
export interface MyStats {
  posts: number
  media: number
  resources: number
  total_size: number
}

// 用户公开信息
export interface UserPublicInfo {
  id: number
  username: string
  nickname: string | null
  signature: string | null
  avatar: string | null
  followers_count?: number
  following_count?: number
  is_admin?: number
  is_root?: number
  created_at: string | null
}

// 用户公开内容
export interface UserPublicContent {
  posts: any[]
  media: any[]
  resources: any[]
}

// 用户公开统计
export interface UserPublicStats {
  posts: number
  media: number
  resources: number
}

export const usersApi = {
  /**
   * 检查用户名是否可用（匿名）
   */
  checkUsername(username: string): Promise<ApiResponse<{ available: boolean; message: string }>> {
    return get('/users/check-username', { username })
  },

  /**
   * 获取用户列表
   * 后端参数: page, page_size (不是 limit)
   */
  getList(params?: PaginationParams & { role?: number }): Promise<ApiResponse<User[]>> {
    const mappedParams = {
      page: params?.page || 1,
      page_size: params?.limit || 20
    }
    return getList('/users', mappedParams)
  },

  /**
   * 获取用户详情
   */
  getDetail(id: number): Promise<ApiResponse<User>> {
    return get(`/users/${id}`)
  },

  /**
   * 创建用户
   */
  create(data: Partial<User>): Promise<ApiResponse<User>> {
    return post('/users', data)
  },

  /**
   * 更新用户
   */
  update(id: number, data: Partial<User>): Promise<ApiResponse<User>> {
    return put(`/users/${id}`, data)
  },

  /**
   * 删除用户
   */
  delete(id: number): Promise<ApiResponse> {
    return del(`/users/${id}`)
  },

  // ==================== 用户主页相关 API ====================

  /**
   * 通过用户名获取用户公开信息
   */
  getUserByUsername(username: string): Promise<ApiResponse<UserPublicInfo>> {
    return get(`/users/username/${username}`)
  },

  /**
   * 获取用户公开内容
   */
  getUserPublicContent(
    username: string,
    params?: { type?: 'all' | 'posts' | 'media' | 'resources'; page?: number; page_size?: number }
  ): Promise<ApiResponse<UserPublicContent>> {
    return get(`/users/username/${username}/public-content`, params)
  },

  /**
   * 获取用户公开统计
   */
  getUserPublicStats(username: string): Promise<ApiResponse<UserPublicStats>> {
    return get(`/users/username/${username}/stats`)
  },

  // ==================== 关注相关 API ====================

  /**
   * 获取用户粉丝列表
   */
  getUserFollowers(userId: number, page = 1, pageSize = 20): Promise<ApiResponse<{
    items: Array<{
      id: number
      username: string
      nickname?: string
      avatar?: string
      signature?: string
      followers_count: number
      following_count: number
      is_admin: number
      is_root: number
      is_following: boolean
    }>
    total: number
    page: number
    page_size: number
    pages: number
  }>> {
    return get(`/users/${userId}/followers`, {
      page,
      page_size: pageSize
    })
  },

  /**
   * 获取用户关注列表
   */
  getUserFollowing(userId: number, page = 1, pageSize = 20): Promise<ApiResponse<{
    items: Array<{
      id: number
      username: string
      nickname?: string
      avatar?: string
      signature?: string
      followers_count: number
      following_count: number
      is_admin: number
      is_root: number
      is_following: boolean
    }>
    total: number
    page: number
    page_size: number
    pages: number
  }>> {
    return get(`/users/${userId}/following`, {
      page,
      page_size: pageSize
    })
  },

  /**
   * 关注用户
   */
  followUser(userId: number): Promise<ApiResponse> {
    return post(`/users/${userId}/follow`)
  },

  /**
   * 取消关注用户
   */
  unfollowUser(userId: number): Promise<ApiResponse> {
    return del(`/users/${userId}/follow`)
  },

  /**
   * 检查关注状态
   */
  checkFollowStatus(userIds: number[]): Promise<ApiResponse<Record<number, boolean>>> {
    return get('/users/me/follow-status', {
      ids: userIds.join(',')
    })
  },

  // ==================== 个人设置相关 API ====================

  /**
   * 更新个人资料（昵称/签名/邮箱）
   */
  updateProfile(data: ProfileUpdateData): Promise<ApiResponse<User>> {
    return put('/users/me/profile', data)
  },

  /**
   * 修改密码
   */
  changePassword(data: ChangePasswordData): Promise<ApiResponse> {
    return put('/users/me/password', data)
  },

  /**
   * 上传头像
   */
  uploadAvatar(formData: FormData): Promise<ApiResponse<User>> {
    return post('/users/me/avatar', formData)
  },

  /**
   * 更新隐私设置
   */
  updatePrivacy(data: PrivacySettings): Promise<ApiResponse<User>> {
    return put('/users/me/privacy', data)
  },

  /**
   * 获取当前用户统计数据（posts/media/resources/total_size）
   */
  getMyStats(): Promise<ApiResponse<MyStats>> {
    return get('/users/me/stats')
  },

  /**
   * 兑换内测码
   */
  redeemInviteCode(inviteCode: string): Promise<ApiResponse> {
    return post('/users/me/redeem-code', { invite_code: inviteCode })
  }
}
