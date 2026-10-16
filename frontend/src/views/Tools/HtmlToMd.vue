<template>
  <div class="tool-page">
    <div class="tool-header">
      <h1 class="tool-title">HTML → Markdown</h1>
      <p class="tool-desc">将网页内容转换为 Markdown，支持数学公式、图片本地化打包下载</p>
    </div>

    <!-- 方法 Tabs -->
    <div class="method-tabs">
      <button
        v-for="(label, idx) in ['方法一：网址', '方法二：本地文件', '方法三：粘贴源码']"
        :key="idx"
        :class="['method-tab', { active: activeMethod === idx }]"
        @click="activeMethod = idx"
      >{{ label }}</button>
    </div>

    <!-- Input Card -->
    <div class="input-card">

      <!-- 方法一：URL -->
      <div v-if="activeMethod === 0">
        <div class="url-row">
          <input
            v-model="urlValue"
            class="url-input"
            type="url"
            placeholder="输入网址，按 Enter 或点击「转换」"
            @keydown.enter="fetchUrl"
          />
          <button class="btn btn-primary" :disabled="isFetching" @click="fetchUrl">
            <span v-if="isFetching" class="btn-spinner" />
            <template v-else>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1C3.69 1 1 3.69 1 7s2.69 6 6 6 6-2.69 6-6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
                <path d="M10 1v4h-4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              转换
            </template>
          </button>
        </div>
        <p class="method-note">部分网站启用了访问保护，遇到失败时请改用方法二</p>
      </div>

      <!-- 方法二：本地文件 -->
      <div v-if="activeMethod === 1">
        <div
          class="drop-zone"
          :class="{ active: isDragOver }"
          @dragover.prevent="isDragOver = true"
          @dragleave="onDragLeave"
          @drop="onDrop"
          @click="fileInputRef?.click()"
        >
          <input ref="fileInputRef" type="file" accept=".html,.htm" multiple style="display:none" @change="onFileInputChange" />
          <input ref="folderInputRef" type="file" webkitdirectory multiple style="display:none" @change="onFileInputChange" />
          <svg class="drop-icon" viewBox="0 0 32 32" fill="none">
            <rect x="3" y="3" width="19" height="24" rx="2" stroke="currentColor" stroke-width="1.4"/>
            <path d="M7 11h11M7 15h7M7 19h9" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            <path d="M24 19v8M21 23l3-4 3 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p class="drop-title">拖入 HTML 文件或文件夹</p>
          <p class="drop-sub">
            也可<em>点击选择文件</em>，或
            <em @click.stop="folderInputRef?.click()">选择文件夹</em>，支持批量处理
          </p>
        </div>

        <p class="tip-inline">
          <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
            <circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" stroke-width="1.2"/>
            <path d="M6.5 5.5v3.5M6.5 4v.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <span>连同 <code>_files</code> 文件夹一起拖入，可保留本地图片</span>
        </p>

        <!-- 获取网页文件教学 -->
        <details class="how-to">
          <summary>如何获取网页文件？</summary>
          <ol class="how-to-steps">
            <li>在 Chrome / Edge 打开目标网页</li>
            <li>按 <kbd>Ctrl</kbd>+<kbd>S</kbd>（Mac：<kbd>⌘S</kbd>）→「另存为」</li>
            <li>格式选择 <strong>「网页，完整」</strong>（会同时生成 <code>.html</code> 文件和同名 <code>_files</code> 文件夹）</li>
            <li>将 <code>.html</code> 文件与 <code>_files</code> 文件夹<strong>一起</strong>拖入上方区域</li>
          </ol>
          <p class="how-to-note">⚠️ 必须选「网页，完整」，「仅 HTML」不会保存图片资源</p>
        </details>
      </div>

      <!-- 方法三：粘贴源码 -->
      <div v-if="activeMethod === 2">
        <div class="paste-zone">
          <div class="paste-inputs">
            <input
              v-model="pasteUrlValue"
              class="url-input paste-url"
              type="url"
              placeholder="页面地址（选填，用于解析图片相对路径，如 https://example.com/page）"
            />
            <textarea
              v-model="pasteValue"
              class="paste-textarea"
              placeholder="在目标网页按 Ctrl+U 查看源码，全选 Ctrl+A 复制，粘贴到这里"
              rows="6"
              spellcheck="false"
            />
          </div>
          <button
            class="btn btn-primary btn-sm paste-btn"
            :disabled="!pasteValue.trim()"
            @click="convertPasted"
          >转换</button>
        </div>
      </div>
    </div>

    <!-- Options -->
    <div class="options-row">
      <label class="opt-label">
        <input v-model="downloadImagesEnabled" type="checkbox" />
        下载图片，打包为 ZIP（含 images/ 目录）
      </label>
    </div>

    <!-- Actions bar -->
    <transition name="fade">
      <div v-if="entries.size > 0" class="actions-bar">
        <span class="actions-info">已完成 {{ doneCount }} / {{ entries.size }} 个文件</span>
        <div class="actions-right">
          <button class="btn btn-ghost btn-sm" @click="clearAll">清除</button>
          <button class="btn btn-primary btn-sm" :disabled="doneCount === 0" @click="downloadAll">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M6 1v7M3 5.5l3 3 3-3M1 9.5v.5a1 1 0 001 1h8a1 1 0 001-1v-.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            全部下载
          </button>
        </div>
      </div>
    </transition>

    <!-- File cards -->
    <div class="file-list">
      <transition-group name="slide-in" tag="div" class="file-list-inner">
        <div
          v-for="entry in entriesList"
          :key="entry.id"
          class="file-card"
          :data-status="entry.status"
        >
          <div class="card-dot" />
          <div class="card-info">
            <div class="card-name">{{ entry.name }}{{ entry.status === 'done' ? (downloadImagesEnabled && entry.images.length ? '.zip' : '.md') : '' }}</div>
            <div class="card-meta">
              <template v-if="entry.status === 'processing'">
                <span class="meta-processing">{{ entry.statusText }}</span>
              </template>
              <template v-else-if="entry.status === 'done'">
                完成 · {{ entry.lines.toLocaleString() }} 行
                <template v-if="entry.imgCount > 0"> · {{ entry.imgCount }} 张图片</template>
                <template v-if="entry.imgFailed > 0"> · <span class="meta-warn">{{ entry.imgFailed }} 张未能下载</span></template>
              </template>
              <template v-else>
                <span class="meta-error">{{ entry.error || '转换失败' }}</span>
              </template>
            </div>
          </div>
          <div class="card-actions">
            <button
              v-if="entry.status === 'done'"
              class="btn btn-ghost btn-sm"
              @click="downloadOne(entry.id)"
            >下载</button>
          </div>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useHtmlConverter } from '@/composables/useHtmlConverter'

const {
  entries, entriesList, doneCount, downloadImagesEnabled,
  convert, convertFromUrl, downloadOne, downloadAll, clearAll, buildFileMap,
} = useHtmlConverter()

// ── Active method tab (0=URL, 1=File, 2=Paste) ───────────────────────────────
const activeMethod = ref(0)

// ── URL fetch ────────────────────────────────────────────────────────────────
const urlValue = ref('')
const isFetching = ref(false)

async function fetchUrl() {
  if (!urlValue.value.trim() || isFetching.value) return
  isFetching.value = true
  try {
    await convertFromUrl(urlValue.value.trim())
    urlValue.value = ''
  } catch (err) {
    const msg = (err as Error).message
    if (/403|拒绝访问|Forbidden/i.test(msg)) {
      ElMessage.error('该网站启用了访问保护，服务端代理无法绕过。请在浏览器打开页面，按 Ctrl+S 另存为「网页，完整」，再将 .html 文件拖入。')
    } else {
      ElMessage.error(`抓取失败：${msg}。如持续失败，请改用浏览器「另存为 HTML」后拖入。`)
    }
  } finally {
    isFetching.value = false
  }
}

// ── Paste HTML ───────────────────────────────────────────────────────────────
const pasteValue = ref('')
const pasteUrlValue = ref('')

function convertPasted() {
  const html = pasteValue.value.trim()
  if (!html) return
  const titleMatch = html.match(/<title[^>]*>([^<]*)<\/title>/i)
  const rawTitle = titleMatch?.[1]?.trim() || 'pasted'
  // 解码 HTML 实体，避免文件名中出现字面量 &amp; 等
  const decodedTitle = rawTitle
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(+n))
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCharCode(parseInt(h, 16)))
  const name = decodedTitle.replace(/[\\/:*?"<>|]/g, '_') || 'pasted'
  const baseUrl = pasteUrlValue.value.trim() || null
  convert(html, name, baseUrl, new Map())
  pasteValue.value = ''
}

// ── Drop zone ────────────────────────────────────────────────────────────────
const isDragOver = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const folderInputRef = ref<HTMLInputElement | null>(null)

function onDragLeave(e: DragEvent) {
  if (!(e.currentTarget as Element).contains(e.relatedTarget as Node)) {
    isDragOver.value = false
  }
}

// IMPORTANT: drop handler is synchronous — DataTransfer is invalidated after any await.
// Capture all file/entry refs synchronously, then call async expandAndDispatch().
function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false

  const plainFiles: File[] = []
  const dirEntries: FileSystemDirectoryEntry[] = []

  if (e.dataTransfer?.items && e.dataTransfer.items.length > 0) {
    for (const item of e.dataTransfer.items) {
      if (item.kind !== 'file') continue
      const entry = item.webkitGetAsEntry?.()
      if (entry?.isDirectory) {
        dirEntries.push(entry as FileSystemDirectoryEntry)
      } else {
        const f = item.getAsFile()
        if (f) plainFiles.push(f)
      }
    }
  } else if (e.dataTransfer?.files) {
    for (const f of e.dataTransfer.files) plainFiles.push(f)
  }

  expandAndDispatch(plainFiles, dirEntries)
}

async function expandAndDispatch(plainFiles: File[], dirEntries: FileSystemDirectoryEntry[]) {
  // 平铺文件：相对路径 = 文件名本身（无所属目录）
  const allEntries: { file: File; relPath: string }[] =
    plainFiles.map(f => ({ file: f, relPath: f.name }))
  // 递归读取目录，保留完整相对路径（dir.name/subdir/file.ext）
  for (const dir of dirEntries) await readDirEntry(dir, allEntries, dir.name)
  dispatch(allEntries)
}

function dispatch(allEntries: { file: File; relPath: string }[]) {
  const htmlEntries = allEntries.filter(e => /\.html?$/i.test(e.file.name))
  const assetEntries = allEntries.filter(e => !/\.html?$/i.test(e.file.name))
  const fileMap = buildFileMap(assetEntries)

  if (htmlEntries.length === 0) {
    if (allEntries.length > 0) ElMessage.warning('没有找到 HTML 文件，请同时拖入 .html 文件。')
    return
  }
  htmlEntries.forEach(({ file }) =>
    file.text().then(html => convert(html, file.name.replace(/\.html?$/i, ''), null, fileMap)),
  )
}

async function readDirEntry(
  dirEntry: FileSystemDirectoryEntry,
  entries: { file: File; relPath: string }[],
  prefix: string,
) {
  const reader = dirEntry.createReader()
  let batch: FileSystemEntry[]
  do {
    batch = await new Promise<FileSystemEntry[]>((res, rej) => reader.readEntries(res, rej))
    for (const entry of batch) {
      const path = `${prefix}/${entry.name}`
      if (entry.isFile) {
        const file = await new Promise<File>((res, rej) => (entry as FileSystemFileEntry).file(res, rej))
        entries.push({ file, relPath: path })
      } else if (entry.isDirectory) {
        await readDirEntry(entry as FileSystemDirectoryEntry, entries, path)
      }
    }
  } while (batch.length > 0)
}

function onFileInputChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    // webkitRelativePath 在 <input webkitdirectory> 时携带完整相对路径
    const entries = [...input.files].map(f => ({
      file: f,
      relPath: f.webkitRelativePath || f.name,
    }))
    dispatch(entries)
  }
  input.value = ''
}
</script>

<style scoped lang="scss">
.tool-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 40px 28px 80px;

  @media (max-width: 640px) {
    padding: 24px 16px 72px;
  }
}

.tool-title {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.4px;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.tool-desc {
  font-size: 13px;
  color: var(--color-text-muted);
  margin: 0;
}

.tool-header { margin-bottom: 16px; }

// ── Method tabs ──────────────────────────────────────────────────────────────
.method-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0;
}

.method-tab {
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-muted);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  cursor: pointer;
  transition: color $transition-fast, border-color $transition-fast;
  font-family: inherit;

  &:hover { color: var(--color-text-primary); }

  &.active {
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
  }
}

.method-note {
  margin-top: 10px;
  font-size: 12px;
  color: var(--color-text-muted);
}

// ── How-to tutorial ──────────────────────────────────────────────────────────
.how-to {
  margin-top: 16px;
  border-top: 1px solid var(--color-border-subtle);
  padding-top: 12px;

  summary {
    font-size: 12.5px;
    color: var(--color-text-secondary);
    cursor: pointer;
    user-select: none;
    list-style: none;
    display: flex;
    align-items: center;
    gap: 5px;

    &::before {
      content: '▶';
      font-size: 9px;
      transition: transform 0.15s;
    }
  }

  &[open] summary::before { transform: rotate(90deg); }
}

.how-to-steps {
  margin: 10px 0 6px 16px;
  padding: 0;
  font-size: 12.5px;
  color: var(--color-text-secondary);
  line-height: 2;

  li { margin-bottom: 2px; }

  strong { color: var(--color-text-primary); font-weight: 500; }

  code {
    font-family: 'DM Mono', 'JetBrains Mono', monospace;
    font-size: 11.5px;
    background: var(--color-bg);
    border: 1px solid var(--color-border);
    border-radius: 3px;
    padding: 1px 5px;
  }

  kbd {
    display: inline-block;
    font-size: 11px;
    padding: 1px 5px;
    background: var(--color-surface-hover);
    border: 1px solid var(--color-border);
    border-radius: 3px;
    font-family: inherit;
    color: var(--color-text-primary);
  }
}

.how-to-note {
  font-size: 12px;
  color: #f59e0b;
  margin: 4px 0 0 0;
  padding-left: 16px;
}

// ── Input card ────────────────────────────────────────────────────────────────
.input-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: $radius-lg;
  padding: 20px;
  margin-bottom: 16px;
}

.url-row {
  display: flex;
  gap: 8px;
}

.url-input {
  flex: 1;
  min-width: 0;
  height: 40px;
  padding: 0 12px;
  border: 1.5px solid var(--color-border);
  border-radius: $radius-md;
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  font-size: 12.5px;
  color: var(--color-text-primary);
  background: var(--color-bg);
  outline: none;
  transition: border-color $transition-fast;

  &::placeholder {
    font-family: inherit;
    color: var(--color-text-muted);
    font-size: 13px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  }

  &:focus {
    border-color: var(--color-primary);
  }
}

.or-divider {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 16px 0;
  font-size: 12px;
  color: var(--color-text-muted);

  &::before, &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--color-border);
  }
}

// ── Drop zone ──────────────────────────────────────────────────────────────────
.drop-zone {
  border: 1.5px dashed var(--color-border);
  border-radius: $radius-md;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  transition: border-color $transition-base, background $transition-base;

  &:hover {
    border-color: rgba(var(--color-primary-rgb, 90, 103, 216), 0.4);
    background: var(--color-primary-subtle);
  }

  &.active {
    border-color: var(--color-primary);
    background: var(--color-primary-subtle);

    .drop-icon { color: var(--color-primary); transform: translateY(-3px); }
  }
}

.drop-icon {
  width: 32px;
  height: 32px;
  margin: 0 auto 12px;
  color: var(--color-text-muted);
  transition: color $transition-base, transform $transition-base;
}

.drop-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.drop-sub {
  font-size: 13px;
  color: var(--color-text-secondary);

  em { color: var(--color-primary); font-style: normal; }
}

// ── Tip ──────────────────────────────────────────────────────────────────────
.tip-inline {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border-subtle);
  font-size: 12.5px;
  color: var(--color-text-muted);
  line-height: 1.55;

  svg { flex-shrink: 0; margin-top: 1px; }

  code {
    font-family: 'DM Mono', 'JetBrains Mono', monospace;
    font-size: 11.5px;
    background: var(--color-bg);
    border: 1px solid var(--color-border);
    border-radius: 3px;
    padding: 1px 5px;
  }
}

// ── Paste zone ────────────────────────────────────────────────────────────────
.paste-zone {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.paste-inputs {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.paste-url {
  height: 34px;
  font-size: 12.5px;
}

.paste-textarea {
  flex: 1;
  min-width: 0;
  padding: 10px 12px;
  border: 1.5px solid var(--color-border);
  border-radius: $radius-md;
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--color-text-primary);
  background: var(--color-bg);
  resize: vertical;
  outline: none;
  line-height: 1.5;
  transition: border-color $transition-fast;

  &::placeholder {
    color: var(--color-text-muted);
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 12.5px;
  }

  &:focus { border-color: var(--color-primary); }
}

.paste-btn {
  flex-shrink: 0;
  align-self: flex-end;
}

// ── Options ────────────────────────────────────────────────────────────────────
.options-row {
  margin-bottom: 20px;
}

.opt-label {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  user-select: none;

  input[type="checkbox"] {
    width: 15px;
    height: 15px;
    accent-color: var(--color-primary);
    cursor: pointer;
  }
}

// ── Buttons ───────────────────────────────────────────────────────────────────
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 40px;
  padding: 0 16px;
  border-radius: $radius-md;
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all $transition-fast;
  border: 1.5px solid transparent;
  white-space: nowrap;

  &-primary {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);

    &:hover:not(:disabled) { background: var(--color-primary-hover, #4c59c9); }
  }

  &-ghost {
    background: transparent;
    color: var(--color-text-secondary);
    border-color: var(--color-border);

    &:hover:not(:disabled) {
      color: var(--color-text-primary);
      border-color: var(--color-border-strong, #d1d5db);
    }
  }

  &-sm { height: 32px; padding: 0 12px; font-size: 12px; }
  &:disabled { opacity: 0.45; cursor: not-allowed; }
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

// ── Actions bar ───────────────────────────────────────────────────────────────
.actions-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  margin-bottom: 12px;
  border-top: 1px solid var(--color-border);
}

.actions-info {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.actions-right {
  display: flex;
  gap: 8px;
}

// ── File cards ────────────────────────────────────────────────────────────────
.file-list-inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--status-color, var(--color-border));
  border-radius: $radius-md;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: border-left-color 0.4s;

  &[data-status="processing"] { --status-color: var(--color-primary); }
  &[data-status="done"]       { --status-color: #10b981; }
  &[data-status="error"]      { --status-color: #ef4444; }
}

.card-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--status-color, var(--color-border));
  flex-shrink: 0;

  .file-card[data-status="processing"] & {
    animation: blink 1.2s ease-in-out infinite;
  }
}

@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.2; } }

.card-info {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  font-size: 12.5px;
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 3px;
}

.meta-processing { color: var(--color-primary); }
.meta-warn { color: #f59e0b; }
.meta-error { color: #ef4444; }

.card-actions { flex-shrink: 0; }

// ── Transitions ───────────────────────────────────────────────────────────────
.fade-enter-active, .fade-leave-active { transition: opacity $transition-base; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-in-enter-active { animation: slideIn 0.2s ease; }
@keyframes slideIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: none; }
}

.slide-in-leave-active { transition: opacity $transition-fast; }
.slide-in-leave-to { opacity: 0; }
</style>
