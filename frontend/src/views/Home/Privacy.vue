<template>
  <div class="privacy-page">
    <button class="page-back-btn" @click="goBack" title="返回">
      <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="10 3 5 8 10 13"/>
      </svg>
    </button>

    <div class="privacy-wrap">

      <header class="page-header">
        <div class="header-eyebrow">隐私政策</div>
        <h1 class="header-title">你的数据，清清楚楚</h1>
        <p class="header-desc">v1.0 &nbsp;·&nbsp; 2026 年 3 月</p>
      </header>

      <div class="sections">

        <section class="section">
          <h2 class="section-title">我们收集什么</h2>
          <div class="item-groups">
            <div class="item-group">
              <span class="item-label">账户信息</span>
              <p class="item-text">用户名、邮箱、哈希密码（原始密码不可还原）；昵称、头像、简介由你自愿填写。</p>
            </div>
            <div class="item-group">
              <span class="item-label">内容数据</span>
              <p class="item-text">上传的文件、博文草稿、评论、点赞收藏和关注关系。浏览量按每用户每日去重计数。</p>
            </div>
            <div class="item-group">
              <span class="item-label">技术数据</span>
              <p class="item-text">服务端 Session（HttpOnly Cookie）；访问日志（IP + 请求路径），30 天自动清除。</p>
            </div>
          </div>
        </section>

        <section class="section">
          <h2 class="section-title">我们不碰什么</h2>
          <ul class="clean-list">
            <li>不集成任何第三方统计、广告或埋点 SDK</li>
            <li>不收集设备指纹或地理位置</li>
            <li>不追踪你在本站以外的行为</li>
            <li>密码以 bcrypt 单向哈希存储，无法还原明文</li>
          </ul>
        </section>

        <section class="section">
          <h2 class="section-title">谁能看到你的数据</h2>
          <div class="access-table">
            <div class="access-row access-header">
              <span></span>
              <span>其他用户</span>
              <span>管理员</span>
            </div>
            <div v-for="row in accessRows" :key="row.type" class="access-row">
              <span class="row-type">{{ row.type }}</span>
              <span :class="['badge', `badge-${row.others}`]">{{ badgeText(row.others) }}</span>
              <span :class="['badge', `badge-${row.admin}`]">{{ badgeText(row.admin) }}</span>
            </div>
          </div>
          <p class="section-note">管理员仅负责内容审核，无权访问你的云盘文件。</p>
        </section>

        <section class="section">
          <h2 class="section-title">你的权利</h2>
          <div class="rights-grid">
            <div v-for="r in rights" :key="r.name" class="right-item">
              <div class="right-icon">{{ r.icon }}</div>
              <div class="right-name">{{ r.name }}</div>
              <div class="right-desc">{{ r.desc }}</div>
            </div>
          </div>
        </section>

        <section class="section">
          <h2 class="section-title">Cookie</h2>
          <p class="section-text">本站仅使用一个 Session Cookie 维持登录状态，无广告 Cookie，无跨站追踪。退出后立即失效，默认 7 天过期。</p>
        </section>

        <div class="policy-footer">
          政策如有更新，将提前 7 天在首页公告通知。如需删除数据，请通过站内
          <button class="inline-link" @click="showFeedback = true">反馈</button>
          联系管理员。
        </div>

      </div>
    </div>

    <FeedbackModal v-model="showFeedback" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import FeedbackModal from '@/components/business/FeedbackModal.vue'

const router = useRouter()
const showFeedback = ref(false)

function goBack() {
  if (window.history.state?.back) router.back()
  else router.push('/blog')
}

const accessRows = [
  { type: '云盘文件',   others: 'no',  admin: 'no'  },
  { type: '已发布博文', others: 'yes', admin: 'yes' },
  { type: '草稿',       others: 'no',  admin: 'no'  },
  { type: '邮箱地址',   others: 'no',  admin: 'mid' },
]

const rights = [
  { icon: '✎', name: '查看与修改', desc: '设置 → 个人资料随时更改' },
  { icon: '⌫', name: '删除内容',  desc: '博文、评论、文件随时可删' },
  { icon: '◎', name: '注销账户',  desc: '申请后 7 天内全部删除' },
]

function badgeText(v: string) {
  return v === 'yes' ? '可见' : v === 'mid' ? '后台可见' : '不可见'
}
</script>

<style scoped lang="scss">
.privacy-page {
  min-height: calc(100vh - 52px);
  background: var(--color-surface-raised, #f8f9fb);
  padding: $spacing-2xl $spacing-md $spacing-2xl;
}

.privacy-wrap {
  max-width: 560px;
  margin: 0 auto;
}

// ── 页眉（与 About.vue 完全一致）─────────────────────
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

// ── 内容区 ───────────────────────────────────────────
.sections { display: flex; flex-direction: column; gap: 32px; }

.section { display: flex; flex-direction: column; gap: 12px; }

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

.section-note {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 6px 0 0;
  line-height: 1.6;
}

// ── 收集内容分组 ─────────────────────────────────────
.item-groups { display: flex; flex-direction: column; gap: 10px; }

.item-group { display: flex; align-items: flex-start; gap: 12px; }

.item-label {
  flex-shrink: 0;
  width: 60px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
  padding-top: 2px;
  line-height: 1.75;
}

.item-text {
  flex: 1;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.75;
  margin: 0;
}

// ── 无序列表 ─────────────────────────────────────────
.clean-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 7px;

  li {
    font-size: 13px;
    color: var(--color-text-secondary);
    line-height: 1.6;
    padding-left: 14px;
    position: relative;

    &::before {
      content: '—';
      position: absolute;
      left: 0;
      color: var(--color-text-muted);
      font-size: 10px;
      top: 3px;
    }
  }
}

// ── 权限表格 ─────────────────────────────────────────
.access-table {
  border: 1px solid var(--color-border);
  border-radius: $radius-lg;
  overflow: hidden;
}

.access-row {
  display: grid;
  grid-template-columns: 1fr 90px 90px;
  align-items: center;
  padding: 9px 14px;
  font-size: 13px;
  border-bottom: 1px solid var(--color-border-subtle);

  &:last-child { border-bottom: none; }

  &.access-header {
    background: var(--color-surface-hover);
    font-size: 11px;
    font-weight: 600;
    color: var(--color-text-muted);
    letter-spacing: 0.04em;
    padding: 7px 14px;

    span:not(:first-child) { text-align: center; }
  }
}

.row-type {
  font-size: 13px;
  color: var(--color-text-primary);
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 20px;
  padding: 0 7px;
  border-radius: $radius-sm;
  font-size: 11px;
  font-weight: 500;
  margin: 0 auto;

  &.badge-yes {
    background: rgba(34, 197, 94, 0.1);
    color: #16a34a;
  }

  &.badge-no {
    background: var(--color-surface-hover);
    color: var(--color-text-muted);
  }

  &.badge-mid {
    background: rgba(245, 158, 11, 0.1);
    color: #b45309;
  }
}

// ── 权利三格 ─────────────────────────────────────────
.rights-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;

  @media (max-width: $breakpoint-xs) {
    grid-template-columns: 1fr;
  }
}

.right-item {
  padding: 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: $radius-lg;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.right-icon {
  font-size: 16px;
  color: $color-primary;
  line-height: 1;
  margin-bottom: 2px;
}

.right-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.right-desc {
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.5;
}

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

// ── 底部说明 ─────────────────────────────────────────
.policy-footer {
  padding-top: 20px;
  border-top: 1px solid var(--color-border-subtle);
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.7;
}

.inline-link {
  all: unset;
  cursor: pointer;
  color: $color-primary;
  font-size: 12px;

  &:hover { text-decoration: underline; }
}
</style>
