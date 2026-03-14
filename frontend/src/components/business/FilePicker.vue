<template>
  <el-dialog
    :model-value="modelValue"
    :title="filter === 'image' ? '选择封面图' : '选择附件'"
    width="700px"
    :close-on-click-modal="false"
    @update:model-value="$emit('update:modelValue', $event)"
    @open="onOpen"
  >
    <div class="picker-body">
      <!-- 面包屑导航 -->
      <div class="breadcrumb">
        <button class="crumb-item crumb-root" @click="navTo(null)">
          <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 6l6-4 6 4v8H2z"/><path d="M6 16V9h4v7"/></svg>
          全部文件
        </button>
        <template v-for="(crumb, i) in breadcrumb" :key="crumb.id">
          <span class="crumb-sep">/</span>
          <button
            :class="['crumb-item', { 'crumb-current': i === breadcrumb.length - 1 }]"
            @click="navTo(crumb.id)"
          >{{ crumb.name }}</button>
        </template>
      </div>

      <!-- 内容区 -->
      <div v-loading="loading" class="picker-content">
        <div v-if="!loading && folders.length === 0 && files.length === 0" class="picker-empty">
          <el-empty description="此文件夹为空" :image-size="54" />
        </div>

        <div v-else class="file-grid">
          <!-- 文件夹 -->
          <div
            v-for="folder in folders"
            :key="'folder-' + folder.id"
            class="grid-item folder-item"
            @click="enterFolder(folder)"
          >
            <div class="item-thumb folder-thumb">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#5a67d8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
              </svg>
            </div>
            <div class="item-info">
              <p class="item-name" :title="folder.name">{{ folder.name }}</p>
              <p class="item-meta">{{ folder.file_count }} 个文件</p>
            </div>
          </div>

          <!-- 文件 -->
          <div
            v-for="file in files"
            :key="'file-' + file.id"
            class="grid-item file-item"
            @click="selectFile(file)"
          >
            <div class="item-thumb file-thumb">
              <img
                v-if="file.file_category === 'image'"
                :src="getThumbnail(file.id)"
                :alt="file.title"
                class="thumb-img"
              />
              <div v-else class="thumb-icon">
                <component :is="categoryIcon(file.file_category)" style="width:20px;height:20px;color:var(--el-text-color-placeholder)" />
              </div>
            </div>
            <div class="item-info">
              <p class="item-name" :title="file.title">{{ file.title }}</p>
              <p class="item-meta">{{ formatFileSize(file.file_size) }}</p>
            </div>
            <div class="select-overlay">
              <svg viewBox="0 0 16 16" width="16" height="16" fill="white" stroke="none">
                <path d="M13.5 2.5l-7 7-3-3L2 8l4.5 4.5 8.5-8.5z"/>
              </svg>
            </div>
          </div>
        </div>

        <div v-if="hasMore" class="load-more">
          <el-button size="small" :loading="loadingMore" @click="loadMore">加载更多</el-button>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, VideoPlay, Paperclip } from '@element-plus/icons-vue'
import { filesApi } from '@/api/modules/files'
import { groupsApi } from '@/api/modules/groups'
import type { FileItem } from '@/types/models'
import type { FileGroup, BreadcrumbItem } from '@/api/modules/groups'
import { formatFileSize } from '@/utils/format'

const props = withDefaults(defineProps<{
  modelValue: boolean
  // 'image': 只显示图片文件（文件夹始终显示）；'all': 显示全部
  filter?: 'image' | 'all'
}>(), {
  filter: 'all'
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'select', file: FileItem): void
}>()

const loading = ref(false)
const loadingMore = ref(false)
const currentGroupId = ref<number | null>(null) // null = 根目录
const breadcrumb = ref<BreadcrumbItem[]>([])
const folders = ref<FileGroup[]>([])
const files = ref<FileItem[]>([])
const page = ref(1)
const hasMore = ref(false)

function getThumbnail(id: number) {
  return filesApi.getThumbnailUrl(id)
}

function categoryIcon(cat: string) {
  if (cat === 'video') return VideoPlay
  if (cat === 'document') return Document
  return Paperclip
}

async function loadContent(reset = false) {
  if (reset) {
    page.value = 1
    files.value = []
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    // 并行加载子文件夹（仅第一页加载）和文件
    if (reset) {
      const [foldersRes, filesRes] = await Promise.all([
        loadFolders(),
        loadFiles(1)
      ])
      folders.value = foldersRes
      files.value = filesRes.items
      hasMore.value = filesRes.hasMore
    } else {
      const filesRes = await loadFiles(page.value)
      files.value = [...files.value, ...filesRes.items]
      hasMore.value = filesRes.hasMore
    }
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function loadFolders(): Promise<FileGroup[]> {
  try {
    if (currentGroupId.value === null) {
      const res = await groupsApi.list()
      return res.data || []
    } else {
      const res = await groupsApi.getChildren(currentGroupId.value)
      return res.data || []
    }
  } catch {
    return []
  }
}

async function loadFiles(p: number): Promise<{ items: FileItem[]; hasMore: boolean }> {
  try {
    const params: any = {
      page: p,
      page_size: 18,
      group_id: currentGroupId.value === null ? -1 : currentGroupId.value
    }
    // 图片模式：只返回图片文件
    if (props.filter === 'image') params.category = 'image'

    const res = await filesApi.getList(params)
    const items = res.items || []
    const pagination = res.pagination
    return {
      items,
      hasMore: pagination ? p < pagination.pages : false
    }
  } catch {
    return { items: [], hasMore: false }
  }
}

async function enterFolder(folder: FileGroup) {
  currentGroupId.value = folder.id
  // 更新面包屑
  try {
    const res = await groupsApi.getBreadcrumb(folder.id)
    breadcrumb.value = res.data || []
  } catch {
    breadcrumb.value = [...breadcrumb.value, { id: folder.id, name: folder.name }]
  }
  await loadContent(true)
}

async function navTo(groupId: number | null) {
  currentGroupId.value = groupId
  if (groupId === null) {
    breadcrumb.value = []
  } else {
    try {
      const res = await groupsApi.getBreadcrumb(groupId)
      breadcrumb.value = res.data || []
    } catch {
      const idx = breadcrumb.value.findIndex(b => b.id === groupId)
      if (idx >= 0) breadcrumb.value = breadcrumb.value.slice(0, idx + 1)
    }
  }
  await loadContent(true)
}

async function loadMore() {
  page.value++
  await loadContent(false)
}

function onOpen() {
  currentGroupId.value = null
  breadcrumb.value = []
  loadContent(true)
}

function selectFile(file: FileItem) {
  if (props.filter === 'image' && file.file_category !== 'image') {
    ElMessage.warning('请选择图片文件作为封面')
    return
  }
  emit('select', file)
  emit('update:modelValue', false)
}
</script>

<style scoped lang="scss">
.picker-body {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  min-height: 340px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: $spacing-xs $spacing-sm;
  background: var(--el-fill-color-lighter);
  border-radius: $radius-md;
  flex-wrap: wrap;
}

.crumb-sep {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  padding: 0 2px;
}

.crumb-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  padding: 3px 6px;
  border-radius: $radius-sm;
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: all $transition-fast;

  &:hover { background: var(--el-fill-color); color: $color-primary; }
  &.crumb-current { color: var(--el-text-color-primary); font-weight: 500; cursor: default; &:hover { background: none; color: var(--el-text-color-primary); } }
  &.crumb-root { color: $color-primary; font-weight: 500; }
}

.picker-content { flex: 1; }

.picker-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 220px;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: $spacing-xs;

  @media (max-width: 600px) {
    grid-template-columns: repeat(3, 1fr);
  }
}

.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-xs;
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  cursor: pointer;
  transition: all $transition-fast;
  position: relative;
  overflow: hidden;

  &:hover {
    border-color: $color-primary;
    background: rgba(90, 103, 216, 0.04);
  }
}

.folder-item:hover {
  background: rgba(90, 103, 216, 0.06);
}

.item-thumb {
  width: 100%;
  aspect-ratio: 1;
  border-radius: $radius-md;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.folder-thumb {
  background: rgba(90, 103, 216, 0.08);
}

.file-thumb {
  background: var(--el-fill-color);
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-icon { color: var(--el-text-color-placeholder); }

.item-info {
  width: 100%;
  text-align: center;
}

.item-name {
  font-size: $font-xs;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
  line-height: 1.4;
}

.item-meta {
  font-size: 10px;
  color: var(--el-text-color-placeholder);
  margin: 2px 0 0;
}

.select-overlay {
  position: absolute;
  inset: 0;
  background: rgba(90, 103, 216, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity $transition-fast;
  border-radius: $radius-lg;
}

.file-item:hover .select-overlay { opacity: 1; }

.load-more {
  display: flex;
  justify-content: center;
  margin-top: $spacing-md;
}
</style>
