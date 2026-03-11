import { getList, get, post, put, del } from '../request'
import type { FileItem } from '@/types/models'
import type { ApiResponse, PaginationParams } from '@/types/api'

export const mediaApi = {
  /**
   * 获取公共媒体列表（image / video）
   * 改调 /files/public，通过 category 对应旧的 type 参数
   */
  getList(params?: PaginationParams & { type?: 'image' | 'video' }): Promise<ApiResponse<FileItem[]>> {
    const mappedParams: Record<string, any> = {
      page: params?.page || 1,
      page_size: params?.limit || 12
    }
    if (params?.type) {
      mappedParams.category = params.type
    }
    return getList('/files/public', mappedParams)
  },

  /**
   * 获取媒体详情
   */
  getDetail(id: number): Promise<ApiResponse<FileItem>> {
    return get(`/files/${id}`)
  },

  /**
   * 上传媒体
   * FormData 需包含：file, title, category(image/video)
   * 可选：description, visibility, thumbnail
   */
  upload(formData: FormData): Promise<ApiResponse<FileItem>> {
    return post('/files', formData)
  },

  /**
   * 获取媒体查看 URL（图片/视频直链）
   * 复用旧 /media/:id/view 端点（向后兼容）
   */
  getViewUrl(id: number): string {
    return `${import.meta.env.VITE_API_BASE_URL}/media/${id}/view`
  },

  /**
   * 获取缩略图 URL
   * 复用旧 /media/:id/thumbnail 端点（向后兼容）
   */
  getThumbnailUrl(id: number): string {
    return `${import.meta.env.VITE_API_BASE_URL}/media/${id}/thumbnail`
  },

  /**
   * 更新媒体信息（title / description / visibility）
   */
  update(id: number, data: Pick<FileItem, 'title' | 'description' | 'visibility'>): Promise<ApiResponse<FileItem>> {
    return put(`/files/${id}`, data)
  },

  /**
   * 删除媒体
   */
  delete(id: number): Promise<ApiResponse> {
    return del(`/files/${id}`)
  }
}
