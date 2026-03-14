<template>
  <el-dialog
    v-model="visible"
    :show-close="false"
    width="456px"
    class="cpd-outer"
    destroy-on-close
    align-center
  >
    <template #header>
      <div class="cpd-header">
        <span class="cpd-title">选择封面背景</span>
        <button class="cpd-close" @click="cancel">
          <svg viewBox="0 0 14 14" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <line x1="2" y1="2" x2="12" y2="12" />
            <line x1="12" y1="2" x2="2" y2="12" />
          </svg>
        </button>
      </div>
    </template>

    <div class="cpd-body">
      <!-- 渐变系列 -->
      <div class="cpd-section-label">渐变</div>
      <div class="cpd-grid">
        <button
          v-for="(p, i) in gradients"
          :key="p.id"
          class="cpd-cell"
          :class="{ active: selectedId === p.id }"
          :style="{ '--i': i, backgroundImage: p.image }"
          :title="p.label"
          @click="selectedId = p.id"
        >
          <span class="cpd-lbl">{{ p.label }}</span>
          <Transition name="cpd-check-fade">
            <span v-if="selectedId === p.id" class="cpd-check">
              <svg viewBox="0 0 10 10" width="9" height="9" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="1.5,5 4,7.5 8.5,2.5" />
              </svg>
            </span>
          </Transition>
        </button>
      </div>

      <!-- 图案系列 -->
      <div class="cpd-section-label" style="margin-top: 14px">图案</div>
      <div class="cpd-grid cpd-grid--patterns">
        <button
          v-for="(p, i) in patterns"
          :key="p.id"
          class="cpd-cell"
          :class="{ active: selectedId === p.id }"
          :style="{ '--i': i + 9, backgroundImage: p.image, backgroundSize: p.size, backgroundRepeat: 'repeat' }"
          :title="p.label"
          @click="selectedId = p.id"
        >
          <span class="cpd-lbl">{{ p.label }}</span>
          <Transition name="cpd-check-fade">
            <span v-if="selectedId === p.id" class="cpd-check">
              <svg viewBox="0 0 10 10" width="9" height="9" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="1.5,5 4,7.5 8.5,2.5" />
              </svg>
            </span>
          </Transition>
        </button>
      </div>
    </div>

    <template #footer>
      <div class="cpd-footer">
        <button class="cpd-btn ghost" @click="cancel">取消</button>
        <button class="cpd-btn primary" :disabled="!selectedId" @click="apply">应用</button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ modelValue: boolean }>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  select: [value: { image: string; size: string }]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})

const selectedId = ref<string | null>(null)

interface Preset {
  id: string
  label: string
  image: string
  size?: string
}

function enc(svg: string) {
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`
}

const gradients: Preset[] = [
  { id: 'brand',   label: 'Folio',  image: 'linear-gradient(140deg, #5a67d8 0%, #4c51bf 100%)' },
  { id: 'aurora',  label: '极光',   image: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { id: 'dusk',    label: '暮色',   image: 'linear-gradient(135deg, #f5576c 0%, #f093fb 100%)' },
  { id: 'ocean',   label: '深海',   image: 'linear-gradient(160deg, #0f2027 0%, #2c5364 100%)' },
  { id: 'coral',   label: '珊瑚',   image: 'linear-gradient(135deg, #ff6b6b 0%, #feca57 100%)' },
  { id: 'jade',    label: '翡翠',   image: 'linear-gradient(135deg, #0f9b8e 0%, #32d583 100%)' },
  { id: 'night',   label: '午夜',   image: 'linear-gradient(135deg, #090e1a 0%, #1a237e 100%)' },
  { id: 'flame',   label: '火焰',   image: 'linear-gradient(135deg, #e74c3c 0%, #8e44ad 100%)' },
  { id: 'ink',     label: '烟墨',   image: 'linear-gradient(135deg, #1a1a2e 0%, #4a4a7a 100%)' },
]

const patterns: Preset[] = [
  {
    id: 'grid',
    label: '方格',
    image: enc(`<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><rect width="32" height="32" fill="#1a1d3a"/><path d="M32 0H0V32" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></svg>`),
    size: '32px 32px',
  },
  {
    id: 'dots',
    label: '点阵',
    image: enc(`<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20" fill="#1e2040"/><circle cx="10" cy="10" r="1.5" fill="rgba(90,103,216,0.55)"/></svg>`),
    size: '20px 20px',
  },
  {
    id: 'waves',
    label: '波纹',
    image: enc(`<svg xmlns="http://www.w3.org/2000/svg" width="100" height="30"><rect width="100" height="30" fill="#0f1122"/><path d="M0,15 C12,0 25,0 37,15 S63,30 75,15 S88,0 100,15" fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="1.2"/><path d="M0,22 C12,7 25,7 37,22 S63,37 75,22 S88,7 100,22" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1"/></svg>`),
    size: '100px 30px',
  },
]

const allPresets = [...gradients, ...patterns]

function cancel() {
  selectedId.value = null
  visible.value = false
}

function apply() {
  const p = allPresets.find(x => x.id === selectedId.value)
  if (!p) return
  emit('select', { image: p.image, size: p.size || 'cover' })
  visible.value = false
}
</script>

<style scoped lang="scss">
:deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  padding: 0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--color-border, #e5e7eb);
}

:deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}

:deep(.el-dialog__body) {
  padding: 0;
}

:deep(.el-dialog__footer) {
  padding: 0;
}

// ── Header ─────────────────────────────────────────────
.cpd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--color-border-subtle, #f1f2f4);
}

.cpd-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary, #1a1d23);
  letter-spacing: 0.01em;
}

.cpd-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  background: transparent;
  border-radius: 6px;
  color: var(--color-text-muted, #9ca3af);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;

  &:hover {
    background: var(--color-surface-raised, #f3f4f6);
    color: var(--color-text-primary, #1a1d23);
  }
}

// ── Body ───────────────────────────────────────────────
.cpd-body {
  padding: 16px 18px 6px;
}

.cpd-section-label {
  font-size: 10.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--color-text-muted, #9ca3af);
  margin-bottom: 9px;
}

// ── Grid ───────────────────────────────────────────────
.cpd-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

// ── Cell ───────────────────────────────────────────────
.cpd-cell {
  position: relative;
  height: 64px;
  border-radius: 8px;
  border: 1.5px solid transparent;
  cursor: pointer;
  overflow: hidden;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  outline: none;
  transition: transform 0.13s ease, border-color 0.13s ease, box-shadow 0.13s ease;
  animation: cpd-pop 0.22s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: calc(var(--i, 0) * 0.022s);

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
  }

  &.active {
    border-color: #5a67d8;
    box-shadow: 0 0 0 2px rgba(90, 103, 216, 0.28);
  }
}

@keyframes cpd-pop {
  from { opacity: 0; transform: scale(0.88); }
  to   { opacity: 1; transform: scale(1); }
}

.cpd-lbl {
  position: absolute;
  bottom: 5px;
  left: 7px;
  font-size: 10px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.82);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.55);
  pointer-events: none;
  letter-spacing: 0.01em;
  user-select: none;
}

.cpd-check {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 17px;
  height: 17px;
  border-radius: 50%;
  background: #5a67d8;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.28);
}

.cpd-check-fade-enter-active { transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.12s ease; }
.cpd-check-fade-leave-active { transition: transform 0.1s ease, opacity 0.1s ease; }
.cpd-check-fade-enter-from   { transform: scale(0); opacity: 0; }
.cpd-check-fade-leave-to     { transform: scale(0); opacity: 0; }

// ── Footer ─────────────────────────────────────────────
.cpd-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 20px 16px;
  border-top: 1px solid var(--color-border-subtle, #f1f2f4);
  margin-top: 12px;
}

.cpd-btn {
  display: inline-flex;
  align-items: center;
  padding: 7px 20px;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.13s ease;
  outline: none;

  &.ghost {
    background: transparent;
    border: 1px solid var(--color-border, #e5e7eb);
    color: var(--color-text-secondary, #6b7280);

    &:hover {
      border-color: #9ca3af;
      color: var(--color-text-primary, #1a1d23);
    }
  }

  &.primary {
    background: #5a67d8;
    border: 1px solid #5a67d8;
    color: #fff;

    &:hover:not(:disabled) {
      background: #4c57c8;
    }

    &:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
  }
}
</style>
