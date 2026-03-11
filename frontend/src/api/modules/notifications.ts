import { get, put, del, getPaginated } from '../request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type { Notification } from '@/types/models'

export const notificationsApi = {
  /**
   * 获取通知列表
   */
  getList(page = 1, pageSize = 20): Promise<PaginatedResponse<Notification>> {
    return getPaginated('/notifications', { page, limit: pageSize })
  },

  /**
   * 获取未读数量
   */
  getUnreadCount(): Promise<ApiResponse<{ count: number }>> {
    return get('/notifications/unread-count')
  },

  /**
   * 全部标为已读
   */
  readAll(): Promise<ApiResponse> {
    return put('/notifications/read-all')
  },

  /**
   * 删除单条通知
   */
  delete(id: number): Promise<ApiResponse> {
    return del(`/notifications/${id}`)
  }
}
