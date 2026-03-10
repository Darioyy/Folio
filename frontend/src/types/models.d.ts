// 用户相关类型
export interface User {
  id: number
  username: string
  email?: string
  avatar?: string
  nickname?: string
  signature?: string
  is_admin: number // 0: User, 1: Admin
  is_root: number // 0: Not Root, 1: Root
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  code?: string // 内测码
}

// 文章相关类型
export interface Post {
  id: number
  title: string
  content: string
  summary?: string
  category_id?: number
  category_name?: string
  author_id: number
  author_name?: string
  status: 'draft' | 'published'
  view_count: number
  created_at: string
  updated_at: string
}

export interface Category {
  id: number
  name: string
  description?: string
  sort_order?: number
  created_at: string
}

// 媒体相关类型
export interface Media {
  id: number
  title: string
  type: 'image' | 'video'
  file_path: string
  file_size: number
  width?: number
  height?: number
  duration?: number
  thumbnail_path?: string
  uploaded_by: number
  uploader_name?: string
  created_at: string
}

// 资源相关类型
export interface Resource {
  id: number
  title: string
  description?: string
  file_path: string
  file_name: string
  file_size: number
  category?: string
  download_count: number
  uploaded_by: number
  uploader_name?: string
  created_at: string
}

// 系统信息类型
export interface SystemInfo {
  database_stats: {
    users: number
    posts: number
    media: number
    resources: number
    categories: number
  }
  database_size: string
  version: string
}
