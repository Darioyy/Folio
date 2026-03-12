<template>
  <div v-if="allFiles.length > 0 || subFolders.length > 0" class="file-list">
    <div :class="['list-header', { 'with-check': isEditMode }]">
      <span v-if="isEditMode" class="col-check"></span>
      <span class="col-icon"></span>
      <span class="col-name">文件名</span>
      <span class="col-size hide-mobile">大小</span>
      <span class="col-time">时间</span>
      <span class="col-actions">操作</span>
    </div>

    <!-- 文件夹行 -->
    <div
      v-for="folder in subFolders"
      :key="`f-${folder.id}`"
      :class="['list-row', 'folder-row', { 'drag-over': dragOverFolderId === folder.id, 'is-selected': isEditMode && selectedItems.has(`folder:${folder.id}`), 'with-check': isEditMode, 'is-dragging-folder': draggingFolder?.id === folder.id }]"
      :draggable="!isEditMode"
      @click="isEditMode ? toggleSelect('folder', folder.id) : navigateDeep(folder)"
      @dragstart="!isEditMode && onFolderDragStart($event, folder)"
      @dragend="!isEditMode && onFolderDragEnd()"
      @dragenter.prevent="!isEditMode && onFolderDragEnter($event, folder)"
      @dragover="!isEditMode && onFolderDragOver($event)"
      @dragleave="!isEditMode && onFolderDragLeave($event)"
      @drop.stop.prevent="!isEditMode && onFolderDrop($event, folder)"
    >
      <span v-if="isEditMode" class="col-check" @click.stop="toggleSelect('folder', folder.id)">
        <svg :class="['check-circle', { checked: selectedItems.has(`folder:${folder.id}`) }]" viewBox="0 0 16 16" width="16" height="16">
          <circle cx="8" cy="8" r="7"/><polyline points="4.5,8 7,10.5 11.5,5"/>
        </svg>
      </span>
      <span class="col-icon">
        <svg viewBox="0 0 40 34" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="20" height="17" style="color: var(--el-color-primary); opacity: 0.8">
          <path d="M2 8a2 2 0 012-2h9l2.5 3.5H36a2 2 0 012 2v16a2 2 0 01-2 2H4a2 2 0 01-2-2V8z"/>
        </svg>
      </span>
      <div class="col-name">
        <span class="row-title">{{ folder.name }}</span>
        <span class="row-desc">{{ folder.file_count }} 个文件<template v-if="folder.children_count > 0"> · {{ folder.children_count }} 子文件夹</template></span>
      </div>
      <span class="col-size hide-mobile">—</span>
      <span class="col-time hide-mobile" :title="formatDate(folder.created_at)">{{ formatDate(folder.created_at, 'MM-DD') }}</span>
      <div class="col-actions" @click.stop>
        <template v-if="!isEditMode">
          <el-button text size="small" :icon="EditIcon" @click.stop="openFolderEdit(folder)" />
          <el-button text size="small" :icon="DeleteIcon" class="danger-btn" @click.stop="deleteFolderWithCheck(folder)" />
        </template>
      </div>
    </div>

    <!-- 文件行 -->
    <div
      v-for="file in allFiles"
      :key="file.id"
      :class="['list-row', { 'is-selected': isEditMode && selectedItems.has(`file:${file.id}`), 'with-check': isEditMode }]"
      :draggable="!isEditMode"
      @dragstart="!isEditMode && onFileDragStart($event, file)"
      @dragend="!isEditMode && onFileDragEnd()"
      @click="isEditMode ? toggleSelect('file', file.id) : handlePreview(file)"
    >
      <span v-if="isEditMode" class="col-check" @click.stop="toggleSelect('file', file.id)">
        <svg :class="['check-circle', { checked: selectedItems.has(`file:${file.id}`) }]" viewBox="0 0 16 16" width="16" height="16">
          <circle cx="8" cy="8" r="7"/><polyline points="4.5,8 7,10.5 11.5,5"/>
        </svg>
      </span>
      <span class="col-icon">
        <div v-if="file.file_category === 'image'" class="list-thumb">
          <img :src="getFileUrl(file.thumbnail_path || file.file_path)" :alt="file.file_name" loading="lazy" @error="(e) => ((e.target as HTMLImageElement).style.display = 'none')" />
        </div>
        <div v-else-if="file.file_category === 'video'" class="list-thumb">
          <img v-if="file.thumbnail_path" :src="getFileUrl(file.thumbnail_path)" :alt="file.file_name" loading="lazy" @error="(e) => ((e.target as HTMLImageElement).style.display = 'none')" />
          <el-icon v-else :size="20" style="color: #6366f1"><VideoPlay /></el-icon>
        </div>
        <FileTypeIcon v-else :mime-type="file.mime_type" :file-name="file.file_name" size="sm" />
      </span>
      <div class="col-name">
        <span class="row-title">{{ file.file_name }}</span>
      </div>
      <span class="col-size hide-mobile">{{ formatFileSize(file.file_size) }}</span>
      <span class="col-time" :title="formatDate(file.created_at)">{{ formatDate(file.created_at, 'MM-DD HH:mm') }}</span>
      <div class="col-actions" @click.stop>
        <el-button text size="small" :icon="EditIcon" @click="openEdit(file)" />
        <el-popconfirm title="确认删除该文件？" confirm-button-text="删除" cancel-button-text="取消" confirm-button-type="danger" @confirm="handleDelete(file)">
          <template #reference>
            <el-button text size="small" :icon="DeleteIcon" class="danger-btn" />
          </template>
        </el-popconfirm>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue'
import { VideoPlay, Edit as EditIcon, Delete as DeleteIcon } from '@element-plus/icons-vue'
import FileTypeIcon from '@/components/business/FileTypeIcon.vue'
import type { useGroupNav } from '@/composables/useGroupNav'
import type { useFileManager } from '@/composables/useFileManager'
import type { useBatchSelect } from '@/composables/useBatchSelect'
import type { useDragDrop } from '@/composables/useDragDrop'
import type { FileItem } from '@/types/models'
import { formatFileSize, formatDate, getFileUrl } from '@/utils/format'

const { subFolders, navigateDeep } = inject('groupNav') as ReturnType<typeof useGroupNav>
const { displayFiles: allFiles, currentFile, previewVisible, openEdit, handleDelete } = inject('fileManager') as ReturnType<typeof useFileManager>
const { isEditMode, selectedItems, toggleSelect } = inject('batchSelect') as ReturnType<typeof useBatchSelect>
const {
  draggingFolder, dragOverFolderId,
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
.file-list {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  overflow: hidden;
  margin-bottom: $spacing-lg;
}

.list-header {
  display: grid;
  grid-template-columns: 44px 1fr 70px 100px 100px;
  gap: $spacing-sm;
  align-items: center;
  padding: $spacing-sm $spacing-md;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
  font-size: $font-xs;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.list-header.with-check,
.list-row.with-check { grid-template-columns: 32px 44px 1fr 70px 100px 100px; }

.list-row {
  display: grid;
  grid-template-columns: 44px 1fr 70px 100px 100px;
  gap: $spacing-sm;
  align-items: center;
  padding: $spacing-sm $spacing-md;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background $transition-fast;

  &:last-child { border-bottom: none; }
  &:hover { background: var(--el-fill-color-light); }
  &.is-selected { background: rgba(99, 102, 241, 0.06) !important; outline: 1px solid rgba(99, 102, 241, 0.3); }
  &.folder-row { font-weight: 500; }
  &.folder-row.drag-over { background: rgba(99, 102, 241, 0.06); outline: 1px solid $color-primary; outline-offset: -1px; }
  &.is-dragging-folder { opacity: 0.4; cursor: grabbing; }
}

.col-check { display: flex; align-items: center; justify-content: center; width: 32px; flex-shrink: 0; }

.col-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .list-thumb {
    width: 36px; height: 36px;
    border-radius: $radius-sm;
    overflow: hidden;
    background: var(--el-fill-color);
    display: flex;
    align-items: center;
    justify-content: center;

    img { width: 100%; height: 100%; object-fit: cover; }
  }
}

.col-name {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;

  .row-title { font-size: $font-sm; font-weight: 500; color: var(--el-text-color-primary); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
  .row-desc { font-size: $font-xs; color: var(--el-text-color-secondary); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
}

.col-size, .col-time { font-size: $font-xs; color: var(--el-text-color-secondary); white-space: nowrap; }

.col-actions { display: flex; align-items: center; gap: 2px; flex-shrink: 0; }

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

.hide-mobile { @media (max-width: $breakpoint-md) { display: none; } }

@media (max-width: $breakpoint-md) {
  .list-header, .list-row { grid-template-columns: 44px 1fr 90px 140px; }
}
</style>
