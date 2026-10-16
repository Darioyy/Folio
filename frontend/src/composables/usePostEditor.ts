import { ref, watch, onUnmounted } from 'vue'
import { postsApi } from '@/api/modules/posts'
import { filesApi } from '@/api/modules/files'
import { useUserStore } from '@/stores/user'
import type { Post, Category, PostAttachment } from '@/types/models'

export function usePostEditor() {
  // saveTimer 在 composable 实例内部，避免多实例共享同一 timer 引用导致内存泄漏
  let saveTimer: ReturnType<typeof setTimeout> | null = null
  const userStore = useUserStore()

  // localStorage 键名含用户 ID，防止多账号草稿污染
  const getDraftNewKey = () => `folio_draft_new_${userStore.currentUser?.id ?? ''}`
  const getDraftKey = (id: number) => `folio_draft_${id}_${userStore.currentUser?.id ?? ''}`

  const postId = ref<number | null>(null)
  const title = ref('')
  const content = ref('')
  const summary = ref('')
  const categoryId = ref<number | null>(null)
  const coverImageId = ref<number | null>(null)
  const coverImageUrl = ref('')
  const attachments = ref<PostAttachment[]>([])
  const status = ref<'draft' | 'published'>('draft')
  const saving = ref(false)
  const categories = ref<Category[]>([])

  async function loadCategories() {
    try {
      const res = await postsApi.getCategories()
      if (res.data) categories.value = res.data
    } catch { /* 静默 */ }
  }

  function readLocalDraft(key: string) {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) return
      const d = JSON.parse(raw)
      if (d.title) title.value = d.title
      if (d.content) content.value = d.content
      if (d.summary) summary.value = d.summary
    } catch { /* 忽略 */ }
  }

  function writeLocalDraft(key: string) {
    localStorage.setItem(key, JSON.stringify({ title: title.value, content: content.value, summary: summary.value }))
  }

  /** 立即将当前内容写入 localStorage（用于 beforeunload 等无法等待 debounce 的场景） */
  function flushLocalDraft() {
    const key = postId.value ? getDraftKey(postId.value) : getDraftNewKey()
    writeLocalDraft(key)
  }

  function scheduleAutoSave() {
    const key = postId.value ? getDraftKey(postId.value) : getDraftNewKey()
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => writeLocalDraft(key), 2000)
  }

  function initNew() {
    postId.value = null; title.value = ''; content.value = ''; summary.value = ''
    categoryId.value = null; coverImageId.value = null; coverImageUrl.value = ''; attachments.value = []
    status.value = 'draft'
    // 始终清除残留的"新建"草稿 key，保证新建时为空白编辑器
    localStorage.removeItem(getDraftNewKey())
    loadCategories()
    watch([title, content], scheduleAutoSave)
  }

  async function initEdit(id: number) {
    postId.value = id
    loadCategories()
    try {
      const res = await postsApi.getDetail(id)
      if (!res.success || !res.data) return
      const p: Post = res.data
      title.value = p.title; content.value = p.content; summary.value = p.summary || ''
      categoryId.value = p.category_id ?? null; coverImageId.value = p.cover_image_id ?? null
      coverImageUrl.value = p.cover_image_id ? filesApi.getViewUrl(p.cover_image_id) : ''
      attachments.value = p.attachments || []; status.value = p.status === 'published' ? 'published' : 'draft'
    } catch { /* 静默 */ }
    watch([title, content], scheduleAutoSave)
  }

  async function saveDraft(): Promise<number | null> {
    saving.value = true
    try {
      const payload: Partial<Post> = {
        title: title.value, content: content.value,
        summary: summary.value || undefined,
        category_id: categoryId.value ?? undefined,
        cover_image_id: coverImageId.value ?? undefined
      }
      if (postId.value) {
        const res = await postsApi.update(postId.value, payload)
        return res.success ? postId.value : null
      } else {
        const res = await postsApi.create(payload)
        if (res.success && res.data) {
          postId.value = res.data.id
          // 新建草稿首次保存后立即清除"新建"key，防止下次新建时恢复旧内容
          localStorage.removeItem(getDraftNewKey())
          return res.data.id
        }
        return null
      }
    } finally { saving.value = false }
  }

  async function publish(): Promise<number | null> {
    const id = await saveDraft()
    if (!id) return null
    // 若已是发布状态，直接返回 id（无需再次调用 publish 接口）
    if (status.value === 'published') {
      clearLocalDraft()
      return id
    }
    const res = await postsApi.publish(id)
    if (res.success) { status.value = 'published'; clearLocalDraft(); return id }
    return null
  }

  async function addAttachment(fileId: number) {
    if (!postId.value) return
    const res = await postsApi.addAttachment(postId.value, fileId)
    if (res.success) {
      const detail = await postsApi.getDetail(postId.value)
      if (detail.data) attachments.value = detail.data.attachments || []
    }
  }

  async function removeAttachment(fileId: number) {
    if (!postId.value) return
    const res = await postsApi.removeAttachment(postId.value, fileId)
    if (res.success) attachments.value = attachments.value.filter(a => a.file_id !== fileId)
  }

  function setCoverImage(fileId: number) {
    coverImageId.value = fileId
    coverImageUrl.value = filesApi.getViewUrl(fileId)
  }

  function clearLocalDraft() {
    // 始终清除"新建"草稿 key，确保下次新建时得到空白编辑器
    localStorage.removeItem(getDraftNewKey())
    if (postId.value) localStorage.removeItem(getDraftKey(postId.value))
  }

  // 组件卸载时清除待触发的自动保存定时器，防止对已销毁组件写入
  onUnmounted(() => {
    if (saveTimer) {
      clearTimeout(saveTimer)
      saveTimer = null
    }
  })

  return {
    postId, title, content, summary, categoryId,
    coverImageId, coverImageUrl, attachments, status, saving, categories,
    initNew, initEdit, saveDraft, publish,
    addAttachment, removeAttachment, setCoverImage, clearLocalDraft, flushLocalDraft
  }
}
