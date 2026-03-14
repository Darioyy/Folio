<template>
  <div v-if="allFiles.length > 0 || subFolders.length > 0" class="file-list">
    <div :class="['list-header', { 'with-check': isEditMode }]">
      <span v-if="isEditMode" class="col-check"></span>
      <span class="col-icon"></span>
      <span class="col-name sort-col" :class="{ active: sortKey === 'name' }" @click="toggleSort('name')">
        文件名<SortArrow :active="sortKey === 'name'" :dir="sortDir" />
      </span>
      <span class="col-size hide-mobile sort-col" :class="{ active: sortKey === 'size' }" @click="toggleSort('size')">
        大小<SortArrow :active="sortKey === 'size'" :dir="sortDir" />
      </span>
      <span class="col-time sort-col" :class="{ active: sortKey === 'time' }" @click="toggleSort('time')">
        时间<SortArrow :active="sortKey === 'time'" :dir="sortDir" />
      </span>
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
      @dragover.prevent="!isEditMode && onFolderDragOver($event)"
      @dragleave="!isEditMode && onFolderDragLeave($event)"
      @drop.stop.prevent="!isEditMode && onFolderDrop($event, folder)"
    >
      <span v-if="isEditMode" class="col-check" @click.stop="toggleSelect('folder', folder.id)">
        <svg :class="['check-circle', { checked: selectedItems.has(`folder:${folder.id}`) }]" viewBox="0 0 16 16" width="16" height="16">
          <circle cx="8" cy="8" r="7"/><polyline points="4.5,8 7,10.5 11.5,5"/>
        </svg>
      </span>
      <span class="col-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="#f59e0b" stroke="none">
          <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" opacity="0.9"/>
        </svg>
      </span>
      <div class="col-name">
        <span class="row-title">{{ folder.name }}</span>
      </div>
      <span class="col-size hide-mobile" @mouseenter="loadFolderSize(folder.id)">{{ folderSizes[folder.id] ?? '—' }}</span>
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
      v-for="file in sortedFiles"
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
        <FileTypeIcon :mime-type="file.mime_type" :file-name="file.file_name" :file-category="file.file_category" size="sm" />
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
import { inject, ref, computed } from 'vue'
import type { Ref } from 'vue'
import { Edit as EditIcon, Delete as DeleteIcon } from '@element-plus/icons-vue'
import FileTypeIcon from '@/components/business/FileTypeIcon.vue'
import type { useGroupNav } from '@/composables/useGroupNav'
import type { useFileManager } from '@/composables/useFileManager'
import type { useBatchSelect } from '@/composables/useBatchSelect'
import type { useDragDrop } from '@/composables/useDragDrop'
import type { FileItem } from '@/types/models'
import { formatFileSize, formatDate } from '@/utils/format'
import { groupsApi } from '@/api/modules/groups'

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
const { sortKey, sortDir, toggleSort } = inject('fileSort') as { sortKey: Ref<string>; sortDir: Ref<'asc' | 'desc'>; toggleSort: (k: string) => void }

// 内联排序箭头组件
const SortArrow = {
  props: ['active', 'dir'],
  template: `<span class="sort-arrow" :class="{ 'is-active': active }">{{ active ? (dir === 'asc' ? '↑' : '↓') : '↕' }}</span>`,
}

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
.file-list {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  overflow: hidden;
  margin-bottom: $spacing-lg;
}

.list-header {
  display: grid;
  grid-template-columns: 40px 1fr 72px 120px 80px;
  gap: $spacing-sm;
  align-items: center;
  height: 36px;
  padding: 0 12px;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--color-border);
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.list-header.with-check,
.list-row.with-check { grid-template-columns: 32px 40px 1fr 72px 120px 80px; }

.list-row {
  display: grid;
  grid-template-columns: 40px 1fr 72px 120px 80px;
  gap: $spacing-sm;
  align-items: center;
  min-height: 40px;
  padding: 0 12px;
  border-top: 1px solid var(--color-border-subtle);
  cursor: pointer;
  transition: background $transition-fast;

  &:first-child { border-top: none; }
  &:hover { background: var(--color-primary-subtle); }
  &:hover .col-actions { opacity: 1; }
  &.is-selected { background: rgba(90, 103, 216, 0.06) !important; outline: 1px solid rgba(90, 103, 216, 0.3); }
  &.is-selected .col-actions { opacity: 1; }
  &.folder-row { font-weight: 500; }
  &.folder-row.drag-over { background: rgba(90, 103, 216, 0.06); outline: 1px solid $color-primary; outline-offset: -1px; }
  &.is-dragging-folder { opacity: 0.4; cursor: grabbing; }
}

.col-check { display: flex; align-items: center; justify-content: center; width: 32px; flex-shrink: 0; }

.col-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

}

.col-name {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 1px;

  .row-title { font-size: $font-13; font-weight: 500; color: var(--el-text-color-primary); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; line-height: 1.4; }
  .row-desc { font-size: $font-xs; color: var(--el-text-color-secondary); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; line-height: 1.3; }
}

.col-size { font-size: $font-xs; color: var(--color-text-muted); white-space: nowrap; }
.col-time { font-size: $font-xs; color: var(--color-text-muted); white-space: nowrap; }

.col-actions { display: flex; align-items: center; gap: 2px; flex-shrink: 0; opacity: 0; transition: opacity $transition-fast; }

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

.sort-col {
  cursor: pointer;
  user-select: none;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  transition: color $transition-fast;

  &:hover { color: $color-primary; }
  &.active { color: $color-primary; }
}

.sort-arrow {
  font-size: 10px;
  opacity: 0.6;
  transition: opacity $transition-fast;
  &.is-active { opacity: 1; color: $color-primary; }
}

@media (max-width: $breakpoint-md) {
  .list-header, .list-row { grid-template-columns: 40px 1fr 80px; }
  .list-header.with-check, .list-row.with-check { grid-template-columns: 32px 40px 1fr 80px; }
}
</style>
