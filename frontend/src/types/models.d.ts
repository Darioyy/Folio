// 用户相关类型
export interface User {
  id: number
  uid: string
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
  captcha: string
}

export interface RegisterRequest {
  username: string
  password: string
  captcha: string
  invite_code?: string
  email?: string
  nickname?: string
}

// 博文附件
export interface PostAttachment {
  file_id: number
  title: string
  file_name: string
  file_size: number
  mime_type?: string
  file_category: 'image' | 'video' | 'document'
  sort_order: number
}

// 文章相关类型
export interface Post {
  id: number
  title: string
  content: string
  summary?: string
  category_id?: number
  category_name?: string
  cover_image_id?: number
  cover_image_url?: string
  author_id: number
  author_name?: string
  author_nickname?: string
  author_avatar?: string
  status: 'draft' | 'published' | 'archived'
  is_pinned?: number
  is_hidden?: number
  hide_reason?: string
  review_status?: 'none' | 'pending' | 'rejected'
  appeal_reason?: string
  view_count: number
  like_count: number
  comment_count: number
  collect_count: number
  published_at?: string
  created_at: string
  updated_at: string
  attachments?: PostAttachment[]
}

export interface Category {
  id: number
  name: string
  description?: string
  avatar_path?: string
  avatar_url?: string
  sort_order?: number
  created_at: string
}

// 统一文件类型（对应后端 File 模型 to_dict() 输出）
export interface FileItem {
  id: number
  user_id: number
  group_id?: number | null
  title: string
  description?: string
  file_path: string
  file_name: string
  file_size?: number
  mime_type?: string
  file_category: 'image' | 'video' | 'document'
  visibility: 'private' | 'public'
  thumbnail_path?: string
  duration?: number
  download_count: number
  view_count: number
  like_count: number
  collect_count: number
  created_at: string
  updated_at: string
  // include_user=True 时后端附加以下字段
  username?: string
  nickname?: string
  avatar?: string
}

// 媒体相关类型（已废弃，迁移至 FileItem）
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

// 管理员数据概览
export interface AdminStats {
  users_total: number
  files_total: number
  files_by_category: {
    image: number
    video: number
    document: number
  }
  storage_total: number
  new_users_7d: number
}

// 系统配置
export interface SystemConfig {
  register_enabled: boolean
  invite_code_required: boolean
  captcha_enabled: boolean
  storage_quota_root: number
  storage_quota_admin: number
  storage_quota_user: number
  max_file_size: number
  allowed_extensions: string
}

// 评论
export interface Comment {
  id: number
  post_id: number
  user_id: number
  parent_id: number | null
  content: string
  created_at: string
  username?: string
  nickname?: string
  avatar?: string
  replies?: Comment[]
}

// 通知
export interface Notification {
  id: number
  user_id: number
  type: 'like' | 'collect' | 'comment' | 'reply' | 'follow' | 'new_post' | 'admin' | 'appeal' | 'review_result' | 'report' | 'pinned'
  actor_id: number
  target_id: number | null
  extra: Record<string, any> | null
  is_read: number
  created_at: string
  actor_username?: string
  actor_nickname?: string
  actor_avatar?: string
}

// 搜索结果
export interface SearchResult {
  files: FileItem[]
  users: UserSearchItem[]
  file_total?: number
  user_total?: number
  page: number
  page_size: number
}

export interface UserSearchItem {
  id: number
  uid: string
  username: string
  nickname?: string
  avatar?: string
  signature?: string
  is_admin: number
  is_root: number
  followers_count: number
  following_count: number
  created_at: string
}

// 内测码
export interface InviteCode {
  code: string
  used: boolean
  used_by: string | null
  used_at: string | null
  created_at: string
}
