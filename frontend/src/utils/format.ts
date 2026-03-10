import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.locale('zh-cn')
dayjs.extend(relativeTime)

/**
 * 格式化日期
 */
export function formatDate(date: string | Date, format = 'YYYY-MM-DD HH:mm'): string {
  return dayjs(date).format(format)
}

/**
 * 相对时间
 */
export function fromNow(date: string | Date): string {
  return dayjs(date).fromNow()
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes || bytes === 0) return '-'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

/**
 * 格式化时长（秒 -> HH:MM:SS）
 */
export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60

  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m}:${s.toString().padStart(2, '0')}`
}

/**
 * 截断文本
 */
export function truncate(text: string, length = 100): string {
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

/**
 * 转义 HTML（防止 XSS）
 */
export function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * 获取上传文件 URL
 * 注意：uploads 路由不在 /api/v1 前缀下
 */
export function getFileUrl(path: string | null | undefined): string {
  if (!path) return ''

  // 开发环境使用完整路径，生产环境使用相对路径
  if (import.meta.env.DEV) {
    return `http://localhost:5000/uploads/${path}`
  }
  return `/uploads/${path}`
}

/**
 * 获取 API 基础 URL
 */
export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL || '/api/v1'
}
