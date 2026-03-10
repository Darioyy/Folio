import { get, getList, post, put, del } from '../request'
import type { Post, Category } from '@/types/models'
import type { ApiResponse, PaginationParams } from '@/types/api'
import { systemApi } from './system'

export const postsApi = {
  /**
   * 获取文章列表
   * 后端参数: page, limit, status, category_id, search
   */
  getList(params?: PaginationParams & { status?: string; category_id?: number; q?: string }): Promise<ApiResponse<Post[]>> {
    const mappedParams = {
      page: params?.page || 1,
      limit: params?.limit || 10,
      status: params?.status,
      category_id: params?.category_id,
      search: params?.q
    }
    return getList('/posts', mappedParams)
  },

  /**
   * 获取文章详情
   */
  getDetail(id: number): Promise<ApiResponse<Post>> {
    return get(`/posts/${id}`)
  },

  /**
   * 创建文章
   */
  create(data: Partial<Post>): Promise<ApiResponse<Post>> {
    return post('/posts', data)
  },

  /**
   * 更新文章
   */
  update(id: number, data: Partial<Post>): Promise<ApiResponse<Post>> {
    return put(`/posts/${id}`, data)
  },

  /**
   * 删除文章
   */
  delete(id: number): Promise<ApiResponse> {
    return del(`/posts/${id}`)
  },

  /**
   * 获取分类列表
   * 注意：实际调用 system API 的分类接口
   */
  getCategories(): Promise<ApiResponse<Category[]>> {
    return systemApi.getCategories()
  }
}
