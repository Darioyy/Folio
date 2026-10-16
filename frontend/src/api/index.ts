import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types/api'
import { storage } from '@/utils/storage'

// 防止多个并发 401 响应触发多次跳转
let isRedirectingToLogin = false

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  withCredentials: true // 支持 cookie
})

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
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
    const silent = (response.config as any)._silent

    // 后端统一响应格式：{ success: boolean, data?: any, error?: {code, message} | string }
    if (data.success === false) {
      // 兼容两种错误格式：{error: string} 或 {error: {code, message}}
      const errorMsg = typeof data.error === 'string'
        ? data.error
        : data.error?.message || '请求失败'
      if (!silent) ElMessage.error({ message: errorMsg, duration: 5000, showClose: true })
      return Promise.reject(new Error(errorMsg))
    }

    return response
  },
  (error: AxiosError<ApiResponse>) => {
    // 静默模式：不显示错误 toast（用于批量上传，由调用方统一汇总）
    if ((error.config as any)?._silent) return Promise.reject(error)

    const { response } = error

    if (response) {
      const { status, data } = response

      // 兼容错误格式
      const errorMsg = typeof data?.error === 'string'
        ? data.error
        : data?.error?.message || ''

      const msgOpts = (msg: string) => ({ message: msg, duration: 5000, showClose: true })
      switch (status) {
        case 401:
          if (!isRedirectingToLogin) {
            isRedirectingToLogin = true
            ElMessage.error(msgOpts(errorMsg || '未登录或登录已过期'))
            storage.clear()
            window.location.href = '/login'
          }
          break
        case 403:
          ElMessage.error(msgOpts(errorMsg || '没有权限访问'))
          break
        case 404:
          ElMessage.error(msgOpts(errorMsg || '请求的资源不存在'))
          break
        case 500:
          ElMessage.error(msgOpts(errorMsg || '服务器错误'))
          break
        default:
          ElMessage.error(msgOpts(errorMsg || `请求失败 (${status})`))
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error({ message: '请求超时', duration: 5000, showClose: true })
    } else {
      ElMessage.error({ message: '网络错误，请检查网络连接', duration: 5000, showClose: true })
    }

    return Promise.reject(error)
  }
)

export default service
