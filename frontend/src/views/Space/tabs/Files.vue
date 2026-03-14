<template>
  <div class="files-layout">
    <!-- 左侧分组侧边栏 -->
    <FolderSidebar />

    <!-- 右侧主内容区 -->
    <div
      class="files-main"
      :class="{ 'drag-active': isDragOver }"
      @dragenter.prevent="onDragEnter"
      @dragleave="onDragLeave"
      @dragover.prevent
      @drop.prevent="onDrop"
    >
      <UploadZone />

      <!-- 工具栏 -->
      <div class="files-toolbar">
        <div class="toolbar-left">
          <div v-if="!isEditMode" class="content-tabs">
            <span
              v-for="tab in typeTabs"
              :key="tab.value"
              :class="['tab-item', { active: typeFilter === tab.value }]"
              @click="handleTypeChange(tab.value)"
            >
              <el-icon><component :is="tab.icon" /></el-icon>
              {{ tab.label }}
            </span>
          </div>
        </div>
        <div class="toolbar-right">
          <!-- 搜索框 -->
          <div v-if="!isEditMode" :class="['file-search-box', { expanded: searchExpanded }]">
            <button class="search-icon-btn" @click="toggleSearch">
              <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="6.5" cy="6.5" r="4.5"/><line x1="10" y1="10" x2="14" y2="14"/>
              </svg>
            </button>
            <input
              v-if="searchExpanded"
              ref="searchInputRef"
              v-model="searchQuery"
              class="file-search-input"
              placeholder="搜索文件…"
              @blur="onSearchBlur"
              @keyup.esc="toggleSearch"
            />
            <button v-if="searchExpanded && searchQuery" class="search-clear-btn" @click="searchQuery = ''">
              <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/></svg>
            </button>
          </div>
          <BatchActions />
          <div v-if="!isMobile" class="view-toggle-wrap">
            <button class="icon-btn view-btn" :data-tip="viewMode === 'grid' ? '网格' : '列表'" @click="toggleViewMode">
              <svg v-if="viewMode === 'list'" viewBox="0 0 16 16" width="15" height="15" fill="currentColor"><rect x="1" y="2" width="14" height="2" rx="1"/><rect x="1" y="7" width="14" height="2" rx="1"/><rect x="1" y="12" width="14" height="2" rx="1"/></svg>
              <svg v-else viewBox="0 0 16 16" width="15" height="15" fill="currentColor"><rect x="1" y="1" width="6" height="6" rx="1"/><rect x="9" y="1" width="6" height="6" rx="1"/><rect x="1" y="9" width="6" height="6" rx="1"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>
            </button>
          </div>
          <!-- 排序按钮 -->
          <el-dropdown v-if="!isEditMode" trigger="click" @command="toggleSort">
            <button
              :class="['icon-btn', { active: !!sortKey }]"
              :data-tip="sortKey ? (sortLabels[sortKey] + ' ' + (sortDir === 'asc' ? '↑' : '↓')) : '排序'"
            >
              <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="2" y1="4"  x2="10" y2="4"/>
                <line x1="2" y1="8"  x2="7"  y2="8"/>
                <line x1="2" y1="12" x2="4"  y2="12"/>
                <polyline points="13,3 13,13"/>
                <polyline points="10.5,10.5 13,13 15.5,10.5"/>
              </svg>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="name">
                  <span class="sort-menu-item">名称<span v-if="sortKey === 'name'" class="sort-dir-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span></span>
                </el-dropdown-item>
                <el-dropdown-item command="size">
                  <span class="sort-menu-item">大小<span v-if="sortKey === 'size'" class="sort-dir-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span></span>
                </el-dropdown-item>
                <el-dropdown-item command="time">
                  <span class="sort-menu-item">时间<span v-if="sortKey === 'time'" class="sort-dir-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span></span>
                </el-dropdown-item>
                <el-dropdown-item v-if="sortKey" command="clear" divided>
                  <span class="sort-menu-item sort-clear">清除排序</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-dropdown v-if="!isEditMode" trigger="click" @command="handleAddCommand">
            <button class="icon-btn add-btn" :class="{ 'is-full': isStorageFull }" :data-tip="isStorageFull ? '存储已满' : '上传 / 新建'">
              <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="8" y1="3" x2="8" y2="13"/><line x1="3" y1="8" x2="13" y2="8"/></svg>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="upload" :disabled="isStorageFull">上传文件 / 文件夹</el-dropdown-item>
                <el-dropdown-item command="folder">新建文件夹</el-dropdown-item>
                <el-dropdown-item disabled class="drag-tip-item">
                  <svg viewBox="0 0 14 14" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;opacity:0.6"><path d="M7 2v7M4 6l3-4 3 4"/><path d="M2 11h10"/></svg>
                  可直接拖拽到页面上传
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <button :class="['icon-btn', { active: isEditMode }]" :data-tip="isEditMode ? '完成' : '编辑'" @click="toggleEditMode">
            <svg v-if="!isEditMode" viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 2.5a1.414 1.414 0 012 2L5 13H3v-2L11.5 2.5z"/></svg>
            <svg v-else viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3,8 7,12 13,4"/></svg>
          </button>
        </div>
      </div>

      <!-- 面包屑导航 -->
      <div class="breadcrumb-bar">
        <button class="crumb-item crumb-home" @click="navigateToAll" title="返回根目录">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" width="13" height="13">
            <path d="M1.5 5a1 1 0 011-1H5.6l1.1 1.5H13.5a1 1 0 011 1V12a1 1 0 01-1 1h-11a1 1 0 01-1-1V5z"/>
          </svg>
        </button>
        <!-- 移动端折叠：超过 2 层时显示省略号 -->
        <template v-if="isMobile && breadcrumb.length > 2">
          <svg class="crumb-sep" viewBox="0 0 8 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" width="6" height="11"><polyline points="1,2 6,7 1,12"/></svg>
          <span class="crumb-item crumb-ellipsis">···</span>
        </template>
        <template v-for="(crumb, idx) in displayBreadcrumb" :key="crumb.id">
          <svg class="crumb-sep" viewBox="0 0 8 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" width="6" height="11"><polyline points="1,2 6,7 1,12"/></svg>
          <button :class="['crumb-item', { 'crumb-current': idx === displayBreadcrumb.length - 1 }]" @click="navigateToCrumb(isMobile && breadcrumb.length > 2 ? breadcrumb.length - 1 : idx)">{{ crumb.name }}</button>
        </template>
      </div>

      <!-- 内容区 -->
      <div class="files-area" v-loading="filesLoading || subFoldersLoading">
        <!-- 新建子文件夹内联输入 -->
        <div v-if="creatingSubFolder" class="new-subfolder-form">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" width="15" height="15" style="flex-shrink:0;color:var(--el-color-primary)"><path d="M1.5 5a1 1 0 011-1H5.6l1.1 1.5H13.5a1 1 0 011 1V12a1 1 0 01-1 1h-11a1 1 0 01-1-1V5z"/></svg>
          <input
            class="rename-input subfolder-name-input"
            v-model="newSubFolderName"
            placeholder="文件夹名称"
            ref="newSubFolderInputRef"
            @blur="confirmCreateSubFolder"
            @keyup.enter="confirmCreateSubFolder"
            @keyup.esc="cancelCreateSubFolder"
          />
          <span class="subfolder-hint">↵ 确认 · ESC 取消</span>
        </div>

        <FileGrid v-if="viewMode === 'grid'" />
        <FileListView v-else-if="viewMode === 'list'" />
        <el-empty
          v-if="!filesLoading && !subFoldersLoading && displayFiles.length === 0 && filteredSubFolders.length === 0 && !creatingSubFolder"
          :description="searchQuery.trim() ? '未找到匹配文件' : '还没有文件，去上传吧'"
          class="empty-state"
        />
      </div>
    </div>

    <!-- ===== 对话框（teleport 到 body，位置不受此层级影响） ===== -->
  <!-- 上传对话框（支持文件和文件夹） -->
  <el-dialog v-model="uploadDialogVisible" title="上传文件 / 文件夹" width="480px" :close-on-click-modal="!uploading" @close="resetUploadForm">
    <div class="upload-drag-banner">
      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0">
        <path d="M10 3v10M6 8l4-5 4 5"/><path d="M3 16h14"/>
      </svg>
      <span>可直接将文件或文件夹<b>拖拽到页面任意位置</b>批量上传，支持嵌套文件夹结构</span>
    </div>
    <el-divider style="margin: 12px 0 16px">或通过对话框选择</el-divider>
    <el-form :model="uploadForm" label-width="70px" :disabled="uploading">
      <el-form-item label="选择">
        <div class="upload-pick-row">
          <el-button @click="triggerFileInput" style="flex:1; justify-content: flex-start; overflow: hidden">
            <el-icon style="margin-right: 6px; flex-shrink:0"><UploadIcon /></el-icon>
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ uploadForm.file ? uploadForm.file.name : '选择文件…' }}</span>
          </el-button>
          <el-button :disabled="isStorageFull" plain @click="triggerFolderFromDialog" style="flex-shrink:0">
            <svg viewBox="0 0 16 16" fill="#f59e0b" stroke="none" width="14" height="14" style="margin-right:5px"><path d="M10 4H4c-1.1 0-2 .9-2 2v6c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2H10z" opacity="0.9"/></svg>
            文件夹
          </el-button>
        </div>
        <input ref="fileInputRef" type="file" hidden @change="handleFileChange" />
      </el-form-item>
      <el-form-item label="上传到">
        <el-cascader
          v-model="uploadForm.targetFolderId"
          :options="folderCascaderOptions"
          :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name', children: 'children' }"
          :placeholder="currentFolderId && currentFolderId > 0 ? breadcrumb[breadcrumb.length-1]?.name : '根目录'"
          clearable style="width: 100%"
          @visible-change="(v: boolean) => v && loadFolderTree()"
        />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="uploadForm.description" type="textarea" :rows="2" placeholder="可选" maxlength="500" />
      </el-form-item>
      <el-form-item v-if="uploadProgress > 0" label="">
        <el-progress :percentage="uploadProgress" style="width: 100%" :status="uploadProgress === 100 ? 'success' : undefined" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button :disabled="uploading" @click="uploadDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="uploading" :disabled="!uploadForm.file" @click="handleUpload">上传</el-button>
    </template>
  </el-dialog>

  <!-- 编辑对话框 -->
  <el-dialog v-model="editDialogVisible" title="编辑文件信息" width="480px">
    <el-form :model="editForm" label-width="70px">
      <el-form-item label="名称"><el-input v-model="editForm.title" maxlength="200" show-word-limit placeholder="文件名称" /></el-form-item>
      <el-form-item label="描述"><el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="可选" maxlength="500" /></el-form-item>
      <el-form-item label="文件名">
        <el-input v-model="editForm.fileName" maxlength="255" placeholder="含扩展名，如 report.pdf" />
        <p class="edit-filename-tip">修改文件名不影响已分享的链接</p>
      </el-form-item>
      <el-form-item label="移动到">
        <el-cascader v-model="editForm.targetGroupId" :options="folderCascaderOptions" :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name', children: 'children' }" placeholder="保留当前位置" clearable style="width: 100%" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="editDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="editLoading" @click="handleEdit">保存</el-button>
    </template>
  </el-dialog>

  <!-- 文件夹编辑对话框 -->
  <el-dialog v-model="folderEditDialogVisible" title="编辑文件夹" width="400px">
    <el-form :model="editFolderForm" label-width="70px">
      <el-form-item label="名称"><el-input v-model="editFolderForm.name" maxlength="100" show-word-limit /></el-form-item>
      <el-form-item label="描述"><el-input v-model="editFolderForm.description" type="textarea" :rows="2" placeholder="可选" maxlength="500" /></el-form-item>
      <el-form-item label="移动到">
        <el-cascader v-model="editFolderForm.targetParentId" :options="folderCascaderOptions" :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name', children: 'children' }" placeholder="保留当前位置" clearable style="width: 100%" @visible-change="(v: boolean) => v && loadFolderTree()" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="folderEditDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="folderEditLoading" @click="handleFolderEdit">保存</el-button>
    </template>
  </el-dialog>

    <!-- 文件预览 -->
    <FilePreview v-model="previewVisible" :file="currentFile" :type="previewType" />

    <!-- 文件夹上传隐藏输入 -->
    <input ref="folderInputRef" type="file" webkitdirectory="" style="display:none" @change="handleFolderInput" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, provide, onMounted, onActivated, onUnmounted, nextTick, onBeforeUnmount } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { Folder, Picture, VideoPlay, Grid, Upload as UploadIcon } from '@element-plus/icons-vue'
import FilePreview from '@/components/business/FilePreview.vue'
import FolderSidebar from '../components/FolderSidebar.vue'
import UploadZone from '../components/UploadZone.vue'
import BatchActions from '../components/BatchActions.vue'
import FileGrid from '../components/FileGrid.vue'
import FileListView from '../components/FileListView.vue'
import { useFileManager } from '@/composables/useFileManager'
import { useGroupNav } from '@/composables/useGroupNav'
import { useBatchSelect } from '@/composables/useBatchSelect'
import { useDragDrop } from '@/composables/useDragDrop'
import { useShortcuts } from '@/composables/useShortcuts'
import type { FileItem } from '@/types/models'

// ===== Composables =====
const groupNav = useGroupNav()
const {
  currentFolderId, rootGroups, breadcrumb, subFolders, subFoldersLoading,
  creatingSubFolder, newSubFolderName, newSubFolderInputRef,
  loadRootGroups, loadSubFolders,
  navigateToAll, navigateToCrumb,
  startCreateSubFolder, confirmCreateSubFolder, cancelCreateSubFolder,
} = groupNav

const fileManager = useFileManager(currentFolderId)
const {
  typeFilter, viewMode, allFiles, displayFiles, filesLoading,
  searchQuery,
  previewVisible, currentFile, storageInfo, myStats, isStorageFull,
  editDialogVisible, editLoading, editForm,
  folderCascaderOptions,
  uploadDialogVisible, uploading, uploadProgress, fileInputRef, uploadForm,
  loadFiles, loadOverview,
  handleTypeChange, toggleViewMode,
  loadFolderTree,
  openUpload, triggerFileInput, handleFileChange, handleUpload, resetUploadForm,
  handleEdit,
} = fileManager

const searchExpanded = ref(false)
const searchInputRef  = ref<HTMLInputElement | null>(null)
const folderInputRef  = ref<HTMLInputElement | null>(null)

// 移动端检测
const isMobile = ref(window.innerWidth <= 640)
function onResize() { isMobile.value = window.innerWidth <= 640 }

// 面包屑折叠：移动端超过 2 层时，只显示第一项 + 最后一项
const displayBreadcrumb = computed(() => {
  if (!isMobile.value || breadcrumb.value.length <= 2) return breadcrumb.value
  return [breadcrumb.value[breadcrumb.value.length - 1]] // 仅显示当前层
})

function toggleSearch() {
  searchExpanded.value = !searchExpanded.value
  if (searchExpanded.value) {
    nextTick(() => searchInputRef.value?.focus())
  } else {
    searchQuery.value = ''
  }
}

function onSearchBlur() {
  if (!searchQuery.value.trim()) {
    searchExpanded.value = false
  }
}

function handleAddCommand(command: 'upload' | 'folder') {
  if (command === 'upload') openUpload()
  else startCreateSubFolder()
}

function triggerFolderFromDialog() {
  uploadDialogVisible.value = false
  nextTick(() => folderInputRef.value?.click())
}

async function handleFolderInput(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  await startFolderUpload(input.files)
  input.value = ''
}

// Filter subFolders by searchQuery for real-time search
const filteredSubFolders = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return subFolders.value
  return subFolders.value.filter((f: any) => f.name.toLowerCase().includes(q))
})

const shortcuts = useShortcuts(
  currentFolderId, breadcrumb, loadSubFolders, loadFiles,
  fileManager.folderTree, loadFolderTree,
)
const { addShortcut } = shortcuts

const dragDrop = useDragDrop(currentFolderId, allFiles, isStorageFull, addShortcut, loadFiles, loadSubFolders, loadRootGroups, groupNav.navigateDeep, loadOverview, shortcuts.removeShortcutByFolderId)
const {
  isDragOver, folderEditDialogVisible, folderEditLoading, editFolderForm,
  onDragEnter, onDragLeave, onDrop,
  handleFolderEdit,
  startFolderUpload,
} = dragDrop

const batch = useBatchSelect(allFiles, subFolders, loadFiles, loadSubFolders, loadRootGroups, loadFolderTree, folderCascaderOptions, loadOverview)
const { isEditMode, toggleEditMode } = batch

// ===== 共享排序状态 =====
type SortKeyType = '' | 'name' | 'size' | 'time'
const sortKey = ref<SortKeyType>('')
const sortDir = ref<'asc' | 'desc'>('asc')
const sortLabels: Record<string, string> = { name: '名称', size: '大小', time: '时间' }
function toggleSort(key: string) {
  if (!key || key === 'clear') { sortKey.value = ''; sortDir.value = 'asc'; return }
  if (sortKey.value === key) { sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc' }
  else { sortKey.value = key as SortKeyType; sortDir.value = 'asc' }
}

// ===== Provide to child components =====
provide('groupNav', { ...groupNav, subFolders: filteredSubFolders })
provide('fileManager', fileManager)
provide('batchSelect', batch)
provide('dragDrop', dragDrop)
provide('shortcuts', shortcuts)
provide('fileSort', { sortKey, sortDir, toggleSort })

// Watch currentFolderId to reload files
watch(currentFolderId, () => loadFiles())

// Watch user change: 切换账户时重置云盘状态并重新加载
const userStore = useUserStore()
let prevUserId: number | undefined
watch(() => userStore.currentUser?.id, async (newId) => {
  if (prevUserId !== undefined && newId !== prevUserId) {
    currentFolderId.value = null
    await Promise.all([loadFiles(), loadRootGroups(), loadOverview()])
    shortcuts.loadShortcuts()
  }
  prevUserId = newId
}, { immediate: true })

// ===== Type tabs =====
const typeTabs = [
  { value: '' as const, label: '全部', icon: Grid },
  { value: 'document' as const, label: '文档', icon: Folder },
  { value: 'image' as const, label: '图片', icon: Picture },
  { value: 'video' as const, label: '视频', icon: VideoPlay },
]

// ===== Preview =====
const previewType = computed<'media' | 'resource'>(() => {
  if (!currentFile.value) return 'media'
  return currentFile.value.file_category === 'document' ? 'resource' : 'media'
})

function handlePreview(file: FileItem) {
  currentFile.value = file
  previewVisible.value = true
}

// ===== Keyboard shortcut: Ctrl+Z undo =====
function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'z' && dragDrop.moveHistory.value.length > 0) {
    e.preventDefault()
    dragDrop.undoLastMove()
  }
}

onMounted(async () => {
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', onResize)
  // 移动端强制列表视图
  if (isMobile.value) viewMode.value = 'list'
  await Promise.all([loadFiles(), loadRootGroups(), loadOverview()])
  shortcuts.loadShortcuts()
})

onActivated(async () => {
  await Promise.all([loadFiles(), loadOverview()])
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', onResize)
})

defineExpose({ storageInfo, myStats, loadOverview })
</script>

<style scoped lang="scss">
.files-area {
  flex: 1;
  min-height: 520px;
  position: relative;
}

.files-layout {
  display: flex;
  gap: $spacing-md;
  align-items: flex-start;
  flex: 1;
  min-height: 0;
}

.files-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  position: relative;

  &.drag-active {
    outline: 2px dashed $color-primary;
    outline-offset: -4px;
    border-radius: $radius-lg;
  }
}

.files-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex: 1;
  min-width: 0;
}

.file-search-box {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-md;
  padding: 0 8px;
  background: var(--el-bg-color);
  transition: width $transition-base, border-color $transition-base;
  overflow: hidden;
  width: 32px;

  &.expanded {
    width: 200px;
    border-color: $color-primary;
  }
}

.search-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
  transition: color $transition-fast;

  &:hover { color: $color-primary; }
}

.file-search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: $font-sm;
  color: var(--el-text-color-primary);
  min-width: 0;

  &::placeholder { color: var(--el-text-color-placeholder); }
}

.search-clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  transition: color $transition-fast, background $transition-fast;

  &:hover { color: var(--el-text-color-primary); background: var(--el-fill-color); }
}

.content-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  border-bottom: 1px solid var(--el-border-color-light);

  .tab-item {
    display: inline-flex;
    align-items: center;
    gap: $spacing-xs;
    padding: $spacing-sm $spacing-md;
    font-size: $font-sm;
    color: var(--el-text-color-secondary);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: color $transition-fast, border-color $transition-fast;
    white-space: nowrap;

    &:hover { color: var(--el-text-color-primary); }
    &.active { color: $color-primary; border-bottom-color: $color-primary; font-weight: 500; }
  }
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-shrink: 0;
}

.view-toggle-wrap {
  background: var(--color-surface-hover);
  border-radius: 6px;
  padding: 2px;
  display: flex;
}

.view-btn {
  border: none !important;
  background: var(--color-surface) !important;
  box-shadow: var(--shadow) !important;
}

.icon-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-md;
  transition: background $transition-fast, color $transition-fast, border-color $transition-fast;
  flex-shrink: 0;

  &:hover { border-color: $color-primary; color: $color-primary; }
  &.active { border-color: $color-primary; background: rgba(90, 103, 216, 0.08); color: $color-primary; }

  &[data-tip]::after {
    content: attr(data-tip);
    position: absolute;
    top: calc(100% + 6px);
    left: 50%;
    translate: -50% 0;
    z-index: 9999;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11.5px;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transform: translateY(-4px) scale(0.96);
    transform-origin: top center;
    transition: opacity 0.12s ease, transform 0.12s ease;
    transition-delay: 0.06s;
    background: rgba(22, 24, 30, 0.82);
    color: rgba(255, 255, 255, 0.92);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.07);
  }

  &[data-tip]:hover::after { opacity: 1; transform: translateY(0) scale(1); }
}

:global(html.dark) .icon-btn[data-tip]::after {
  background: rgba(48, 51, 62, 0.90);
  color: rgba(222, 225, 232, 0.92);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.40);
  border-color: rgba(255, 255, 255, 0.10);
}

.add-btn {
  background: $color-primary;
  border-color: $color-primary;
  color: #fff;

  &:hover { background: rgba(90, 103, 216, 0.82); border-color: $color-primary; color: #fff; }
  &.is-full { background: var(--el-color-danger); border-color: var(--el-color-danger); }
  &.is-full:hover { background: var(--el-color-danger-light-3); border-color: var(--el-color-danger-light-3); }
}

.breadcrumb-bar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 5px $spacing-sm;
  margin-top: 3px;
  margin-bottom: $spacing-sm;
  background: var(--el-fill-color-light);
  border-radius: $radius-md;
  overflow: hidden;
  flex-wrap: nowrap;
}

.crumb-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border: none;
  background: transparent;
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background $transition-fast, color $transition-fast;
  white-space: nowrap;

  &.crumb-home { padding: 2px 5px; color: var(--el-text-color-placeholder); &:hover { color: $color-primary; } }
  &:hover:not(.crumb-current) { background: var(--el-fill-color); color: var(--el-text-color-primary); }
  &.crumb-current { color: var(--el-text-color-primary); font-weight: 500; cursor: default; }
}

.crumb-sep { color: var(--el-text-color-placeholder); flex-shrink: 0; }
.crumb-spacer { flex: 1; min-width: $spacing-xs; }
.crumb-ellipsis { color: var(--el-text-color-placeholder); font-size: $font-xs; padding: 2px 4px; cursor: default; }

.new-subfolder-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  border-radius: $radius-sm;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color $transition-fast, color $transition-fast;

  &:hover { border-color: $color-primary; color: $color-primary; }

  &[data-tip]::after {
    content: attr(data-tip);
    position: absolute;
    top: calc(100% + 6px);
    left: 50%;
    translate: -50% 0;
    z-index: 9999;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11.5px;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transform: translateY(-4px) scale(0.96);
    transform-origin: top center;
    transition: opacity 0.12s ease, transform 0.12s ease;
    transition-delay: 0.06s;
    background: rgba(22, 24, 30, 0.82);
    color: rgba(255, 255, 255, 0.92);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.07);
  }

  &[data-tip]:hover::after { opacity: 1; transform: translateY(0) scale(1); }
}

.new-subfolder-form {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: 6px $spacing-sm;
  margin-bottom: $spacing-sm;
  background: var(--el-fill-color-light);
  border-radius: $radius-md;

  .subfolder-name-input { flex: 1; max-width: 200px; }
  .subfolder-hint { font-size: 11px; color: var(--el-text-color-placeholder); white-space: nowrap; }
}

.rename-input {
  flex: 1;
  min-width: 0;
  border: 1px solid $color-primary;
  border-radius: $radius-sm;
  padding: 2px 6px;
  font-size: $font-xs;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  outline: none;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: $spacing-sm;
}

.empty-state { padding: $spacing-3xl $spacing-lg; }

.upload-drag-banner {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(90, 103, 216, 0.06);
  border: 1px solid rgba(90, 103, 216, 0.18);
  border-radius: $radius-md;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
  margin-bottom: 4px;

  svg { margin-top: 1px; color: $color-primary; }
  b { color: $color-primary; font-weight: 600; }
}

.upload-pick-row {
  display: flex;
  gap: $spacing-sm;
  width: 100%;
}

.edit-filename-tip {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  line-height: 1.4;
}

.sort-menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-width: 56px;
  font-size: $font-sm;
}
.sort-dir-arrow { color: $color-primary; font-weight: 600; font-size: 12px; }
.sort-clear { color: var(--el-text-color-placeholder); font-size: 12px; }

:global(.drag-tip-item.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px !important;
  color: var(--el-text-color-placeholder) !important;
  cursor: default !important;
  border-top: 1px solid var(--el-border-color-lighter);
  margin-top: 2px;
  padding-top: 6px;
}

@media (max-width: $breakpoint-md) {
  .files-layout { flex-direction: column; }
  .breadcrumb-bar { overflow-x: auto; }
  .content-grid { grid-template-columns: repeat(2, 1fr); gap: $spacing-sm; }
}
</style>
