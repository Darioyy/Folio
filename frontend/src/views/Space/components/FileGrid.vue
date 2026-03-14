<template>
  <template v-if="subFolders.length > 0 || allFiles.length > 0">
    <!-- 文件格 -->
    <div class="content-grid">
      <!-- 文件夹卡片 -->
      <div
        v-for="folder in subFolders"
        :key="`folder-${folder.id}`"
        :class="['folder-grid-card', { 'drag-over': dragOverFolderId === folder.id, 'is-selected': isEditMode && selectedItems.has(`folder:${folder.id}`), 'is-dragging-folder': draggingFolder?.id === folder.id }]"
        :draggable="!isEditMode"
        @click="isEditMode ? toggleSelect('folder', folder.id) : navigateDeep(folder)"
        @dragstart="!isEditMode && onFolderDragStart($event, folder)"
        @dragend="!isEditMode && onFolderDragEnd()"
        @dragenter.prevent="!isEditMode && onFolderDragEnter($event, folder)"
        @dragover.prevent="!isEditMode && onFolderDragOver($event)"
        @dragleave="!isEditMode && onFolderDragLeave($event)"
        @drop.stop.prevent="!isEditMode && onFolderDrop($event, folder)"
      >
        <div class="thumbnail-wrap folder-thumb-area">
          <div v-if="isEditMode" class="item-checkbox" @click.stop="toggleSelect('folder', folder.id)">
            <svg :class="['check-circle', { checked: selectedItems.has(`folder:${folder.id}`) }]" viewBox="0 0 16 16" width="16" height="16">
              <circle cx="8" cy="8" r="7"/><polyline points="4.5,8 7,10.5 11.5,5"/>
            </svg>
          </div>
          <svg width="36" height="36" viewBox="0 0 24 24" fill="#f59e0b" stroke="none">
            <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" opacity="0.9"/>
          </svg>
        </div>
        <div class="card-body" @mouseenter="loadFolderSize(folder.id)">
          <p class="card-title">{{ folder.name }}</p>
          <p class="folder-size">{{ folderSizes[folder.id] ?? '' }}</p>
        </div>
        <!-- 操作按钮：hover 显示 -->
        <div v-if="!isEditMode" class="card-overlay-actions" @click.stop>
          <button class="overlay-action-btn" title="编辑" @click.stop="openFolderEdit(folder)">
            <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 2.5a1.414 1.414 0 012 2L5 13H3v-2L11.5 2.5z"/></svg>
          </button>
          <button class="overlay-action-btn danger" title="删除" @click.stop="deleteFolderWithCheck(folder)">
            <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3,5 13,5"/><path d="M5 5V3h6v2"/><path d="M4 5l.7 8h6.6L12 5"/></svg>
          </button>
        </div>
      </div>

      <!-- 文件卡片 -->
      <div
        v-for="file in sortedFiles"
        :key="`file-${file.id}`"
        :class="['hub-file-item', { 'is-dragging': draggingFile?.id === file.id, 'is-selected': isEditMode && selectedItems.has(`file:${file.id}`) }]"
        :draggable="!isEditMode"
        @dragstart="!isEditMode && onFileDragStart($event, file)"
        @dragend="!isEditMode && onFileDragEnd()"
        @click="isEditMode ? toggleSelect('file', file.id) : undefined"
      >
        <div v-if="isEditMode" class="item-checkbox" @click.stop="toggleSelect('file', file.id)">
          <svg :class="['check-circle', { checked: selectedItems.has(`file:${file.id}`) }]" viewBox="0 0 16 16" width="16" height="16">
            <circle cx="8" cy="8" r="7"/><polyline points="4.5,8 7,10.5 11.5,5"/>
          </svg>
        </div>
        <FileCard :file="file" :show-author="false" :show-thumbnail="false" @click="!isEditMode && handlePreview(file)" />
        <div v-if="!isEditMode" class="card-overlay-actions" @click.stop>
          <button class="overlay-action-btn" title="编辑" @click.stop="openEdit(file)">
            <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 2.5a1.414 1.414 0 012 2L5 13H3v-2L11.5 2.5z"/></svg>
          </button>
          <el-popconfirm title="确认删除该文件？" confirm-button-text="删除" cancel-button-text="取消" confirm-button-type="danger" @confirm="handleDelete(file)">
            <template #reference>
              <button class="overlay-action-btn danger" title="删除">
                <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3,5 13,5"/><path d="M5 5V3h6v2"/><path d="M4 5l.7 8h6.6L12 5"/></svg>
              </button>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </div>
  </template>
</template>

<script setup lang="ts">
import { inject, ref, computed } from 'vue'
import type { Ref } from 'vue'
import FileCard from '@/components/business/FileCard.vue'
import type { useGroupNav } from '@/composables/useGroupNav'
import type { useFileManager } from '@/composables/useFileManager'
import type { useBatchSelect } from '@/composables/useBatchSelect'
import type { useDragDrop } from '@/composables/useDragDrop'
import type { FileItem } from '@/types/models'
import { groupsApi } from '@/api/modules/groups'
import { formatFileSize } from '@/utils/format'

// 文件夹大小懒加载
const folderSizes = ref<Record<number, string>>({})
const _loadingFolderIds = new Set<number>()
async function loadFolderSize(folderId: number) {
  if (folderSizes.value[folderId] !== undefined || _loadingFolderIds.has(folderId)) return
  _loadingFolderIds.add(folderId)
  try {
    const res = await groupsApi.getSize(folderId)
    if (res.data !== undefined) folderSizes.value = { ...folderSizes.value, [folderId]: formatFileSize(res.data) }
  } finally {
    _loadingFolderIds.delete(folderId)
  }
}

// 共享排序状态（由 Files.vue provide）
const { sortKey, sortDir } = inject('fileSort') as { sortKey: Ref<string>; sortDir: Ref<'asc' | 'desc'>; toggleSort: (k: string) => void }

const { subFolders, navigateDeep } = inject('groupNav') as ReturnType<typeof useGroupNav>
const { displayFiles: allFiles, currentFile, previewVisible, openEdit, handleDelete } = inject('fileManager') as ReturnType<typeof useFileManager>
const { isEditMode, selectedItems, toggleSelect } = inject('batchSelect') as ReturnType<typeof useBatchSelect>
const {
  draggingFile, draggingFolder, dragOverFolderId,
  onFileDragStart, onFileDragEnd,
  onFolderDragStart, onFolderDragEnd,
  onFolderDragEnter, onFolderDragOver, onFolderDragLeave, onFolderDrop,
  openFolderEdit, deleteFolderWithCheck,
} = inject('dragDrop') as ReturnType<typeof useDragDrop>

const sortedFiles = computed(() => {
  if (!sortKey.value) return allFiles.value
  return [...allFiles.value].sort((a, b) => {
    let cmp = 0
    if (sortKey.value === 'name') cmp = a.file_name.localeCompare(b.file_name, 'zh')
    else if (sortKey.value === 'size') cmp = (a.file_size || 0) - (b.file_size || 0)
    else if (sortKey.value === 'time') cmp = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    return sortDir.value === 'asc' ? cmp : -cmp
  })
})

function handlePreview(file: FileItem) {
  currentFile.value = file
  previewVisible.value = true
}
</script>

<style scoped lang="scss">
// ==================== 文件格 ====================

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
  padding: 8px;
}

// ==================== 公共覆盖操作按钮 ====================

.card-overlay-actions {
  position: absolute;
  top: 4px; right: 4px;
  display: flex;
  align-items: center;
  gap: 3px;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: opacity 0.15s, visibility 0.15s;
  z-index: 2;
}

.overlay-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px; height: 24px;
  border: none;
  border-radius: $radius-sm;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  color: var(--el-text-color-secondary);
  transition: background $transition-fast, color $transition-fast, box-shadow $transition-fast;

  html.dark & { background: rgba(38, 42, 54, 0.90); box-shadow: 0 1px 4px rgba(0, 0, 0, 0.32); }
  &:hover { background: #fff; color: var(--el-text-color-primary); box-shadow: 0 2px 6px rgba(0,0,0,0.18); }
  &.danger:hover { background: rgba(239, 68, 68, 0.1); color: var(--el-color-danger); }
}

// ==================== 文件夹卡片 ====================

.folder-grid-card {
  background: var(--color-surface);
  border-radius: $radius-md;
  border: 1px solid var(--color-border);
  cursor: pointer;
  overflow: hidden;
  transition: border-color $transition-base;
  user-select: none;
  position: relative;

  &:hover { border-color: var(--color-text-muted); }
  &:hover .card-overlay-actions { opacity: 1; visibility: visible; pointer-events: auto; }
  &:hover .folder-thumb-area { background: var(--color-primary-subtle); }
  &.drag-over { box-shadow: 0 0 0 2px $color-primary; background: rgba(90, 103, 216, 0.04); }
  &.is-selected { box-shadow: 0 0 0 2px $color-primary; background: rgba(90, 103, 216, 0.05); }
  &.is-dragging-folder { opacity: 0.4; cursor: grabbing; }

  .card-body { padding: 7px 8px; min-height: 42px; display: flex; flex-direction: column; justify-content: center; gap: 2px; }
  .card-title { margin: 0; font-size: 13px; font-weight: 500; line-height: 1.35; color: var(--color-text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .folder-size { margin: 0; font-size: 10px; color: var(--color-text-muted); min-height: 13px; font-variant-numeric: tabular-nums; }
}

.folder-thumb-area {
  position: relative;
  height: 72px;
  overflow: hidden;
  background: var(--color-surface-raised);
  border-bottom: 1px solid var(--color-border);
  transition: background $transition-fast;

  & > svg { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
}

// ==================== 文件卡片 ====================

.hub-file-item {
  position: relative;
  border-radius: $radius-md;
  overflow: hidden;

  :deep(.file-card) {
    border-radius: $radius-md;
    box-shadow: none !important;
    border: 1px solid var(--color-border) !important;
    background: var(--color-surface) !important;
    transition: border-color $transition-base;
    &:hover { transform: none !important; box-shadow: none !important; border-color: var(--color-text-muted) !important; }
  }
  :deep(.card-desc) { display: none; }
  :deep(.card-meta) {
    margin-top: 2px;
    .meta-time { font-size: 11px; color: var(--color-text-muted); font-family: $font-mono; margin-left: 0 !important; }
    .meta-likes { font-size: 10px; }
    .meta-sep { display: none; }
  }
  :deep(.thumbnail-wrap) {
    padding-top: 0 !important;
    height: 72px !important;
    background: var(--color-surface-raised) !important;
    border-bottom: 1px solid var(--color-border) !important;
    transition: background $transition-fast !important;
  }
  &:hover :deep(.thumbnail-wrap) { background: var(--color-primary-subtle) !important; }
  :deep(.card-body) { padding: 6px 8px !important; }
  :deep(.card-title) { font-size: 13px !important; font-weight: 500 !important; margin: 0 0 0 !important; color: var(--color-text-primary) !important; }

  &.is-dragging { opacity: 0.4; cursor: grabbing; }
  &.is-selected :deep(.file-card) { box-shadow: 0 0 0 2px $color-primary !important; }
  &:hover .card-overlay-actions { opacity: 1; visibility: visible; pointer-events: auto; }
}

// ==================== 체크박스 ====================

.item-checkbox {
  position: absolute;
  top: 7px; left: 7px;
  z-index: 10;
  cursor: pointer;
}

.check-circle {
  display: block;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: all 0.15s ease;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.18));

  circle { stroke: rgba(150, 155, 170, 0.9); stroke-width: 1.5; fill: rgba(255,255,255,0.85); }
  polyline { stroke: transparent; stroke-width: 2; }

  &.checked {
    circle { fill: $color-primary; stroke: $color-primary; }
    polyline { stroke: #fff; }
  }
}

@media (max-width: $breakpoint-md) {
  .content-grid { grid-template-columns: repeat(auto-fill, minmax(84px, 1fr)); gap: 6px; }
}
</style>
