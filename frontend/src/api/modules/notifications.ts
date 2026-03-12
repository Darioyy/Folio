import { get, put, del, getPaginated } from '../request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type { Notification } from '@/types/models'

export const notificationsApi = {
  getList(page = 1, pageSize = 20): Promise<PaginatedResponse<Notification>> {
    return getPaginated('/notifications', { page, limit: pageSize })
  },

  getUnreadCount(): Promise<ApiResponse<{ count: number }>> {
    return get('/notifications/unread-count')
  },

  readAll(): Promise<ApiResponse> {
    return put('/notifications/read-all')
  },

  readOne(id: number): Promise<ApiResponse> {
    return put(`/notifications/${id}/read`)
  },

  delete(id: number): Promise<ApiResponse> {
    return del(`/notifications/${id}`)
  },

  clearAll(): Promise<ApiResponse> {
    return del('/notifications')
  }
}
