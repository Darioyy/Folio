import { ref, reactive, computed, watch } from 'vue'
import type { Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { usersApi } from '@/api/modules/users'

export function useSpaceCover(userId: Ref<number | undefined>) {
  const coverMeta = reactive({ image: '', size: 'cover' })
  const presetVisible = ref(false)
  const cropperVisible = ref(false)
  const cropperSrc = ref('')
  const cropperMode = ref<'avatar' | 'cover'>('avatar')

  function coverStorageKey(uid: number) {
    return `space_cover_${uid}`
  }

  function loadCustomCover() {
    const uid = userId.value
    if (!uid) return
    const stored = localStorage.getItem(coverStorageKey(uid))
    if (!stored) { coverMeta.image = ''; return }
    try {
      const parsed = JSON.parse(stored)
      if (parsed.image) {
        coverMeta.image = parsed.image
        coverMeta.size = parsed.size || 'cover'
        return
      }
    } catch { /* legacy bare data URL */ }
    coverMeta.image = `url(${stored})`
    coverMeta.size = 'cover'
  }

  const coverStyle = computed(() => {
    if (!coverMeta.image) return {}
    return {
      backgroundImage: coverMeta.image,
      backgroundSize: coverMeta.size,
      backgroundPosition: 'center',
      backgroundRepeat: coverMeta.size !== 'cover' ? 'repeat' : 'no-repeat',
    }
  })

  watch(userId, (uid) => { if (uid) loadCustomCover() }, { immediate: true })

  function openCropper(file: File, mode: 'avatar' | 'cover') {
    cropperSrc.value = URL.createObjectURL(file)
    cropperMode.value = mode
    cropperVisible.value = true
  }

  async function saveCoverToBackend(image: string, size: string) {
    usersApi.saveCover(JSON.stringify({ image, size })).catch(() => {
      ElMessage.warning('封面同步失败，刷新后可能无法恢复，请重试')
    })
  }

  async function onCoverCropped(dataUrl: string) {
    const imgValue = `url(${dataUrl})`
    coverMeta.image = imgValue
    coverMeta.size = 'cover'
    const uid = userId.value
    if (uid) {
      localStorage.setItem(coverStorageKey(uid), JSON.stringify({ image: imgValue, size: 'cover' }))
    }
    saveCoverToBackend(imgValue, 'cover')
  }

  function onPresetSelected(value: { image: string; size: string }) {
    coverMeta.image = value.image
    coverMeta.size = value.size
    const uid = userId.value
    if (uid) localStorage.setItem(coverStorageKey(uid), JSON.stringify(value))
    saveCoverToBackend(value.image, value.size)
  }

  return {
    coverMeta,
    presetVisible,
    coverStyle,
    cropperVisible,
    cropperSrc,
    cropperMode,
    openCropper,
    onCoverCropped,
    onPresetSelected,
  }
}
