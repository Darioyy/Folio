import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useMediaStore = defineStore('media', () => {
  // 状态
  const mediaType = ref<'image' | 'video'>('image')
  const selectedMedia = ref<number[]>([])

  // 设置媒体类型
  function setMediaType(type: 'image' | 'video') {
    mediaType.value = type
    selectedMedia.value = [] // 切换类型时清空选择
  }

  // 选择/取消选择媒体
  function toggleMedia(id: number) {
    const index = selectedMedia.value.indexOf(id)
    if (index > -1) {
      selectedMedia.value.splice(index, 1)
    } else {
      selectedMedia.value.push(id)
    }
  }

  // 全选/取消全选
  function toggleSelectAll(ids: number[]) {
    if (selectedMedia.value.length === ids.length) {
      selectedMedia.value = []
    } else {
      selectedMedia.value = [...ids]
    }
  }

  // 清空选择
  function clearSelection() {
    selectedMedia.value = []
  }

  return {
    mediaType,
    selectedMedia,
    setMediaType,
    toggleMedia,
    toggleSelectAll,
    clearSelection
  }
})
