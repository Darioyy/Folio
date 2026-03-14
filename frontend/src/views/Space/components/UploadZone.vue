<template>
  <!-- 拖拽放置遮罩 -->
  <div v-if="isDragOver" class="drop-overlay">
    <div class="drop-overlay-inner">
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="52" height="52">
        <path d="M24 4v28M12 20l12-16 12 16"/>
        <path d="M8 36h32a2 2 0 002 2v4H6v-4a2 2 0 012-2z"/>
      </svg>
      <p>松开鼠标上传文件</p>
      <span v-if="currentFolderName">上传到「{{ currentFolderName }}」</span>
      <span v-else>上传到未分组</span>
    </div>
  </div>

  <!-- 批量上传进度面板 -->
  <Transition name="upload-panel">
    <div v-if="showUploadPanel" class="batch-upload-panel">
      <div class="batch-panel-header">
        <span>上传队列（{{ uploadTasks.filter(t => t.status === 'done').length }}/{{ uploadTasks.length }}）</span>
        <button class="batch-panel-close" :disabled="batchUploading" @click="closeBatchPanel">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" width="14" height="14">
            <line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/>
          </svg>
        </button>
      </div>
      <div class="batch-panel-list">
        <div v-for="task in uploadTasks" :key="task.id" class="batch-task-row">
          <div class="batch-task-name" :title="task.file.name">{{ task.file.name }}</div>
          <div class="batch-task-bar">
            <div class="batch-task-fill" :class="task.status" :style="{ width: task.progress + '%' }"></div>
          </div>
          <span class="batch-task-status">
            <template v-if="task.status === 'pending'">等待</template>
            <template v-else-if="task.status === 'uploading'">{{ task.progress }}%</template>
            <template v-else-if="task.status === 'done'">✓</template>
            <template v-else>✗</template>
          </span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import type { useGroupNav } from '@/composables/useGroupNav'
import type { useDragDrop } from '@/composables/useDragDrop'

const { currentFolderId, breadcrumb } = inject('groupNav') as ReturnType<typeof useGroupNav>
const { isDragOver, uploadTasks, showUploadPanel, batchUploading, closeBatchPanel } = inject('dragDrop') as ReturnType<typeof useDragDrop>

const currentFolderName = computed(() =>
  currentFolderId.value && currentFolderId.value > 0
    ? breadcrumb.value[breadcrumb.value.length - 1]?.name
    : null
)
</script>

<style scoped lang="scss">
.drop-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  background: rgba(90, 103, 216, 0.08);
  border-radius: $radius-lg;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.drop-overlay-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;
  color: $color-primary;

  svg { opacity: 0.85; }

  p {
    font-size: $font-xl;
    font-weight: 600;
    margin: 0;
    color: $color-primary;
  }

  span { font-size: $font-sm; color: var(--el-text-color-secondary); }
}

.batch-upload-panel {
  position: fixed;
  bottom: $spacing-xl; right: $spacing-xl;
  z-index: 2000;
  width: 320px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  box-shadow: $shadow-lg;
  overflow: hidden;
}

.batch-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-md;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-lighter);
  font-size: $font-sm; font-weight: 500;
  color: var(--el-text-color-primary);
}

.batch-panel-close {
  display: flex; align-items: center; justify-content: center;
  width: 22px; height: 22px;
  border: none; background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background $transition-fast;

  &:hover:not(:disabled) { background: var(--el-fill-color); }
  &:disabled { opacity: 0.4; cursor: not-allowed; }
}

.batch-panel-list { max-height: 280px; overflow-y: auto; padding: $spacing-xs $spacing-sm; }

.batch-task-row {
  display: grid;
  grid-template-columns: 1fr 100px 32px;
  align-items: center;
  gap: $spacing-xs;
  padding: 5px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);

  &:last-child { border-bottom: none; }
}

.batch-task-name { font-size: $font-xs; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; color: var(--el-text-color-primary); }
.batch-task-bar { height: 4px; background: var(--el-fill-color); border-radius: $radius-full; overflow: hidden; }
.batch-task-fill { height: 100%; border-radius: $radius-full; transition: width 0.2s; background: $color-primary; &.done { background: var(--el-color-success); } &.error { background: var(--el-color-danger); } }
.batch-task-status { font-size: 11px; text-align: right; color: var(--el-text-color-secondary); }

.upload-panel-enter-active, .upload-panel-leave-active { transition: opacity 0.2s, transform 0.2s; }
.upload-panel-enter-from, .upload-panel-leave-to { opacity: 0; transform: translateY(12px); }
</style>
