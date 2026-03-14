import { ref, computed, reactive } from 'vue'
import type { Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { groupsApi } from '@/api/modules/groups'
import type { Crumb } from './useGroupNav'
import type { FolderNode } from './useFileManager'

export interface Shortcut { type: 'folder' | 'file'; id: number; name: string }

export function useShortcuts(
  currentFolderId: Ref<number | null>,
  breadcrumb: Ref<Crumb[]>,
  loadSubFolders: () => Promise<void>,
  loadFiles: () => Promise<void>,
  folderTree: Ref<FolderNode[]>,
  loadFolderTree: () => Promise<void>,
) {
  const userStore = useUserStore()
  const shortcuts = ref<Shortcut[]>([])
  const staleShortcutIds = reactive(new Set<number>())
  const SHORTCUT_KEY = computed(() => `vs-shortcuts:${userStore.currentUser?.id ?? 'anon'}`)

  function loadShortcuts() {
    try {
      const raw = localStorage.getItem(SHORTCUT_KEY.value)
      shortcuts.value = raw ? JSON.parse(raw) : []
    } catch { shortcuts.value = [] }
  }

  function saveShortcuts() {
    localStorage.setItem(SHORTCUT_KEY.value, JSON.stringify(shortcuts.value))
  }

  function addShortcut(type: 'folder' | 'file', id: number, name: string) {
    if (shortcuts.value.some(s => s.type === type && s.id === id)) {
      ElMessage.warning('该文件夹已在快捷方式中')
      return
    }
    shortcuts.value.push({ type, id, name })
    saveShortcuts()
    ElMessage.success('已添加到快捷入口')
  }

  function removeShortcut(sc: Shortcut) {
    shortcuts.value = shortcuts.value.filter(s => !(s.type === sc.type && s.id === sc.id))
    if (sc.type === 'folder') staleShortcutIds.delete(sc.id)
    saveShortcuts()
  }

  function removeShortcutByFolderId(id: number) {
    const before = shortcuts.value.length
    shortcuts.value = shortcuts.value.filter(s => !(s.type === 'folder' && s.id === id))
    if (shortcuts.value.length !== before) saveShortcuts()
  }

  async function navigateShortcut(sc: Shortcut) {
    if (sc.type === 'folder') {
      // 先检查文件夹是否还存在（getBreadcrumb 返回空数组 = 已删除）
      const breadcrumbRes = await groupsApi.getBreadcrumb(sc.id).catch(() => null)
      if (!breadcrumbRes?.data || breadcrumbRes.data.length === 0) {
        staleShortcutIds.add(sc.id)
        return
      }
      staleShortcutIds.delete(sc.id)
      currentFolderId.value = sc.id
      breadcrumb.value = breadcrumbRes.data
      await Promise.all([loadSubFolders(), loadFiles()])
    }
  }

  const showShortcutPickerDialog = ref(false)
  const shortcutPickerSelected = ref<number | null>(null)

  function openShortcutPicker() {
    shortcutPickerSelected.value = null
    loadFolderTree()
    showShortcutPickerDialog.value = true
  }

  function findFolderName(nodes: FolderNode[], targetId: number): string | undefined {
    for (const n of nodes) {
      if (n.id === targetId) return n.name
      if (n.children) {
        const found = findFolderName(n.children, targetId)
        if (found) return found
      }
    }
    return undefined
  }

  function confirmAddShortcut() {
    const id = shortcutPickerSelected.value
    if (!id) { ElMessage.warning('请选择文件夹'); return }
    if (shortcuts.value.some(s => s.type === 'folder' && s.id === id)) {
      ElMessage.warning('该文件夹已在快捷方式中')
      return
    }
    const name = findFolderName(folderTree.value, id)
    if (name) {
      addShortcut('folder', id, name)
      showShortcutPickerDialog.value = false
    }
  }

  return {
    shortcuts, staleShortcutIds, loadShortcuts,
    addShortcut, removeShortcut, removeShortcutByFolderId, navigateShortcut,
    showShortcutPickerDialog, shortcutPickerSelected,
    openShortcutPicker, confirmAddShortcut,
  }
}
