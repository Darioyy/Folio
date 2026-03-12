import { getList, get, post, put, del } from '../request'
import type { FileItem } from '@/types/models'
import type { ApiResponse, PaginationParams } from '@/types/api'

export const resourcesApi = {
  /**
   * 获取公共文档列表
   * 改调 /files/public?category=document
   */
  getList(params?: PaginationParams): Promise<ApiResponse<FileItem[]>> {
    const mappedParams = {
      page: params?.page || 1,
      page_size: params?.limit || 10,
      category: 'document'
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
   * 上传文档文件
   * FormData 需包含：file, title，category 固定为 document
   * 可选：description, visibility
   */
  upload(formData: FormData): Promise<ApiResponse<FileItem>> {
    formData.set('category', 'document')
    return post('/files', formData)
  },

  /**
   * 获取文件下载 URL
   */
  getDownloadUrl(id: number): string {
    return `${import.meta.env.VITE_API_BASE_URL}/api/v1/files/${id}/download`
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
