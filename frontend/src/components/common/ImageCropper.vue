<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'

const props = withDefaults(defineProps<{
  modelValue: boolean
  src: string
  circular?: boolean
  aspectRatio?: number   // undefined = free crop
  outputWidth?: number   // max pixel width of exported image
  displayHint?: string   // 显示区域提示，如 "封面 全宽×132px"
}>(), {
  circular: false,
  outputWidth: 800,
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'confirm', dataUrl: string): void
}>()

const imageRef = ref<HTMLImageElement | null>(null)
const naturalSize = ref<{ w: number; h: number } | null>(null)
let cropper: Cropper | null = null

function init() {
  if (!imageRef.value) return
  destroy()
  naturalSize.value = null
  cropper = new Cropper(imageRef.value, {
    aspectRatio: props.circular ? 1 : (props.aspectRatio ?? NaN),
    viewMode: 1,
    dragMode: 'move',
    autoCropArea: props.circular ? 0.82 : 0.78,
    guides: true,
    center: true,
    highlight: false,
    background: false,
    cropBoxMovable: true,
    cropBoxResizable: !props.circular,
    toggleDragModeOnDblclick: false,
    minContainerHeight: 280,
    ready() {
      // 图片加载完成后再读取原始尺寸，避免读到 0×0
      if (imageRef.value) {
        naturalSize.value = { w: imageRef.value.naturalWidth, h: imageRef.value.naturalHeight }
      }
    },
  })
}

function destroy() {
  cropper?.destroy()
  cropper = null
}

watch(() => props.modelValue, (v) => {
  if (v) nextTick(init)
  else destroy()
})

function zoom(step: number) { cropper?.zoom(step) }
function rotate(deg: number) { cropper?.rotate(deg) }
function reset() { cropper?.reset() }

function confirm() {
  if (!cropper) return
  const raw = cropper.getCroppedCanvas({
    maxWidth: props.outputWidth,
    maxHeight: props.outputWidth,
    imageSmoothingEnabled: true,
    imageSmoothingQuality: 'high',
  })
  let dataUrl: string
  if (props.circular) {
    const sz = Math.min(raw.width, raw.height)
    const c = document.createElement('canvas')
    c.width = c.height = sz
    const ctx = c.getContext('2d')!
    ctx.beginPath()
    ctx.arc(sz / 2, sz / 2, sz / 2, 0, Math.PI * 2)
    ctx.clip()
    ctx.drawImage(raw, 0, 0, sz, sz)
    dataUrl = c.toDataURL('image/png', 1)
  } else {
    dataUrl = raw.toDataURL('image/jpeg', 0.88)
  }
  emit('confirm', dataUrl)
  emit('update:modelValue', false)
}

function cancel() {
  emit('update:modelValue', false)
}

onBeforeUnmount(destroy)
</script>

<template>
  <Teleport to="body">
    <Transition name="crop-fade">
      <div v-if="modelValue" class="crop-overlay" @mousedown.self="cancel">
        <div class="crop-panel" :class="{ 'is-round': circular }">

          <!-- Header -->
          <div class="crop-hd">
            <div class="crop-hd-left">
              <svg class="crop-hd-icon" viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                <rect x="3.5" y="3.5" width="9" height="9" rx="0.5"/>
                <line x1="0.5" y1="3.5" x2="3.5" y2="3.5"/><line x1="12.5" y1="3.5" x2="15.5" y2="3.5"/>
                <line x1="3.5" y1="0.5" x2="3.5" y2="3.5"/><line x1="12.5" y1="0.5" x2="12.5" y2="3.5"/>
                <line x1="0.5" y1="12.5" x2="3.5" y2="12.5"/><line x1="12.5" y1="12.5" x2="15.5" y2="12.5"/>
                <line x1="3.5" y1="12.5" x2="3.5" y2="15.5"/><line x1="12.5" y1="12.5" x2="12.5" y2="15.5"/>
              </svg>
              <span class="crop-title">{{ circular ? '裁剪头像' : '调整封面' }}</span>
              <span v-if="naturalSize" class="crop-dim">{{ naturalSize.w }}×{{ naturalSize.h }}</span>
            </div>
            <button class="crop-close" @click="cancel">
              <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/>
              </svg>
            </button>
          </div>

          <!-- Canvas -->
          <div class="crop-canvas">
            <img ref="imageRef" :src="src" class="crop-img" alt="" />
            <div v-if="displayHint" class="crop-area-badge">
              <svg viewBox="0 0 14 14" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="1" y="4" width="12" height="6" rx="1"/>
                <line x1="4" y1="4" x2="4" y2="1"/><line x1="10" y1="4" x2="10" y2="1"/>
                <line x1="1" y1="7" x2="13" y2="7" stroke-dasharray="2 1.5"/>
              </svg>
              {{ displayHint }}
            </div>
          </div>

          <!-- Controls -->
          <div class="crop-ft">
            <div class="crop-tools">
              <button class="ct-btn" data-tip="缩小" @click="zoom(-0.12)">
                <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                  <circle cx="6.5" cy="6.5" r="5"/><line x1="3.5" y1="6.5" x2="9.5" y2="6.5"/>
                  <line x1="12.5" y1="12.5" x2="15" y2="15"/>
                </svg>
              </button>
              <button class="ct-btn" data-tip="放大" @click="zoom(0.12)">
                <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                  <circle cx="6.5" cy="6.5" r="5"/><line x1="3.5" y1="6.5" x2="9.5" y2="6.5"/>
                  <line x1="6.5" y1="3.5" x2="6.5" y2="9.5"/><line x1="12.5" y1="12.5" x2="15" y2="15"/>
                </svg>
              </button>
              <span class="ct-sep"/>
              <button class="ct-btn" data-tip="向左旋转 90°" @click="rotate(-90)">
                <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3.5 9.5A5 5 0 1 0 3.5 5.5"/><polyline points="1 7.5 3.5 5.5 6 7.5"/>
                </svg>
              </button>
              <button class="ct-btn" data-tip="向右旋转 90°" @click="rotate(90)">
                <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12.5 9.5A5 5 0 1 1 12.5 5.5"/><polyline points="15 7.5 12.5 5.5 10 7.5"/>
                </svg>
              </button>
              <span class="ct-sep"/>
              <button class="ct-btn" data-tip="重置" @click="reset">
                <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 8a6 6 0 1 0 1.5-3.9"/><polyline points="2 3 2 7 6 7"/>
                </svg>
              </button>
            </div>
            <div class="crop-actions">
              <button class="crop-cancel" @click="cancel">取消</button>
              <button class="crop-confirm" @click="confirm">确认</button>
            </div>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped lang="scss">
// ── 遮罩层 ────────────────────────────────────────────
.crop-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  background: rgba(0, 0, 0, 0.62);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

// ── 面板 ──────────────────────────────────────────────
.crop-panel {
  background: var(--color-surface, #fff);
  border-radius: 12px;
  overflow: hidden;
  width: 100%;
  max-width: 560px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 2px 8px rgba(0, 0, 0, 0.12);
  animation: crop-panel-in 0.22s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

@keyframes crop-panel-in {
  from { opacity: 0; transform: scale(0.95) translateY(12px); }
  to   { opacity: 1; transform: none; }
}

// ── 头部 ──────────────────────────────────────────────
.crop-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--color-border, #e8eaed);
  flex-shrink: 0;
}

.crop-hd-left {
  display: flex;
  align-items: center;
  gap: 7px;
}

.crop-hd-icon {
  color: var(--color-text-muted, #9ca3af);
  flex-shrink: 0;
}

.crop-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary, #1a1d23);
  letter-spacing: 0.01em;
}

.crop-dim {
  font-size: 11px;
  color: var(--color-text-muted, #9ca3af);
  font-variant-numeric: tabular-nums;
  font-family: $font-mono, monospace;
  margin-left: 2px;
}

.crop-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px; height: 26px;
  border: none;
  background: none;
  color: var(--color-text-muted, #9ca3af);
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.12s, color 0.12s;
  &:hover {
    background: var(--color-surface-hover, #f3f4f6);
    color: var(--color-text-primary, #1a1d23);
  }
}

// ── 画布区 ────────────────────────────────────────────
.crop-canvas {
  height: 320px;
  background: #0e1117;
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
}

.crop-img {
  display: block;
  max-width: 100%;
  opacity: 0; // cropperjs 接管显示
}

.crop-area-badge {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 99px;
  background: rgba(10, 12, 20, 0.72);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.92);
  font-size: 11.5px;
  font-weight: 500;
  white-space: nowrap;
  pointer-events: none;
  letter-spacing: 0.01em;
  svg { opacity: 0.75; flex-shrink: 0; }
}

// 圆形裁切预览 (仅显示效果，输出由 canvas clip 保证)
.is-round :deep(.cropper-view-box),
.is-round :deep(.cropper-face) {
  border-radius: 50%;
}

// 覆盖 cropperjs 默认样式，统一为项目主色
:deep(.cropper-container) { width: 100% !important; }
:deep(.cropper-modal) { background: #0e1117; opacity: 0.6; }
:deep(.cropper-dashed) { border-color: rgba(90, 103, 216, 0.35); }
:deep(.cropper-line) { background-color: rgba(90, 103, 216, 0.7); }
:deep(.cropper-point) {
  background-color: #5a67d8;
  width: 6px; height: 6px;
  opacity: 1;
  border-radius: 1px;
}
:deep(.cropper-point.point-se) {
  width: 8px; height: 8px;
  border-radius: 2px;
}
:deep(.cropper-view-box) {
  outline: 1.5px solid rgba(90, 103, 216, 0.9);
  outline-offset: 0;
}

// ── 工具栏 ────────────────────────────────────────────
.crop-ft {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-top: 1px solid var(--color-border, #e8eaed);
  gap: 8px;
  flex-shrink: 0;
}

.crop-tools {
  display: flex;
  align-items: center;
  gap: 1px;
  flex: 1;
}

.ct-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border: none;
  background: none;
  color: var(--color-text-muted, #9ca3af);
  cursor: pointer;
  border-radius: 6px;
  flex-shrink: 0;
  transition: background 0.1s, color 0.1s;

  &:hover {
    background: var(--color-surface-hover, #f3f4f6);
    color: var(--color-text-primary, #1a1d23);
  }
  &:active { transform: scale(0.92); }

  // 即时 tooltip（无延迟）
  &[data-tip]::after {
    content: attr(data-tip);
    position: absolute;
    bottom: calc(100% + 5px);
    left: 50%;
    transform: translateX(-50%);
    background: rgba(15, 15, 20, 0.82);
    color: #fff;
    font-size: 11px;
    line-height: 1;
    padding: 4px 7px;
    border-radius: 4px;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.06s;
    z-index: 10;
  }
  &[data-tip]:hover::after { opacity: 1; }
}

.ct-sep {
  display: inline-block;
  width: 1px; height: 14px;
  background: var(--color-border, #e8eaed);
  margin: 0 4px;
  flex-shrink: 0;
}

// ── 操作按钮 ──────────────────────────────────────────
.crop-actions {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
}

.crop-cancel {
  padding: 5px 14px;
  border: 1px solid var(--color-border, #e8eaed);
  background: none;
  color: var(--color-text-secondary, #6b7280);
  font-size: 13px;
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.12s, color 0.12s;
  &:hover { border-color: #9ca3af; color: var(--color-text-primary, #1a1d23); }
}

.crop-confirm {
  padding: 5px 16px;
  border: none;
  background: #5a67d8;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  border-radius: 6px;
  cursor: pointer;
  letter-spacing: 0.01em;
  transition: background 0.12s, box-shadow 0.12s;
  &:hover { background: #4c5abf; box-shadow: 0 2px 8px rgba(90,103,216,0.36); }
  &:active { transform: scale(0.97); }
}

// ── 过渡动画 ──────────────────────────────────────────
.crop-fade-enter-active { transition: opacity 0.18s ease; }
.crop-fade-leave-active { transition: opacity 0.14s ease; }
.crop-fade-enter-from,
.crop-fade-leave-to { opacity: 0; }

// ── 暗色模式 ──────────────────────────────────────────
:global(html.dark) .crop-panel {
  background: #1c1f26;
  box-shadow: 0 20px 60px rgba(0,0,0,0.55), 0 2px 8px rgba(0,0,0,0.25);
}
:global(html.dark) .crop-hd,
:global(html.dark) .crop-ft { border-color: #2d3242; }
:global(html.dark) .ct-sep { background: #2d3242; }
:global(html.dark) .ct-btn:hover { background: rgba(255,255,255,0.07); color: #d1d5db; }
:global(html.dark) .crop-close:hover { background: rgba(255,255,255,0.07); color: #d1d5db; }
:global(html.dark) .crop-cancel {
  border-color: #374151; color: #9ca3af;
  &:hover { border-color: #6b7280; color: #d1d5db; }
}
:global(html.dark) .crop-canvas { background: #060a10; }

// ── 响应式 ───────────────────────────────────────────
@media (max-width: 600px) {
  .crop-canvas { height: 240px; }
  .crop-title { font-size: 12px; }
  .crop-cancel, .crop-confirm { padding: 5px 10px; font-size: 12px; }
}
</style>
