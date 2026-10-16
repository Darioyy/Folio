<template>
  <div class="pdf-page">
    <div class="pdf-tabs">
      <button
        v-for="t in TABS"
        :key="t.id"
        class="tab-btn"
        :class="{ active: activeTab === t.id }"
        @click="activeTab = t.id"
      >{{ t.label }}</button>
    </div>

    <div v-show="activeTab === 'edit'" class="tab-panel">
      <PdfEditor />
    </div>
    <div v-show="activeTab === 'scan'" class="tab-panel">
      <PdfScan />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PdfEditor from './components/PdfEditor.vue'
import PdfScan from './components/PdfScan.vue'

const TABS = [
  { id: 'edit', label: 'PDF 编辑' },
  { id: 'scan', label: '扫描增强' },
] as const

const activeTab = ref<'edit' | 'scan'>('edit')
</script>

<style scoped lang="scss">
.pdf-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.pdf-tabs {
  display: flex;
  border-bottom: 1px solid var(--color-border);
  padding: 0 24px;
  background: var(--color-surface);
  flex-shrink: 0;

  @media (max-width: 640px) { padding: 0 16px; }
}

.tab-btn {
  padding: 13px 0;
  margin-right: 24px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: color $transition-fast, border-color $transition-fast;

  &.active {
    color: var(--color-text-primary);
    border-bottom-color: var(--color-primary);
  }

  &:hover:not(.active) { color: var(--color-text-primary); }
}

.tab-panel { flex: 1; min-height: 0; }
</style>
