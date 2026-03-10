import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types/api'
import { storage } from '@/utils/storage'

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  withCredentials: true // 支持 cookie
})

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 添加 token（如果使用 Bearer Token）
    const token = storage.getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse

    // 后端统一响应格式：{ success: boolean, data?: any, error?: {code, message} | string }
    if (data.success === false) {
      // 兼容两种错误格式：{error: string} 或 {error: {code, message}}
      const errorMsg = typeof data.error === 'string'
        ? data.error
        : data.error?.message || '请求失败'
      ElMessage.error(errorMsg)
      return Promise.reject(new Error(errorMsg))
    }

    return response
  },
  (error: AxiosError<ApiResponse>) => {
    const { response } = error

    if (response) {
      const { status, data } = response

      // 兼容错误格式
      const errorMsg = typeof data?.error === 'string'
        ? data.error
        : data?.error?.message || ''

      switch (status) {
        case 401:
          ElMessage.error(errorMsg || '未登录或登录已过期')
          storage.clear()
          window.location.href = '/login'
          break
        case 403:
          ElMessage.error(errorMsg || '没有权限访问')
          break
        case 404:
          ElMessage.error(errorMsg || '请求的资源不存在')
          break
        case 500:
          ElMessage.error(errorMsg || '服务器错误')
          break
        default:
          ElMessage.error(errorMsg || `请求失败 (${status})`)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时')
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

export default service
