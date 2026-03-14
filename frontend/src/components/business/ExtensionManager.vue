<template>
  <div class="ext-manager">
    <!-- 快速预设 —— nav-link 下划线风格 -->
    <div class="preset-row">
      <span class="preset-lead">快速添加</span>
      <button
        v-for="p in PRESETS"
        :key="p.name"
        class="preset-btn"
        :class="{ 'preset-btn--on': isAllAdded(p.exts) }"
        @click="togglePreset(p.exts)"
        :title="p.exts.map(e => '.' + e).join('  ')"
        type="button"
      >{{ p.name }}<em>{{ p.exts.length }}</em></button>
    </div>

    <!-- 已允许后缀标签区 -->
    <div class="tags-wrap" :class="{ 'tags-wrap--empty': !currentExts.length }">
      <template v-if="currentExts.length">
        <span
          v-for="ext in currentExts"
          :key="ext"
          class="ext-tag"
          @click="removeExt(ext)"
          :title="`点击移除 .${ext}`"
        >.{{ ext }}<i class="tag-x">×</i></span>
      </template>
      <div v-else class="empty-warn">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" style="flex-shrink:0">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        当前为空 — 所有文件上传均将被拒绝
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="ext-bar">
      <span class="bar-count" :class="{ 'bar-count--warn': !currentExts.length }">
        {{ currentExts.length ? `已允许 ${currentExts.length} 种格式` : '已禁止所有上传' }}
      </span>
      <div class="bar-actions">
        <input
          v-model="customInput"
          class="custom-in"
          placeholder="自定义后缀（如 epub）"
          maxlength="12"
          @keydown.enter.prevent="addCustom"
        />
        <button class="btn-add" type="button" @click="addCustom" title="添加">+</button>
        <button
          v-if="currentExts.length"
          class="btn-clear"
          type="button"
          @click="clearAll"
        >清空</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const PRESETS = [
  { name: '文档', exts: ['txt', 'md', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'csv', 'json', 'xml'] },
  { name: '图片', exts: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'tif', 'tiff'] },
  { name: '音频', exts: ['mp3', 'wav', 'aac', 'flac', 'm4a'] },
  { name: '视频', exts: ['mp4', 'webm', 'avi', 'mov', 'mkv', 'm4v', 'wmv', 'flv'] },
  { name: '压缩', exts: ['zip', 'rar', '7z'] },
]

const customInput = ref('')

const currentExts = computed<string[]>(() => {
  if (!props.modelValue?.trim()) return []
  return props.modelValue.split(',').map(s => s.trim().toLowerCase()).filter(Boolean)
})

function commit(exts: string[]) {
  emit('update:modelValue', exts.join(','))
}

function removeExt(ext: string) {
  commit(currentExts.value.filter(e => e !== ext))
}

function clearAll() {
  commit([])
}

function addCustom() {
  const raw = customInput.value.trim().toLowerCase().replace(/^\.+/, '')
  if (!raw) return
  if (!currentExts.value.includes(raw)) {
    commit([...currentExts.value, raw])
  }
  customInput.value = ''
}

function isAllAdded(exts: string[]) {
  return exts.every(e => currentExts.value.includes(e))
}

function togglePreset(exts: string[]) {
  if (isAllAdded(exts)) {
    commit(currentExts.value.filter(e => !exts.includes(e)))
  } else {
    const merged = [...currentExts.value]
    for (const e of exts) {
      if (!merged.includes(e)) merged.push(e)
    }
    commit(merged)
  }
}
</script>

<style scoped lang="scss">
// ── 外框 ────────────────────────────────────────────────────────
.ext-manager {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-surface);
}

// ── 预设行（与顶栏 nav-link 一致的线性风格） ──────────────────
.preset-row {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0 12px;
  background: var(--color-surface-raised);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-wrap: wrap;
  min-height: 38px;
}

.preset-lead {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-right: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}

.preset-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 0 10px;
  height: 38px;
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.15s ease;

  // 底线指示器
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 10px;
    right: 10px;
    height: 2px;
    background: var(--color-primary);
    border-radius: 2px 2px 0 0;
    opacity: 0;
    transform: scaleX(0.5);
    transition: opacity 0.15s ease, transform 0.15s ease;
  }

  em {
    font-style: normal;
    font-size: 11px;
    color: var(--color-text-muted);
    transition: color 0.15s ease;
  }

  &:hover {
    color: var(--color-text-primary);
    em { color: var(--color-text-secondary); }
  }

  &--on {
    color: var(--color-primary);
    em { color: var(--color-primary); opacity: 0.7; }

    &::after {
      opacity: 1;
      transform: scaleX(1);
    }
  }
}

// ── 标签区 ──────────────────────────────────────────────────────
.tags-wrap {
  min-height: 72px;
  padding: 10px 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-content: flex-start;
  background: var(--color-surface);

  &--empty {
    align-items: center;
    justify-content: center;
  }
}

.ext-tag {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 7px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-family: var(--font-mono, 'JetBrains Mono', 'Fira Code', monospace);
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  background: var(--color-surface-raised);
  transition: border-color 0.12s ease, color 0.12s ease, background 0.12s ease;
  user-select: none;

  .tag-x {
    font-style: normal;
    font-size: 13px;
    color: var(--color-text-muted);
    line-height: 1;
    margin-left: 1px;
    transition: color 0.12s ease;
  }

  &:hover {
    border-color: var(--color-danger);
    color: var(--color-danger);
    background: rgba(239, 68, 68, 0.06);
    .tag-x { color: var(--color-danger); }
  }
}

.empty-warn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #d97706;

  html.dark & {
    color: #f59e0b;
  }
}

// ── 底部栏 ──────────────────────────────────────────────────────
.ext-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 12px;
  border-top: 1px solid var(--color-border-subtle);
  background: var(--color-surface-raised);
  gap: 8px;
  flex-wrap: wrap;
}

.bar-count {
  font-size: 12px;
  color: var(--color-text-muted);

  &--warn {
    color: #d97706;
    font-weight: 500;

    html.dark & {
      color: #f59e0b;
    }
  }
}

.bar-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.custom-in {
  height: 26px;
  padding: 0 8px;
  font-size: 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  outline: none;
  width: 160px;
  background: var(--color-surface);
  color: var(--color-text-primary);
  transition: border-color 0.15s ease;

  &:focus { border-color: var(--color-primary); }

  &::placeholder { color: var(--color-text-muted); }
}

.btn-add {
  height: 26px;
  width: 26px;
  border-radius: 4px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.15s ease, color 0.15s ease;

  &:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
  }
}

.btn-clear {
  height: 26px;
  padding: 0 10px;
  border-radius: 4px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  cursor: pointer;
  font-size: 12px;
  color: var(--color-text-muted);
  transition: border-color 0.15s ease, color 0.15s ease;

  &:hover {
    border-color: var(--color-danger);
    color: var(--color-danger);
  }
}
</style>
