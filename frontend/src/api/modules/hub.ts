import { get, getPaginated, patch } from '../request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type { FileItem } from '@/types/models'

// 存储配额信息
export interface StorageInfo {
  storage_used: number
  storage_quota: number
  storage_percentage: number
}

export const hubApi = {
  /**
   * 获取存储配额信息
   */
  getStorageInfo(): Promise<ApiResponse<StorageInfo>> {
    return get('/hub/storage')
  },

  /**
   * 获取用户私有文件列表（媒体：image / video）
   * 改调 /files，通过 category 筛选媒体类型
   *
   * 注意：不传 type 时查询所有 category 的文件（Phase 2 UI 完成前的过渡行为）
   */
  getUserMedia(params?: {
    page?: number
    page_size?: number
    visibility?: 'private' | 'public'
    type?: 'image' | 'video'
  }): Promise<PaginatedResponse<FileItem>> {
    const { type, ...rest } = params || {}
    return getPaginated('/files', {
      ...rest,
      ...(type ? { category: type } : {})
    })
  },

  /**
   * 获取用户私有文档文件列表
   * 改调 /files?category=document
   */
  getUserResources(params?: {
    page?: number
    page_size?: number
    visibility?: 'private' | 'public'
  }): Promise<PaginatedResponse<FileItem>> {
    return getPaginated('/files', { ...params, category: 'document' })
  },

  /**
   * 切换媒体文件可见性（private ↔ public）
   * 改调 /files/:id/visibility
   */
  toggleMediaVisibility(id: number): Promise<ApiResponse<{ visibility: string }>> {
    return patch(`/files/${id}/visibility`)
  },

  /**
   * 切换资源文件可见性（private ↔ public）
   * 改调 /files/:id/visibility（与媒体共用同一端点）
   */
  toggleResourceVisibility(id: number): Promise<ApiResponse<{ visibility: string }>> {
    return patch(`/files/${id}/visibility`)
  },

  /**
   * 获取公共媒体文件列表（供公共大厅，无需登录）
   * 改调 /files/public，通过 category 筛选媒体类型
   */
  getPublicMedia(params?: {
    page?: number
    page_size?: number
    type?: 'image' | 'video'
  }): Promise<PaginatedResponse<FileItem>> {
    const { type, ...rest } = params || {}
    return getPaginated('/files/public', {
      ...rest,
      ...(type ? { category: type } : {})
    })
  },

  /**
   * 获取公共文档文件列表（供公共大厅，无需登录）
   * 改调 /files/public?category=document
   */
  getPublicResources(params?: {
    page?: number
    page_size?: number
  }): Promise<PaginatedResponse<FileItem>> {
    return getPaginated('/files/public', { ...params, category: 'document' })
  }
}
