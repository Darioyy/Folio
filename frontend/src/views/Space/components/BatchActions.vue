<template>
  <!-- 批量操作按钮（渲染到工具栏 toolbar-right 内联位置） -->
  <template v-if="isEditMode">
    <span class="batch-count">{{ selectedItems.size }} 项</span>
    <button class="batch-action-btn" @click="selectAllItems">{{ isAllSelected ? '取消' : '全选' }}</button>
    <button class="batch-action-btn" :disabled="selectedItems.size === 0" @click="openBatchMove">移动</button>
    <button class="batch-action-btn" :disabled="selectedItems.size !== 1" @click="startBatchRename">重命名</button>
    <button class="batch-action-btn danger" :disabled="selectedItems.size === 0" @click="batchDelete">删除</button>
    <div class="toolbar-sep"></div>
  </template>

  <!-- 批量移动对话框 -->
  <el-dialog v-model="showBatchMove" title="移动到文件夹" width="400px">
    <el-cascader
      v-model="batchMoveTarget"
      :options="folderCascaderOptions"
      :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name', children: 'children' }"
      placeholder="选择目标文件夹（空=未分组）"
      clearable style="width: 100%"
    />
    <template #footer>
      <el-button @click="showBatchMove = false">取消</el-button>
      <el-button type="primary" :loading="batchMoveLoading" @click="executeBatchMove">移动</el-button>
    </template>
  </el-dialog>

  <!-- 批量重命名对话框 -->
  <el-dialog v-model="showBatchRenameDialog" title="重命名" width="400px">
    <el-form label-width="70px">
      <el-form-item label="新名称">
        <el-input v-model="batchRenameName" placeholder="输入新名称" maxlength="200" />
      </el-form-item>
      <el-form-item v-if="batchRenameIsMulti">
        <span style="font-size:12px;color:var(--el-text-color-secondary)">多项重命名时，后续项自动附加 (1)、(2)... 以避免重名</span>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showBatchRenameDialog = false">取消</el-button>
      <el-button type="primary" :loading="batchRenameLoading" @click="executeBatchRename">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { inject } from 'vue'
import type { useBatchSelect } from '@/composables/useBatchSelect'
import type { useFileManager } from '@/composables/useFileManager'

const {
  isEditMode, selectedItems, isAllSelected, batchRenameIsMulti,
  showBatchMove, batchMoveTarget, batchMoveLoading,
  showBatchRenameDialog, batchRenameName, batchRenameLoading,
  selectAllItems, openBatchMove, executeBatchMove,
  startBatchRename, executeBatchRename, batchDelete,
} = inject('batchSelect') as ReturnType<typeof useBatchSelect>

const { folderCascaderOptions } = inject('fileManager') as ReturnType<typeof useFileManager>
</script>

<style scoped lang="scss">
.batch-count { font-size: $font-xs; color: var(--el-text-color-secondary); white-space: nowrap; flex-shrink: 0; }
.toolbar-sep { width: 1px; height: 18px; background: var(--el-border-color-light); flex-shrink: 0; margin: 0 2px; }

.batch-action-btn {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  height: 24px;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  border-radius: $radius-sm;
  font-size: $font-xs;
  transition: all $transition-fast;
  flex-shrink: 0;

  &:hover { border-color: $color-primary; color: $color-primary; }
  &.danger:hover { border-color: var(--el-color-danger); color: var(--el-color-danger); }
  &:disabled { opacity: 0.4; cursor: not-allowed; &:hover { border-color: var(--el-border-color-light); color: var(--el-text-color-regular); } }
}
</style>
