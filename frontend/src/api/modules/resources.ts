import { get, getList, post, put, del } from '../request'
import type { Resource } from '@/types/models'
import type { ApiResponse, PaginationParams } from '@/types/api'

export const resourcesApi = {
  /**
   * 获取资源列表
   * 后端参数: page, page_size, category_id
   */
  getList(params?: PaginationParams & { category?: string }): Promise<ApiResponse<Resource[]>> {
    const mappedParams = {
      page: params?.page || 1,
      page_size: params?.limit || 10,
      category_id: params?.category
    }
    return getList('/resources', mappedParams)
  },

  /**
   * 获取资源详情
   */
  getDetail(id: number): Promise<ApiResponse<Resource>> {
    return get(`/resources/${id}`)
  },

  /**
   * 上传资源
   */
  upload(formData: FormData): Promise<ApiResponse<Resource>> {
    return post('/resources/upload', formData)
  },

  /**
   * 下载资源
   */
  getDownloadUrl(id: number): string {
    return `${import.meta.env.VITE_API_BASE_URL}/resources/${id}/download`
  },

  /**
   * 更新资源信息
   */
  update(id: number, data: Partial<Resource>): Promise<ApiResponse<Resource>> {
    return put(`/resources/${id}`, data)
  },

  /**
   * 删除资源
   */
  delete(id: number): Promise<ApiResponse> {
    return del(`/resources/${id}`)
  }
}
