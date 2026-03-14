import service from '../index'
import { get, getPaginated, post, put, patch, del } from '../request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type { FileItem } from '@/types/models'

export type { FileItem }

// 文件列表查询参数
export interface FileListParams {
  page?: number
  page_size?: number
  category?: 'image' | 'video' | 'document'
  visibility?: 'private' | 'public'
  user_id?: number     // admin 专用：筛选指定用户的文件
  group_id?: number    // 分组筛选：-1=未分组，正整数=指定分组
}

// 文件更新参数
export interface FileUpdateData {
  title?: string
  description?: string
  visibility?: 'private' | 'public'
  file_name?: string
}

export const filesApi = {
  /**
   * 获取文件列表（需登录）
   * - 普通用户：只能查自己的文件
   * - admin：可查全局，可传 user_id 筛选
   */
  getList(params?: FileListParams): Promise<PaginatedResponse<FileItem>> {
    return getPaginated('/files', params)
  },

  /**
   * 获取公共文件列表（无需登录）
   * visibility 固定为 public，支持 category 筛选
   */
  getPublicList(
    params?: Pick<FileListParams, 'page' | 'page_size' | 'category'>
  ): Promise<PaginatedResponse<FileItem>> {
    return getPaginated('/files/public', params)
  },

  /**
   * 获取文件详情
   */
  getDetail(id: number): Promise<ApiResponse<FileItem>> {
    return get(`/files/${id}`)
  },

  /**
   * 上传文件（统一入口）
   */
  upload(formData: FormData): Promise<ApiResponse<FileItem>> {
    return post('/files', formData)
  },

  /**
   * 上传文件（带进度回调）
   * @param silent 设为 true 时抑制逐条错误 toast（批量上传时使用）
   */
  uploadWithProgress(
    formData: FormData,
    onProgress: (percent: number) => void,
    silent = false
  ): Promise<ApiResponse<FileItem>> {
    return service.post<ApiResponse<FileItem>>('/files', formData, {
      onUploadProgress: (e: any) => {
        if (e.total) onProgress(Math.round((e.loaded / e.total) * 100))
      },
      _silent: silent,
    } as any).then(res => res.data)
  },

  /**
   * 更新文件信息（title / description / visibility）
   */
  update(id: number, data: FileUpdateData): Promise<ApiResponse<FileItem>> {
    return put(`/files/${id}`, data)
  },

  /**
   * 删除文件（含物理文件）
   */
  delete(id: number): Promise<ApiResponse> {
    return del(`/files/${id}`)
  },

  /**
   * 修改文件所属分组（group_id=null 表示移到未分组）
   */
  updateGroup(id: number, groupId: number | null): Promise<ApiResponse<{ group_id: number | null }>> {
    return patch(`/files/${id}/group`, { group_id: groupId })
  },

  /**
   * 批量更新同一文件夹内文件的排序（ids 按新顺序排列）
   */
  sortInGroup(fileIds: number[]): Promise<ApiResponse> {
    return patch('/files/sort', { ids: fileIds })
  },

  /**
   * 获取媒体文件查看 URL（图片 / 视频直链，inline 模式）
   */
  getViewUrl(id: number): string {
    return `${import.meta.env.VITE_API_BASE_URL}/files/${id}/download`
  },

  /**
   * 获取缩略图 URL（图片原图 / 视频封面）
   */
  getThumbnailUrl(id: number): string {
    return `${import.meta.env.VITE_API_BASE_URL}/files/${id}/thumbnail`
  },

  /**
   * 获取文件下载 URL
   */
  getDownloadUrl(id: number): string {
    return `${import.meta.env.VITE_API_BASE_URL}/files/${id}/download?dl=1`
  }
}
