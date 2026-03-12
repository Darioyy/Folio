import { get, getList, post, put, del, getPaginated } from '../request'
import type { Post, Category } from '@/types/models'
import type { ApiResponse, PaginationParams, PaginatedResponse } from '@/types/api'
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
   */
  getCategories(): Promise<ApiResponse<Category[]>> {
    return systemApi.getCategories()
  },

  /**
   * 获取博客文章列表（含分页信息）
   * 用于博客首页
   */
  getPaginatedList(params?: {
    page?: number
    limit?: number
    category_id?: number
    sort?: 'latest' | 'hot'
  }): Promise<PaginatedResponse<Post>> {
    return getPaginated<Post>('/posts', {
      page: params?.page ?? 1,
      limit: params?.limit ?? 12,
      status: 'published',
      ...(params?.category_id ? { category_id: params.category_id } : {}),
      ...(params?.sort ? { sort: params.sort } : {})
    } as PaginationParams)
  },

  /**
   * 获取我的博文列表
   */
  getMyPosts(params?: { status?: string; page?: number; page_size?: number }): Promise<ApiResponse<{ items: Post[]; total: number; page: number; page_size: number; pages: number }>> {
    return get('/posts/my', params)
  },

  /**
   * 发布博文
   */
  publish(id: number): Promise<ApiResponse<Post>> {
    return post(`/posts/${id}/publish`)
  },

  /**
   * 添加附件
   */
  addAttachment(postId: number, fileId: number): Promise<ApiResponse> {
    return post(`/posts/${postId}/attachments`, { file_id: fileId })
  },

  /**
   * 移除附件
   */
  removeAttachment(postId: number, fileId: number): Promise<ApiResponse> {
    return del(`/posts/${postId}/attachments/${fileId}`)
  },

  /**
   * 管理员获取所有博文列表（分页+筛选）
   */
  adminGetAll(params?: {
    page?: number
    page_size?: number
    username?: string
    category_id?: number | ''
    status?: string
  }): Promise<ApiResponse<{ items: any[]; total: number }>> {
    return get('/posts/admin/all', params)
  },

  /**
   * 管理员设置博文可见性
   */
  setVisibility(id: number, hidden: boolean, reason?: string): Promise<ApiResponse<{ is_hidden: number }>> {
    return put(`/posts/${id}/visibility`, { hidden, reason })
  },

  /**
   * 创建分类
   */
  createCategory(data: { name: string; description?: string }): Promise<ApiResponse> {
    return post('/system/categories', data)
  },

  /**
   * 更新分类
   */
  updateCategory(id: number, data: { name?: string; description?: string }): Promise<ApiResponse> {
    return put('/system/categories/' + id, data)
  },

  /**
   * 删除分类
   */
  deleteCategory(id: number): Promise<ApiResponse> {
    return del('/system/categories/' + id)
  },

  /**
   * 作者提交申诉
   */
  appeal(id: number, reason: string): Promise<ApiResponse<{ review_status: string }>> {
    return post(`/posts/${id}/appeal`, { reason })
  },

  /**
   * 管理员审核申诉
   */
  reviewAppeal(id: number, action: 'approve' | 'reject', reason?: string): Promise<ApiResponse<{ review_status: string; is_hidden: number }>> {
    return put(`/posts/${id}/review`, { action, reason })
  },

}
