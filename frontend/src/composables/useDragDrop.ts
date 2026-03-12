import { ref } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { filesApi } from '@/api/modules/files'
import { groupsApi } from '@/api/modules/groups'
import type { FileItem } from '@/types/models'
import type { FileGroup } from '@/api/modules/groups'

export interface UploadTask {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'done' | 'error'
}

export function useDragDrop(
  currentFolderId: Ref<number | null>,
  allFiles: Ref<FileItem[]>,
  isStorageFull: ComputedRef<boolean>,
  addShortcut: (type: 'folder' | 'file', id: number, name: string) => void,
  loadFiles: () => Promise<void>,
  loadSubFolders: () => Promise<void>,
  loadRootGroups: () => Promise<void>,
  navigateDeep: (folder: FileGroup) => Promise<void>,
  loadOverview?: () => Promise<void>,
) {
  // Upload drag
  const isDragOver = ref(false)
  const dragCounter = ref(0)
  const uploadTasks = ref<UploadTask[]>([])
  const showUploadPanel = ref(false)
  const batchUploading = ref(false)

  // File/folder item drag
  const draggingFile = ref<FileItem | null>(null)
  const draggingFolder = ref<FileGroup | null>(null)
  const isSidebarDragOver = ref(false)
  const dragOverFolderId = ref<number | null>(null)
  let folderHoverTimer: ReturnType<typeof setTimeout> | null = null
  const moveHistory = ref<Array<{ fileId: number; prevGroupId: number | null }>>([])

  // Folder edit dialog
  const folderEditDialogVisible = ref(false)
  const folderEditLoading = ref(false)
  const editFolderTarget = ref<FileGroup | null>(null)
  const editFolderForm = ref({ name: '', targetParentId: undefined as number | undefined })

  function detectCategory(file: File): 'image' | 'video' | 'document' {
    if (file.type.startsWith('image/')) return 'image'
    if (file.type.startsWith('video/')) return 'video'
    return 'document'
  }

  // File item dragging (move between folders)
  function onFileDragStart(e: DragEvent, file: FileItem) {
    draggingFile.value = file
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('application/vaultshare-file', String(file.id))
    }
  }

  function onFileDragEnd() {
    draggingFile.value = null
    dragOverFolderId.value = null
    if (folderHoverTimer) { clearTimeout(folderHoverTimer); folderHoverTimer = null }
  }

  async function moveFileTo(file: FileItem, targetGroupId: number | null) {
    const prevGroupId = file.group_id ?? null
    if (prevGroupId === targetGroupId) return
    // 乐观更新：立即移除，避免界面延迟
    allFiles.value = allFiles.value.filter(f => f.id !== file.id)
    try {
      await filesApi.updateGroup(file.id, targetGroupId)
      moveHistory.value.push({ fileId: file.id, prevGroupId })
      await Promise.all([loadSubFolders(), loadFiles()])
      ElMessage.success('已移动，Ctrl+Z 可撤销')
    } catch {
      // 回滚：重新加载文件列表
      await loadFiles()
      ElMessage.error('移动失败')
    }
  }

  async function undoLastMove() {
    const last = moveHistory.value.pop()
    if (!last) return
    try {
      await filesApi.updateGroup(last.fileId, last.prevGroupId)
      ElMessage.success('已撤销')
      await loadFiles()
    } catch { ElMessage.error('撤销失败') }
  }

  // Folder item dragging
  function onFolderDragStart(e: DragEvent, folder: FileGroup) {
    draggingFolder.value = folder
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('application/vaultshare-folder', String(folder.id))
    }
  }

  function onFolderDragEnd() {
    draggingFolder.value = null
    dragOverFolderId.value = null
    if (folderHoverTimer) { clearTimeout(folderHoverTimer); folderHoverTimer = null }
  }

  function openFolderEdit(folder: FileGroup) {
    editFolderTarget.value = folder
    editFolderForm.value = { name: folder.name, targetParentId: undefined }
    folderEditDialogVisible.value = true
  }

  async function handleFolderEdit() {
    const folder = editFolderTarget.value
    if (!folder) return
    const name = editFolderForm.value.name.trim()
    if (!name) { ElMessage.warning('名称不能为空'); return }
    folderEditLoading.value = true
    try {
      if (name !== folder.name) await groupsApi.rename(folder.id, name)
      if (editFolderForm.value.targetParentId !== undefined) {
        const newParent = editFolderForm.value.targetParentId === -1 ? null : editFolderForm.value.targetParentId
        await groupsApi.move(folder.id, newParent)
      }
      folderEditDialogVisible.value = false
      ElMessage.success('已保存')
      await Promise.all([loadRootGroups(), loadSubFolders()])
    } catch (err: any) {
      ElMessage.error(err?.response?.data?.error?.message || '操作失败')
    } finally {
      folderEditLoading.value = false
    }
  }

  async function deleteFolderWithCheck(folder: FileGroup) {
    const hasContent = folder.file_count > 0 || folder.children_count > 0
    const msg = hasContent
      ? `文件夹「${folder.name}」包含 ${folder.file_count} 个文件和 ${folder.children_count} 个子文件夹，确认删除将递归删除所有内容，此操作不可撤销。`
      : `确认删除文件夹「${folder.name}」？`
    try {
      await ElMessageBox.confirm(msg, '删除文件夹', {
        confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
      })
    } catch { return }
    try {
      await groupsApi.delete(folder.id, hasContent)
      await Promise.all([loadSubFolders(), loadFiles(), loadRootGroups()])
    } catch { ElMessage.error('删除文件夹失败') }
  }

  // Sidebar drag (shortcut creation)
  function onSidebarDragEnter(e: DragEvent) {
    if (draggingFile.value || draggingFolder.value) { e.preventDefault(); isSidebarDragOver.value = true }
  }
  function onSidebarDragOver(e: DragEvent) {
    if (draggingFile.value || draggingFolder.value) {
      e.preventDefault()
      if (e.dataTransfer) e.dataTransfer.dropEffect = 'link'
    }
  }
  function onSidebarDragLeave(e: DragEvent) {
    const related = e.relatedTarget as Node | null
    if (!(e.currentTarget as HTMLElement).contains(related)) isSidebarDragOver.value = false
  }
  function onSidebarDrop(e: DragEvent) {
    e.preventDefault()
    isSidebarDragOver.value = false
    if (draggingFile.value) {
      addShortcut('file', draggingFile.value.id, draggingFile.value.file_name)
      draggingFile.value = null
    } else if (draggingFolder.value) {
      addShortcut('folder', draggingFolder.value.id, draggingFolder.value.name)
      draggingFolder.value = null
    }
  }

  // Subfolder hover spring-load
  function onFolderDragEnter(e: DragEvent, folder: FileGroup) {
    const isFileDrag = !!draggingFile.value
    const isFolderDrag = !!draggingFolder.value
    const isDiskDrag = e.dataTransfer?.types.includes('Files') ?? false
    if (!isFileDrag && !isFolderDrag && !isDiskDrag) return
    e.preventDefault()
    dragOverFolderId.value = folder.id
    if (folderHoverTimer) clearTimeout(folderHoverTimer)
    folderHoverTimer = setTimeout(async () => {
      folderHoverTimer = null
      await navigateDeep(folder)
    }, 600)
  }
  function onFolderDragOver(e: DragEvent) {
    if (draggingFile.value || draggingFolder.value || e.dataTransfer?.types.includes('Files')) {
      e.preventDefault()
      if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
    }
  }
  function onFolderDragLeave(e: DragEvent) {
    const related = e.relatedTarget as Node | null
    if ((e.currentTarget as HTMLElement).contains(related)) return
    if (folderHoverTimer) { clearTimeout(folderHoverTimer); folderHoverTimer = null }
    dragOverFolderId.value = null
  }
  async function onFolderDrop(e: DragEvent, folder: FileGroup) {
    e.stopPropagation(); e.preventDefault()
    if (folderHoverTimer) { clearTimeout(folderHoverTimer); folderHoverTimer = null }
    dragOverFolderId.value = null
    if (draggingFolder.value) {
      const src = draggingFolder.value; draggingFolder.value = null
      if (src.id === folder.id) return
      try {
        await groupsApi.move(src.id, folder.id)
        await Promise.all([loadRootGroups(), loadSubFolders()])
        ElMessage.success('文件夹已移动')
      } catch (err: any) { ElMessage.error(err?.response?.data?.error?.message || '移动失败') }
      return
    }
    if (draggingFile.value) {
      const file = draggingFile.value; draggingFile.value = null
      await moveFileTo(file, folder.id); return
    }
    if (e.dataTransfer?.types.includes('Files')) {
      isDragOver.value = false; dragCounter.value = 0
      await navigateDeep(folder)
      const items = e.dataTransfer.items
      if (!items || items.length === 0) return
      const files: File[] = []
      await Promise.all(Array.from(items).map(item => {
        const entry = item.webkitGetAsEntry?.()
        if (entry) return collectEntryFiles(entry, files)
        const f = item.getAsFile(); if (f) files.push(f)
        return Promise.resolve()
      }))
      if (files.length > 0) startBatchUpload(files)
    }
  }

  // Main area drag upload
  function onDragEnter(e: DragEvent) {
    if (isStorageFull.value) return
    if (e.dataTransfer?.types.includes('Files')) { dragCounter.value++; isDragOver.value = true }
  }
  function onDragLeave() {
    dragCounter.value--
    if (dragCounter.value <= 0) { dragCounter.value = 0; isDragOver.value = false }
  }
  async function onDrop(e: DragEvent) {
    isDragOver.value = false; dragCounter.value = 0
    if (draggingFile.value) {
      const file = draggingFile.value; draggingFile.value = null
      if (currentFolderId.value !== null && currentFolderId.value > 0) await moveFileTo(file, currentFolderId.value)
      return
    }
    if (isStorageFull.value) { ElMessage.warning('存储空间已满，无法上传'); return }
    const items = e.dataTransfer?.items
    if (!items || items.length === 0) return
    const files: File[] = []
    await Promise.all(Array.from(items).map(item => {
      const entry = item.webkitGetAsEntry?.()
      if (entry) return collectEntryFiles(entry, files)
      const f = item.getAsFile(); if (f) files.push(f)
      return Promise.resolve()
    }))
    if (files.length > 0) startBatchUpload(files)
  }

  function collectEntryFiles(entry: FileSystemEntry, files: File[]): Promise<void> {
    if (entry.isFile) {
      return new Promise(resolve => {
        (entry as FileSystemFileEntry).file(f => { files.push(f); resolve() }, () => resolve())
      })
    }
    if (entry.isDirectory) {
      const reader = (entry as FileSystemDirectoryEntry).createReader()
      return new Promise(resolve => {
        const read = () => {
          reader.readEntries(async entries => {
            if (entries.length === 0) { resolve(); return }
            await Promise.all(entries.map(e => collectEntryFiles(e, files)))
            read()
          }, () => resolve())
        }
        read()
      })
    }
    return Promise.resolve()
  }

  async function startBatchUpload(files: File[]) {
    const existingNames = new Set(allFiles.value.map(f => f.file_name))
    const duplicates = files.filter(f => existingNames.has(f.name))
    let skipAll = false
    if (duplicates.length > 0) {
      try {
        const action = await ElMessageBox.confirm(
          `以下 ${duplicates.length} 个文件已存在同名文件：\n${duplicates.slice(0, 5).map(f => f.name).join('\n')}${duplicates.length > 5 ? `\n...（共 ${duplicates.length} 个）` : ''}\n\n选择"覆盖"将重新上传，选择"跳过"将跳过这些文件。`,
          '发现同名文件',
          { distinguishCancelAndClose: true, confirmButtonText: '覆盖', cancelButtonText: '跳过', type: 'warning' }
        )
        if (action !== 'confirm') skipAll = true
      } catch (action) {
        if (action === 'cancel') skipAll = true
        else return
      }
    }
    const filesToUpload = skipAll ? files.filter(f => !existingNames.has(f.name)) : files
    if (filesToUpload.length === 0) { ElMessage.info('没有需要上传的文件'); return }
    const tasks: UploadTask[] = filesToUpload.map((file, i) => ({
      id: `${Date.now()}-${i}`, file, progress: 0, status: 'pending',
    }))
    uploadTasks.value = tasks
    showUploadPanel.value = true
    batchUploading.value = true
    const errorTypes = new Map<string, number>()
    for (const task of uploadTasks.value) {
      task.status = 'uploading'
      try {
        const fd = new FormData()
        fd.append('file', task.file)
        fd.append('category', detectCategory(task.file))
        if (currentFolderId.value && currentFolderId.value > 0) fd.append('group_id', String(currentFolderId.value))
        await filesApi.uploadWithProgress(fd, p => { task.progress = p })
        task.status = 'done'; task.progress = 100
      } catch (err: any) {
        task.status = 'error'
        const errMsg = err?.response?.data?.error?.message || err?.message || '上传失败'
        const errKey = errMsg.includes('类型') || errMsg.includes('format') || errMsg.includes('extension') ? '不支持的文件类型'
          : errMsg.includes('大小') || errMsg.includes('size') || errMsg.includes('large') ? '文件超出大小限制'
          : errMsg.includes('空间') || errMsg.includes('quota') || errMsg.includes('storage') ? '存储空间不足'
          : '上传失败'
        errorTypes.set(errKey, (errorTypes.get(errKey) || 0) + 1)
      }
    }
    batchUploading.value = false
    if (errorTypes.size > 0) {
      const summary = [...errorTypes.entries()].map(([type, count]) => `${type}：${count} 个文件`).join('；')
      ElMessage.warning(`部分文件上传失败 — ${summary}`)
    }
    await loadFiles()
    if (loadOverview) loadOverview()
    setTimeout(() => { if (!batchUploading.value) closeBatchPanel() }, 3000)
  }

  function closeBatchPanel() {
    if (batchUploading.value) return
    showUploadPanel.value = false
    uploadTasks.value = []
  }

  return {
    isDragOver, dragCounter, uploadTasks, showUploadPanel, batchUploading,
    draggingFile, draggingFolder, isSidebarDragOver, dragOverFolderId, moveHistory,
    folderEditDialogVisible, folderEditLoading, editFolderTarget, editFolderForm,
    onFileDragStart, onFileDragEnd, moveFileTo, undoLastMove,
    onFolderDragStart, onFolderDragEnd,
    openFolderEdit, handleFolderEdit, deleteFolderWithCheck,
    onSidebarDragEnter, onSidebarDragOver, onSidebarDragLeave, onSidebarDrop,
    onFolderDragEnter, onFolderDragOver, onFolderDragLeave, onFolderDrop,
    onDragEnter, onDragLeave, onDrop,
    startBatchUpload, closeBatchPanel,
  }
}
