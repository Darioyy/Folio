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
        </div>
        <div class="toolbar-right">
          <BatchActions />
          <button class="icon-btn" :data-tip="viewMode === 'grid' ? '列表' : '网格'" @click="toggleViewMode">
            <svg v-if="viewMode === 'list'" viewBox="0 0 16 16" width="15" height="15" fill="currentColor"><rect x="1" y="2" width="14" height="2" rx="1"/><rect x="1" y="7" width="14" height="2" rx="1"/><rect x="1" y="12" width="14" height="2" rx="1"/></svg>
            <svg v-else viewBox="0 0 16 16" width="15" height="15" fill="currentColor"><rect x="1" y="1" width="6" height="6" rx="1"/><rect x="9" y="1" width="6" height="6" rx="1"/><rect x="1" y="9" width="6" height="6" rx="1"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>
          </button>
          <button v-if="!isEditMode" :class="['icon-btn', 'upload-btn', { 'is-full': isStorageFull }]" :data-tip="isStorageFull ? '空间已满' : '上传'" @click="openUpload">
            <svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 10.5V3"/><polyline points="5,5.5 8,3 11,5.5"/><path d="M2.5 12.5h11"/></svg>
          </button>
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
        <template v-for="(crumb, idx) in breadcrumb" :key="crumb.id">
          <svg class="crumb-sep" viewBox="0 0 8 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" width="6" height="11"><polyline points="1,2 6,7 1,12"/></svg>
          <button :class="['crumb-item', { 'crumb-current': idx === breadcrumb.length - 1 }]" @click="navigateToCrumb(idx)">{{ crumb.name }}</button>
        </template>
        <span class="crumb-spacer"></span>
        <button class="new-subfolder-btn" :data-tip="currentFolderId ? '新建子文件夹' : '新建文件夹'" @click="startCreateSubFolder">
          <svg viewBox="0 0 18 16" width="17" height="16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M1 4a1 1 0 011-1h3.5l1.2 1.5H16a1 1 0 011 1V13a1 1 0 01-1 1H2a1 1 0 01-1-1V4z"/><line x1="9" y1="7" x2="9" y2="11"/><line x1="7" y1="9" x2="11" y2="9"/></svg>
        </button>
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
          v-if="!filesLoading && !subFoldersLoading && displayFiles.length === 0 && subFolders.length === 0 && !creatingSubFolder"
          :description="searchQuery.trim() ? '未找到匹配文件' : '还没有文件，去上传吧'"
          class="empty-state"
        />
      </div>
    </div>
  </div>

  <!-- ===== 对话框 ===== -->
  <!-- 上传对话框 -->
  <el-dialog v-model="uploadDialogVisible" title="上传文件" width="480px" :close-on-click-modal="!uploading" @close="resetUploadForm">
    <el-form :model="uploadForm" label-width="70px" :disabled="uploading">
      <el-form-item label="文件">
        <el-button @click="triggerFileInput" style="width: 100%; justify-content: flex-start">
          <el-icon style="margin-right: 6px"><UploadIcon /></el-icon>
          {{ uploadForm.file ? uploadForm.file.name : '点击选择文件' }}
        </el-button>
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
      <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
    </template>
  </el-dialog>

  <!-- 编辑对话框 -->
  <el-dialog v-model="editDialogVisible" title="编辑文件信息" width="480px">
    <el-form :model="editForm" label-width="70px">
      <el-form-item label="描述"><el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="可选" maxlength="500" /></el-form-item>
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
      <el-form-item label="移动到">
        <el-cascader v-model="editFolderForm.targetParentId" :options="folderCascaderOptions" :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name', children: 'children' }" placeholder="保留当前位置" clearable style="width: 100%" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="folderEditDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="folderEditLoading" @click="handleFolderEdit">保存</el-button>
    </template>
  </el-dialog>

  <!-- 文件预览 -->
  <FilePreview v-model="previewVisible" :file="currentFile" :type="previewType" />
</template>

<script setup lang="ts">
import { ref, computed, watch, provide, onMounted, onActivated, onUnmounted, nextTick } from 'vue'
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
const searchInputRef = ref<HTMLInputElement | null>(null)

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

const shortcuts = useShortcuts(
  currentFolderId, breadcrumb, loadSubFolders, loadFiles,
  fileManager.folderTree, loadFolderTree,
)
const { addShortcut } = shortcuts

const dragDrop = useDragDrop(currentFolderId, allFiles, isStorageFull, addShortcut, loadFiles, loadSubFolders, loadRootGroups, groupNav.navigateDeep, loadOverview)
const {
  isDragOver, folderEditDialogVisible, folderEditLoading, editFolderForm,
  onDragEnter, onDragLeave, onDrop,
  handleFolderEdit,
} = dragDrop

const batch = useBatchSelect(allFiles, subFolders, loadFiles, loadSubFolders, loadRootGroups, loadFolderTree, folderCascaderOptions, loadOverview)
const { isEditMode, toggleEditMode } = batch

// ===== Provide to child components =====
provide('groupNav', groupNav)
provide('fileManager', fileManager)
provide('batchSelect', batch)
provide('dragDrop', dragDrop)
provide('shortcuts', shortcuts)

// Watch currentFolderId to reload files
watch(currentFolderId, () => loadFiles())

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
  await Promise.all([loadFiles(), loadRootGroups(), loadOverview()])
  shortcuts.loadShortcuts()
})

onActivated(async () => {
  await Promise.all([loadFiles(), loadOverview()])
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
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
  &.active { border-color: $color-primary; background: rgba(99, 102, 241, 0.08); color: $color-primary; }

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

.upload-btn {
  background: $color-primary;
  border-color: $color-primary;
  color: #fff;

  &:hover { background: rgba(99, 102, 241, 0.82); border-color: $color-primary; color: #fff; }
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

@media (max-width: $breakpoint-md) {
  .files-layout { flex-direction: column; }
  .breadcrumb-bar { overflow-x: auto; }
  .content-grid { grid-template-columns: repeat(2, 1fr); gap: $spacing-sm; }
}
</style>
