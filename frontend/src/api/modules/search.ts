import { get } from '../request'
import type { ApiResponse } from '@/types/api'
import type { SearchResult } from '@/types/models'

export const searchApi = {
  /**
   * 全站搜索
   */
  search(
    q: string,
    type: 'file' | 'user' | 'all' = 'all',
    page = 1,
    pageSize = 20
  ): Promise<ApiResponse<SearchResult>> {
    return get('/search', { q, type, page, page_size: pageSize })
  }
}
