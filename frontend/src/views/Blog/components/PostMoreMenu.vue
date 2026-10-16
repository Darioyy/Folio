<template>
  <div v-if="showMoreMenu" class="more-wrap" ref="moreWrapRef">
    <button class="more-btn" :class="{ active: moreOpen }" @click.stop="moreOpen = !moreOpen" title="更多操作">
      <svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor">
        <circle cx="3" cy="8" r="1.3"/><circle cx="8" cy="8" r="1.3"/><circle cx="13" cy="8" r="1.3"/>
      </svg>
    </button>
    <Transition name="menu-pop">
      <div v-if="moreOpen" class="more-menu" @click.stop>

        <!-- ① 编辑 / 置顶 — 作者与 Root 的内容管理 -->
        <button v-if="showEdit" class="more-item"
          @click="() => { moreOpen = false; router.push({ name: 'PostEdit', params: { id: post!.id } }) }">
          <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11.5 2.5a1.414 1.414 0 0 1 2 2L5 13 2 14l1-3 8.5-8.5z"/>
          </svg>
          编辑
        </button>
        <button v-if="showPin" class="more-item pin-item" @click="handlePin">
          <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9.5 1.5L14.5 6.5L11 10L10 13L3 6L6 5Z"/><line x1="1.5" y1="14.5" x2="5.5" y2="10.5"/>
          </svg>
          {{ post?.is_pinned ? '取消置顶' : '置顶' }}
        </button>

        <div v-if="sep1" class="more-sep" />

        <!-- ② 隐藏 / 取消隐藏 — 管理员审核操作 -->
        <button v-if="showHide" class="more-item hide-item" @click="emitOpenHide">
          <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M13.5 13.5L2.5 2.5"/><path d="M6.3 3.2A6.6 6.6 0 018 3c4 0 6.5 5 6.5 5a13 13 0 01-2.1 2.8M4.6 4.6A13 13 0 001.5 8s2.5 5 6.5 5a6.5 6.5 0 003.4-1"/>
            <circle cx="8" cy="8" r="2" stroke-dasharray="3 1.4"/>
          </svg>
          {{ post?.is_hidden ? '取消隐藏' : '隐藏博文' }}
        </button>

        <div v-if="sep2" class="more-sep" />

        <!-- ③ 举报 — 普通用户对他人内容的反馈 -->
        <button v-if="showReport" class="more-item report-item" @click="emitOpenReport">
          <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 2h10l-3 5 3 5H3V2z"/>
          </svg>
          举报
        </button>

        <div v-if="sep3" class="more-sep" />

        <!-- ④ 删除 — 不可逆操作，置于最末 -->
        <button v-if="showDelete" class="more-item delete-item" :disabled="deleteLoading" @click="handleDelete">
          <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="2 4 14 4"/><path d="M5 4V2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 .5.5V4"/><path d="M13 4l-.8 8.5a1 1 0 0 1-1 .9H4.8a1 1 0 0 1-1-.9L3 4"/>
          </svg>
          删除
        </button>

      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Post } from '@/types/models'
import { postsApi } from '@/api/modules/posts'
import { useUserStore } from '@/stores/user'

const props = defineProps<{
  post: Post | null
}>()

const emit = defineEmits<{
  'pin-updated': [isPinned: boolean | undefined]
  'open-report': []
  'open-hide': []
}>()

const router = useRouter()
const userStore = useUserStore()

const moreOpen = ref(false)
const moreWrapRef = ref<HTMLElement | null>(null)
const deleteLoading = ref(false)

const isAuthor     = computed(() => !!userStore.currentUser && userStore.currentUser.id === props.post?.author_id)
const isAdminOrRoot = computed(() => !!(userStore.currentUser?.is_admin || userStore.currentUser?.is_root))

const canHidePost = computed(() => {
  if (!isAdminOrRoot.value) return false
  if (userStore.isRoot) return true
  return !(props.post as any)?.author_is_root
})
const canDeletePost = computed(() => {
  if (!userStore.isLoggedIn) return false
  if (isAuthor.value) return true
  if (!isAdminOrRoot.value) return false
  if (userStore.isRoot) return true
  return !(props.post as any)?.author_is_root
})

const showEdit   = computed(() => isAuthor.value)
const showPin    = computed(() => userStore.isRoot)
const showHide   = computed(() => canHidePost.value)
const showReport = computed(() => userStore.isLoggedIn && !isAuthor.value && !isAdminOrRoot.value)
const showDelete = computed(() => canDeletePost.value)

const hasG1 = computed(() => showEdit.value || showPin.value)
const hasG2 = computed(() => showHide.value)
const hasG3 = computed(() => showReport.value)
const hasG4 = computed(() => showDelete.value)

const showMoreMenu = computed(() => hasG1.value || hasG2.value || hasG3.value || hasG4.value)
const sep1 = computed(() => hasG1.value && (hasG2.value || hasG3.value || hasG4.value))
const sep2 = computed(() => hasG2.value && (hasG3.value || hasG4.value))
const sep3 = computed(() => hasG3.value && hasG4.value)

async function handlePin() {
  if (!props.post) return
  moreOpen.value = false
  const newPinned = !props.post.is_pinned
  try {
    const res = await postsApi.togglePin(props.post.id, newPinned)
    if (res.success) {
      emit('pin-updated', res.data?.is_pinned)
      ElMessage.success(newPinned ? '已置顶，已通知所有成员' : '已取消置顶')
    }
  } catch { /* 拦截器已处理 */ }
}

function emitOpenReport() {
  moreOpen.value = false
  emit('open-report')
}

function emitOpenHide() {
  moreOpen.value = false
  emit('open-hide')
}

async function handleDelete() {
  if (!props.post) return
  moreOpen.value = false
  try {
    await ElMessageBox.confirm(
      `确定要永久删除「${props.post.title}」吗？此操作不可恢复。`,
      '删除博文',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning', confirmButtonClass: 'el-button--danger' }
    )
  } catch { return }
  deleteLoading.value = true
  try {
    await postsApi.delete(props.post.id)
    ElMessage.success('博文已删除')
    router.push('/blog')
  } catch { /* 拦截器已处理 */ } finally { deleteLoading.value = false }
}

function handleOutside(e: MouseEvent) {
  if (moreWrapRef.value && !moreWrapRef.value.contains(e.target as Node)) moreOpen.value = false
}

onMounted(() => document.addEventListener('click', handleOutside))
onUnmounted(() => document.removeEventListener('click', handleOutside))
</script>

<style scoped lang="scss">
.more-wrap { position: relative; flex-shrink: 0; margin-top: 6px; }

.more-btn {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border: none; background: transparent;
  border-radius: $radius-sm; color: var(--el-text-color-placeholder);
  cursor: pointer; transition: color $transition-fast, background $transition-fast;
  &:hover, &.active { color: var(--el-text-color-primary); background: var(--el-fill-color-light); }
}

.more-menu {
  position: absolute; top: calc(100% + 4px); right: 0;
  min-width: 124px; background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.09);
  padding: 4px; z-index: 50;
}

.more-sep { height: 1px; background: var(--el-border-color-lighter); margin: 4px 0; }

.more-item {
  display: flex; align-items: center; gap: 8px;
  width: 100%; padding: 7px 10px; border: none; background: transparent;
  border-radius: 5px; font-size: 13px; color: var(--el-text-color-primary);
  cursor: pointer; text-align: left; white-space: nowrap; font-family: inherit;
  transition: background $transition-fast;
  &:hover { background: var(--el-fill-color-light); }
  svg { flex-shrink: 0; color: var(--el-text-color-secondary); }
  &.pin-item    { color: $color-primary; svg { color: $color-primary; } &:hover { background: var(--color-primary-subtle); } }
  &.hide-item   { color: #d97706; svg { color: #d97706; } &:hover { background: rgba(217,119,6,0.06); } }
  &.report-item { color: #f97316; svg { color: #f97316; } &:hover { background: rgba(249,115,22,0.06); } }
  &.delete-item { color: #ef4444; svg { color: #ef4444; } &:hover { background: rgba(239,68,68,0.06); } &:disabled { opacity: 0.5; cursor: not-allowed; } }
}

.menu-pop-enter-active { transition: opacity 0.12s ease, transform 0.14s cubic-bezier(0.34,1.56,0.64,1); }
.menu-pop-leave-active { transition: opacity 0.08s ease; }
.menu-pop-enter-from { opacity: 0; transform: translateY(-4px) scale(0.96); }
.menu-pop-leave-to { opacity: 0; }
</style>
