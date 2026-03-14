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

// 内部类型：扫描出的文件及其目标文件夹
interface ScanEntry {
  file: File
  groupId: number | null
  overwrite?: boolean
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
  onFolderDeleted?: (folderId: number) => void,
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
  const editFolderForm = ref({ name: '', description: '', targetParentId: undefined as number | undefined })

  function detectCategory(file: File): 'image' | 'video' | 'document' {
    if (file.type.startsWith('image/')) return 'image'
    if (file.type.startsWith('video/')) return 'video'
    return 'document'
  }

  // File item dragging (move between folders)
  function onFileDragStart(e: DragEvent, file: FileItem) {
    draggingFile.value = file
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'all'
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
      // B-1a: 根目录视图不重新 loadFiles()，防止移走的文件被重新加回
      // B-1b: 追加 loadRootGroups() 更新侧栏文件夹计数
      const tasks: Promise<void>[] = [loadSubFolders(), loadRootGroups()]
      if (currentFolderId.value !== null) tasks.push(loadFiles())
      await Promise.all(tasks)
      const stackSize = moveHistory.value.length
      ElMessage.success(stackSize > 1 ? `已移动，Ctrl+Z 可撤销（还有 ${stackSize} 步）` : '已移动，Ctrl+Z 可撤销')
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
      e.dataTransfer.effectAllowed = 'all'
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
    editFolderForm.value = { name: folder.name, description: folder.description || '', targetParentId: undefined }
    folderEditDialogVisible.value = true
  }

  async function handleFolderEdit() {
    const folder = editFolderTarget.value
    if (!folder) return
    const name = editFolderForm.value.name.trim()
    if (!name) { ElMessage.warning('名称不能为空'); return }
    folderEditLoading.value = true
    try {
      const desc = editFolderForm.value.description.trim()
      if (name !== folder.name || desc !== (folder.description || '')) {
        await groupsApi.update(folder.id, { name, description: desc || undefined })
      }
      if (editFolderForm.value.targetParentId !== undefined) {
        const newParent = editFolderForm.value.targetParentId === -1 ? null : editFolderForm.value.targetParentId
        await groupsApi.move(folder.id, newParent)
      }
      folderEditDialogVisible.value = false
      ElMessage.success('已保存')
      // B-1c: 追加 loadFiles() 确保主内容区刷新
      await Promise.all([loadRootGroups(), loadSubFolders(), loadFiles()])
    } catch { /* 错误由拦截器展示 */ } finally {
      folderEditLoading.value = false
    }
  }

  async function deleteFolderWithCheck(folder: FileGroup) {
    const hasContent = folder.file_count > 0 || folder.children_count > 0
    const msg = hasContent
      ? `将永久删除文件夹「${folder.name}」及其包含的 ${folder.file_count} 个文件、${folder.children_count} 个子文件夹，所有内容将被彻底删除，此操作不可撤销。`
      : `将永久删除文件夹「${folder.name}」，此操作不可撤销。`
    try {
      await ElMessageBox.confirm(msg, '删除文件夹', {
        confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
      })
    } catch { return }
    try {
      await groupsApi.delete(folder.id, true)
      onFolderDeleted?.(folder.id)
      await Promise.all([loadSubFolders(), loadFiles(), loadRootGroups()])
    } catch { ElMessage.error('删除文件夹失败') }
  }

  // Sidebar drag (shortcut creation — 仅允许文件夹)
  function onSidebarDragEnter(e: DragEvent) {
    if (draggingFolder.value) { e.preventDefault(); isSidebarDragOver.value = true }
  }
  function onSidebarDragOver(e: DragEvent) {
    if (draggingFolder.value) {
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
    if (draggingFolder.value) {
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
      // 同步提取（在 await navigateDeep 之前）
      const itemList = Array.from(e.dataTransfer.items).map(item => ({
        entry: item.webkitGetAsEntry?.() ?? null,
        file: item.getAsFile(),
      }))
      await navigateDeep(folder)
      const hasFolder = itemList.some(({ entry }) => entry?.isDirectory)
      if (hasFolder) ElMessage.info('正在创建文件夹结构，请稍候...')
      const collected: ScanEntry[] = []
      const failedFolders: string[] = []
      await Promise.all(itemList.map(({ entry, file }) => {
        if (entry) return scanWithStructure(entry, currentFolderId.value, collected, failedFolders)
        if (file) collected.push({ file, groupId: currentFolderId.value })
        return Promise.resolve()
      }))
      if (failedFolders.length > 0) {
        const names = failedFolders.slice(0, 3).map(n => `「${n}」`).join('、')
        const suffix = failedFolders.length > 3 ? ` 等共 ${failedFolders.length} 个` : ''
        ElMessage.warning(`部分文件夹创建失败，已跳过：${names}${suffix}`)
      }
      if (collected.length > 0) {
        startBatchUploadEntries(collected)
      } else {
        // 无文件上传（空文件夹），刷新 UI 显示新建的文件夹
        await Promise.all([loadRootGroups(), loadSubFolders()])
      }
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
    // 文件夹拖拽到主内容区：移动到当前目录
    if (draggingFolder.value) {
      const folder = draggingFolder.value; draggingFolder.value = null
      const targetParent = (currentFolderId.value !== null && currentFolderId.value > 0) ? currentFolderId.value : null
      try {
        await groupsApi.move(folder.id, targetParent)
        await Promise.all([loadRootGroups(), loadSubFolders()])
        ElMessage.success(targetParent === null ? '文件夹已移到根目录' : '文件夹已移动')
      } catch (err: any) { ElMessage.error(err?.response?.data?.error?.message || '移动失败') }
      return
    }
    if (isStorageFull.value) { ElMessage.warning('存储空间已满，无法上传'); return }
    const items = e.dataTransfer?.items
    if (!items || items.length === 0) return
    // 同步提取所有 entry/file（DataTransferItemList 在 await 后会被清空）
    const itemList = Array.from(items).map(item => ({
      entry: item.webkitGetAsEntry?.() ?? null,
      file: item.getAsFile(),
    }))
    const hasFolder = itemList.some(({ entry }) => entry?.isDirectory)
    if (hasFolder) ElMessage.info('正在创建文件夹结构，请稍候...')
    const collected: ScanEntry[] = []
    const failedFolders: string[] = []
    await Promise.all(itemList.map(({ entry, file }) => {
      if (entry) return scanWithStructure(entry, currentFolderId.value, collected, failedFolders)
      if (file) collected.push({ file, groupId: currentFolderId.value })
      return Promise.resolve()
    }))
    if (failedFolders.length > 0) {
      const names = failedFolders.slice(0, 3).map(n => `「${n}」`).join('、')
      const suffix = failedFolders.length > 3 ? ` 等共 ${failedFolders.length} 个` : ''
      ElMessage.warning(`部分文件夹创建失败，已跳过：${names}${suffix}`)
    }
    if (collected.length > 0) {
      startBatchUploadEntries(collected)
    } else {
      // 无文件上传（空文件夹），刷新 UI 显示新建的文件夹
      await Promise.all([loadRootGroups(), loadSubFolders()])
    }
  }

  // 读取目录下全部 entries（自动循环，因 readEntries 每次最多返回 100 条）
  function readAllEntries(reader: FileSystemDirectoryReader): Promise<FileSystemEntry[]> {
    return new Promise(resolve => {
      const all: FileSystemEntry[] = []
      const read = () => {
        reader.readEntries(entries => {
          if (entries.length === 0) { resolve(all); return }
          all.push(...entries); read()
        }, () => resolve(all))
      }
      read()
    })
  }

  // 递归扫描 entry：文件直接收集，目录先建（或合并）文件夹再递归
  // merge=true：同名文件夹自动使用已有 ID（覆盖上传场景）
  // 任何错误（含配额限制）均跳过整个子树，不回退到父目录（防止文件出现在错误目录）
  async function scanWithStructure(
    entry: FileSystemEntry,
    parentGroupId: number | null,
    collected: ScanEntry[],
    failedFolders: string[]
  ): Promise<void> {
    if (entry.isFile) {
      await new Promise<void>(resolve => {
        (entry as FileSystemFileEntry).file(
          f => { collected.push({ file: f, groupId: parentGroupId }); resolve() },
          () => resolve()
        )
      })
    } else if (entry.isDirectory) {
      let newGroupId: number | null = null
      try {
        const res = await groupsApi.create(entry.name, parentGroupId, true) // merge=true
        if (res.data) {
          newGroupId = res.data.id
        } else {
          failedFolders.push(entry.name)
          return // 无法获取 ID，跳过子树
        }
      } catch {
        failedFolders.push(entry.name)
        return // 任何错误（配额、权限等）均跳过子树，不回退到父目录
      }
      const children = await readAllEntries((entry as FileSystemDirectoryEntry).createReader())
      // 顺序处理，避免并发创建子文件夹导致 parentGroupId 错乱
      for (const child of children) {
        await scanWithStructure(child, newGroupId, collected, failedFolders)
      }
    }
  }

  async function startBatchUploadEntries(entries: ScanEntry[]) {
    // 按 (groupId, fileName) 判断重复，避免子文件夹中同名文件被误标为重复
    const existingKeys = new Set(
      allFiles.value.map(f => `${f.group_id ?? 'null'}:${f.file_name}`)
    )
    const getKey = (e: ScanEntry) => `${e.groupId ?? 'null'}:${e.file.name}`
    const duplicates = entries.filter(e => existingKeys.has(getKey(e)) && !e.overwrite)
    const newFiles = entries.filter(e => !existingKeys.has(getKey(e)) || e.overwrite)
    let toUpload = newFiles
    if (duplicates.length > 0) {
      const preview = duplicates.slice(0, 3).map(e => `「${e.file.name}」`).join('、')
      const suffix = duplicates.length > 3 ? ` 等共 ${duplicates.length} 个` : ''
      try {
        await ElMessageBox.confirm(
          `${preview}${suffix} 同名文件已存在，是否覆盖上传？`,
          '文件已存在',
          { confirmButtonText: '覆盖上传', cancelButtonText: '跳过', type: 'warning' }
        )
        toUpload = [...newFiles, ...duplicates.map(e => ({ ...e, overwrite: true }))]
      } catch {
        // 用户选择跳过，只上传新文件
      }
    }
    if (toUpload.length === 0) { ElMessage.info('没有需要上传的文件'); return }
    const tasks: UploadTask[] = toUpload.map((e, i) => ({
      id: `${Date.now()}-${i}`, file: e.file, progress: 0, status: 'pending',
    }))
    uploadTasks.value = tasks
    showUploadPanel.value = true
    batchUploading.value = true
    const typeErrors = new Map<string, number>()  // ".ext" → count
    const otherErrors = new Map<string, number>() // category → count
    for (let i = 0; i < uploadTasks.value.length; i++) {
      const task = uploadTasks.value[i]
      const entry = toUpload[i]
      task.status = 'uploading'
      try {
        const fd = new FormData()
        fd.append('file', task.file)
        fd.append('category', detectCategory(task.file))
        if (entry.groupId && entry.groupId > 0) fd.append('group_id', String(entry.groupId))
        if (entry.overwrite) fd.append('overwrite', 'true')
        // silent=true：批量上传时抑制逐条错误 toast，由下方统一汇报
        await filesApi.uploadWithProgress(fd, p => { task.progress = p }, true)
        task.status = 'done'; task.progress = 100
      } catch (err: any) {
        task.status = 'error'
        const errMsg = err?.response?.data?.error?.message || err?.message || '上传失败'
        if (errMsg.includes('类型') || errMsg.includes('format') || errMsg.includes('extension')) {
          // 从后端消息 "不支持的文件类型 .exe" 中提取扩展名，回退到文件名后缀
          const extMatch = errMsg.match(/\.\w+/)
          const ext = extMatch ? extMatch[0]
            : task.file.name.includes('.') ? `.${task.file.name.split('.').pop()!.toLowerCase()}` : '未知格式'
          typeErrors.set(ext, (typeErrors.get(ext) || 0) + 1)
        } else {
          const errKey = errMsg.includes('大小') || errMsg.includes('size') || errMsg.includes('large') ? '文件超出大小限制'
            : errMsg.includes('空间') || errMsg.includes('quota') || errMsg.includes('storage') ? '存储空间不足'
            : '上传失败'
          otherErrors.set(errKey, (otherErrors.get(errKey) || 0) + 1)
        }
      }
    }
    batchUploading.value = false
    if (typeErrors.size > 0 || otherErrors.size > 0) {
      const parts: string[] = []
      if (typeErrors.size > 0) {
        const typeList = [...typeErrors.entries()]
          .map(([ext, count]) => count > 1 ? `${ext}（${count}个）` : ext)
          .join('、')
        parts.push(`不支持的文件类型：${typeList}`)
      }
      for (const [category, count] of otherErrors) {
        parts.push(`${category}：${count} 个文件`)
      }
      ElMessage.warning(`部分文件上传失败 — ${parts.join('；')}`)
    }
    await Promise.all([loadFiles(), loadRootGroups(), loadSubFolders()])
    if (loadOverview) loadOverview()
    setTimeout(() => { if (!batchUploading.value) closeBatchPanel() }, 3000)
  }

  // 兼容旧调用：纯文件列表（不含文件夹结构），使用当前目录作为目标
  async function startBatchUpload(files: File[]) {
    const entries: ScanEntry[] = files.map(f => ({ file: f, groupId: currentFolderId.value }))
    await startBatchUploadEntries(entries)
  }

  // 上传文件夹（通过 <input webkitdirectory> 获取的 FileList）
  async function startFolderUpload(fileList: FileList) {
    if (isStorageFull.value) { ElMessage.warning('存储空间已满，无法上传'); return }
    const files = Array.from(fileList)
    if (files.length === 0) return
    ElMessage.info('正在创建文件夹结构，请稍候...')
    // 构建路径→group_id 映射
    const baseGroupId = currentFolderId.value
    const folderMap = new Map<string, number | null>()
    folderMap.set('', baseGroupId)
    const skipPaths = new Set<string>() // 创建失败或父级失败的路径
    const failedFolders: string[] = [] // 用于提示的根级失败文件夹名
    // 收集所有唯一文件夹路径并按深度排序
    const folderPaths = new Set<string>()
    for (const file of files) {
      const parts = file.webkitRelativePath.split('/')
      for (let i = 1; i < parts.length; i++) {
        folderPaths.add(parts.slice(0, i).join('/'))
      }
    }
    const sortedPaths = Array.from(folderPaths).sort((a, b) => a.split('/').length - b.split('/').length)
    // 顺序创建文件夹（merge=true：同名自动使用已有文件夹 ID）
    for (const path of sortedPaths) {
      const parts = path.split('/')
      const name = parts[parts.length - 1]
      const parentPath = parts.slice(0, -1).join('/')
      // 父级失败则本级也跳过
      if (skipPaths.has(parentPath)) { skipPaths.add(path); continue }
      const parentId = folderMap.get(parentPath) ?? baseGroupId
      try {
        const res = await groupsApi.create(name, parentId, true) // merge=true
        if (res.data) {
          folderMap.set(path, res.data.id)
        } else {
          // 无法获取 ID，跳过此路径及其子树
          skipPaths.add(path)
          if (parts.length === 1) failedFolders.push(name)
        }
      } catch {
        // 任何错误（配额限制等）均跳过此路径，不回退到父目录
        skipPaths.add(path)
        if (parts.length === 1) failedFolders.push(name)
      }
    }
    if (failedFolders.length > 0) {
      const names = failedFolders.map(n => `「${n}」`).join('、')
      ElMessage.warning(`部分文件夹创建失败，已跳过：${names}`)
    }
    // 构建上传条目，跳过位于被跳过文件夹中的文件
    const entries: ScanEntry[] = []
    for (const file of files) {
      const parts = file.webkitRelativePath.split('/')
      const folderPath = parts.slice(0, -1).join('/')
      // 检查文件夹路径或其任意祖先是否被跳过
      const isSkipped = Array.from({ length: parts.length - 1 }, (_, i) =>
        parts.slice(0, i + 1).join('/')
      ).some(p => skipPaths.has(p))
      if (!isSkipped) {
        entries.push({ file, groupId: folderMap.get(folderPath) ?? baseGroupId })
      }
    }
    await startBatchUploadEntries(entries)
    await Promise.all([loadRootGroups(), loadSubFolders()])
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
    startBatchUpload, startFolderUpload, closeBatchPanel,
  }
}
