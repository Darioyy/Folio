<template>
  <div v-if="subFolders.length > 0 || allFiles.length > 0" class="content-grid">
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
      @dragover="!isEditMode && onFolderDragOver($event)"
      @dragleave="!isEditMode && onFolderDragLeave($event)"
      @drop.stop.prevent="!isEditMode && onFolderDrop($event, folder)"
    >
      <div class="thumbnail-wrap folder-thumb-area">
        <div v-if="isEditMode" class="item-checkbox" @click.stop="toggleSelect('folder', folder.id)">
          <svg :class="['check-circle', { checked: selectedItems.has(`folder:${folder.id}`) }]" viewBox="0 0 16 16" width="16" height="16">
            <circle cx="8" cy="8" r="7"/><polyline points="4.5,8 7,10.5 11.5,5"/>
          </svg>
        </div>
        <svg viewBox="0 0 48 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="48" height="40" style="color: var(--el-color-primary); opacity: 0.75">
          <path d="M2 10a2 2 0 012-2h10l3 4H44a2 2 0 012 2v20a2 2 0 01-2 2H4a2 2 0 01-2-2V10z"/>
        </svg>
        <div v-if="!isEditMode" class="folder-actions-overlay" @click.stop>
          <button class="overlay-action-btn" title="编辑" @click.stop="openFolderEdit(folder)">
            <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 2.5a1.414 1.414 0 012 2L5 13H3v-2L11.5 2.5z"/></svg>
          </button>
          <button class="overlay-action-btn danger" title="删除" @click.stop="deleteFolderWithCheck(folder)">
            <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3,5 13,5"/><path d="M5 5V3h6v2"/><path d="M4 5l.7 8h6.6L12 5"/></svg>
          </button>
        </div>
      </div>
      <div class="card-body">
        <p class="card-title">{{ folder.name }}</p>
        <p class="card-desc">{{ folder.file_count }} 个文件<template v-if="folder.children_count > 0"> · {{ folder.children_count }} 子文件夹</template></p>
      </div>
    </div>

    <!-- 文件卡片 -->
    <div
      v-for="file in allFiles"
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
      <FileCard :file="file" :show-author="false" :show-badge="false" @click="!isEditMode && handlePreview(file)" />
      <div v-if="!isEditMode" class="card-actions" @click.stop>
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

<script setup lang="ts">
import { inject } from 'vue'
import FileCard from '@/components/business/FileCard.vue'
import type { useGroupNav } from '@/composables/useGroupNav'
import type { useFileManager } from '@/composables/useFileManager'
import type { useBatchSelect } from '@/composables/useBatchSelect'
import type { useDragDrop } from '@/composables/useDragDrop'
import type { FileItem } from '@/types/models'

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

function handlePreview(file: FileItem) {
  currentFile.value = file
  previewVisible.value = true
}
</script>

<style scoped lang="scss">
.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: $spacing-sm;
}

.folder-grid-card {
  background: var(--el-bg-color);
  border-radius: $radius-lg;
  border: 1px solid var(--el-border-color-light);
  box-shadow: $shadow-sm;
  cursor: pointer;
  overflow: hidden;
  transition: transform $transition-base, box-shadow $transition-base;
  user-select: none;
  position: relative;

  &:hover { transform: translateY(-2px); box-shadow: $shadow-lg; }
  &.drag-over { box-shadow: 0 0 0 2px $color-primary; background: rgba(99, 102, 241, 0.04); transform: none; }
  &.is-selected { box-shadow: 0 0 0 2px $color-primary; background: rgba(99, 102, 241, 0.05); }
  &.is-dragging-folder { opacity: 0.4; cursor: grabbing; }

  .card-body { padding: $spacing-md; }
  .card-title { margin: 0 0 $spacing-xs; font-size: $font-sm; font-weight: 600; color: var(--el-text-color-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .card-desc { margin: 0; font-size: $font-xs; color: var(--el-text-color-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
}

.folder-thumb-area {
  position: relative;
  padding-top: 56.25%;
  overflow: hidden;
  background: var(--el-fill-color);

  & > svg { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
}

.folder-actions-overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(6px);
  opacity: 0;
  transition: opacity 0.15s;

  html.dark & { background: rgba(15, 23, 42, 0.9); }
  .folder-grid-card:hover & { opacity: 1; }
}

.overlay-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px; height: 26px;
  border: none;
  border-radius: $radius-sm;
  background: transparent;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  transition: background $transition-fast, color $transition-fast;

  &:hover { background: var(--el-fill-color); color: var(--el-text-color-primary); }
  &.danger:hover { background: var(--el-color-danger-light-9); color: var(--el-color-danger); }
}

.hub-file-item {
  position: relative;
  border-radius: $radius-lg;
  overflow: hidden;

  &:hover :deep(.file-card) { box-shadow: $shadow-lg; }
  :deep(.file-card) { border-radius: $radius-lg; transition: box-shadow $transition-base; &:hover { transform: none; } }
  :deep(.card-desc) { display: none; }

  &.is-dragging { opacity: 0.4; cursor: grabbing; }
  &.is-selected :deep(.file-card) { box-shadow: 0 0 0 2px $color-primary; }
}

.card-actions {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(6px);
  opacity: 0;
  transition: opacity 0.15s;

  html.dark & { background: rgba(15, 23, 42, 0.9); }
}

.hub-file-item:hover .card-actions { opacity: 1; }

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
  .content-grid { grid-template-columns: repeat(2, 1fr); gap: $spacing-sm; }
}
</style>
