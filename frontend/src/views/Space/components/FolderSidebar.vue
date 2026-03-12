<template>
  <div
    class="groups-sidebar"
    :class="{ 'sidebar-drop-active': isSidebarDragOver }"
    @dragenter="onSidebarDragEnter"
    @dragover="onSidebarDragOver"
    @dragleave="onSidebarDragLeave"
    @drop="onSidebarDrop"
  >
    <!-- 快捷方式区 -->
    <div class="sidebar-section-header shortcuts-header">
      <span class="sidebar-section-title">快捷方式</span>
    </div>

    <div
      v-for="sc in shortcuts"
      :key="`sc-${sc.type}-${sc.id}`"
      :class="['group-item', 'shortcut-item']"
      @click="navigateShortcut(sc)"
    >
      <span class="group-icon-wrap shortcut-icon">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
          <path d="M1.5 5a1 1 0 011-1H5.6l1.1 1.5H13.5a1 1 0 011 1V12a1 1 0 01-1 1h-11a1 1 0 01-1-1V5z"/>
        </svg>
      </span>
      <span class="group-name shortcut-name">{{ sc.name }}</span>
      <span class="shortcut-remove" @click.stop="removeShortcut(sc)" title="移除">×</span>
    </div>

    <div v-if="isSidebarDragOver" class="sidebar-drop-hint">拖放到此添加快捷方式</div>

    <!-- 操作按钮 -->
    <div class="sidebar-actions">
      <button class="sidebar-action-btn shortcut-btn" @click="openShortcutPicker">
        <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="3" x2="8" y2="13"/><line x1="3" y1="8" x2="13" y2="8"/></svg>
        添加快捷方式
      </button>
    </div>

    <!-- 快捷方式选取对话框 -->
    <el-dialog
      v-model="showShortcutPickerDialog"
      title="添加快捷方式"
      width="340px"
      :align-center="true"
      append-to-body
    >
      <el-tree
        :data="folderTree"
        :props="{ children: 'children', label: 'name' }"
        node-key="id"
        highlight-current
        :expand-on-click-node="false"
        :default-expand-all="false"
        class="shortcut-tree"
        @current-change="(data: any) => { shortcutPickerSelected = data?.id ?? null }"
      />
      <template #footer>
        <el-button @click="showShortcutPickerDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddShortcut">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue'
import type { useGroupNav } from '@/composables/useGroupNav'
import type { useFileManager } from '@/composables/useFileManager'
import type { useDragDrop } from '@/composables/useDragDrop'
import type { useShortcuts } from '@/composables/useShortcuts'

const { folderTree } = inject('fileManager') as ReturnType<typeof useFileManager>

const { isSidebarDragOver, onSidebarDragEnter, onSidebarDragOver, onSidebarDragLeave, onSidebarDrop } =
  inject('dragDrop') as ReturnType<typeof useDragDrop>

const { shortcuts, removeShortcut, navigateShortcut, showShortcutPickerDialog, shortcutPickerSelected, openShortcutPicker, confirmAddShortcut } =
  inject('shortcuts') as ReturnType<typeof useShortcuts>
</script>

<style scoped lang="scss">
.groups-sidebar {
  width: 168px;
  flex-shrink: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  padding: $spacing-sm $spacing-xs;
  position: sticky;
  top: 76px;
  max-height: calc(100vh - 88px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.sidebar-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px $spacing-sm 2px;
  margin-bottom: 2px;
}

.sidebar-section-title {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--el-text-color-placeholder);
}

.group-item {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  padding: 5px $spacing-sm;
  border-radius: $radius-md;
  cursor: pointer;
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  transition: background $transition-fast, color $transition-fast;
  user-select: none;

  &:hover { background: var(--el-fill-color-light); color: var(--el-text-color-primary); }
}

.group-name {
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  min-width: 0;
}

.shortcut-item { color: var(--el-text-color-secondary); }

.shortcut-remove {
  font-size: 13px;
  line-height: 1;
  width: 15px;
  height: 15px;
  display: none;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  flex-shrink: 0;
  border-radius: 3px;
  transition: color $transition-fast, background $transition-fast;

  &:hover { color: var(--el-color-danger); background: var(--el-color-danger-light-9); }
}

.shortcut-item:hover .shortcut-remove { display: flex; }

.sidebar-drop-hint {
  font-size: 10px;
  color: $color-primary;
  text-align: center;
  padding: 4px $spacing-xs;
  background: rgba(99, 102, 241, 0.05);
  border-radius: $radius-sm;
  margin: 2px 0;
}

.sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 1px;
  margin-top: $spacing-sm;
  padding-top: 6px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.sidebar-action-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  width: 100%;
  padding: 5px $spacing-sm;
  border: none;
  background: transparent;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  font-size: $font-xs;
  border-radius: $radius-md;
  transition: background $transition-fast, color $transition-fast;

  &:hover { background: var(--el-fill-color-light); color: $color-primary; }
  &:disabled { opacity: 0.45; cursor: not-allowed; }

  &.shortcut-btn:hover { color: $color-secondary; }
}

.group-icon-wrap {
  position: relative;
  width: 15px;
  height: 15px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;

  svg { position: absolute; }
}

.shortcut-icon svg { opacity: 1; }

.shortcut-tree {
  max-height: 300px;
  overflow-y: auto;

  :deep(.el-tree-node__content) {
    height: 34px;
    border-radius: 6px;

    &:hover { background: var(--el-fill-color-light); }
  }

  :deep(.el-tree-node.is-current > .el-tree-node__content) {
    background: rgba(99, 102, 241, 0.08);
    color: $color-primary;
  }
}

@media (max-width: $breakpoint-md) {
  .groups-sidebar {
    width: 100%;
    display: flex;
    flex-direction: row;
    overflow-x: auto;
    position: static;
    padding: $spacing-xs;
    gap: $spacing-xs;
    border-radius: $radius-md;
    max-height: none;

    .sidebar-section-header { display: none; }
    .shortcuts-header { display: none; }
    .group-item { flex-shrink: 0; white-space: nowrap; }
    .sidebar-actions { flex-direction: row; margin-top: 0; padding-top: 0; border-top: none; }
    .sidebar-drop-hint { display: none; }
  }
}
</style>
