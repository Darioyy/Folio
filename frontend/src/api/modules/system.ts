import { get, post, put, del } from '../request'
import type { SystemInfo, AdminStats, SystemConfig, InviteCode, FileItem, Category } from '@/types/models'
import type { ApiResponse, PaginatedResponse } from '@/types/api'

export interface SiteInfo {
  site_bio: string
  site_contact: string
}

export interface SiteOwner {
  id: number
  username: string
  nickname: string | null
  avatar: boolean
  signature: string | null
}

export const systemApi = {
  /**
   * 获取站点介绍/联系方式（公开）
   */
  getSiteInfo(): Promise<ApiResponse<SiteInfo>> {
    return get('/system/site-info')
  },

  /**
   * 更新站点介绍/联系方式（Root）
   */
  updateSiteInfo(data: SiteInfo): Promise<ApiResponse<SiteInfo>> {
    return put('/system/site-info', data)
  },

  /**
   * 获取站主公开信息（公开）
   */
  getOwner(): Promise<ApiResponse<SiteOwner | null>> {
    return get('/system/owner')
  },
  /**
   * 获取系统信息
   */
  getInfo(): Promise<ApiResponse<SystemInfo>> {
    return get('/system/info')
  },

  /**
   * 获取管理员数据概览（admin+）
   */
  getStats(): Promise<ApiResponse<AdminStats>> {
    return get('/system/stats')
  },

  /**
   * 管理员文件列表查询（admin+）
   * 支持按 category / username 筛选，返回全站文件
   */
  getAdminFiles(params?: {
    page?: number
    page_size?: number
    category?: string
    username?: string
  }): Promise<ApiResponse<{ items: FileItem[]; total: number; page: number; page_size: number; pages: number }>> {
    return get('/system/files', params)
  },

  /**
   * 获取系统配置（admin+）
   */
  getConfig(): Promise<ApiResponse<SystemConfig>> {
    return get('/system/config')
  },

  /**
   * 更新系统配置（root only）
   */
  updateConfig(data: Partial<SystemConfig>): Promise<ApiResponse<SystemConfig>> {
    return put('/system/config', data)
  },

  /**
   * 获取所有内测码（root only）
   */
  getInviteCodes(): Promise<ApiResponse<InviteCode[]>> {
    return get('/system/invite-codes')
  },

  /**
   * 生成新内测码（root only）
   */
  createInviteCode(): Promise<ApiResponse<InviteCode>> {
    return post('/system/invite-codes', {})
  },

  /**
   * 删除内测码（root only）
   */
  deleteInviteCode(code: string): Promise<ApiResponse> {
    return del(`/system/invite-codes/${code}`)
  },

  /**
   * 获取分类列表
   */
  getCategories(): Promise<ApiResponse<Category[]>> {
    return get('/system/categories')
  },

}
