import { get, post, put, del, patch } from '../request'
import type { ApiResponse } from '@/types/api'

export interface FileGroup {
  id: number
  parent_id: number | null
  name: string
  sort_order: number
  created_at: string
  file_count: number
  children_count: number
}

export interface BreadcrumbItem {
  id: number
  name: string
}

export const groupsApi = {
  /** 获取根分组列表（侧边栏，parent_id=NULL） */
  list(): Promise<ApiResponse<FileGroup[]>> {
    return get('/groups')
  },

  /** 获取某分组的直接子文件夹 */
  getChildren(id: number): Promise<ApiResponse<FileGroup[]>> {
    return get(`/groups/${id}/children`)
  },

  /** 获取从根到当前分组的面包屑路径 */
  getBreadcrumb(id: number): Promise<ApiResponse<BreadcrumbItem[]>> {
    return get(`/groups/${id}/breadcrumb`)
  },

  /** 创建分组（parentId=null/undefined → 根目录，否则为子文件夹） */
  create(name: string, parentId?: number | null): Promise<ApiResponse<FileGroup>> {
    return post('/groups', { name, parent_id: parentId ?? null })
  },

  /** 更新根分组排序（侧边栏拖拽后调用） */
  sort(ids: number[]): Promise<ApiResponse> {
    return patch('/groups/sort', { ids })
  },

  /** 重命名分组 */
  rename(id: number, name: string): Promise<ApiResponse<FileGroup>> {
    return put(`/groups/${id}`, { name })
  },

  /** 删除分组（force=true 时递归删除所有内容，否则文件解除关联，子分组上移一级） */
  delete(id: number, force = false): Promise<ApiResponse> {
    return del(`/groups/${id}${force ? '?force=true' : ''}`)
  },

  /** 移动分组到新父级（parent_id=null 表示移到根目录） */
  move(id: number, parentId: number | null): Promise<ApiResponse<FileGroup>> {
    return patch(`/groups/${id}/parent`, { parent_id: parentId })
  },
}
