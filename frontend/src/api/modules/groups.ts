import { get, post, put, del, patch } from '../request'
import type { ApiResponse } from '@/types/api'

export interface FileGroup {
  id: number
  parent_id: number | null
  name: string
  description?: string | null
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

  /** 创建分组（parentId=null/undefined → 根目录，否则为子文件夹）
   *  merge=true：若同名文件夹已存在则返回已有文件夹（用于文件夹上传覆盖场景） */
  create(name: string, parentId?: number | null, merge = false): Promise<ApiResponse<FileGroup>> {
    return post('/groups', { name, parent_id: parentId ?? null, ...(merge ? { merge: true } : {}) })
  },

  /** 更新根分组排序（侧边栏拖拽后调用） */
  sort(ids: number[]): Promise<ApiResponse> {
    return patch('/groups/sort', { ids })
  },

  /** 重命名分组（仅传 name，供内联重命名使用） */
  rename(id: number, name: string): Promise<ApiResponse<FileGroup>> {
    return put(`/groups/${id}`, { name })
  },

  /** 更新分组信息（name + description，供编辑对话框使用） */
  update(id: number, data: { name?: string; description?: string }): Promise<ApiResponse<FileGroup>> {
    return put(`/groups/${id}`, data)
  },

  /** 删除分组（force=true 时递归删除所有内容，否则文件解除关联，子分组上移一级） */
  delete(id: number, force = false): Promise<ApiResponse> {
    return del(`/groups/${id}${force ? '?force=true' : ''}`)
  },

  /** 移动分组到新父级（parent_id=null 表示移到根目录） */
  move(id: number, parentId: number | null): Promise<ApiResponse<FileGroup>> {
    return patch(`/groups/${id}/parent`, { parent_id: parentId })
  },

  /** 获取分组（含所有子分组）的递归总大小（字节） */
  getSize(id: number): Promise<ApiResponse<number>> {
    return get(`/groups/${id}/size`)
  },
}
