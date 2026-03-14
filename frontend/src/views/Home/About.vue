<template>
  <div class="about-page">
    <button class="page-back-btn" @click="goBack" title="返回">
      <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="10 3 5 8 10 13"/>
      </svg>
    </button>

    <div class="about-wrap">

      <!-- 页眉 -->
      <header class="page-header">
        <div class="header-eyebrow">关于</div>
        <h1 class="header-title">Folio</h1>
        <p class="header-desc">私有云存储 · 轻博客社区</p>
      </header>

      <!-- 数据概览（紧跟标题，有数据时显示）-->
      <div v-if="stats.posts > 0" class="stats-strip">
        <div class="stat-item">
          <span class="stat-num">{{ stats.posts }}</span>
          <span class="stat-label">篇文章</span>
        </div>
        <div class="stat-dot">·</div>
        <div class="stat-item">
          <span class="stat-num">{{ stats.users }}</span>
          <span class="stat-label">位用户</span>
        </div>
        <div class="stat-dot">·</div>
        <div class="stat-item">
          <span class="stat-num">{{ stats.categories }}</span>
          <span class="stat-label">个专栏</span>
        </div>
      </div>

      <div class="sections">

        <!-- 联系我们 / 站主卡 -->
        <section class="section" id="contact">
          <h2 class="section-title">站主</h2>
          <div
            v-if="owner"
            class="owner-card"
            :class="{ clickable: !!owner.username }"
            @click="goToProfile"
          >
            <div class="owner-avatar">
              <img
                v-if="owner.username && !avatarError"
                :src="avatarUrl"
                alt=""
                @error="avatarError = true"
              />
              <span class="avatar-fallback">
                {{ (owner.nickname || owner.username || 'F')[0].toUpperCase() }}
              </span>
            </div>
            <div class="owner-info">
              <span class="owner-name">{{ owner.nickname || owner.username }}</span>
              <span class="owner-handle">@{{ owner.username }} · 站主</span>
              <p v-if="siteInfo.site_bio" class="owner-bio">{{ siteInfo.site_bio }}</p>
            </div>
          </div>
          <div v-if="siteInfo.site_contact" class="contact-row">
            <span class="contact-label">联系</span>
            <span class="contact-value">{{ siteInfo.site_contact }}</span>
          </div>
        </section>

        <div class="divider"></div>

        <!-- 功能特色 -->
        <section class="section">
          <h2 class="section-title">功能特色</h2>
          <div class="features-list">
            <div v-for="f in features" :key="f.title" class="feature-row">
              <div class="feature-icon" v-html="f.icon"></div>
              <div class="feature-body">
                <span class="feature-name">{{ f.title }}</span>
                <span class="feature-sep">—</span>
                <span class="feature-desc">{{ f.desc }}</span>
              </div>
            </div>
          </div>
        </section>

        <div class="divider"></div>

        <!-- 技术栈 -->
        <section class="section">
          <h2 class="section-title">技术栈</h2>
          <div class="stack-list">
            <div v-for="g in techGroups" :key="g.label" class="stack-group">
              <span class="stack-label">{{ g.label }}</span>
              <div class="stack-items">
                <span v-for="t in g.items" :key="t" class="stack-tag">{{ t }}</span>
              </div>
            </div>
          </div>
        </section>

      </div>

      <footer class="page-footer">© {{ year }} Folio</footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { systemApi, type SiteOwner, type SiteInfo } from '@/api/modules/system'

const router = useRouter()

function goBack() {
  if (window.history.state?.back) router.back()
  else router.push('/blog')
}

const owner = ref<SiteOwner | null>(null)
const siteInfo = ref<SiteInfo>({ site_bio: '', site_contact: '' })
const avatarError = ref(false)
const year = new Date().getFullYear()
const stats = ref({ posts: 0, users: 0, categories: 0 })

const SVG_ATTRS = `viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"`
const features = [
  {
    icon: `<svg ${SVG_ATTRS}><path d="M15.5 9.5A4 4 0 0 0 8.2 7 5 5 0 1 0 5 16.5h10a3.5 3.5 0 0 0 .5-7z"/><polyline points="8 13 10 11 12 13"/><line x1="10" y1="11" x2="10" y2="16"/></svg>`,
    title: '私有云盘', desc: '文件上传与分组、拖拽整理、批量操作，数据完全自托管。',
  },
  {
    icon: `<svg ${SVG_ATTRS}><path d="M13.5 3.5a1.5 1.5 0 0 1 2.121 2.121L6.5 14.75l-3 .75.75-3 9.25-9z"/><line x1="4" y1="17" x2="16" y2="17"/></svg>`,
    title: '轻博客', desc: 'Markdown 编辑、封面图、附件挂载、专栏分类，发布属于自己的文章。',
  },
  {
    icon: `<svg ${SVG_ATTRS}><circle cx="7.5" cy="7" r="2.5"/><path d="M2 17a5.5 5.5 0 0 1 11 0"/><circle cx="14.5" cy="7" r="2" opacity=".55"/><path d="M14.5 11a4.5 4.5 0 0 1 3.5 4.3" opacity=".55"/></svg>`,
    title: '社区互动', desc: '关注、点赞、收藏、评论，构建有温度的小型内容社区。',
  },
  {
    icon: `<svg ${SVG_ATTRS}><rect x="4" y="9" width="12" height="9" rx="2"/><path d="M7 9V6.5a3 3 0 0 1 6 0V9"/><circle cx="10" cy="13.5" r="1" fill="currentColor" stroke="none"/></svg>`,
    title: '权限分级', desc: '三级权限体系（用户 / 管理员 / Root），精细控制访问与内容管理。',
  },
]

const techGroups = [
  { label: '前端', items: ['Vue 3', 'TypeScript', 'Vite', 'Element Plus', 'Pinia'] },
  { label: '后端', items: ['Flask', 'Python', 'SQLAlchemy', 'Pydantic'] },
  { label: '基础设施', items: ['MySQL 8', 'Docker', 'Nginx', 'Gunicorn'] },
]

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const avatarUrl = computed(() =>
  owner.value?.username ? `${BASE_URL}/users/username/${owner.value.username}/avatar/view` : ''
)

function goToProfile() {
  if (owner.value?.username)
    router.push({ name: 'UserProfile', params: { username: owner.value.username } })
}

onMounted(async () => {
  try {
    const [ownerRes, siteRes, infoRes] = await Promise.all([
      systemApi.getOwner().catch(() => ({ data: null })),
      systemApi.getSiteInfo().catch(() => ({ data: null })),
      systemApi.getInfo().catch(() => ({ data: null })),
    ])
    owner.value = ownerRes.data || null
    if (siteRes.data) siteInfo.value = siteRes.data
    if (infoRes.data?.database_stats) {
      const s = infoRes.data.database_stats
      stats.value = { posts: s.posts || 0, users: s.users || 0, categories: s.categories || 0 }
    }
  } catch { /* silent */ }
})
</script>

<style scoped lang="scss">
.about-page {
  min-height: calc(100vh - 52px);
  background: var(--color-surface-raised, #f8f9fb);
  padding: $spacing-2xl $spacing-md $spacing-2xl;
}

.about-wrap {
  max-width: 560px;
  margin: 0 auto;
}

// ── 页眉 ─────────────────────────────────────────────
.page-header {
  margin-bottom: 40px;
  padding-bottom: 28px;
  border-bottom: 1px solid var(--color-border);
  position: relative;

  &::after {
    content: '';
    position: absolute;
    left: 0; bottom: -1px;
    width: 40px; height: 2px;
    background: linear-gradient(90deg, $color-primary, transparent);
    border-radius: 1px;
  }
}

.header-eyebrow {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: $color-primary;
  margin-bottom: 10px;
}

.header-title {
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -1.5px;
  margin: 0 0 10px;
  background: linear-gradient(135deg, $color-primary 0%, #7c3aed 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.6;
}

// ── 内容区 ────────────────────────────────────────────
.sections { display: flex; flex-direction: column; gap: 32px; }
.section { display: flex; flex-direction: column; gap: 14px; }

.section-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  margin: 0;
}

.section-text {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.75;
  margin: 0;
}

// ── 技术栈 ────────────────────────────────────────────
.stack-list { display: flex; flex-direction: column; gap: 9px; }
.stack-group { display: flex; align-items: flex-start; gap: 12px; }
.stack-label {
  flex-shrink: 0;
  width: 64px;
  font-size: 12px;
  color: var(--color-text-muted);
  padding-top: 4px;
}
.stack-items { display: flex; flex-wrap: wrap; gap: 5px; }
.stack-tag {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 9px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: $radius-sm;
  font-size: 12px;
  color: var(--color-text-secondary);
  font-family: $font-mono;
}

// ── 分隔线 ────────────────────────────────────────────
.divider { height: 1px; background: var(--color-border); }

// ── 站主卡片 ──────────────────────────────────────────
.owner-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: $radius-lg;
  transition: border-color $transition-fast;

  &.clickable { cursor: pointer; &:hover { border-color: $color-primary; } }
}

.owner-avatar {
  position: relative;
  width: 40px; height: 40px;
  border-radius: 50%;
  background: rgba(90, 103, 216, 0.08);
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;

  img {
    position: absolute; inset: 0;
    width: 100%; height: 100%;
    object-fit: cover; border-radius: 50%;
  }
}

.avatar-fallback {
  font-size: 15px; font-weight: 700;
  color: $color-primary; user-select: none;
}

.owner-info { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.owner-name { font-size: 14px; font-weight: 600; color: var(--color-text-primary); }
.owner-handle { font-size: 12px; color: var(--color-text-muted); }
.owner-bio {
  font-size: 13px; color: var(--color-text-secondary);
  margin: 5px 0 0; line-height: 1.6;
  overflow: hidden; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}

// ── 联系方式 ──────────────────────────────────────────
.contact-row {
  display: flex; gap: 12px; align-items: baseline;
}
.contact-label {
  flex-shrink: 0; width: 36px;
  font-size: 12px; color: var(--color-text-muted);
}
.contact-value { font-size: 13px; color: var(--color-text-primary); word-break: break-all; }

// ── 功能特色 ──────────────────────────────────────────
.features-list { display: flex; flex-direction: column; gap: 10px; }
.feature-row {
  display: flex; align-items: flex-start; gap: 10px;
}
.feature-icon { font-size: 16px; flex-shrink: 0; line-height: 1.5; }
.feature-body {
  font-size: 13px; line-height: 1.6; color: var(--color-text-secondary);
  flex: 1; min-width: 0;
}
.feature-name { font-weight: 600; color: var(--color-text-primary); }
.feature-sep { color: var(--color-text-muted); margin: 0 5px; }

// ── 数据概览 ──────────────────────────────────────────
.stats-strip {
  display: flex; align-items: center; justify-content: center; gap: 20px;
  padding: 16px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: $radius-lg;
  margin-bottom: 32px;
}
.stat-item { display: flex; flex-direction: column; align-items: center; gap: 3px; }
.stat-num {
  font-size: 22px; font-weight: 700;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums; letter-spacing: -0.5px;
}
.stat-label { font-size: 11px; color: var(--color-text-muted); }
.stat-dot { font-size: 18px; color: var(--color-border); }

// ── 返回按钮（fixed，与 Blog/Detail.vue 同款）────────
.page-back-btn {
  position: fixed;
  top: 100px;
  left: max(16px, calc(50vw - 450px));
  z-index: 40;
  width: 30px; height: 30px;
  border-radius: 50%;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0.75;
  transition: opacity 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  &:hover {
    opacity: 1;
    color: $color-primary;
    border-color: $color-primary;
    box-shadow: 0 2px 8px rgba(90,103,216,0.15);
  }
}

// ── 页脚 ─────────────────────────────────────────────
.page-footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border-subtle);
  font-size: 11px;
  color: var(--color-text-muted);
  opacity: 0.55;
  text-align: center;
}
</style>
