<template>
  <div class="scan-wrap">
    <!-- Hidden file inputs (always present) -->
    <input ref="imgInputRef" type="file" accept="image/*" multiple style="display:none" @change="onImgInput" />
    <input ref="pdfInputRef" type="file" accept=".pdf" style="display:none" @change="onPdfInput" />

    <!-- ① Empty state: drop zone (mirrors PdfEditor) -->
    <div
      v-if="pages.length === 0 && !isLoading"
      class="drop-zone"
      :class="{ active: isDragOver }"
      @dragover.prevent="isDragOver = true"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <svg class="dz-icon" viewBox="0 0 40 40" fill="none">
        <rect x="3" y="5" width="20" height="28" rx="2" stroke="currentColor" stroke-width="1.4"/>
        <path d="M7 13h12M7 18h8M7 23h10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        <rect x="20" y="20" width="16" height="14" rx="1.5" fill="var(--color-bg)" stroke="currentColor" stroke-width="1.4"/>
        <path d="M24 29l4-5 4 5M28 28v-4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <p class="dz-title">拖入图片或 PDF 文件</p>
      <p class="dz-sub">或使用下方按钮选择文件</p>
      <div class="dz-actions">
        <button class="dz-btn" @click.stop="imgInputRef?.click()">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><rect x="1" y="3" width="14" height="10" rx="1.5"/><circle cx="5.5" cy="7" r="1.5"/><path d="M1 11l4-4 3 3 2-2 4 4"/></svg>
          选择图片
        </button>
        <button class="dz-btn" @click.stop="pdfInputRef?.click()">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M9 1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V5L9 1z"/><polyline points="9 1 9 5 13 5"/></svg>
          选择 PDF
        </button>
        <button class="dz-btn" @click.stop="openCamera">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M1 5.5A1.5 1.5 0 0 1 2.5 4H4l1-2h6l1 2h1.5A1.5 1.5 0 0 1 15 5.5v7A1.5 1.5 0 0 1 13.5 14h-11A1.5 1.5 0 0 1 1 12.5v-7z"/><circle cx="8" cy="9" r="2.5"/></svg>
          拍摄
        </button>
      </div>
    </div>

    <!-- Loading overlay when rendering PDF pages -->
    <div v-if="isLoading" class="dz-loading">
      <span class="spinner lg" />
      <p>渲染页面中…</p>
    </div>

    <!-- ② Has pages: slim toolbar + strip + panel -->
    <template v-if="pages.length > 0">
      <!-- Slim toolbar (mirrors PdfEditor toolbar style) -->
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="page-badge">{{ pages.length }} 页</span>
        </div>
        <div class="toolbar-center">
          <button class="tbtn" title="添加图片" @click="imgInputRef?.click()">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><rect x="1" y="3" width="14" height="10" rx="1.5"/><circle cx="5.5" cy="7" r="1.5"/><path d="M1 11l4-4 3 3 2-2 4 4"/></svg>
          </button>
          <button class="tbtn" title="添加 PDF" @click="pdfInputRef?.click()">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M9 1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V5L9 1z"/><polyline points="9 1 9 5 13 5"/></svg>
          </button>
          <button class="tbtn" title="拍摄" @click="openCamera">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M1 5.5A1.5 1.5 0 0 1 2.5 4H4l1-2h6l1 2h1.5A1.5 1.5 0 0 1 15 5.5v7A1.5 1.5 0 0 1 13.5 14h-11A1.5 1.5 0 0 1 1 12.5v-7z"/><circle cx="8" cy="9" r="2.5"/></svg>
          </button>
        </div>
        <div class="toolbar-right">
          <span class="done-info">已增强 {{ doneCount }} / {{ pages.length }}</span>
          <button class="btn btn-ghost btn-sm" :disabled="isProcessingAll" @click="processAll">
            <span v-if="isProcessingAll" class="spinner sm" />
            全部处理
          </button>
          <button class="btn btn-primary btn-sm" :disabled="doneCount === 0" @click="exportScanPdf">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M6 1v7M3 5.5l3 3 3-3M1 9.5v.5a1 1 0 001 1h8a1 1 0 001-1v-.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
            导出 PDF
          </button>
          <button class="tbtn danger" title="清除全部" @click="clear">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M2 4h12M5 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1M6 7v5M10 7v5M3 4l1 9a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l1-9"/></svg>
          </button>
        </div>
      </div>

      <!-- Horizontal thumb strip -->
      <div class="thumb-strip">
        <div
          v-for="(page, idx) in pages"
          :key="page.id"
          class="thumb-item"
          :class="{ active: idx === currentIndex }"
          @click="selectPage(idx)"
        >
          <img :src="page.processedDataUrl || page.thumbnailDataUrl" :alt="page.name" />
          <span class="thumb-num">{{ idx + 1 }}</span>
          <span class="thumb-status" :class="page.status" :title="page.errorMsg || undefined" />
          <button class="thumb-del" @click.stop="removePage(page.id)" title="移除">×</button>
        </div>
      </div>

      <!-- Enhancement panel -->
      <div class="enhance-panel">
        <!-- Preview -->
        <div class="preview-col">
          <div class="preview-toggle">
            <button class="toggle-btn" :class="{ active: showOriginal }" @click="showOriginal = true">原图</button>
            <button class="toggle-btn" :class="{ active: !showOriginal }" @click="showOriginal = false">增强后</button>
          </div>
          <div class="preview-frame">
            <img v-if="previewSrc" :src="previewSrc" class="preview-img" :key="previewSrc" />
            <div v-else class="preview-empty">
              <svg viewBox="0 0 40 40" fill="none"><rect x="4" y="6" width="22" height="28" rx="2" stroke="currentColor" stroke-width="1.3"/><path d="M8 14h14M8 19h10M8 24h12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
              <p>选择页面预览</p>
            </div>
          </div>
          <div class="preview-status" v-if="currentPage">
            <template v-if="currentPage.status === 'processing'">
              <span class="spinner sm" />处理中…
            </template>
            <template v-else-if="currentPage.status === 'done'">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2.5 7l3 3 6-6" stroke="#10b981" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
              已处理
            </template>
            <template v-else-if="currentPage.status === 'error'">
              <span style="color:#ef4444">处理失败</span>
            </template>
            <template v-else>
              <button class="btn-process" @click="processCurrentPage">处理当前页（高清）</button>
            </template>
          </div>
        </div>

        <!-- Controls -->
        <div class="controls-col">
          <!-- 实时预览开关 -->
          <button
            class="live-preview-btn"
            :class="{ active: livePreviewEnabled }"
            @click="toggleLivePreview"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="8" cy="8" r="5"/>
              <path d="M8 3v2M8 11v2M3 8h2M11 8h2"/>
              <circle cx="8" cy="8" r="2" fill="currentColor" stroke="none"/>
            </svg>
            <span v-if="isLiveProcessing" class="spinner sm" style="margin: 0" />
            {{ livePreviewEnabled ? (isLiveProcessing ? '预览更新中…' : '实时预览 开') : '实时预览 关' }}
          </button>

          <div class="ctrl-section">
            <div class="ctrl-label">预设</div>
            <div class="preset-pills">
              <button
                v-for="(cfg, key) in PRESETS"
                :key="key"
                class="preset-pill"
                :class="{ active: activePreset === key }"
                @click="applyPreset(key as keyof typeof PRESETS)"
              >{{ PRESET_LABELS[key as keyof typeof PRESETS] }}</button>
            </div>
          </div>

          <div class="ctrl-section">
            <div v-for="slider in SLIDERS" :key="slider.key" class="slider-row">
              <span class="slider-label">{{ slider.label }}</span>
              <input
                v-model.number="settings[slider.key as keyof typeof settings]"
                type="range" :min="slider.min" :max="slider.max"
                class="slider" @input="activePreset = null"
              />
              <span class="slider-val">{{ settings[slider.key as keyof typeof settings] }}</span>
              <button class="reset-btn" @click="(settings[slider.key as keyof typeof settings] as unknown) = 0; activePreset = null" title="重置">↺</button>
            </div>
          </div>

          <div class="ctrl-section">
            <div class="ctrl-label">
              DPI 导出质量
              <span class="info-icon" :title="DPI_TIP">ⓘ</span>
            </div>
            <div class="dpi-pills">
              <button v-for="d in [150, 200, 300]" :key="d" class="dpi-pill" :class="{ active: dpi === d }" @click="dpi = d">
                {{ d }}{{ d === 150 ? ' 低' : d === 200 ? ' 标准' : ' 高' }}
              </button>
            </div>
          </div>

          <div class="ctrl-section">
            <label class="bw-toggle">
              <input v-model="settings.binarize" type="checkbox" @change="activePreset = null" />
              黑白模式（Sauvola 自适应二值化）
            </label>
          </div>
        </div>
      </div>
    </template>

    <!-- Camera modal -->
    <el-dialog v-model="showCamera" title="拍摄" width="480px" :append-to-body="true" @close="stopCamera">
      <div class="camera-wrap">
        <video ref="videoRef" class="camera-video" autoplay playsinline />
        <canvas ref="captureCanvasRef" style="display:none" />
      </div>
      <template #footer>
        <button class="btn btn-ghost" @click="showCamera = false">取消</button>
        <button class="btn btn-primary" @click="capturePhoto">拍照</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useScanQueue } from '@/composables/useScanQueue'
import { useImageEnhancer, PRESETS, DEFAULT_SETTINGS, type EnhancementSettings } from '@/composables/useImageEnhancer'
import { PDFDocument } from 'pdf-lib'

const { pages, currentIndex, currentPage, doneCount, addImages, addPdf, renderPdfPageAtDpi, removePage, clear, selectPage } = useScanQueue()
const { processDataUrl } = useImageEnhancer()

// ── File inputs ───────────────────────────────────────────────────────────────
const imgInputRef = ref<HTMLInputElement | null>(null)
const pdfInputRef = ref<HTMLInputElement | null>(null)
const isLoading = ref(false)

const PRESET_LABELS = { document: '文档', photo: '照片', bw: '黑白' }
const DPI_TIP = '150 = 轻量分享；200 = 标准打印；300 = 高精度存档'
const SLIDERS = [
  { key: 'brightness', label: '亮度',  min: -100, max: 100 },
  { key: 'contrast',   label: '对比度', min: -100, max: 100 },
  { key: 'sharpen',    label: '锐化',  min: 0,    max: 100 },
  { key: 'denoise',    label: '去噪',  min: 0,    max: 100 },
]

async function onImgInput(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files?.length) { isLoading.value = true; await addImages([...files]); isLoading.value = false }
  ;(e.target as HTMLInputElement).value = ''
}

async function onPdfInput(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) { isLoading.value = true; await addPdf(file); isLoading.value = false }
  ;(e.target as HTMLInputElement).value = ''
}

// ── Drop zone ─────────────────────────────────────────────────────────────────
const isDragOver = ref(false)

function onDragLeave(e: DragEvent) {
  if (!(e.currentTarget as Element).contains(e.relatedTarget as Node)) isDragOver.value = false
}

async function onDrop(e: DragEvent) {
  e.preventDefault(); isDragOver.value = false
  const files = [...(e.dataTransfer?.files || [])]
  const images = files.filter(f => f.type.startsWith('image/'))
  const pdfs = files.filter(f => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'))
  if (!images.length && !pdfs.length) { ElMessage.warning('请拖入图片或 PDF 文件'); return }
  isLoading.value = true
  try {
    if (images.length) await addImages(images)
    for (const pdf of pdfs) await addPdf(pdf)
  } finally {
    isLoading.value = false
  }
}

// ── Settings ──────────────────────────────────────────────────────────────────
const settings = reactive<EnhancementSettings>({ ...DEFAULT_SETTINGS })
const activePreset = ref<keyof typeof PRESETS | null>(null)
const dpi = ref<150 | 200 | 300>(200)
const showOriginal = ref(false)

function applyPreset(key: keyof typeof PRESETS) {
  activePreset.value = key
  Object.assign(settings, PRESETS[key])
}

// ── Live preview ──────────────────────────────────────────────────────────────
const livePreviewEnabled = ref(false)
const livePreviewUrl = ref<string | null>(null)
const isLiveProcessing = ref(false)
let _liveTimer: ReturnType<typeof setTimeout> | null = null

function triggerLivePreview() {
  if (!livePreviewEnabled.value || !currentPage.value) return
  if (_liveTimer) clearTimeout(_liveTimer)
  _liveTimer = setTimeout(async () => {
    const page = currentPage.value
    if (!page) return
    isLiveProcessing.value = true
    try {
      livePreviewUrl.value = await processDataUrl(page.thumbnailDataUrl, { ...settings })
    } catch { /* ignore */ } finally {
      isLiveProcessing.value = false
    }
  }, 400)
}

watch(settings, triggerLivePreview, { deep: true })
watch(currentIndex, () => { livePreviewUrl.value = null; if (livePreviewEnabled.value) triggerLivePreview() })

function toggleLivePreview() {
  livePreviewEnabled.value = !livePreviewEnabled.value
  if (livePreviewEnabled.value) { showOriginal.value = false; triggerLivePreview() }
  else livePreviewUrl.value = null
}

const previewSrc = computed(() => {
  if (!currentPage.value) return null
  if (showOriginal.value) return currentPage.value.originalDataUrl
  if (livePreviewEnabled.value && livePreviewUrl.value) return livePreviewUrl.value
  if (currentPage.value.processedDataUrl) return currentPage.value.processedDataUrl
  return currentPage.value.originalDataUrl
})

// ── Processing ────────────────────────────────────────────────────────────────
async function processCurrentPage() {
  const page = currentPage.value
  if (!page || page.status === 'processing') return
  page.status = 'processing'
  try {
    let src = page.originalDataUrl
    if (page.pdfSource) src = await renderPdfPageAtDpi(page, dpi.value)
    page.processedDataUrl = await processDataUrl(src, { ...settings })
    page.status = 'done'
    showOriginal.value = false
  } catch (err) {
    page.status = 'error'
    page.errorMsg = (err as Error).message
  }
}

const isProcessingAll = ref(false)

async function processAll() {
  isProcessingAll.value = true
  for (let i = 0; i < pages.value.length; i++) {
    selectPage(i)
    await processCurrentPage()
  }
  isProcessingAll.value = false
}

// ── Export ────────────────────────────────────────────────────────────────────
async function exportScanPdf() {
  const doc = await PDFDocument.create()
  for (const page of pages.value) {
    const src = page.processedDataUrl || page.originalDataUrl
    const resp = await fetch(src)
    const bytes = new Uint8Array(await resp.arrayBuffer())
    const img = src.includes('image/png') ? await doc.embedPng(bytes) : await doc.embedJpg(bytes)
    const pdfPage = doc.addPage([img.width, img.height])
    pdfPage.drawImage(img, { x: 0, y: 0, width: img.width, height: img.height })
  }
  const bytes = await doc.save()
  const url = URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: 'scan-export.pdf' })
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}

// ── Camera ────────────────────────────────────────────────────────────────────
const showCamera = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)
const captureCanvasRef = ref<HTMLCanvasElement | null>(null)
let cameraStream: MediaStream | null = null

async function openCamera() {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    showCamera.value = true
    setTimeout(() => { if (videoRef.value) videoRef.value.srcObject = cameraStream }, 100)
  } catch {
    ElMessage.error('无法访问摄像头，请检查权限')
  }
}

function stopCamera() { cameraStream?.getTracks().forEach(t => t.stop()); cameraStream = null }

async function capturePhoto() {
  const video = videoRef.value, canvas = captureCanvasRef.value
  if (!video || !canvas) return
  canvas.width = video.videoWidth; canvas.height = video.videoHeight
  canvas.getContext('2d')!.drawImage(video, 0, 0)
  const dataUrl = canvas.toDataURL('image/jpeg', 0.92)
  showCamera.value = false; stopCamera()
  await addImages([dataUrlToFile(dataUrl, `photo-${Date.now()}.jpg`)])
}

function dataUrlToFile(dataUrl: string, name: string): File {
  const [head, b64] = dataUrl.split(','), mime = head.match(/:(.*?);/)![1]
  const bstr = atob(b64), u8 = new Uint8Array(bstr.length)
  for (let i = 0; i < bstr.length; i++) u8[i] = bstr.charCodeAt(i)
  return new File([u8], name, { type: mime })
}
</script>

<style scoped lang="scss">
.scan-wrap {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 104px);
  background: var(--color-bg);
}

// ── Drop zone (identical to PdfEditor) ───────────────────────────────────────
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
.dz-sub { font-size: 13px; color: var(--color-text-muted); margin-bottom: 16px; }

.dz-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.dz-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 32px;
  padding: 0 14px;
  border: 1.5px solid var(--color-border);
  border-radius: $radius-md;
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    color: var(--color-text-primary);
    border-color: var(--color-primary);
    color: var(--color-primary);
    background: var(--color-primary-subtle);
  }
}

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

// ── Toolbar (identical to PdfEditor) ─────────────────────────────────────────
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
}

.toolbar-left { flex-shrink: 0; }
.toolbar-center { display: flex; align-items: center; gap: 4px; flex: 1; justify-content: center; }
.toolbar-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

.page-badge {
  font-size: 11px; font-weight: 500;
  color: var(--color-text-muted);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 1px 8px;
}

.done-info { font-size: 12px; color: var(--color-text-muted); }

.tbtn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border: 1.5px solid var(--color-border); border-radius: $radius-md;
  background: transparent; color: var(--color-text-secondary);
  cursor: pointer; transition: all $transition-fast;
  svg { width: 14px; height: 14px; }

  &:hover { color: var(--color-text-primary); border-color: var(--color-border-strong, #d1d5db); }
  &.danger:hover { color: #ef4444; border-color: #ef4444; }
}

// ── Thumb strip ───────────────────────────────────────────────────────────────
.thumb-strip {
  display: flex; gap: 8px; padding: 12px 20px;
  overflow-x: auto; border-bottom: 1px solid var(--color-border);
  background: var(--color-surface); scrollbar-width: thin;

  &::-webkit-scrollbar { height: 4px; }
  &::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 2px; }
}

.thumb-item {
  position: relative; flex-shrink: 0; width: 64px;
  border: 1.5px solid var(--color-border); border-radius: $radius-md;
  overflow: hidden; cursor: pointer; transition: border-color $transition-fast;

  &.active { border-color: var(--color-primary); }
  &:hover:not(.active) { border-color: var(--color-border-strong, #d1d5db); }
  img { width: 100%; height: 80px; object-fit: cover; display: block; }
}

.thumb-num {
  display: block; text-align: center;
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  color: var(--color-text-muted); padding: 2px 0 3px;
}

.thumb-status {
  position: absolute; top: 4px; left: 4px;
  width: 8px; height: 8px; border-radius: 50%; background: var(--color-border);
  &.done { background: #10b981; }
  &.processing { background: var(--color-primary); animation: blink 1s ease infinite; }
  &.error { background: #ef4444; }
}

@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.25; } }

.thumb-del {
  position: absolute; top: 2px; right: 2px;
  width: 16px; height: 16px; border-radius: 50%;
  background: rgba(0,0,0,0.5); border: none; color: white;
  font-size: 11px; cursor: pointer; opacity: 0; transition: opacity $transition-fast;
  display: flex; align-items: center; justify-content: center;
  .thumb-item:hover & { opacity: 1; }
}

// ── Enhance panel ─────────────────────────────────────────────────────────────
.enhance-panel {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 300px;
  @media (max-width: 768px) { grid-template-columns: 1fr; }
}

.preview-col {
  display: flex; flex-direction: column; gap: 10px;
  border-right: 1px solid var(--color-border); padding: 16px;
}

.preview-toggle {
  display: flex; border: 1px solid var(--color-border);
  border-radius: $radius-md; overflow: hidden; width: fit-content;
}

.toggle-btn {
  padding: 5px 14px; font-size: 12px; font-weight: 500;
  border: none; background: transparent; color: var(--color-text-secondary);
  cursor: pointer; transition: all $transition-fast;
  &.active { background: var(--color-primary); color: white; }
}

.preview-frame {
  flex: 1; background: var(--color-bg);
  border: 1px solid var(--color-border); border-radius: $radius-md;
  overflow: hidden; display: flex; align-items: center; justify-content: center; min-height: 300px;
}

.preview-img {
  max-width: 100%; max-height: 520px; object-fit: contain; display: block;
  animation: fadeIn 0.15s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.preview-empty {
  text-align: center; color: var(--color-text-muted);
  svg { width: 40px; height: 40px; margin: 0 auto 10px; display: block; }
  p { font-size: 13px; }
}

.preview-status {
  display: flex; align-items: center; gap: 6px; font-size: 12px;
  color: var(--color-text-muted); height: 24px;
}

.btn-process {
  height: 26px; padding: 0 12px; border-radius: $radius-md;
  font-size: 12px; font-weight: 500; font-family: inherit;
  border: 1.5px solid var(--color-primary); color: var(--color-primary);
  background: var(--color-primary-subtle); cursor: pointer;
  transition: all $transition-fast;
  &:hover { background: var(--color-primary); color: white; }
}

.live-preview-btn {
  display: flex; align-items: center; justify-content: center; gap: 7px;
  width: 100%; height: 36px; border-radius: $radius-md;
  font-size: 13px; font-weight: 600; font-family: inherit; cursor: pointer;
  border: 1.5px solid var(--color-border);
  background: var(--color-bg); color: var(--color-text-secondary);
  transition: all $transition-fast;

  &:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
    background: var(--color-primary-subtle);
  }

  &.active {
    border-color: var(--color-primary);
    background: var(--color-primary);
    color: white;

    &:hover { background: var(--color-primary-hover, #4c59c9); }
  }
}

.controls-col { padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; }

.ctrl-section { display: flex; flex-direction: column; gap: 8px; }

.ctrl-label {
  font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--color-text-muted);
  display: flex; align-items: center; gap: 5px;
}

.info-icon { cursor: help; font-size: 13px; }

.preset-pills { display: flex; gap: 6px; }

.preset-pill {
  padding: 4px 12px; border: 1.5px solid var(--color-border); border-radius: 20px;
  font-size: 12px; font-weight: 500; background: transparent; color: var(--color-text-secondary);
  cursor: pointer; transition: all $transition-fast;
  &.active { border-color: var(--color-primary); color: var(--color-primary); background: var(--color-primary-subtle); }
  &:hover:not(.active) { border-color: var(--color-border-strong, #d1d5db); }
}

.dpi-pills { display: flex; gap: 6px; }

.dpi-pill {
  padding: 4px 10px; border: 1.5px solid var(--color-border); border-radius: $radius-md;
  font-size: 12px; background: transparent; color: var(--color-text-secondary);
  cursor: pointer; transition: all $transition-fast;
  &.active { border-color: var(--color-primary); color: var(--color-primary); background: var(--color-primary-subtle); }
}

.slider-row {
  display: grid; grid-template-columns: 50px 1fr 30px 20px; align-items: center; gap: 8px;
}

.slider-label { font-size: 12px; color: var(--color-text-secondary); }
.slider { accent-color: var(--color-primary); height: 3px; cursor: pointer; width: 100%; }
.slider-val { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--color-text-muted); text-align: right; }
.reset-btn { background: none; border: none; cursor: pointer; color: var(--color-text-muted); font-size: 13px; &:hover { color: var(--color-text-primary); } }

.bw-toggle {
  display: flex; align-items: center; gap: 7px; font-size: 13px;
  color: var(--color-text-secondary); cursor: pointer;
  input { width: 15px; height: 15px; accent-color: var(--color-primary); }
}

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

// ── Spinners ──────────────────────────────────────────────────────────────────
.spinner {
  display: inline-block; border-radius: 50%; animation: spin 0.6s linear infinite; flex-shrink: 0;
  width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.35); border-top-color: white;

  &.sm { width: 12px; height: 12px; border-color: var(--color-border); border-top-color: var(--color-primary); }
  &.lg { width: 28px; height: 28px; border-color: var(--color-border); border-top-color: var(--color-primary); }
}
@keyframes spin { to { transform: rotate(360deg); } }

// ── Camera ────────────────────────────────────────────────────────────────────
.camera-wrap { display: flex; justify-content: center; }
.camera-video { width: 100%; max-height: 320px; object-fit: cover; border-radius: $radius-md; background: #000; }
</style>
