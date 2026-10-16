<template>
  <div class="editor-wrap">
    <!-- Hidden file inputs -->
    <input ref="loadInputRef" type="file" accept=".pdf" style="display:none" @change="onLoadInput" />
    <input ref="mergeInputRef" type="file" accept=".pdf" multiple style="display:none" @change="onMergeInput" />
    <input ref="wmImgInputRef" type="file" accept="image/jpeg,image/png" style="display:none" @change="onWmImgInput" />

    <!-- Loading state (file being parsed) -->
    <div v-if="isLoading && !hasPages" class="dz-loading">
      <span class="spinner lg" />
      <p>加载文件中…</p>
    </div>

    <!-- Empty drop zone -->
    <div
      v-if="!hasPages && !isLoading"
      class="drop-zone"
      :class="{ active: isDragOver }"
      @dragover.prevent="isDragOver = true"
      @dragleave="onDragLeave"
      @drop="onDrop"
      @click="loadInputRef?.click()"
    >
      <svg class="dz-icon" viewBox="0 0 40 40" fill="none">
        <rect x="4" y="4" width="24" height="32" rx="2" stroke="currentColor" stroke-width="1.5"/>
        <path d="M12 14h16M12 20h10M28 4v8h8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
        <path d="M32 28v8M29 32l3-4 3 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <p class="dz-title">拖入 PDF 文件</p>
      <p class="dz-sub">或<em>点击选择</em></p>
    </div>

    <!-- Toolbar (sticky) -->
    <div v-if="hasPages" class="toolbar" :class="{ loading: isLoading || rendering }">
      <div class="toolbar-left">
        <span class="file-chip">{{ fileName || 'document' }}</span>
        <span class="page-badge">{{ pages.length }} 页</span>
      </div>
      <div class="toolbar-center">
        <button class="tbtn" data-tip="合并更多 PDF" @click="mergeInputRef?.click()">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M2 8h5M10 8h4M14 8l-3-3M14 8l-3 3M8 2v3M8 11v3"/></svg>
        </button>
        <button class="tbtn" :class="{ active: selectedCount > 0 }" data-tip="拆分选中页" @click="splitSelected">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M3 4l5 4-5 4M8 8h5"/></svg>
        </button>
        <button class="tbtn" :class="{ active: selectedCount > 0 }" data-tip="旋转选中页 +90°" @click="rotateSelected(90)">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M13 4a6 6 0 1 0 1 4"/><path d="M13 1v3h-3"/></svg>
        </button>
        <button class="tbtn danger" :class="{ active: selectedCount > 0 }" data-tip="删除选中页" @click="deleteSelected">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M2 4h12M5 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1M6 7v5M10 7v5M3 4l1 9a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l1-9"/></svg>
        </button>
        <div class="tbtn-divider" />
        <span class="select-info" v-if="selectedCount > 0">已选 {{ selectedCount }}</span>
        <button v-if="selectedCount > 0" class="tbtn-text" @click="deselectAll">取消</button>
        <button v-else class="tbtn-text" @click="selectAll">全选</button>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-ghost btn-sm" @click="showWmModal = true">水印</button>
        <button class="btn btn-ghost btn-sm" @click="showEncModal = true">加密</button>
        <button class="btn btn-primary btn-sm" :disabled="isLoading || rendering || isExporting" @click="exportPdf()">
          <span v-if="isExporting" class="spinner sm export-spinner" />
          <template v-else>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M6 1v7M3 5.5l3 3 3-3M1 9.5v.5a1 1 0 001 1h8a1 1 0 001-1v-.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </template>
          {{ isExporting ? '导出中…' : '导出 PDF' }}
        </button>
        <button class="tbtn danger" data-tip="重置" @click="reset">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M4 8A6 6 0 1 0 5 4"/><path d="M5 1v3H2"/></svg>
        </button>
      </div>
    </div>

    <!-- Page grid -->
    <div v-if="hasPages" class="page-grid">
      <div
        v-for="(page, idx) in pages"
        :key="page.id"
        class="page-card"
        :class="{ selected: page.selected, 'drag-over': dragOverId === page.id }"
        draggable="true"
        @dragstart="onPageDragStart($event, page.id)"
        @dragover.prevent="dragOverId = page.id"
        @dragleave="dragOverId = null"
        @drop.prevent="onPageDrop(page.id)"
        @dragend="draggingId = null; dragOverId = null"
      >
        <div class="card-check" @click.stop="toggleSelect(page.id)">
          <input type="checkbox" :checked="page.selected" @change="toggleSelect(page.id)" />
        </div>
        <div class="card-drag">⠿</div>
        <div
          class="card-thumb"
          :style="{ transform: `rotate(${page.rotation}deg)`, aspectRatio: `1/${page.aspectRatio}` }"
          @click="toggleSelect(page.id)"
        >
          <img v-if="page.thumbnail" :src="page.thumbnail" :alt="`第 ${idx + 1} 页`" />
          <div v-else class="thumb-placeholder" />
        </div>
        <div class="card-num">{{ idx + 1 }}</div>
      </div>
    </div>

    <!-- Watermark Modal -->
    <el-dialog v-model="showWmModal" title="添加水印" width="560px" :append-to-body="true">
      <div class="modal-tabs">
        <button class="mtab" :class="{ active: wmType === 'text' }" @click="wmType = 'text'">文字水印</button>
        <button class="mtab" :class="{ active: wmType === 'image' }" @click="wmType = 'image'">图片水印</button>
      </div>
      <div v-if="wmType === 'text'" class="modal-form">
        <label class="form-label">水印文字</label>
        <input v-model="wmText" class="form-input" placeholder="例：机密  DRAFT" />
        <label class="form-label">字体大小 (pt) — {{ wmFontSize }}</label>
        <input v-model.number="wmFontSize" type="range" min="20" max="120" class="form-range" />
        <label class="form-label">透明度 — {{ Math.round(wmOpacity * 100) }}%</label>
        <input v-model.number="wmOpacity" type="range" min="0.05" max="0.8" step="0.05" class="form-range" />
        <label class="form-label">旋转角度 — {{ wmAngle }}°</label>
        <input v-model.number="wmAngle" type="range" min="-90" max="90" class="form-range" />
        <label class="form-label">颜色</label>
        <input v-model="wmColor" type="color" class="form-color" />
      </div>
      <div v-else class="modal-form">
        <div
          class="img-drop"
          :class="{ 'has-img': !!wmImageUrl }"
          @click="wmImgInputRef?.click()"
        >
          <img v-if="wmImageUrl" :src="wmImageUrl" class="wm-preview-img" />
          <span v-else>点击上传图片（JPG / PNG）</span>
        </div>
        <label class="form-label">透明度 — {{ Math.round(wmOpacity * 100) }}%</label>
        <input v-model.number="wmOpacity" type="range" min="0.05" max="0.8" step="0.05" class="form-range" />
      </div>
      <template #footer>
        <button class="btn btn-ghost" @click="showWmModal = false">取消</button>
        <button class="btn btn-primary" @click="applyWatermark">应用水印</button>
      </template>
    </el-dialog>

    <!-- Encrypt Modal -->
    <el-dialog v-model="showEncModal" title="加密保护" width="440px" :append-to-body="true">
      <div class="enc-notice">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#f59e0b" stroke-width="1.3"/><path d="M8 5v4M8 10.5v.5" stroke="#f59e0b" stroke-width="1.5" stroke-linecap="round"/></svg>
        pdf-lib 当前版本不支持加密，该功能将在后续版本中加入。
      </div>
      <template #footer>
        <button class="btn btn-ghost" @click="showEncModal = false">关闭</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { usePdfEditor } from '@/composables/usePdfEditor'
import type { WatermarkOptions } from '@/composables/usePdfEditor'

const {
  pages, fileName, isLoading, isExporting, rendering, hasPages, selectedCount,
  loadFile, mergeFile, toggleSelect, selectAll, deselectAll,
  deleteSelected, rotatePage, reorderPage, splitSelected, exportPdf, reset,
} = usePdfEditor()

// ── File inputs ───────────────────────────────────────────────────────────────
const loadInputRef = ref<HTMLInputElement | null>(null)
const mergeInputRef = ref<HTMLInputElement | null>(null)
const wmImgInputRef = ref<HTMLInputElement | null>(null)

async function onLoadInput(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) {
    await loadFile(f)
    ElMessage.success('文件加载成功')
  }
  ;(e.target as HTMLInputElement).value = ''
}

async function onMergeInput(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files) for (const f of files) await mergeFile(f)
  ;(e.target as HTMLInputElement).value = ''
}

// ── Drop zone ─────────────────────────────────────────────────────────────────
const isDragOver = ref(false)

function onDragLeave(e: DragEvent) {
  if (!(e.currentTarget as Element).contains(e.relatedTarget as Node)) isDragOver.value = false
}

async function onDrop(e: DragEvent) {
  e.preventDefault(); isDragOver.value = false
  const file = e.dataTransfer?.files[0]
  if (file?.type === 'application/pdf') await loadFile(file)
  else ElMessage.warning('请拖入 PDF 文件')
}

// ── Page drag-reorder ─────────────────────────────────────────────────────────
const draggingId = ref<string | null>(null)
const dragOverId = ref<string | null>(null)

function onPageDragStart(e: DragEvent, id: string) {
  draggingId.value = id
  e.dataTransfer!.effectAllowed = 'move'
}

function onPageDrop(toId: string) {
  if (draggingId.value && draggingId.value !== toId) reorderPage(draggingId.value, toId)
  draggingId.value = null; dragOverId.value = null
}

// ── Rotate ────────────────────────────────────────────────────────────────────
function rotateSelected(delta: 90 | -90) {
  const sel = pages.value.filter(p => p.selected)
  if (!sel.length) { ElMessage.info('请先选择要旋转的页面'); return }
  sel.forEach(p => rotatePage(p.id, delta))
}

// ── Watermark ─────────────────────────────────────────────────────────────────
const showWmModal = ref(false)
const wmType = ref<'text' | 'image'>('text')
const wmText = ref('DRAFT')
const wmFontSize = ref(60)
const wmOpacity = ref(0.2)
const wmAngle = ref(-45)
const wmColor = ref('#d1d5db')
const wmImageUrl = ref<string | null>(null)
const wmImageBytes = ref<Uint8Array | null>(null)

function onWmImgInput(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    wmImageUrl.value = reader.result as string
    const arr = new Uint8Array(reader.result as ArrayBuffer)
    wmImageBytes.value = arr
  }
  reader.readAsArrayBuffer(file)
  const urlReader = new FileReader()
  urlReader.onload = () => { wmImageUrl.value = urlReader.result as string }
  urlReader.readAsDataURL(file)
}

async function applyWatermark() {
  const opt: WatermarkOptions = {
    type: wmType.value,
    text: wmText.value, fontSizePt: wmFontSize.value,
    opacity: wmOpacity.value, angleDeg: wmAngle.value, color: wmColor.value,
    imageBytes: wmImageBytes.value ?? undefined,
  }
  showWmModal.value = false
  await exportPdf(opt)
}

// ── Encrypt (stub) ────────────────────────────────────────────────────────────
const showEncModal = ref(false)
</script>

<style scoped lang="scss">
.editor-wrap {
  padding: 0;
  background: var(--color-bg);
  min-height: 100%;
}

// ── Loading state ─────────────────────────────────────────────────────────────
.dz-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 80px 20px;
  color: var(--color-text-muted);
  font-size: 13px;
}

// ── Instant CSS tooltips ──────────────────────────────────────────────────────
[data-tip] {
  position: relative;

  &::after {
    content: attr(data-tip);
    position: absolute;
    bottom: calc(100% + 6px);
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.78);
    color: #fff;
    font-size: 11px;
    white-space: nowrap;
    padding: 3px 8px;
    border-radius: 4px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.08s ease;
    z-index: 200;
  }

  &:hover::after { opacity: 1; }
}

// ── Drop zone ─────────────────────────────────────────────────────────────────
.drop-zone {
  max-width: 480px;
  margin: 60px auto;
  border: 1.5px dashed var(--color-border);
  border-radius: $radius-lg;
  padding: 60px 40px;
  text-align: center;
  cursor: pointer;
  transition: border-color $transition-base, background $transition-base;

  &:hover, &.active {
    border-color: var(--color-primary);
    background: var(--color-primary-subtle);
    .dz-icon { color: var(--color-primary); }
  }
}

.dz-icon { width: 40px; height: 40px; margin: 0 auto 16px; color: var(--color-text-muted); }
.dz-title { font-size: 16px; font-weight: 500; color: var(--color-text-primary); margin-bottom: 4px; }
.dz-sub { font-size: 13px; color: var(--color-text-muted); em { color: var(--color-primary); font-style: normal; } }

// ── Toolbar ───────────────────────────────────────────────────────────────────
.toolbar {
  position: sticky;
  top: 52px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  animation: slideDown 0.18s ease;

  @media (max-width: 768px) {
    flex-wrap: wrap;
    .toolbar-center { order: 3; width: 100%; }
  }
}

@keyframes slideDown { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }

.toolbar-left { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.toolbar-center { display: flex; align-items: center; gap: 4px; flex: 1; justify-content: center; }
.toolbar-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

.file-chip {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--color-text-primary);
}

.page-badge {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-muted);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 1px 8px;
}

.tbtn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid var(--color-border);
  border-radius: $radius-md;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all $transition-fast;

  svg { width: 14px; height: 14px; }

  &:hover { color: var(--color-text-primary); border-color: var(--color-border-strong, #d1d5db); }
  &.active { color: var(--color-primary); border-color: var(--color-primary); background: var(--color-primary-subtle); }
  &.danger:hover { color: #ef4444; border-color: #ef4444; }
}

.tbtn-divider { width: 1px; height: 20px; background: var(--color-border); margin: 0 4px; }
.select-info { font-size: 12px; color: var(--color-text-muted); padding: 0 4px; }
.tbtn-text { font-size: 12px; color: var(--color-primary); background: none; border: none; cursor: pointer; padding: 0 4px; }

// ── Page grid ─────────────────────────────────────────────────────────────────
.page-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 14px;
  padding: 20px;

  @media (max-width: 480px) { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); }
}

.page-card {
  position: relative;
  background: var(--color-surface);
  border: 1.5px solid var(--color-border);
  border-radius: $radius-md;
  overflow: hidden;
  cursor: grab;
  transition: border-color $transition-fast, box-shadow $transition-fast;
  user-select: none;

  &:hover {
    border-color: var(--color-border-strong, #d1d5db);
    .card-check, .card-drag { opacity: 1; }
  }

  &.selected {
    border-color: var(--color-primary);
    .card-check { opacity: 1; }
  }

  &.drag-over { border-color: var(--color-primary); border-style: dashed; }
}

.card-check {
  position: absolute; top: 6px; left: 6px; z-index: 2;
  opacity: 0; transition: opacity $transition-fast;

  input[type="checkbox"] { width: 15px; height: 15px; accent-color: var(--color-primary); cursor: pointer; }
}

.card-drag {
  position: absolute; top: 6px; right: 6px; z-index: 2;
  opacity: 0; transition: opacity $transition-fast;
  font-size: 14px; color: var(--color-text-muted); cursor: grab; line-height: 1;
}

.card-thumb {
  width: 100%;
  background: var(--color-bg);
  transition: transform 0.3s ease;
  display: block;

  img { width: 100%; height: auto; display: block; }
}

.thumb-placeholder {
  width: 100%; padding-top: 141%;
  background: repeating-linear-gradient(45deg, var(--color-bg) 0, var(--color-bg) 4px, var(--color-border) 4px, var(--color-border) 5px);
}

.card-num {
  padding: 5px 0 6px;
  text-align: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--color-text-muted);
}

// ── Spinner ───────────────────────────────────────────────────────────────────
.spinner {
  display: inline-block; border-radius: 50%; animation: spin 0.6s linear infinite; flex-shrink: 0;
  width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.35); border-top-color: white;

  &.sm { width: 12px; height: 12px; }
  &.lg { width: 28px; height: 28px; border-color: var(--color-border); border-top-color: var(--color-primary); }
}

.export-spinner { border-color: rgba(255,255,255,0.35); border-top-color: white; }

@keyframes spin { to { transform: rotate(360deg); } }

// ── Buttons ───────────────────────────────────────────────────────────────────
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 5px;
  height: 34px; padding: 0 14px; border-radius: $radius-md;
  font-size: 13px; font-weight: 500; font-family: inherit; cursor: pointer;
  transition: all $transition-fast; border: 1.5px solid transparent; white-space: nowrap;

  &-primary {
    background: var(--color-primary); color: white; border-color: var(--color-primary);
    &:hover:not(:disabled) { background: var(--color-primary-hover, #4c59c9); }
  }
  &-ghost {
    background: transparent; color: var(--color-text-secondary); border-color: var(--color-border);
    &:hover:not(:disabled) { color: var(--color-text-primary); }
  }
  &-sm { height: 32px; padding: 0 12px; font-size: 12px; }
  &:disabled { opacity: 0.45; cursor: not-allowed; }
}

// ── Modal forms ───────────────────────────────────────────────────────────────
.modal-tabs {
  display: flex; gap: 16px; margin-bottom: 20px;
  border-bottom: 1px solid var(--color-border); padding-bottom: 0;
}

.mtab {
  padding: 8px 0; font-size: 14px; font-weight: 500;
  color: var(--color-text-secondary); background: none; border: none;
  border-bottom: 2px solid transparent; cursor: pointer;
  transition: color $transition-fast, border-color $transition-fast;
  margin-bottom: -1px;

  &.active { color: var(--color-primary); border-bottom-color: var(--color-primary); }
}

.modal-form { display: flex; flex-direction: column; gap: 10px; }

.form-label { font-size: 12px; font-weight: 500; color: var(--color-text-secondary); margin-bottom: 2px; }

.form-input {
  height: 38px; padding: 0 12px;
  border: 1.5px solid var(--color-border); border-radius: $radius-md;
  font-size: 13px; color: var(--color-text-primary); background: var(--color-bg);
  outline: none; &:focus { border-color: var(--color-primary); }
}

.form-range { width: 100%; accent-color: var(--color-primary); height: 4px; cursor: pointer; }
.form-color { width: 40px; height: 30px; border: 1.5px solid var(--color-border); border-radius: $radius-md; cursor: pointer; padding: 2px; }

.img-drop {
  border: 1.5px dashed var(--color-border); border-radius: $radius-md;
  padding: 32px; text-align: center; cursor: pointer;
  font-size: 13px; color: var(--color-text-muted); transition: border-color $transition-fast;
  &:hover { border-color: var(--color-primary); }
  &.has-img { padding: 8px; }
}

.wm-preview-img { max-width: 100%; max-height: 120px; object-fit: contain; }

.enc-notice {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 14px; background: #fffbeb; border: 1px solid #fde68a; border-radius: $radius-md;
  font-size: 13px; color: #92400e; line-height: 1.5;
}
</style>
