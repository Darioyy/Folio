import { ref, computed, reactive } from 'vue'
import type { Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { filesApi } from '@/api/modules/files'
import { groupsApi } from '@/api/modules/groups'
import { hubApi } from '@/api/modules/hub'
import { usersApi } from '@/api/modules/users'
import type { FileItem } from '@/types/models'
import type { StorageInfo } from '@/api/modules/hub'
import type { MyStats } from '@/api/modules/users'

type TypeFilter = '' | 'image' | 'video' | 'document'

const TAB_DEFAULT_VIEW: Record<TypeFilter, 'grid' | 'list'> = {
  '': 'grid', resource: 'list', image: 'grid', video: 'grid',
}

function getTabViewKey(tab: TypeFilter) {
  return `vs-space-view:${tab || 'all'}`
}

function getSavedTabView(tab: TypeFilter): 'grid' | 'list' {
  return (localStorage.getItem(getTabViewKey(tab)) as 'grid' | 'list' | null) ?? TAB_DEFAULT_VIEW[tab]
}

export interface FolderNode { id: number; name: string; children?: FolderNode[] }

export function useFileManager(currentFolderId: Ref<number | null>) {
  const typeFilter = ref<TypeFilter>('')
  const viewMode = ref<'grid' | 'list'>(getSavedTabView(''))
  const allFiles = ref<FileItem[]>([])
  const filesLoading = ref(false)
  const searchQuery = ref('')
  const displayFiles = computed(() => {
    const q = searchQuery.value.trim().toLowerCase()
    if (!q) return allFiles.value
    return allFiles.value.filter(f =>
      f.file_name.toLowerCase().includes(q) ||
      (f.title && f.title.toLowerCase().includes(q))
    )
  })
  const previewVisible = ref(false)
  const currentFile = ref<FileItem | null>(null)

  // Storage / stats
  const storageInfo = ref<StorageInfo | null>(null)
  const myStats = reactive<MyStats>({ posts: 0, media: 0, resources: 0, total_size: 0 })

  const isStorageFull = computed(() => {
    if (!storageInfo.value) return false
    const { storage_used, storage_quota } = storageInfo.value
    return storage_quota > 0 && storage_used >= storage_quota
  })

  // Edit dialog
  const editDialogVisible = ref(false)
  const editLoading = ref(false)
  const editTargetId = ref<number | null>(null)
  const editForm = reactive({
    title: '', description: '', fileName: '', targetGroupId: undefined as number | undefined,
  })

  // Folder tree for move/edit dialogs
  const folderTree = ref<FolderNode[]>([])
  const folderCascaderOptions = computed<FolderNode[]>(() => [
    { id: -1, name: '根目录' },
    ...folderTree.value,
  ])

  // Upload dialog
  const uploadDialogVisible = ref(false)
  const uploading = ref(false)
  const uploadProgress = ref(0)
  const fileInputRef = ref<HTMLInputElement | null>(null)
  const uploadForm = reactive({
    file: null as File | null,
    description: '',
    targetFolderId: undefined as number | undefined,
  })

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
  }

  function detectCategory(file: File): 'image' | 'video' | 'document' {
    if (file.type.startsWith('image/')) return 'image'
    if (file.type.startsWith('video/')) return 'video'
    return 'document'
  }

  async function loadFiles() {
    filesLoading.value = true
    try {
      const cat = typeFilter.value || undefined
      const folderId = currentFolderId.value
      const res = await filesApi.getList({
        page_size: 200,
        ...(cat ? { category: cat as 'image' | 'video' | 'document' } : {}),
        // group_id: -1 = 根目录未分组文件；正整数 = 指定文件夹
        group_id: folderId !== null ? folderId : -1,
      })
      allFiles.value = res.items
    } catch { ElMessage.error('加载文件失败') } finally {
      filesLoading.value = false
    }
  }

  async function loadOverview() {
    try {
      const [storageRes, statsRes] = await Promise.all([
        hubApi.getStorageInfo(),
        usersApi.getMyStats(),
      ])
      if (storageRes.data) {
        storageInfo.value = {
          storage_used: storageRes.data.storage_used ?? 0,
          storage_quota: storageRes.data.storage_quota ?? 0,
          storage_percentage: Number(storageRes.data.storage_percentage ?? 0),
        }
      }
      Object.assign(myStats, statsRes.data)
    } catch { /* 静默失败 */ }
  }

  function handleTypeChange(val: TypeFilter) {
    typeFilter.value = val
    viewMode.value = getSavedTabView(val)
    loadFiles()
  }

  function toggleViewMode() {
    viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid'
    localStorage.setItem(getTabViewKey(typeFilter.value), viewMode.value)
  }

  async function handleDelete(file: FileItem) {
    try {
      await filesApi.delete(file.id)
      allFiles.value = allFiles.value.filter(f => f.id !== file.id)
      ElMessage.success('已删除')
      loadOverview()
    } catch { /* 错误已由拦截器展示 */ }
  }

  async function handleFileSortEnd() {
    const ids = allFiles.value.map(f => f.id)
    try { await filesApi.sortInGroup(ids) } catch { /* 排序失败静默 */ }
  }

  async function loadFolderTree() {
    try {
      const rootRes = await groupsApi.list()
      const roots = rootRes.data || []
      async function loadChildren(nodes: FolderNode[]): Promise<FolderNode[]> {
        return Promise.all(nodes.map(async (n) => {
          if (!n.id) return n
          const childRes = await groupsApi.getChildren(n.id)
          const children = childRes.data || []
          if (children.length === 0) return n
          return { ...n, children: await loadChildren(children.map(c => ({ id: c.id, name: c.name }))) }
        }))
      }
      folderTree.value = await loadChildren(roots.map(r => ({ id: r.id, name: r.name })))
    } catch { /* 静默失败 */ }
  }

  function openEdit(file: FileItem) {
    editTargetId.value = file.id
    editForm.title = file.title || ''
    editForm.description = file.description || ''
    editForm.fileName = file.file_name || ''
    editForm.targetGroupId = undefined
    loadFolderTree()
    editDialogVisible.value = true
  }

  async function handleEdit() {
    if (!editTargetId.value) return
    editLoading.value = true
    try {
      const original = allFiles.value.find(f => f.id === editTargetId.value)
      const fileNameChanged = editForm.fileName.trim() && editForm.fileName.trim() !== original?.file_name
      const res = await filesApi.update(editTargetId.value, {
        title: editForm.title.trim() || undefined,
        description: editForm.description.trim() || undefined,
        file_name: fileNameChanged ? editForm.fileName.trim() : undefined,
      })
      const idx = allFiles.value.findIndex(f => f.id === editTargetId.value)
      if (idx >= 0) allFiles.value[idx] = { ...allFiles.value[idx], ...res.data }
      if (editForm.targetGroupId !== undefined) {
        const groupId = editForm.targetGroupId === -1 ? null : editForm.targetGroupId
        await filesApi.updateGroup(editTargetId.value, groupId)
      }
      ElMessage.success('已保存')
      editDialogVisible.value = false
      await loadFiles()
    } catch { /* 拦截器展示 */ } finally {
      editLoading.value = false
    }
  }

  function openUpload() {
    if (isStorageFull.value && storageInfo.value) {
      ElMessage.error(`存储空间已满（${formatSize(storageInfo.value.storage_used)} / ${formatSize(storageInfo.value.storage_quota)}），请先删除部分文件`)
      return
    }
    uploadDialogVisible.value = true
  }

  function triggerFileInput() { fileInputRef.value?.click() }

  const MAX_FILE_SIZE = 16 * 1024 * 1024 // 16MB，与后端 MAX_CONTENT_LENGTH 保持一致

  function handleFileChange(e: Event) {
    const input = e.target as HTMLInputElement
    const file = input.files?.[0]
    if (file) {
      if (file.size > MAX_FILE_SIZE) {
        ElMessage.error(`文件大小不能超过 16MB，当前文件 ${(file.size / 1024 / 1024).toFixed(1)} MB`)
        input.value = ''
        return
      }
      uploadForm.file = file
    }
  }

  async function handleUpload() {
    if (!uploadForm.file) { ElMessage.warning('请选择文件'); return }
    uploading.value = true
    uploadProgress.value = 0
    const formData = new FormData()
    formData.append('file', uploadForm.file)
    formData.append('category', detectCategory(uploadForm.file))
    if (uploadForm.description.trim()) formData.append('description', uploadForm.description.trim())
    const targetId = uploadForm.targetFolderId !== undefined
      ? uploadForm.targetFolderId
      : (currentFolderId.value && currentFolderId.value > 0 ? currentFolderId.value : undefined)
    if (targetId && targetId > 0) formData.append('group_id', String(targetId))
    try {
      await filesApi.uploadWithProgress(formData, p => { uploadProgress.value = p })
      ElMessage.success('上传成功')
      uploadDialogVisible.value = false
      await loadFiles()
      loadOverview()
    } catch (err: any) {
      const code = err?.response?.data?.error?.code
      if (code === 'DUPLICATE_FILE') {
        const fileName = uploadForm.file?.name || '该文件'
        try {
          await ElMessageBox.confirm(
            `「${fileName}」已存在，是否覆盖上传？`,
            '文件已存在',
            { confirmButtonText: '覆盖上传', cancelButtonText: '取消', type: 'warning' }
          )
          formData.append('overwrite', 'true')
          uploading.value = true
          uploadProgress.value = 0
          await filesApi.uploadWithProgress(formData, p => { uploadProgress.value = p })
          ElMessage.success('上传成功（已覆盖）')
          uploadDialogVisible.value = false
          await loadFiles()
          loadOverview()
        } catch { /* 用户取消 */ }
      }
      // 其他错误由拦截器展示
    } finally {
      uploading.value = false
      uploadProgress.value = 0
    }
  }

  function resetUploadForm() {
    uploadForm.file = null
    uploadForm.description = ''
    uploadForm.targetFolderId = undefined
    uploadProgress.value = 0
    if (fileInputRef.value) fileInputRef.value.value = ''
  }

  return {
    typeFilter, viewMode, allFiles, displayFiles, filesLoading,
    searchQuery,
    previewVisible, currentFile, storageInfo, myStats, isStorageFull,
    editDialogVisible, editLoading, editTargetId, editForm,
    folderTree, folderCascaderOptions,
    uploadDialogVisible, uploading, uploadProgress, fileInputRef, uploadForm,
    loadFiles, loadOverview,
    handleTypeChange, toggleViewMode,
    handleDelete, handleFileSortEnd, loadFolderTree,
    openEdit, handleEdit, openUpload, triggerFileInput,
    handleFileChange, handleUpload, resetUploadForm,
    formatSize, detectCategory,
  }
}
