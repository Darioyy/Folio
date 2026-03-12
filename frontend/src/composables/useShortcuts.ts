import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
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
    if (shortcuts.value.some(s => s.type === type && s.id === id)) return
    shortcuts.value.push({ type, id, name })
    saveShortcuts()
    ElMessage.success('已添加到快捷入口')
  }

  function removeShortcut(sc: Shortcut) {
    shortcuts.value = shortcuts.value.filter(s => !(s.type === sc.type && s.id === sc.id))
    saveShortcuts()
  }

  function navigateShortcut(sc: Shortcut) {
    if (sc.type === 'folder') {
      currentFolderId.value = sc.id
      breadcrumb.value = [{ id: sc.id, name: sc.name }]
      Promise.all([loadSubFolders(), loadFiles()])
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
    const name = findFolderName(folderTree.value, id)
    if (name) addShortcut('folder', id, name)
    showShortcutPickerDialog.value = false
  }

  return {
    shortcuts, loadShortcuts,
    addShortcut, removeShortcut, navigateShortcut,
    showShortcutPickerDialog, shortcutPickerSelected,
    openShortcutPicker, confirmAddShortcut,
  }
}
