import { get, post, put, del } from '../request'
import type { SystemInfo, Category } from '@/types/models'
import type { ApiResponse } from '@/types/api'

export const systemApi = {
  /**
   * 获取系统信息
   */
  getInfo(): Promise<ApiResponse<SystemInfo>> {
    return get('/system/info')
  },

  /**
   * 获取分类列表
   */
  getCategories(): Promise<ApiResponse<Category[]>> {
    return get('/system/categories')
  },

  /**
   * 创建分类
   */
  createCategory(data: { name: string }): Promise<ApiResponse<Category>> {
    return post('/system/categories', data)
  },

  /**
   * 更新分类
   */
  updateCategory(id: number, data: { name: string }): Promise<ApiResponse<Category>> {
    return put(`/system/categories/${id}`, data)
  },

  /**
   * 删除分类
   */
  deleteCategory(id: number): Promise<ApiResponse> {
    return del(`/system/categories/${id}`)
  }
}
