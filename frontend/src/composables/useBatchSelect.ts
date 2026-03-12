import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { filesApi } from '@/api/modules/files'
import { groupsApi } from '@/api/modules/groups'
import type { FileItem } from '@/types/models'
import type { FileGroup } from '@/api/modules/groups'

export function useBatchSelect(
  allFiles: Ref<FileItem[]>,
  subFolders: Ref<FileGroup[]>,
  loadFiles: () => Promise<void>,
  loadSubFolders: () => Promise<void>,
  loadRootGroups: () => Promise<void>,
  loadFolderTree: () => Promise<void>,
  folderCascaderOptions: Ref<Array<{ id: number; name: string; children?: any[] }>>,
  loadOverview?: () => Promise<void>,
) {
  const isEditMode = ref(false)
  const selectedItems = ref<Set<string>>(new Set())

  const showBatchMove = ref(false)
  const batchMoveTarget = ref<number | null>(null)
  const batchMoveLoading = ref(false)
  const showBatchRenameDialog = ref(false)
  const batchRenameName = ref('')
  const batchRenameLoading = ref(false)

  const isAllSelected = computed(() => {
    const total = allFiles.value.length + subFolders.value.length
    if (total === 0) return false
    return allFiles.value.every(f => selectedItems.value.has(`file:${f.id}`)) &&
      subFolders.value.every(g => selectedItems.value.has(`folder:${g.id}`))
  })

  const batchRenameIsMulti = computed(() => selectedItems.value.size > 1)

  function toggleEditMode() {
    isEditMode.value = !isEditMode.value
    if (!isEditMode.value) selectedItems.value = new Set()
  }

  function toggleSelect(type: 'file' | 'folder', id: number) {
    const key = `${type}:${id}`
    const next = new Set(selectedItems.value)
    if (next.has(key)) next.delete(key)
    else next.add(key)
    selectedItems.value = next
  }

  function selectAllItems() {
    if (isAllSelected.value) {
      selectedItems.value = new Set()
    } else {
      const next = new Set<string>()
      allFiles.value.forEach(f => next.add(`file:${f.id}`))
      subFolders.value.forEach(g => next.add(`folder:${g.id}`))
      selectedItems.value = next
    }
  }

  async function batchDelete() {
    if (selectedItems.value.size === 0) return
    const fileIds = [...selectedItems.value].filter(k => k.startsWith('file:')).map(k => Number(k.slice(5)))
    const folderIds = [...selectedItems.value].filter(k => k.startsWith('folder:')).map(k => Number(k.slice(7)))
    const total = fileIds.length + folderIds.length
    try {
      await ElMessageBox.confirm(
        `确认删除已选的 ${total} 个项目？文件夹中的文件将移至未分组，此操作不可撤销。`,
        '批量删除',
        { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
      )
    } catch { return }
    let errCount = 0
    for (const id of fileIds) { try { await filesApi.delete(id) } catch { errCount++ } }
    for (const id of folderIds) { try { await groupsApi.delete(id) } catch { errCount++ } }
    if (errCount > 0) ElMessage.warning(`部分项目删除失败（${errCount} 个）`)
    else ElMessage.success(`已删除 ${total} 个项目`)
    selectedItems.value = new Set()
    await Promise.all([loadFiles(), loadRootGroups(), loadSubFolders()])
    if (loadOverview) loadOverview()
  }

  function openBatchMove() {
    loadFolderTree()
    batchMoveTarget.value = null
    showBatchMove.value = true
  }

  async function executeBatchMove() {
    if (selectedItems.value.size === 0) { showBatchMove.value = false; return }
    const fileIds = [...selectedItems.value].filter(k => k.startsWith('file:')).map(k => Number(k.slice(5)))
    batchMoveLoading.value = true
    let errCount = 0
    for (const id of fileIds) {
      try {
        await filesApi.updateGroup(id, batchMoveTarget.value === -1 ? null : batchMoveTarget.value)
      } catch { errCount++ }
    }
    batchMoveLoading.value = false
    showBatchMove.value = false
    batchMoveTarget.value = null
    if (errCount > 0) ElMessage.warning(`部分文件移动失败（${errCount} 个）`)
    else ElMessage.success('移动完成')
    selectedItems.value = new Set()
    await loadFiles()
  }

  function startBatchRename() {
    if (selectedItems.value.size === 0) return
    const first = [...selectedItems.value][0]
    if (first.startsWith('file:')) {
      const id = Number(first.slice(5))
      batchRenameName.value = allFiles.value.find(f => f.id === id)?.title || ''
    } else {
      const id = Number(first.slice(7))
      batchRenameName.value = subFolders.value.find(f => f.id === id)?.name || ''
    }
    showBatchRenameDialog.value = true
  }

  async function executeBatchRename() {
    const baseName = batchRenameName.value.trim()
    if (!baseName) { ElMessage.warning('名称不能为空'); return }
    batchRenameLoading.value = true
    const items = [...selectedItems.value]
    let errCount = 0
    for (let i = 0; i < items.length; i++) {
      const name = i === 0 ? baseName : `${baseName}(${i})`
      const key = items[i]
      try {
        if (key.startsWith('file:')) {
          const id = Number(key.slice(5))
          const res = await filesApi.update(id, { title: name })
          const idx = allFiles.value.findIndex(f => f.id === id)
          if (idx >= 0) allFiles.value[idx] = { ...allFiles.value[idx], ...res.data }
        } else {
          const id = Number(key.slice(7))
          await groupsApi.rename(id, name)
        }
      } catch { errCount++ }
    }
    batchRenameLoading.value = false
    showBatchRenameDialog.value = false
    if (errCount > 0) ElMessage.warning(`部分重命名失败（${errCount} 个）`)
    else ElMessage.success('重命名完成')
    selectedItems.value = new Set()
    await Promise.all([loadFiles(), loadSubFolders()])
  }

  return {
    isEditMode, selectedItems, isAllSelected, batchRenameIsMulti,
    showBatchMove, batchMoveTarget, batchMoveLoading,
    showBatchRenameDialog, batchRenameName, batchRenameLoading,
    toggleEditMode, toggleSelect, selectAllItems,
    batchDelete, openBatchMove, executeBatchMove,
    startBatchRename, executeBatchRename,
  }
}
