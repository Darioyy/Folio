import { get, post, patch, del } from '../request'
import type { ApiResponse } from '@/types/api'

export interface CommentItem {
  id: number
  post_id: number
  user_id: number
  parent_id: number | null
  content: string
  like_count: number
  liked: boolean
  created_at: string
  username?: string
  nickname?: string
  avatar?: string
  replies?: CommentItem[]
}

export interface CommentsResult {
  items: CommentItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export const commentsApi = {
  getList(postId: number, page = 1, pageSize = 20): Promise<ApiResponse<CommentsResult>> {
    return get(`/posts/${postId}/comments`, { page, page_size: pageSize })
  },

  create(postId: number, content: string, parentId?: number): Promise<ApiResponse<CommentItem>> {
    return post(`/posts/${postId}/comments`, { content, parent_id: parentId ?? null })
  },

  update(commentId: number, content: string): Promise<ApiResponse<CommentItem>> {
    return patch(`/posts/comments/${commentId}`, { content })
  },

  delete(commentId: number): Promise<ApiResponse> {
    return del(`/posts/comments/${commentId}`)
  },

  toggleLike(commentId: number): Promise<ApiResponse<{ liked: boolean; like_count: number }>> {
    return post(`/posts/comments/${commentId}/like`, {})
  }
}
