import { post, get, getPaginated } from '../request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type { FileItem } from '@/types/models'

export interface InteractionStatus {
  liked: boolean
  collected: boolean
}

export interface LikeResult {
  liked: boolean
  like_count: number
}

export interface CollectResult {
  collected: boolean
  collect_count: number
}

export const interactionsApi = {
  /**
   * 切换点赞状态
   */
  toggleLike(fileId: number): Promise<ApiResponse<LikeResult>> {
    return post(`/files/${fileId}/like`)
  },

  /**
   * 切换收藏状态
   */
  toggleCollect(fileId: number): Promise<ApiResponse<CollectResult>> {
    return post(`/files/${fileId}/collect`)
  },

  /**
   * 批量查询点赞/收藏状态
   */
  batchStatus(fileIds: number[]): Promise<ApiResponse<Record<number, InteractionStatus>>> {
    return get('/files/batch-status', { ids: fileIds.join(',') })
  },

  /**
   * 获取我的收藏列表
   */
  getMyCollections(page = 1, pageSize = 20): Promise<PaginatedResponse<FileItem>> {
    return getPaginated('/files/me/collections', { page, limit: pageSize })
  }
}
