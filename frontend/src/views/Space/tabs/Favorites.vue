<template>
  <div class="fav-layout">
    <!-- 左侧收藏夹侧边栏 -->
    <aside class="fav-sidebar">
      <div
        :class="['folder-item', { active: activeFolderId === null }]"
        @click="selectFolder(null)"
      >
        <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        <span class="folder-name">全部收藏</span>
        <span class="folder-count">{{ totalCount }}</span>
      </div>

      <div
        v-for="folder in folders"
        :key="folder.id"
        :class="['folder-item', { active: activeFolderId === folder.id }]"
        @click="selectFolder(folder.id)"
        @mouseenter="hoverFolderId = folder.id"
        @mouseleave="hoverFolderId = null"
      >
        <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
          <path d="M1 4a1 1 0 011-1h4l1.5 2H14a1 1 0 011 1v7a1 1 0 01-1 1H2a1 1 0 01-1-1V4z"/>
        </svg>
        <span v-if="renamingFolderId !== folder.id" class="folder-name">{{ folder.name }}</span>
        <input
          v-else
          ref="renameInputRef"
          v-model="renameValue"
          class="folder-rename-input"
          @keyup.enter="confirmRename(folder.id)"
          @keyup.esc="cancelRename"
          @blur="confirmRename(folder.id)"
          @click.stop
        />
        <span class="folder-count">{{ folder.post_count ?? '' }}</span>
        <div
          v-if="hoverFolderId === folder.id && renamingFolderId !== folder.id"
          class="folder-actions"
          @click.stop
        >
          <button class="folder-action-btn" title="重命名" @click="startRename(folder)">
            <svg viewBox="0 0 12 12" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 1l3 3-6.5 6.5H1V8L8 1z"/></svg>
          </button>
          <button class="folder-action-btn danger" title="删除" @click="deleteFolder(folder.id)">
            <svg viewBox="0 0 12 12" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M1 3h10M4 3V1.5h4V3M5 5.5v4M7 5.5v4M2 3l.8 7.5h6.4L10 3"/></svg>
          </button>
        </div>
      </div>

      <button class="new-folder-btn" @click="startCreateFolder">
        <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M8 4v8M4 8h8"/>
        </svg>
        新建收藏夹
      </button>

      <!-- 新建输入框 -->
      <div v-if="creatingFolder" class="new-folder-input-wrap" @click.stop>
        <input
          ref="newFolderInputRef"
          v-model="newFolderName"
          class="folder-rename-input"
          placeholder="收藏夹名称"
          maxlength="30"
          @keyup.enter="confirmCreateFolder"
          @keyup.esc="cancelCreateFolder"
          @blur="confirmCreateFolder"
        />
      </div>
    </aside>

    <!-- 右侧主内容区 -->
    <div class="fav-main">
      <!-- 工具栏 -->
      <div class="fav-toolbar">
        <div class="toolbar-left">
          <h3 class="fav-title">
            {{ activeFolderName }}
            <span class="title-count">{{ posts.length }}</span>
          </h3>
        </div>
        <div class="toolbar-right">
          <!-- 搜索 -->
          <div :class="['fav-search', { expanded: searchExpanded }]">
            <button class="search-icon-btn" @click="toggleSearch">
              <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="6.5" cy="6.5" r="4.5"/><line x1="10" y1="10" x2="14" y2="14"/>
              </svg>
            </button>
            <input
              v-if="searchExpanded"
              ref="searchInputRef"
              v-model="searchQuery"
              class="fav-search-input"
              placeholder="搜索收藏…"
              @keyup.esc="toggleSearch"
              @blur="onSearchBlur"
            />
            <button v-if="searchExpanded && searchQuery" class="search-clear-btn" @click="searchQuery = ''">
              <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/></svg>
            </button>
          </div>
          <!-- 批量选择 -->
          <button :class="['icon-btn', { active: batchMode }]" :title="batchMode ? '退出批量' : '批量操作'" @click="toggleBatchMode">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="1" y="1" width="5" height="5" rx="1"/><rect x="1" y="9" width="5" height="5" rx="1"/>
              <line x1="9" y1="3" x2="15" y2="3"/><line x1="9" y1="11" x2="15" y2="11"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 批量操作栏 -->
      <div v-if="batchMode && selectedIds.size > 0" class="batch-bar">
        <span class="batch-count">已选 {{ selectedIds.size }} 项</span>
        <button class="batch-btn" @click="batchMove">
          <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M1 4a1 1 0 011-1h4l1.5 2H14a1 1 0 011 1v7a1 1 0 01-1 1H2a1 1 0 01-1-1V4z"/></svg>
          移动到
        </button>
        <button class="batch-btn danger" @click="batchUncollect">
          <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/></svg>
          取消收藏
        </button>
        <button class="batch-btn text" @click="selectedIds.clear()">取消选择</button>
      </div>

      <!-- Feed 列表（与发现页格式一致）-->
      <div v-if="loading && displayPosts.length === 0" class="fav-skeleton-list">
        <el-skeleton v-for="i in 5" :key="i" animated :rows="3" style="margin-bottom: 20px" />
      </div>
      <div v-else-if="displayPosts.length > 0" class="feed-list">
        <div
          v-for="post in displayPosts"
          :key="post.id"
          class="fav-item-wrap"
          :class="{ selected: selectedIds.has(post.id), 'batch-mode': batchMode }"
        >
          <!-- 批量模式遮罩 -->
          <div v-if="batchMode" class="batch-overlay" @click="toggleSelect(post.id)" />
          <div v-if="batchMode" class="batch-checkbox" :class="{ checked: selectedIds.has(post.id) }">
            <svg v-if="selectedIds.has(post.id)" viewBox="0 0 12 12" width="10" height="10" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="2,6 5,9 10,3"/></svg>
          </div>

          <!-- 博文条目（与 Blog/index.vue feed-item 一致）-->
          <article class="feed-item" @click="!batchMode && goToPost(post.id)">
            <div class="item-header">
              <el-avatar :size="24" :src="authorAvatarUrl(post)" class="item-avatar">
                {{ displayPostName(post)[0]?.toUpperCase() }}
              </el-avatar>
              <span class="item-author" @click="goToAuthorPost($event, post.author_name)">
                {{ displayPostName(post) }}
              </span>
              <span class="item-dot">·</span>
              <span class="item-time">{{ timeStr(post) }}</span>
              <!-- 上下文菜单按钮：非批量模式显示真实按钮，批量模式用等宽占位符保持时间位置不变 -->
              <div v-if="!batchMode" class="item-menu-area" @click.stop>
                <button class="item-menu-btn" @click="openMenu(post.id, $event)">
                  <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor">
                    <circle cx="8" cy="3" r="1.2"/><circle cx="8" cy="8" r="1.2"/><circle cx="8" cy="13" r="1.2"/>
                  </svg>
                </button>
              </div>
              <div v-else class="item-menu-placeholder" />
            </div>

            <div class="item-body">
              <div class="item-text">
                <h2 class="item-title">{{ post.title }}</h2>
                <p v-if="post.summary" class="item-summary">{{ post.summary }}</p>
              </div>
              <img
                v-if="coverUrl(post)"
                :src="coverUrl(post)"
                :alt="post.title"
                class="item-cover"
                loading="lazy"
              />
            </div>

            <div class="item-footer">
              <span class="item-stat"><el-icon :size="12"><Star /></el-icon>{{ post.like_count }}</span>
              <span class="item-stat"><el-icon :size="12"><ChatLineRound /></el-icon>{{ post.comment_count }}</span>
              <span class="item-stat"><el-icon :size="12"><ViewIcon /></el-icon>{{ post.view_count }}</span>
              <span v-if="post.category_name" class="item-tag">{{ post.category_name }}</span>
            </div>
          </article>
        </div>
      </div>
      <el-empty v-else :description="searchQuery ? '没有匹配的收藏' : '该收藏夹还没有收藏'" :image-size="72" />

      <!-- 加载更多 -->
      <div v-if="hasMore && !searchQuery" class="load-more">
        <el-button text :loading="loadingMore" @click="loadMore">加载更多</el-button>
      </div>
    </div>

    <!-- 悬浮上下文菜单 -->
    <teleport to="body">
      <div
        v-if="menuPostId !== null"
        class="card-context-menu"
        :style="menuStyle"
        @click.stop
      >
        <button class="menu-item" @click="goToPost(menuPostId)">
          <svg viewBox="0 0 14 14" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 7h12M7 1l6 6-6 6"/>
          </svg>
          打开博文
        </button>
        <div class="menu-divider" />
        <button class="menu-item" @click="openMoveDialog(menuPostId)">
          <svg viewBox="0 0 14 14" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 3a1 1 0 011-1h3l1.5 2H13a1 1 0 011 1v6a1 1 0 01-1 1H2a1 1 0 01-1-1V3z"/>
          </svg>
          移动到
        </button>
        <div class="menu-divider" />
        <button class="menu-item danger" @click="uncollect(menuPostId)">
          <svg viewBox="0 0 14 14" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="7 1 9 5.5 14 6.4 10 10.3 11 14 7 11.5 3 14 4 10.3 0 6.4 5 5.5 7 1"/>
            <line x1="2" y1="2" x2="12" y2="12"/>
          </svg>
          取消收藏
        </button>
      </div>
      <!-- 菜单遮罩 -->
      <div v-if="menuPostId !== null" class="menu-mask" @click="closeMenu" />
    </teleport>

    <!-- 移动到对话框 -->
    <el-dialog v-model="moveDialogVisible" title="移动到收藏夹" width="320px" :close-on-click-modal="true">
      <div class="move-folder-list">
        <div
          :class="['move-folder-item', { active: moveTargetFolderId === null }]"
          @click="moveTargetFolderId = null"
        >
          <svg viewBox="0 0 14 14" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="7 1 9 5.5 14 6.4 10 10.3 11 14 7 11.5 3 14 4 10.3 0 6.4 5 5.5 7 1"/>
          </svg>
          未分类
        </div>
        <div
          v-for="folder in folders"
          :key="folder.id"
          :class="['move-folder-item', { active: moveTargetFolderId === folder.id }]"
          @click="moveTargetFolderId = folder.id"
        >
          <svg viewBox="0 0 14 14" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 3a1 1 0 011-1h3l1.5 2H13a1 1 0 011 1v6a1 1 0 01-1 1H2a1 1 0 01-1-1V3z"/>
          </svg>
          {{ folder.name }}
        </div>
      </div>
      <template #footer>
        <el-button @click="moveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="moving" @click="confirmMove">移动</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, nextTick, onMounted, onActivated, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Star, ChatLineRound, View as ViewIcon } from '@element-plus/icons-vue'
import { interactionsApi } from '@/api/modules/interactions'
import type { CollectionFolder } from '@/api/modules/interactions'
import type { Post } from '@/types/models'
import { fromNow, getFileUrl } from '@/utils/format'

const router = useRouter()

// ---- 收藏夹状态 ----
const folders = ref<CollectionFolder[]>([])
const activeFolderId = ref<number | null>(null)
const hoverFolderId = ref<number | null>(null)
const renamingFolderId = ref<number | null>(null)
const renameValue = ref('')
const renameInputRef = ref<HTMLInputElement | null>(null)
const creatingFolder = ref(false)
const newFolderName = ref('')
const newFolderInputRef = ref<HTMLInputElement | null>(null)

// ---- 博文列表状态 ----
const posts = ref<Post[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(false)
const totalCount = ref(0)

// ---- 搜索状态 ----
const searchQuery = ref('')
const searchExpanded = ref(false)
const searchInputRef = ref<HTMLInputElement | null>(null)

// ---- 批量选择 ----
const batchMode = ref(false)
const selectedIds = reactive(new Set<number>())

// ---- 上下文菜单 ----
const menuPostId = ref<number | null>(null)
const menuStyle = ref({ top: '0px', left: '0px' })

// ---- 移动对话框 ----
const moveDialogVisible = ref(false)
const moveTargetPostIds = ref<number[]>([])
const moveTargetFolderId = ref<number | null>(null)
const moving = ref(false)

// ---- 计算属性 ----
const activeFolderName = computed(() => {
  if (activeFolderId.value === null) return '全部收藏'
  return folders.value.find(f => f.id === activeFolderId.value)?.name ?? '收藏夹'
})

const displayPosts = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return posts.value
  return posts.value.filter(p =>
    p.title.toLowerCase().includes(q) ||
    (p.summary || '').toLowerCase().includes(q) ||
    (p.author_nickname || p.author_name || '').toLowerCase().includes(q)
  )
})

// ---- 初始化 ----
async function init(reset = true) {
  if (reset) { page.value = 1; posts.value = []; loading.value = true }
  else loadingMore.value = true
  try {
    const [colRes, folderRes] = await Promise.all([
      interactionsApi.getMyPostCollections(page.value, 24, activeFolderId.value ?? undefined),
      page.value === 1 ? interactionsApi.getCollectionFolders() : Promise.resolve(null),
    ])
    if (colRes.data) {
      const items = colRes.data.items || []
      if (reset) posts.value = items; else posts.value.push(...items)
      hasMore.value = page.value < colRes.data.pages
      if (reset) totalCount.value = colRes.data.total
    }
    if (folderRes?.data) folders.value = folderRes.data
  } catch { /* 静默 */ } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() { page.value++; init(false) }

// ---- 文件夹切换 ----
function selectFolder(id: number | null) {
  activeFolderId.value = id
  selectedIds.clear()
  batchMode.value = false
  searchQuery.value = ''
  init()
}

// ---- 文件夹创建 ----
function startCreateFolder() {
  creatingFolder.value = true
  newFolderName.value = ''
  nextTick(() => newFolderInputRef.value?.focus())
}

async function confirmCreateFolder() {
  const name = newFolderName.value.trim()
  if (!name) { cancelCreateFolder(); return }
  try {
    const res = await interactionsApi.createCollectionFolder(name)
    if (res.data) { folders.value.push(res.data); ElMessage.success('收藏夹已创建') }
  } catch { ElMessage.error('创建失败') } finally { cancelCreateFolder() }
}

function cancelCreateFolder() { creatingFolder.value = false; newFolderName.value = '' }

// ---- 文件夹重命名 ----
function startRename(folder: CollectionFolder) {
  renamingFolderId.value = folder.id
  renameValue.value = folder.name
  nextTick(() => renameInputRef.value?.focus())
}

async function confirmRename(id: number) {
  if (renamingFolderId.value !== id) return
  const name = renameValue.value.trim()
  if (!name) { cancelRename(); return }
  try {
    const res = await interactionsApi.renameCollectionFolder(id, name)
    if (res.data) {
      const idx = folders.value.findIndex(f => f.id === id)
      if (idx !== -1) folders.value[idx] = { ...folders.value[idx], name }
      ElMessage.success('已重命名')
    }
  } catch { ElMessage.error('重命名失败') } finally { cancelRename() }
}

function cancelRename() { renamingFolderId.value = null; renameValue.value = '' }

// ---- 文件夹删除 ----
async function deleteFolder(id: number) {
  try {
    await ElMessageBox.confirm('删除后，该收藏夹中的博文将移至"全部收藏"，确认删除？', '删除收藏夹', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning', confirmButtonClass: 'el-button--danger'
    })
    await interactionsApi.deleteCollectionFolder(id)
    folders.value = folders.value.filter(f => f.id !== id)
    if (activeFolderId.value === id) selectFolder(null)
    ElMessage.success('已删除')
  } catch { /* 取消 */ }
}

// ---- 搜索 ----
function toggleSearch() {
  searchExpanded.value = !searchExpanded.value
  if (searchExpanded.value) nextTick(() => searchInputRef.value?.focus())
  else searchQuery.value = ''
}

function onSearchBlur() {
  if (!searchQuery.value.trim()) {
    searchExpanded.value = false
  }
}

// ---- 批量操作 ----
function toggleBatchMode() {
  batchMode.value = !batchMode.value
  selectedIds.clear()
}

function toggleSelect(id: number) {
  if (selectedIds.has(id)) selectedIds.delete(id); else selectedIds.add(id)
}

async function batchUncollect() {
  if (selectedIds.size === 0) return
  try {
    await ElMessageBox.confirm(`确认取消收藏选中的 ${selectedIds.size} 篇博文？`, '批量取消收藏', {
      confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning'
    })
    await Promise.all([...selectedIds].map(id => interactionsApi.togglePostCollect(id)))
    posts.value = posts.value.filter(p => !selectedIds.has(p.id))
    totalCount.value -= selectedIds.size
    selectedIds.clear()
    ElMessage.success('已取消收藏')
  } catch { /* 取消 */ }
}

function batchMove() {
  if (selectedIds.size === 0) return
  moveTargetPostIds.value = [...selectedIds]
  moveTargetFolderId.value = null
  moveDialogVisible.value = true
}

// ---- 上下文菜单 ----
function openMenu(postId: number, e: MouseEvent) {
  menuPostId.value = postId
  const x = Math.min(e.clientX, window.innerWidth - 160)
  const y = Math.min(e.clientY + 8, window.innerHeight - 120)
  menuStyle.value = { top: y + 'px', left: x + 'px' }
}

function closeMenu() { menuPostId.value = null }

function goToPost(id: number) {
  closeMenu()
  router.push(`/post/${id}`)
}

async function uncollect(postId: number) {
  closeMenu()
  try {
    await interactionsApi.togglePostCollect(postId)
    posts.value = posts.value.filter(p => p.id !== postId)
    totalCount.value = Math.max(0, totalCount.value - 1)
    ElMessage.success('已取消收藏')
  } catch { ElMessage.error('操作失败') }
}

function openMoveDialog(postId: number) {
  closeMenu()
  moveTargetPostIds.value = [postId]
  moveTargetFolderId.value = null
  moveDialogVisible.value = true
}

async function confirmMove() {
  moving.value = true
  try {
    await Promise.all(moveTargetPostIds.value.map(id =>
      interactionsApi.moveCollectionToFolder(id, moveTargetFolderId.value)
    ))
    ElMessage.success('移动成功')
    moveDialogVisible.value = false
    selectedIds.clear()
    if (activeFolderId.value !== null) {
      // 当前在某个文件夹里，移走的博文要从列表移除
      posts.value = posts.value.filter(p => !moveTargetPostIds.value.includes(p.id))
    }
    // 刷新文件夹计数
    const res = await interactionsApi.getCollectionFolders()
    if (res.data) folders.value = res.data
  } catch { ElMessage.error('移动失败') } finally { moving.value = false }
}

// ---- 博文 feed 辅助函数（与 Blog/index.vue 保持一致）----
function authorAvatarUrl(post: Post) {
  if (!post.author_name) return ''
  return `${import.meta.env.VITE_API_BASE_URL || ''}/users/username/${post.author_name}/avatar/view`
}
function coverUrl(post: Post) {
  return post.cover_image_url ? getFileUrl(post.cover_image_url) : ''
}
function displayPostName(post: Post) {
  return post.author_nickname || post.author_name || '未知用户'
}
function timeStr(post: Post) {
  const t = post.published_at || post.created_at
  return t ? fromNow(t) : ''
}
function goToAuthorPost(e: MouseEvent, username?: string) {
  e.stopPropagation()
  if (username) router.push({ name: 'UserProfile', params: { username } })
}

// ---- 全局点击关闭菜单 ----
onBeforeUnmount(() => closeMenu())

onMounted(() => init())
onActivated(() => init())
</script>

<style scoped lang="scss">
.fav-layout {
  display: flex;
  gap: 0;
  min-height: calc(100vh - 52px);
}

// ==================== 侧边栏 ====================

.fav-sidebar {
  width: 188px;
  flex-shrink: 0;
  border-right: 1px solid var(--el-border-color-light);
  padding: $spacing-sm $spacing-sm $spacing-lg;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.folder-item {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  padding: 6px 10px;
  border-radius: $radius-md;
  cursor: pointer;
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  transition: background $transition-fast, color $transition-fast;
  position: relative;
  user-select: none;

  &:hover { background: var(--el-fill-color-light); color: var(--el-text-color-primary); }
  &.active { background: var(--color-primary-subtle); color: var(--color-primary); font-weight: 500; }

  svg { flex-shrink: 0; opacity: 0.7; }
}

.folder-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.folder-count {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
  margin-left: auto;
  padding-right: 2px;
}

.folder-actions {
  display: flex;
  gap: 2px;
  margin-left: auto;
  flex-shrink: 0;
}

.folder-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: none;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background $transition-fast, color $transition-fast;
  padding: 0;

  &:hover { background: var(--el-fill-color); color: var(--el-text-color-primary); }
  &.danger:hover { background: rgba(239, 68, 68, 0.1); color: var(--el-color-danger); }
}

.folder-rename-input {
  flex: 1;
  min-width: 0;
  border: 1px solid $color-primary;
  border-radius: $radius-sm;
  padding: 1px 5px;
  font-size: $font-sm;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  outline: none;
}

.new-folder-btn {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  margin-top: $spacing-xs;
  padding: 6px 10px;
  border: none;
  background: none;
  color: var(--el-text-color-placeholder);
  font-size: $font-xs;
  cursor: pointer;
  border-radius: $radius-md;
  transition: color $transition-fast, background $transition-fast;
  width: 100%;
  text-align: left;

  &:hover { color: $color-primary; background: rgba(90, 103, 216, 0.06); }
}

.new-folder-input-wrap {
  padding: 2px 10px 4px;
  display: flex;

  .folder-rename-input { width: 100%; }
}

// ==================== 主内容区 ====================

.fav-main {
  flex: 1;
  min-width: 0;
  padding: $spacing-sm $spacing-md $spacing-md;
}

.fav-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;
  gap: $spacing-sm;
}

.toolbar-left { display: flex; align-items: center; gap: $spacing-sm; }
.toolbar-right { display: flex; align-items: center; gap: $spacing-xs; }

.fav-title {
  font-size: $font-base;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: $spacing-xs;
}

.title-count {
  font-size: $font-xs;
  font-weight: 400;
  color: var(--el-text-color-placeholder);
}

// 搜索框 — 与 AppHeader .search-box 完全一致
.fav-search {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: $radius-md;
  padding: 0 6px;
  overflow: hidden;
  transition: width $transition-base, border-color $transition-base, background $transition-base;

  &.expanded {
    width: 200px;
    border-color: var(--color-primary);
    background: var(--color-surface);
    padding: 0 8px;

    html.dark & {
      background: var(--color-surface-hover);
    }
  }
}

.search-icon-btn, .search-clear-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
  transition: color $transition-fast;

  &:hover { color: var(--color-text-primary); }
}

.fav-search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--color-text-primary);
  min-width: 0;
  width: 0;

  &::placeholder { color: var(--color-text-muted); }
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background $transition-fast, color $transition-fast;

  &:hover { background: var(--el-fill-color); color: var(--el-text-color-primary); }
  &.active { background: var(--color-primary-subtle); color: var(--color-primary); }
}

// 批量操作栏
.batch-bar {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: 6px $spacing-sm;
  background: rgba(90, 103, 216, 0.06);
  border-radius: $radius-md;
  margin-bottom: $spacing-sm;
  font-size: $font-sm;
}

.batch-count {
  font-weight: 500;
  color: $color-primary;
  flex-shrink: 0;
}

.batch-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: $radius-sm;
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  font-size: $font-xs;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover { border-color: $color-primary; color: $color-primary; }
  &.danger:hover { border-color: var(--el-color-danger); color: var(--el-color-danger); }
  &.text { border-color: transparent; background: none; margin-left: auto; color: var(--el-text-color-placeholder); }
}

// ==================== Feed 列表（与 Blog/index.vue 一致）====================

.fav-skeleton-list { padding: $spacing-sm 0; }

.feed-list { /* dividers via feed-item border-bottom */ }

.fav-item-wrap {
  position: relative;

  &.selected .feed-item { background: rgba(90, 103, 216, 0.04); }
  &:hover .item-menu-area { opacity: 1; }

  // 批量模式：为 checkbox 留出左侧空间，防止覆盖头像
  &.batch-mode .feed-item { padding-left: 28px; }
}

.batch-overlay {
  position: absolute;
  inset: 0;
  z-index: 5;
  cursor: pointer;
}

.batch-checkbox {
  position: absolute;
  top: 20px; // 对齐 feed-item 的 padding-top，与头像顶部齐平
  left: 4px; // 距容器左边 4px，在 padding-left:28px 留出的区域内
  z-index: 10;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid white;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background $transition-fast;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);

  &.checked { background: $color-primary; border-color: $color-primary; }
}

.feed-item {
  padding: 20px 0;
  border-bottom: 1px solid var(--color-border-subtle);
  cursor: pointer;
  transition: background $transition-fast;

  // 不用父级 hover 触发标题变色，改为标题自身 hover —— 判定区域严格收敛到文字范围
  &:last-child { border-bottom: none; }
}

.item-header {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  margin-bottom: 10px;
}

.item-avatar { flex-shrink: 0; }

.item-author {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  &:hover { color: var(--color-primary); }
}

.item-dot {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 0 1px;
}

.item-time {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-left: auto;
}

.item-menu-area {
  opacity: 0;
  transition: opacity $transition-fast;
  flex-shrink: 0;
  margin-left: $spacing-xs;
}

.item-menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: $radius-sm;
  border: none;
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background $transition-fast, color $transition-fast;

  &:hover { background: var(--el-fill-color); color: var(--color-text-primary); }
}

// 批量模式下替代菜单区域的等宽占位，保持时间位置固定
.item-menu-placeholder {
  width: 24px;
  flex-shrink: 0;
}

.item-body {
  display: flex;
  align-items: flex-start;
  gap: $spacing-md;
  margin-bottom: 10px;
}

.item-text {
  flex: 1;
  min-width: 0;
}

.item-title {
  width: fit-content;   // hover 判定收敛到文字宽度
  max-width: 100%;      // 不超出容器
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.45;
  transition: color $transition-fast;
  cursor: pointer;

  &:hover { color: var(--color-primary); }
}

.item-summary {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-cover {
  width: 96px;
  height: 72px;
  border-radius: $radius-sm;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid var(--color-border);
}

.item-footer {
  display: flex;
  align-items: center;
  gap: $spacing-md;
}

.item-stat {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.item-tag {
  font-size: 11px;
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  border-radius: $radius-sm;
  padding: 1px 6px;
  margin-left: auto;
}

.load-more {
  display: flex;
  justify-content: center;
  padding: $spacing-md 0;
}

// ==================== 上下文菜单 ====================

.menu-mask {
  position: fixed;
  inset: 0;
  z-index: 1999;
}

.card-context-menu {
  position: fixed;
  z-index: 2000;
  min-width: 148px;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  box-shadow: $shadow-lg;
  padding: 4px;
  animation: menu-in 0.1s ease;
}

@keyframes menu-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.menu-item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  width: 100%;
  padding: 7px $spacing-md;
  border: none;
  background: none;
  color: var(--el-text-color-regular);
  font-size: $font-sm;
  cursor: pointer;
  border-radius: $radius-md;
  text-align: left;
  transition: background $transition-fast, color $transition-fast;

  &:hover { background: var(--el-fill-color-light); color: var(--el-text-color-primary); }
  &.danger:hover { background: rgba(239, 68, 68, 0.08); color: var(--el-color-danger); }
}

.menu-divider {
  height: 1px;
  background: var(--el-border-color-lighter);
  margin: 3px 0;
}

// ==================== 移动对话框 ====================

.move-folder-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.move-folder-item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: 8px $spacing-md;
  border-radius: $radius-md;
  cursor: pointer;
  font-size: $font-sm;
  color: var(--el-text-color-regular);
  transition: background $transition-fast;
  border: 1px solid transparent;

  &:hover { background: var(--el-fill-color-light); }
  &.active { background: rgba(90, 103, 216, 0.08); border-color: $color-primary; color: $color-primary; font-weight: 500; }
}
</style>
