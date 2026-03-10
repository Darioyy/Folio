import { get, getList, post, put, del } from '../request'
import type { Media } from '@/types/models'
import type { ApiResponse, PaginationParams } from '@/types/api'

export const mediaApi = {
  /**
   * 获取媒体列表
   * 后端参数: page, page_size, type
   */
  getList(params?: PaginationParams & { type?: 'image' | 'video' }): Promise<ApiResponse<Media[]>> {
    const mappedParams = {
      page: params?.page || 1,
      page_size: params?.limit || 12,
      type: params?.type
    }
    return getList('/media', mappedParams)
  },

  /**
   * 获取媒体详情
   */
  getDetail(id: number): Promise<ApiResponse<Media>> {
    return get(`/media/${id}`)
  },

  /**
   * 上传媒体
   */
  upload(formData: FormData): Promise<ApiResponse<Media>> {
    return post('/media/upload', formData)
  },

  /**
   * 获取媒体查看 URL
   */
  getViewUrl(id: number): string {
    return `${import.meta.env.VITE_API_BASE_URL}/media/${id}/view`
  },

  /**
   * 获取缩略图 URL
   */
  getThumbnailUrl(id: number): string {
    return `${import.meta.env.VITE_API_BASE_URL}/media/${id}/thumbnail`
  },

  /**
   * 更新媒体信息
   */
  update(id: number, data: Partial<Media>): Promise<ApiResponse<Media>> {
    return put(`/media/${id}`, data)
  },

  /**
   * 删除媒体
   */
  delete(id: number): Promise<ApiResponse> {
    return del(`/media/${id}`)
  }
}
