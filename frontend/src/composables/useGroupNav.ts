import { ref, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { groupsApi } from '@/api/modules/groups'
import type { FileGroup } from '@/api/modules/groups'

export type Crumb = { id: number; name: string }

export function useGroupNav() {
  const currentFolderId = ref<number | null>(null)
  const rootGroups = ref<FileGroup[]>([])
  const breadcrumb = ref<Crumb[]>([])
  const subFolders = ref<FileGroup[]>([])
  const subFoldersLoading = ref(false)

  // Rename root group
  const renamingGroupId = ref<number | null>(null)
  const renameValue = ref('')
  const renameInputRef = ref<HTMLInputElement | null>(null)
  const creatingGroup = ref(false)
  const newGroupName = ref('')
  const newGroupInputRef = ref<HTMLInputElement | null>(null)
  const creatingSubFolder = ref(false)
  const newSubFolderName = ref('')
  const newSubFolderInputRef = ref<HTMLInputElement | null>(null)

  async function loadRootGroups() {
    try {
      const res = await groupsApi.list()
      rootGroups.value = res.data || []
      if (currentFolderId.value === null) subFolders.value = rootGroups.value
    } catch { /* 静默失败 */ }
  }

  async function loadSubFolders() {
    if (currentFolderId.value === null) { subFolders.value = rootGroups.value; return }
    if (currentFolderId.value === -1) { subFolders.value = []; return }
    subFoldersLoading.value = true
    try {
      const res = await groupsApi.getChildren(currentFolderId.value)
      subFolders.value = res.data || []
    } catch { /* 静默失败 */ } finally {
      subFoldersLoading.value = false
    }
  }

  // Navigation (callers should watch currentFolderId to reload files)
  async function navigateToAll() {
    currentFolderId.value = null
    breadcrumb.value = []
    subFolders.value = rootGroups.value
  }

  async function navigateToUngrouped() {
    currentFolderId.value = -1
    breadcrumb.value = []
    subFolders.value = []
  }

  async function navigateIntoRoot(group: FileGroup) {
    currentFolderId.value = group.id
    breadcrumb.value = [{ id: group.id, name: group.name }]
    await loadSubFolders()
  }

  async function navigateDeep(folder: FileGroup) {
    breadcrumb.value = [...breadcrumb.value, { id: folder.id, name: folder.name }]
    currentFolderId.value = folder.id
    await loadSubFolders()
  }

  async function navigateToCrumb(idx: number) {
    if (idx === breadcrumb.value.length - 1) return
    const crumb = breadcrumb.value[idx]
    breadcrumb.value = breadcrumb.value.slice(0, idx + 1)
    currentFolderId.value = crumb.id
    await loadSubFolders()
  }

  function isRootGroupActive(groupId: number): boolean {
    return breadcrumb.value.length > 0 && breadcrumb.value[0].id === groupId
  }

  async function handleSortEnd() {
    try {
      await groupsApi.sort(rootGroups.value.map(g => g.id))
    } catch {
      await loadRootGroups()
    }
  }

  // Root group rename
  function startRename(group: FileGroup) {
    renamingGroupId.value = group.id
    renameValue.value = group.name
    nextTick(() => {
      const el = Array.isArray(renameInputRef.value) ? renameInputRef.value[0] : renameInputRef.value
      el?.focus()
    })
  }

  async function confirmRename(group: FileGroup) {
    if (renamingGroupId.value === null) return
    const name = renameValue.value.trim()
    renamingGroupId.value = null
    if (!name || name === group.name) return
    try {
      await groupsApi.rename(group.id, name)
      await loadRootGroups()
    } catch { ElMessage.error('重命名失败') }
  }

  function cancelRename() { renamingGroupId.value = null }

  function handleGroupCommand(cmd: string, group: FileGroup) {
    if (cmd === 'rename') {
      startRename(group)
    } else if (cmd === 'delete') {
      ElMessageBox.confirm(
        `确认删除文件夹「${group.name}」？其中的文件将移至未分组，子文件夹将上移一级。`,
        '删除文件夹',
        { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
      ).then(async () => {
        try {
          await groupsApi.delete(group.id)
          if (breadcrumb.value.length > 0 && breadcrumb.value[0].id === group.id) {
            await navigateToAll()
          }
          await loadRootGroups()
        } catch { ElMessage.error('删除文件夹失败') }
      }).catch(() => {})
    }
  }

  // Root group create
  function startCreateGroup() {
    if (rootGroups.value.length >= 20) {
      ElMessage.warning('根目录最多 20 个文件夹，请整理后再新建')
      return
    }
    creatingGroup.value = true
    newGroupName.value = ''
    nextTick(() => {
      const el = Array.isArray(newGroupInputRef.value) ? newGroupInputRef.value[0] : newGroupInputRef.value
      el?.focus()
    })
  }

  async function confirmCreateGroup() {
    if (!creatingGroup.value) return
    const name = newGroupName.value.trim()
    creatingGroup.value = false
    if (!name) return
    try {
      await groupsApi.create(name)
      await loadRootGroups()
    } catch (e: any) { ElMessage.error(e?.response?.data?.error?.message || '创建文件夹失败') }
  }

  function cancelCreateGroup() { creatingGroup.value = false; newGroupName.value = '' }

  // Sub-folder create
  function startCreateSubFolder() {
    creatingSubFolder.value = true
    newSubFolderName.value = ''
    nextTick(() => { newSubFolderInputRef.value?.focus() })
  }

  async function confirmCreateSubFolder() {
    if (!creatingSubFolder.value) return
    const name = newSubFolderName.value.trim()
    creatingSubFolder.value = false
    if (!name || currentFolderId.value === -1) return
    try {
      if (currentFolderId.value === null) {
        // 根目录层级：创建根文件夹
        await groupsApi.create(name)
        await loadRootGroups()
      } else {
        await groupsApi.create(name, currentFolderId.value)
        await loadSubFolders()
      }
    } catch (e: any) { ElMessage.error(e?.response?.data?.error?.message || '创建文件夹失败') }
  }

  function cancelCreateSubFolder() { creatingSubFolder.value = false; newSubFolderName.value = '' }

  function handleSubFolderCommand(cmd: string, folder: FileGroup) {
    if (cmd === 'rename') {
      ElMessageBox.prompt('', '重命名文件夹', {
        confirmButtonText: '确认', cancelButtonText: '取消',
        inputValue: folder.name, inputPlaceholder: '文件夹名称',
      }).then(async ({ value }) => {
        const name = value?.trim()
        if (!name || name === folder.name) return
        try {
          await groupsApi.rename(folder.id, name)
          const idx = breadcrumb.value.findIndex(c => c.id === folder.id)
          if (idx >= 0) breadcrumb.value[idx].name = name
          await loadSubFolders()
        } catch { ElMessage.error('重命名失败') }
      }).catch(() => {})
    } else if (cmd === 'delete') {
      ElMessageBox.confirm(
        `确认删除文件夹「${folder.name}」？其中的文件将移至父文件夹，子文件夹将上移一级。`,
        '删除文件夹',
        { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
      ).then(async () => {
        try {
          await groupsApi.delete(folder.id)
          await loadSubFolders()
        } catch { ElMessage.error('删除文件夹失败') }
      }).catch(() => {})
    }
  }

  return {
    currentFolderId, rootGroups, breadcrumb, subFolders, subFoldersLoading,
    renamingGroupId, renameValue, renameInputRef,
    creatingGroup, newGroupName, newGroupInputRef,
    creatingSubFolder, newSubFolderName, newSubFolderInputRef,
    loadRootGroups, loadSubFolders,
    navigateToAll, navigateToUngrouped, navigateIntoRoot, navigateDeep, navigateToCrumb,
    isRootGroupActive, handleSortEnd,
    startRename, confirmRename, cancelRename, handleGroupCommand,
    startCreateGroup, confirmCreateGroup, cancelCreateGroup,
    startCreateSubFolder, confirmCreateSubFolder, cancelCreateSubFolder,
    handleSubFolderCommand,
  }
}
