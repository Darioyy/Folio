import request from './index'
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api'

/**
 * 通用请求方法
 */
export async function get<T = any>(url: string, params?: any): Promise<ApiResponse<T>> {
  const res = await request.get<ApiResponse<T>>(url, { params })
  return res.data
}

export async function post<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
  // FormData 会自动设置正确的 Content-Type（包括 boundary）
  // 不要手动设置 Content-Type，否则会导致 boundary 缺失
  const res = await request.post<ApiResponse<T>>(url, data)
  return res.data
}

export async function put<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
  const res = await request.put<ApiResponse<T>>(url, data)
  return res.data
}

export async function patch<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
  const res = await request.patch<ApiResponse<T>>(url, data)
  return res.data
}

export async function del<T = any>(url: string): Promise<ApiResponse<T>> {
  const res = await request.delete<ApiResponse<T>>(url)
  return res.data
}

/**
 * 分页请求方法
 * 自动处理后端的分页响应格式: {data: {items: [...], pagination: {...}}}
 */
export async function getPaginated<T = any>(
  url: string,
  params?: PaginationParams
): Promise<PaginatedResponse<T>> {
  const res = await request.get<ApiResponse<{items: T[], pagination: any}>>(url, { params })
  const responseData = res.data.data as any

  // 检测后端是否返回了分页格式
  if (responseData && typeof responseData === 'object' && 'items' in responseData) {
    return {
      items: responseData.items,
      pagination: responseData.pagination
    }
  }

  // 兼容直接返回数组的情况
  return {
    items: responseData || [],
    pagination: {
      page: params?.page || 1,
      page_size: params?.limit || 10,
      total: 0,
      pages: 0
    }
  }
}

/**
 * 获取列表数据（自动提取 items）
 * 用于兼容旧的组件代码，期待 res.data 直接是数组
 */
export async function getList<T = any>(url: string, params?: any): Promise<ApiResponse<T[]>> {
  const res = await request.get<ApiResponse<{items: T[], pagination: any} | T[]>>(url, { params })
  const responseData = res.data.data as any

  // 检测后端是否返回了分页格式
  if (responseData && typeof responseData === 'object' && 'items' in responseData) {
    // 返回提取 items 数组后的响应
    return {
      success: res.data.success,
      data: responseData.items,
      message: res.data.message
    }
  }

  // 兼容直接返回数组的情况
  return res.data
}
