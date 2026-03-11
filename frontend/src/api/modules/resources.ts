import { getList, get, post, put, del } from '../request'
import type { FileItem } from '@/types/models'
import type { ApiResponse, PaginationParams } from '@/types/api'

export const resourcesApi = {
  /**
   * 获取公共资源列表
   * 改调 /files/public?category=resource
   */
  getList(params?: PaginationParams): Promise<ApiResponse<FileItem[]>> {
    const mappedParams = {
      page: params?.page || 1,
      page_size: params?.limit || 10,
      category: 'resource'
    }
    return getList('/files/public', mappedParams)
  },

  /**
   * 获取资源详情
   */
  getDetail(id: number): Promise<ApiResponse<FileItem>> {
    return get(`/files/${id}`)
  },

  /**
   * 上传资源文件
   * FormData 需包含：file, title，category 固定为 resource
   * 可选：description, visibility
   */
  upload(formData: FormData): Promise<ApiResponse<FileItem>> {
    formData.set('category', 'resource')
    return post('/files', formData)
  },

  /**
   * 获取资源下载 URL
   * 复用旧 /resources/:id/download 端点（向后兼容）
   */
  getDownloadUrl(id: number): string {
    return `${import.meta.env.VITE_API_BASE_URL}/resources/${id}/download`
  },

  /**
   * 更新资源信息（title / description / visibility）
   */
  update(id: number, data: Pick<FileItem, 'title' | 'description' | 'visibility'>): Promise<ApiResponse<FileItem>> {
    return put(`/files/${id}`, data)
  },

  /**
   * 删除资源
   */
  delete(id: number): Promise<ApiResponse> {
    return del(`/files/${id}`)
  }
}
