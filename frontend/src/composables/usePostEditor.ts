import { ref, watch } from 'vue'
import { postsApi } from '@/api/modules/posts'
import { filesApi } from '@/api/modules/files'
import { useUserStore } from '@/stores/user'
import type { Post, Category, PostAttachment } from '@/types/models'

let saveTimer: ReturnType<typeof setTimeout> | null = null

export function usePostEditor() {
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

  function scheduleAutoSave() {
    const key = postId.value ? getDraftKey(postId.value) : getDraftNewKey()
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => writeLocalDraft(key), 2000)
  }

  function initNew() {
    postId.value = null; title.value = ''; content.value = ''; summary.value = ''
    categoryId.value = null; coverImageId.value = null; coverImageUrl.value = ''; attachments.value = []
    status.value = 'draft'
    readLocalDraft(getDraftNewKey())
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
      coverImageUrl.value = p.cover_image_id ? filesApi.getThumbnailUrl(p.cover_image_id) : ''
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
        if (res.success && res.data) { postId.value = res.data.id; return res.data.id }
        return null
      }
    } finally { saving.value = false }
  }

  async function publish(): Promise<number | null> {
    const id = await saveDraft()
    if (!id) return null
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
    coverImageUrl.value = filesApi.getThumbnailUrl(fileId)
  }

  function clearLocalDraft() {
    localStorage.removeItem(postId.value ? getDraftKey(postId.value) : getDraftNewKey())
  }

  return {
    postId, title, content, summary, categoryId,
    coverImageId, coverImageUrl, attachments, status, saving, categories,
    initNew, initEdit, saveDraft, publish,
    addAttachment, removeAttachment, setCoverImage, clearLocalDraft
  }
}
