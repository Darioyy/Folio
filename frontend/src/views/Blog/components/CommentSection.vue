<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import type { CommentItem } from '@/api/modules/comments'
import { commentsApi } from '@/api/modules/comments'
import { useUserStore } from '@/stores/user'
import { fromNow } from '@/utils/format'

const PAGE_SIZE = 20

const props = defineProps<{ postId: number }>()

const router = useRouter()
const userStore = useUserStore()
const BASE_URL = import.meta.env.VITE_API_BASE_URL || ""

const comments = ref<CommentItem[]>([])
const total = ref(0)
const page = ref(1)
const hasMore = ref(false)
const loadingMore = ref(false)
const commentInput = ref("")
// parentId: 实际回复目标 ID，forRootId: 所在根评论 ID，afterId: 回复框插在哪条评论/回复之后
const replyTo = ref<{ parentId: number; atName: string; forRootId: number; afterId: number } | null>(null)
const replyInput = ref("")
const submitting = ref(false)
const editingId = ref<number | null>(null)
const editInput = ref("")

function getAvatarUrl(username?: string): string {
  if (!username) return ""
  return BASE_URL + "/users/username/" + username + "/avatar/view"
}

const canDelete = (uid: number) => userStore.currentUser?.id === uid || userStore.isAdminOrRoot
const canEdit = (uid: number) => userStore.currentUser?.id === uid

async function loadComments(reset = false) {
  if (reset) { page.value = 1; comments.value = [] }
  loadingMore.value = true
  try {
    const res = await commentsApi.getList(props.postId, page.value, PAGE_SIZE).catch(() => null)
    if (res?.data) {
      comments.value = reset ? res.data.items : [...comments.value, ...res.data.items]
      total.value = res.data.total
      hasMore.value = page.value < res.data.pages
    }
  } finally {
    loadingMore.value = false
  }
}

async function loadMore() {
  page.value++
  await loadComments()
}

async function send(content: string, parentId?: number) {
  if (!content.trim() || submitting.value) return
  submitting.value = true
  try {
    await commentsApi.create(props.postId, content.trim(), parentId)
    commentInput.value = ""
    replyTo.value = null
    replyInput.value = ""
    await loadComments(true)
  } catch { /* 静默 */ } finally {
    submitting.value = false
  }
}

function sendReply() {
  if (!replyTo.value) return
  send(`@${replyTo.value.atName} ${replyInput.value.trim()}`, replyTo.value.parentId)
}

async function remove(id: number) {
  try {
    await ElMessageBox.confirm('确认删除这条评论？', '删除评论', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })
  } catch { return }
  await commentsApi.delete(id).catch(() => null)
  await loadComments(true)
}

function startEdit(c: CommentItem) { editingId.value = c.id; editInput.value = c.content }
function cancelEdit() { editingId.value = null; editInput.value = "" }

async function submitEdit(id: number) {
  const content = editInput.value.trim()
  if (!content) return
  try {
    await commentsApi.update(id, content)
    cancelEdit()
    await loadComments(true)
  } catch { ElMessage.error('编辑失败') }
}

async function toggleLike(c: CommentItem) {
  if (!userStore.isLoggedIn) return router.push('/login')
  try {
    const res = await commentsApi.toggleLike(c.id)
    if (res?.data) { c.liked = res.data.liked; c.like_count = res.data.like_count }
  } catch { /* 静默 */ }
}

function openReplyTo(parentId: number, atName: string, forRootId: number, afterId: number) {
  const same = replyTo.value?.afterId === afterId && replyTo.value?.atName === atName
  if (same) {
    replyTo.value = null
  } else {
    replyTo.value = { parentId, atName, forRootId, afterId }
    replyInput.value = ""
    nextTick(() => {
      // 直接查询刚出现的 reply-compose 内 input，比 template ref 更可靠
      const el = document.querySelector(`[data-reply-id="${afterId}"] input`) as HTMLInputElement
      el?.focus()
    })
  }
}

onMounted(() => loadComments(true))
</script>

<template>
  <section id="comments" class="comments-section">
    <h3 class="section-title">评论 ({{ total }})</h3>

    <div v-if="userStore.isLoggedIn" class="comment-compose">
      <el-input v-model="commentInput" type="textarea" :rows="2" placeholder="说点什么..." resize="none" />
      <el-button type="primary" size="small" :loading="submitting" @click="send(commentInput)">发布</el-button>
    </div>
    <p v-else class="login-hint">
      <router-link to="/login">登录</router-link>后参与讨论
    </p>

    <div v-for="c in comments" :key="c.id" class="comment-item">
      <el-avatar :size="32" :src="getAvatarUrl(c.username)" class="c-avatar">
        {{ (c.nickname || c.username || '?')[0].toUpperCase() }}
      </el-avatar>
      <div class="c-body">
        <div class="c-header">
          <span class="c-name" @click="c.username && router.push('/u/' + c.username)">
            {{ c.nickname || c.username }}
          </span>
          <span class="c-time">{{ fromNow(c.created_at) }}</span>
          <div class="c-right-actions">
            <button :class="['like-btn', { liked: c.liked }]" @click="toggleLike(c)">
              <svg viewBox="0 0 16 16" width="13" height="13" fill="currentColor" stroke="none">
                <path v-if="c.liked" d="M8 14s-6-3.8-6-8a4 4 0 018 0 4 4 0 018 0c0 4.2-6 8-6 8z"/>
                <path v-else fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" d="M8 14s-6-3.8-6-8a4 4 0 018 0 4 4 0 018 0c0 4.2-6 8-6 8z"/>
              </svg>
              <span v-if="c.like_count">{{ c.like_count }}</span>
            </button>
            <el-dropdown v-if="canDelete(c.user_id)" trigger="click" @command="(cmd: string) => cmd === 'edit' ? startEdit(c) : remove(c.id)">
              <button class="menu-btn">
                <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor"><circle cx="3" cy="8" r="1.2"/><circle cx="8" cy="8" r="1.2"/><circle cx="13" cy="8" r="1.2"/></svg>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="canEdit(c.user_id)" command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="delete" style="color: var(--el-color-danger)">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <div v-if="editingId === c.id" class="edit-compose">
          <el-input v-model="editInput" type="textarea" :rows="2" size="small" resize="none" />
          <div class="edit-actions">
            <el-button size="small" :loading="submitting" @click="submitEdit(c.id)">保存</el-button>
            <el-button size="small" @click="cancelEdit">取消</el-button>
          </div>
        </div>
        <p v-else class="c-text">{{ c.content }}</p>
        <button v-if="userStore.isLoggedIn && editingId !== c.id" class="reply-link"
          @click="openReplyTo(c.id, c.nickname || c.username || '', c.id, c.id)">回复</button>

        <!-- 回复框紧跟在被回复的根评论下（afterId === c.id，且没有被某条回复抢占） -->
        <div v-if="replyTo && replyTo.forRootId === c.id && replyTo.afterId === c.id"
             :data-reply-id="c.id" class="reply-compose">
          <el-input v-model="replyInput" :placeholder="'回复 @' + replyTo.atName" size="small" />
          <el-button size="small" :loading="submitting" @click="sendReply">发送</el-button>
          <el-button size="small" @click="replyTo = null">取消</el-button>
        </div>

        <div v-for="r in c.replies" :key="r.id" class="reply-item">
          <el-avatar :size="24" :src="getAvatarUrl(r.username)" class="c-avatar">
            {{ (r.nickname || r.username || '?')[0].toUpperCase() }}
          </el-avatar>
          <div style="flex:1;min-width:0">
            <div class="c-header">
              <span class="c-name" @click="r.username && router.push('/u/' + r.username)">
                {{ r.nickname || r.username }}
              </span>
              <span class="c-time">{{ fromNow(r.created_at) }}</span>
              <div class="c-right-actions">
                <button :class="['like-btn', { liked: r.liked }]" @click="toggleLike(r)">
                  <svg viewBox="0 0 16 16" width="13" height="13" fill="currentColor" stroke="none">
                    <path v-if="r.liked" d="M8 14s-6-3.8-6-8a4 4 0 018 0 4 4 0 018 0c0 4.2-6 8-6 8z"/>
                    <path v-else fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" d="M8 14s-6-3.8-6-8a4 4 0 018 0 4 4 0 018 0c0 4.2-6 8-6 8z"/>
                  </svg>
                  <span v-if="r.like_count">{{ r.like_count }}</span>
                </button>
                <el-dropdown v-if="canDelete(r.user_id)" trigger="click" @command="(cmd: string) => cmd === 'edit' ? startEdit(r) : remove(r.id)">
                  <button class="menu-btn">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor"><circle cx="3" cy="8" r="1.2"/><circle cx="8" cy="8" r="1.2"/><circle cx="13" cy="8" r="1.2"/></svg>
                  </button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item v-if="canEdit(r.user_id)" command="edit">编辑</el-dropdown-item>
                      <el-dropdown-item command="delete" style="color: var(--el-color-danger)">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
            <div v-if="editingId === r.id" class="edit-compose">
              <el-input v-model="editInput" type="textarea" :rows="2" size="small" resize="none" />
              <div class="edit-actions">
                <el-button size="small" @click="submitEdit(r.id)">保存</el-button>
                <el-button size="small" @click="cancelEdit">取消</el-button>
              </div>
            </div>
            <p v-else class="c-text">{{ r.content }}</p>
            <button v-if="userStore.isLoggedIn && editingId !== r.id" class="reply-link"
              @click="openReplyTo(c.id, r.nickname || r.username || '', c.id, r.id)">回复</button>

            <!-- 回复框紧跟在被回复的子评论下 -->
            <div v-if="replyTo && replyTo.forRootId === c.id && replyTo.afterId === r.id"
                 :data-reply-id="r.id" class="reply-compose reply-compose--inline">
              <el-input v-model="replyInput" :placeholder="'回复 @' + replyTo.atName" size="small" />
              <el-button size="small" :loading="submitting" @click="sendReply">发送</el-button>
              <el-button size="small" @click="replyTo = null">取消</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-empty v-if="!comments.length && !loadingMore" description="暂无评论" :image-size="60" />

    <div v-if="hasMore" class="load-more-comments">
      <el-button text :loading="loadingMore" @click="loadMore">加载更多评论</el-button>
    </div>
  </section>
</template>

<style lang="scss" scoped>
.comments-section { margin-top: $spacing-2xl; }

.section-title {
  font-size: $font-base;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 $spacing-md;
}

.comment-compose {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  align-items: flex-end;
  margin-bottom: $spacing-lg;
}

.login-hint {
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  margin-bottom: $spacing-lg;
  a { color: $color-primary; }
}

.comment-item {
  display: flex;
  gap: $spacing-md;
  padding: $spacing-md 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  &:last-of-type { border-bottom: none; }
}

.c-avatar { flex-shrink: 0; }
.c-body { flex: 1; min-width: 0; }

.c-header {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: 4px;
}

.c-name {
  font-size: $font-sm;
  font-weight: 600;
  color: var(--el-text-color-primary);
  cursor: pointer;
  &:hover { color: $color-primary; }
}

.c-time { font-size: $font-xs; color: var(--el-text-color-placeholder); }

.c-right-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
}

.like-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: none;
  border: none;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  padding: 2px 6px;
  border-radius: $radius-sm;
  font-size: $font-xs;
  transition: color $transition-fast;

  &:hover { color: #ef4444; }
  &.liked { color: #ef4444; }
}

.menu-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: none;
  border: none;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  border-radius: $radius-sm;
  padding: 0;
  transition: background $transition-fast, color $transition-fast;

  &:hover { background: var(--el-fill-color); color: var(--el-text-color-secondary); }
}

.c-text {
  font-size: $font-sm;
  color: var(--el-text-color-regular);
  margin: 4px 0;
  line-height: 1.6;
  word-break: break-word;
}

.reply-link {
  background: none;
  border: none;
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  padding: 2px 0;
  &:hover { color: $color-primary; }
}

.reply-compose {
  display: flex;
  gap: $spacing-xs;
  align-items: center;
  margin-top: $spacing-sm;
}

.reply-item {
  display: flex;
  gap: $spacing-sm;
  margin-top: $spacing-sm;
  padding: $spacing-sm;
  background: var(--el-fill-color-light);
  border-radius: $radius-lg;
}

.edit-compose { margin: 4px 0; }

.edit-actions {
  display: flex;
  gap: $spacing-xs;
  margin-top: $spacing-xs;
  justify-content: flex-end;
}

.load-more-comments {
  display: flex;
  justify-content: center;
  padding-top: $spacing-md;
}
</style>
