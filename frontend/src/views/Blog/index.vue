<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Star, ChatLineRound, View } from '@element-plus/icons-vue'
import { useBlogFeed } from '@/composables/useBlogFeed'
import { postsApi } from '@/api/modules/posts'
import { systemApi, type SiteOwner, type SiteInfo } from '@/api/modules/system'
import { useUserStore } from '@/stores/user'
import { fromNow, getFileUrl } from '@/utils/format'
import type { Post, Category } from '@/types/models'
import FeedbackModal from '@/components/business/FeedbackModal.vue'

const TABS = [
  { value: 'recommend' as const, label: '推荐' },
  { value: 'following' as const, label: '关注' },
  { value: 'column' as const, label: '专栏' },
]

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { activeTab, posts, loading, loadingMore, hasMore, selectedCategory,
  loadPosts, switchTab, loadMore, selectCategory } = useBlogFeed()

const categories = ref<Category[]>([])
const hotPosts = ref<Post[]>([])
const showFeedback = ref(false)
const siteOwner = ref<SiteOwner | null>(null)
const siteInfo = ref<SiteInfo>({ site_bio: '', site_contact: '' })

const currentCategoryName = computed(() =>
  categories.value.find(c => c.id === selectedCategory.value)?.name || ''
)
function backToColumns() { selectedCategory.value = null }

function coverUrl(post: Post) {
  return post.cover_image_url ? getFileUrl(post.cover_image_url) : ''
}
function authorAvatarUrl(post: Post) {
  if (!post.author_name) return ''
  return `${import.meta.env.VITE_API_BASE_URL || ''}/users/username/${post.author_name}/avatar/view`
}
function displayName(post: Post) {
  return post.author_nickname || post.author_name || '未知用户'
}
function timeStr(post: Post) {
  const t = post.published_at || post.created_at
  return t ? fromNow(t) : ''
}
function goToPost(id: number) { router.push(`/post/${id}`) }
function goToAuthor(e: MouseEvent, username?: string) {
  e.stopPropagation()
  if (username) router.push({ name: 'UserProfile', params: { username } })
}
const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
function ownerAvatarUrl(username: string) {
  return `${BASE_URL}/users/username/${username}/avatar/view`
}
function goToOwnerProfile() {
  if (siteOwner.value?.username)
    router.push({ name: 'UserProfile', params: { username: siteOwner.value.username } })
}


async function init() {
  try {
    const [catRes, hotRes, ownerRes, siteRes] = await Promise.all([
      postsApi.getCategories(),
      postsApi.getPaginatedList({ limit: 7, sort: 'hot' }),
      systemApi.getOwner().catch(() => ({ data: null })),
      systemApi.getSiteInfo().catch(() => ({ data: null })),
    ])
    if (catRes.data) categories.value = catRes.data
    hotPosts.value = hotRes.items || []
    siteOwner.value = ownerRes.data || null
    if (siteRes.data) siteInfo.value = siteRes.data
  } catch { /* silent */ }
  await loadPosts(true)
}

onMounted(init)

// 从其他路由导航回发现页时重新加载（应对 keep-alive 及各类边缘情况）
watch(() => route.name, (newName, oldName) => {
  if (newName === 'Blog' && oldName !== undefined && oldName !== 'Blog') {
    init()
  }
})
</script>

<template>
  <div class="discover-page">
    <div class="discover-layout">

      <main class="feed-main">
        <div class="feed-card">

          <!-- Tab 导航 -->
          <div class="feed-header">
            <nav class="feed-tabs">
              <button
                v-for="tab in TABS" :key="tab.value"
                :class="['tab-btn', { active: activeTab === tab.value }]"
                @click="switchTab(tab.value)"
              >{{ tab.label }}</button>
            </nav>
          </div>

          <!-- 专栏目录（未选择专栏时） -->
          <div v-if="activeTab === 'column' && !selectedCategory" class="column-list">
            <p v-if="!categories.length" class="column-empty">暂无专栏</p>
            <div
              v-for="cat in categories" :key="cat.id"
              class="column-item"
              @click="selectCategory(cat.id)"
            >
              <div class="column-badge">{{ cat.name[0] }}</div>
              <div class="column-meta">
                <span class="column-name">{{ cat.name }}</span>
                <span v-if="cat.description" class="column-desc">{{ cat.description }}</span>
                <span v-else class="column-desc">暂无简介</span>
              </div>
              <span class="column-enter">进入 →</span>
            </div>
          </div>

          <!-- 推荐 / 关注 / 已选专栏的文章流 -->
          <template v-else>

            <!-- 专栏面包屑 -->
            <div v-if="activeTab === 'column' && selectedCategory" class="column-crumb">
              <button class="crumb-back" @click="backToColumns">← 专栏</button>
              <span class="crumb-sep">/</span>
              <span class="crumb-name">{{ currentCategoryName }}</span>
            </div>

            <!-- 骨架屏 -->
            <div v-if="loading && posts.length === 0" class="skeleton-list">
              <el-skeleton v-for="i in 5" :key="i" animated :rows="3" style="margin-bottom: 20px" />
            </div>

            <!-- 空状态 -->
            <el-empty
              v-else-if="!loading && posts.length === 0"
              description="暂无文章"
              :image-size="60"
              style="padding: 48px 0"
            />

            <!-- 文章列表 -->
            <div v-else class="feed-list">
              <article
                v-for="post in posts" :key="post.id"
                :class="['feed-item', { 'is-pinned': post.is_pinned }]"
                @click="goToPost(post.id)"
              >
                <div class="item-header">
                  <el-avatar :size="22" :src="authorAvatarUrl(post)">
                    {{ displayName(post)[0]?.toUpperCase() }}
                  </el-avatar>
                  <span class="item-author" @click="goToAuthor($event, post.author_name)">
                    {{ displayName(post) }}
                  </span>
                  <span v-if="post.is_pinned" class="pin-badge">置顶</span>
                  <span class="item-time">{{ timeStr(post) }}</span>
                </div>
                <div class="item-body">
                  <div class="item-text">
                    <h2 class="item-title">{{ post.title }}</h2>
                    <p v-if="post.summary" class="item-summary">{{ post.summary }}</p>
                  </div>
                  <img
                    v-if="coverUrl(post)"
                    :src="coverUrl(post)" :alt="post.title"
                    class="item-cover" loading="lazy"
                  />
                </div>
                <div class="item-footer">
                  <span class="item-stat"><el-icon :size="12"><Star /></el-icon>{{ post.like_count }}</span>
                  <span class="item-stat"><el-icon :size="12"><ChatLineRound /></el-icon>{{ post.comment_count }}</span>
                  <span class="item-stat"><el-icon :size="12"><View /></el-icon>{{ post.view_count }}</span>
                  <span v-if="post.category_name" class="item-tag">{{ post.category_name }}</span>
                </div>
              </article>
            </div>

            <!-- 加载更多 / 已到底 -->
            <div v-if="!loading && posts.length > 0" class="load-more">
              <el-button v-if="hasMore" :loading="loadingMore" @click="loadMore">加载更多</el-button>
              <span v-else class="load-end">· 已显示全部 {{ posts.length }} 篇 ·</span>
            </div>

          </template>
        </div>
      </main>

      <!-- 右侧信息栏 -->
      <aside class="right-sidebar">
        <div class="sidebar-card owner-card">
          <div class="owner-row" :class="{ clickable: !!siteOwner }" @click="goToOwnerProfile">
            <div class="owner-avatar-wrap">
              <img
                v-if="siteOwner?.avatar && siteOwner?.username"
                :src="ownerAvatarUrl(siteOwner.username)" alt=""
                class="owner-avatar-img"
                @error="(e: Event) => (e.target as HTMLImageElement).style.display='none'"
              />
              <span class="owner-avatar-fallback">
                {{ (siteOwner?.nickname || siteOwner?.username || 'F')[0].toUpperCase() }}
              </span>
            </div>
            <div class="owner-info">
              <span class="owner-name">{{ siteOwner?.nickname || siteOwner?.username || 'Folio' }}</span>
              <span class="owner-role">@{{ siteOwner?.username || 'root' }} · 站主</span>
            </div>
          </div>
          <p class="owner-bio">{{ siteInfo.site_bio || '私有云盘 + 轻博客社区' }}</p>
          <router-link v-if="userStore.isLoggedIn" to="/post/create" class="publish-btn">+ 发布文章</router-link>
          <router-link v-else to="/login" class="publish-btn ghost">登录后发布</router-link>
        </div>

        <div v-if="hotPosts.length" class="sidebar-card">
          <div class="sidebar-title">本周热门</div>
          <div class="hot-list">
            <div
              v-for="(p, i) in hotPosts" :key="p.id"
              class="hot-item" @click="goToPost(p.id)"
            >
              <span :class="['hot-rank', `rank-${i + 1}`]">{{ i + 1 }}</span>
              <span class="hot-title">{{ p.title }}</span>
            </div>
          </div>
        </div>

        <!-- 站点链接：始终粘性可见 -->
        <div class="sidebar-meta">
          <div class="meta-links">
            <router-link to="/about" class="meta-link">关于网站</router-link>
            <span class="meta-sep">·</span>
            <router-link to="/privacy" class="meta-link">隐私条款</router-link>
            <span class="meta-sep">·</span>
            <button class="meta-link meta-btn" @click.stop="showFeedback = true">反馈</button>
          </div>
          <span class="meta-copy">© 2026 Folio</span>
        </div>
      </aside>
    </div>


    <FeedbackModal v-model="showFeedback" />
  </div>
</template>

<style lang="scss" scoped>
.discover-page { max-width: 1100px; margin: 0 auto; padding: 0 $spacing-md $spacing-2xl; }
.discover-layout { display: grid; grid-template-columns: minmax(0, 1fr) 248px; gap: 28px; align-items: flex-start; }

// Feed 容器
.feed-main { min-width: 0; min-height: 560px; }
.feed-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: $radius-lg; overflow: hidden; }

// Tab 导航
.feed-header { padding: 0 20px; border-bottom: 1px solid var(--color-border); }
.feed-tabs { display: flex; }
.tab-btn {
  padding: 14px 16px 13px;
  font-size: $font-sm; font-weight: 500; color: var(--color-text-secondary);
  background: none; border: none; border-bottom: 2px solid transparent;
  margin-bottom: -1px; cursor: pointer;
  transition: color $transition-fast, border-color $transition-fast;
  &:hover { color: var(--color-text-primary); }
  &.active { color: var(--color-primary); border-bottom-color: var(--color-primary); font-weight: 600; }
}

// 专栏目录
.column-list { padding: 8px 20px 4px; }
.column-empty { padding: 48px 0; text-align: center; font-size: $font-sm; color: var(--color-text-muted); }
.column-item {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 0; border-bottom: 1px solid var(--color-border-subtle); cursor: pointer;
  &:last-child { border-bottom: none; }
  &:hover { .column-name { color: var(--color-primary); } .column-enter { opacity: 1; color: var(--color-primary); } }
}
.column-badge {
  width: 42px; height: 42px; border-radius: $radius-md; flex-shrink: 0;
  background: var(--color-primary-subtle); color: var(--color-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700;
}
.column-meta { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.column-name { font-size: $font-sm; font-weight: 600; color: var(--color-text-primary); transition: color $transition-fast; }
.column-desc { font-size: 12px; color: var(--color-text-muted); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.column-enter { font-size: 12px; color: var(--color-text-muted); flex-shrink: 0; opacity: 0; transition: all $transition-fast; }

// 专栏面包屑
.column-crumb {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 20px; border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface-raised);
}
.crumb-back { font-size: 13px; color: var(--color-primary); background: none; border: none; padding: 0; cursor: pointer; font-family: inherit; &:hover { text-decoration: underline; } }
.crumb-sep { font-size: 13px; color: var(--color-text-muted); }
.crumb-name { font-size: 13px; font-weight: 500; color: var(--color-text-primary); }

// 文章列表
.skeleton-list { padding: 20px; }
.feed-list { display: flex; flex-direction: column; padding: 0 20px; }
.feed-item {
  padding: 20px 0; border-bottom: 1px solid var(--color-border-subtle); cursor: pointer;
  &:last-child { border-bottom: none; }
}
.feed-item.is-pinned {
  background: var(--color-primary-subtle, rgba(90,103,216,0.04));
  margin: 0 -20px;
  padding: 20px;
  border-radius: 0;
}
.item-header { display: flex; align-items: center; gap: 6px; margin-bottom: 10px; }
.item-author { font-size: 13px; font-weight: 500; color: var(--color-text-secondary); cursor: pointer; &:hover { color: var(--color-primary); } }
.pin-badge {
  font-size: 10px; font-weight: 600; letter-spacing: 0.04em;
  padding: 1px 5px; border-radius: 3px;
  background: rgba(90,103,216,0.1); color: $color-primary;
  flex-shrink: 0;
}
.pin-btn {
  background: none; border: none; padding: 0 2px;
  cursor: pointer; font-size: 13px; opacity: 0.4;
  transition: opacity $transition-fast;
  flex-shrink: 0;
  &:hover, &.active { opacity: 1; }
}
.item-time { font-size: 12px; color: var(--color-text-muted); margin-left: auto; }
.item-body { display: flex; align-items: flex-start; gap: $spacing-md; margin-bottom: 10px; }
.item-text { flex: 1; min-width: 0; }
.item-title {
  width: fit-content; max-width: 100%;
  font-size: 17px; font-weight: 600; color: var(--color-text-primary); margin: 0 0 6px;
  overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  line-height: 1.45; transition: color $transition-fast;
  &:hover { color: var(--color-primary); }
}
.item-summary { font-size: 13px; color: var(--color-text-secondary); margin: 0; line-height: 1.6; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.item-cover { width: 100px; height: 72px; border-radius: $radius-sm; object-fit: cover; flex-shrink: 0; border: 1px solid var(--color-border-subtle); }
.item-footer { display: flex; align-items: center; gap: $spacing-md; }
.item-stat { display: flex; align-items: center; gap: 3px; font-size: 12px; color: var(--color-text-muted); }
.item-tag { font-size: 11px; color: var(--color-text-muted); border: 1px solid var(--color-border-subtle); border-radius: $radius-sm; padding: 1px 6px; margin-left: auto; }
.load-more { display: flex; justify-content: center; align-items: center; padding: 20px 0; border-top: 1px solid var(--color-border-subtle); }
.load-end { font-size: 12px; color: var(--color-text-muted); letter-spacing: 0.02em; }

// 右侧栏
.right-sidebar { position: sticky; top: 64px; padding-top: 4px; }
.sidebar-card { padding: 16px; margin-bottom: 12px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: $radius-lg; }
.owner-card { padding-top: 16px; }
.owner-row {
  display: flex; align-items: center; gap: 10px; margin-bottom: $spacing-sm;
  &.clickable { cursor: pointer; border-radius: $radius-sm; margin: -4px; padding: 4px; transition: background $transition-fast; &:hover { background: var(--color-surface-hover); } }
}
.owner-avatar-wrap { width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, $color-primary, #7c3aed); display: flex; align-items: center; justify-content: center; flex-shrink: 0; position: relative; overflow: hidden; }
.owner-avatar-img { width: 100%; height: 100%; object-fit: cover; position: absolute; inset: 0; border-radius: 50%; }
.owner-avatar-fallback { font-size: 15px; font-weight: 700; color: #fff; }
.owner-info { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.owner-name { font-size: $font-sm; font-weight: 600; color: var(--color-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.owner-role { font-size: $font-xs; color: var(--color-text-muted); }
.owner-bio { font-size: 12px; color: var(--color-text-secondary); line-height: 1.6; margin: $spacing-md 0; white-space: pre-wrap; word-break: break-word; }
.publish-btn { display: block; width: 100%; text-align: center; padding: 7px 0; background: $color-primary; color: #fff; border-radius: $radius-md; font-size: $font-13; font-weight: 500; text-decoration: none; transition: background $transition-fast; &:hover { background: $color-primary-dark; } &.ghost { background: none; color: $color-primary; border: 1px solid $color-primary; &:hover { background: var(--color-primary-subtle); } } }
.sidebar-title { font-size: $font-13; font-weight: 600; color: var(--color-text-primary); margin-bottom: $spacing-sm; }
.hot-list { display: flex; flex-direction: column; }
.hot-item { display: flex; align-items: flex-start; gap: $spacing-sm; cursor: pointer; padding: 7px 0; border-bottom: 1px solid var(--color-border-subtle); &:last-child { border-bottom: none; } &:hover .hot-title { color: $color-primary; } }
.hot-rank {
  font-size: 15px; font-weight: 700; width: 20px; flex-shrink: 0; line-height: 1.4;
  color: var(--color-text-muted);
  &.rank-1 { color: #f59e0b; }
  &.rank-2 { color: #94a3b8; }
  &.rank-3 { color: #b45309; }
}
.hot-title { font-size: 12px; color: var(--color-text-secondary); line-height: 1.45; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; transition: color $transition-fast; }

// 侧边栏元信息（始终可见）
.sidebar-meta {
  margin-top: 8px;
  padding: 12px 0 4px;
  border-top: 1px solid var(--color-border-subtle);
}
.meta-links {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 7px;
}
.meta-link {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  color: var(--color-text-muted);
  text-decoration: none;
  letter-spacing: 0.01em;
  line-height: 1;
  transition: color $transition-fast;
  &:hover { color: var(--color-primary); }
}
.meta-sep {
  margin: 0 7px;
  font-size: 10px;
  color: var(--color-text-muted);
  opacity: 0.35;
  line-height: 1;
  user-select: none;
}
.meta-btn { background: none; border: none; padding: 0; cursor: pointer; font-family: inherit; letter-spacing: inherit; }
.meta-copy { display: block; text-align: center; font-size: 11px; color: var(--color-text-muted); opacity: 0.5; letter-spacing: 0.02em; }

// 响应式
@media (max-width: $breakpoint-lg) {
  .discover-layout { grid-template-columns: 1fr; }
  .right-sidebar { display: none; }
}
@media (max-width: $breakpoint-sm) {
  .discover-page { padding: 0 $spacing-sm $spacing-xl; }
  .item-cover { width: 72px; height: 54px; }
  .item-title { font-size: $font-base; }
}
</style>
