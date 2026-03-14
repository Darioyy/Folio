import { get, post, patch } from '../request'
import type { ApiResponse } from '@/types/api'

export type FeedbackType = 'feature' | 'bug' | 'other'
export type FeedbackStatus = 'pending' | 'resolved'

export interface FeedbackItem {
  id: number
  type: FeedbackType
  title: string
  content: string
  contact?: string
  status: FeedbackStatus
  note?: string
  created_at: string
}

export const feedbackApi = {
  submit(data: {
    type: FeedbackType
    title: string
    content: string
    contact?: string
  }): Promise<ApiResponse> {
    return post('/feedback', data)
  },

  getList(params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<ApiResponse<{ items: FeedbackItem[]; total: number }>> {
    return get('/feedback', params)
  },

  updateStatus(id: number, data: {
    status: FeedbackStatus
    note?: string
  }): Promise<ApiResponse<FeedbackItem>> {
    return patch(`/feedback/${id}`, data)
  },
}
