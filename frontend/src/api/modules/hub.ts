import { get, patch } from '../request'
import type { ApiResponse, PaginationResult } from '@/types/api'

// 存储配额信息
export interface StorageInfo {
  storage_used: number
  storage_quota: number
  storage_percentage: number
}

// 媒体文件（扩展版）
export interface HubMedia {
  id: number
  title: string
  description: string
  file_path: string
  file_name: string
  file_type: 'image' | 'video'
  file_size: number | null
  visibility: 'private' | 'public'
  thumbnail_path: string | null
  duration: number | null
  width: number | null
  height: number | null
  uploader_id: number
  uploader_name?: string
  uploader_username?: string
  created_at: string
}

// 资源文件（扩展版）
export interface HubResource {
  id: number
  title: string
  description: string
  file_path: string
  file_name: string
  file_size: number | null
  file_type: string
  visibility: 'private' | 'public'
  category_id: number | null
  category_name?: string
  uploader_id: number
  uploader_name?: string
  download_count: number
  created_at: string
}

export const hubApi = {
  /**
   * 获取存储配额信息
   */
  getStorageInfo(): Promise<ApiResponse<StorageInfo>> {
    return get('/hub/storage')
  },

  /**
   * 获取用户私有媒体文件列表
   */
  getUserMedia(params?: {
    page?: number
    page_size?: number
    visibility?: 'private' | 'public'
    type?: 'image' | 'video'
  }): Promise<ApiResponse<PaginationResult<HubMedia>>> {
    return get('/hub/media', { params })
  },

  /**
   * 获取用户私有资源文件列表
   */
  getUserResources(params?: {
    page?: number
    page_size?: number
    visibility?: 'private' | 'public'
  }): Promise<ApiResponse<PaginationResult<HubResource>>> {
    return get('/hub/resources', { params })
  },

  /**
   * 切换媒体文件可见性
   */
  toggleMediaVisibility(id: number): Promise<ApiResponse<{ visibility: string }>> {
    return patch(`/hub/media/${id}/visibility`)
  },

  /**
   * 切换资源文件可见性
   */
  toggleResourceVisibility(id: number): Promise<ApiResponse<{ visibility: string }>> {
    return patch(`/hub/resources/${id}/visibility`)
  },

  /**
   * 获取公共媒体文件列表
   */
  getPublicMedia(params?: {
    page?: number
    page_size?: number
    type?: 'image' | 'video'
  }): Promise<ApiResponse<PaginationResult<HubMedia>>> {
    return get('/hub/public/media', { params })
  },

  /**
   * 获取公共资源文件列表
   */
  getPublicResources(params?: {
    page?: number
    page_size?: number
  }): Promise<ApiResponse<PaginationResult<HubResource>>> {
    return get('/hub/public/resources', { params })
  }
}
