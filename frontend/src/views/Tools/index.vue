<template>
  <AppHeader />

  <div class="tools-wrap">
    <!-- Desktop sidebar -->
    <aside class="tools-sidebar">
      <nav class="sidebar-nav">
        <router-link
          v-for="tool in tools"
          :key="tool.path"
          :to="tool.path"
          class="sidebar-item"
          :title="tool.label"
        >
          <span class="item-icon" v-html="tool.icon" />
          <span class="item-label">{{ tool.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <span class="footer-label">Folio 工具箱</span>
      </div>
    </aside>

    <!-- Content -->
    <main class="tools-content">
      <router-view />
    </main>
  </div>

  <!-- Mobile tab bar -->
  <nav class="tools-tabbar">
    <router-link
      v-for="tool in tools"
      :key="tool.path"
      :to="tool.path"
      class="tabbar-item"
    >
      <span class="tabbar-icon" v-html="tool.icon" />
      <span class="tabbar-label">{{ tool.shortLabel }}</span>
    </router-link>
  </nav>
</template>

<script setup lang="ts">
const tools = [
  {
    path: '/tools/html2md',
    label: 'HTML → MD',
    shortLabel: 'HTML→MD',
    // 经典 </> 代码符号：全球通用的「代码/标记语言」图标，与文档形状完全不同
    icon: `<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
      <path d="M7 5.5L3 10L7 14.5"/>
      <path d="M13 5.5L17 10L13 14.5"/>
      <path d="M11.5 4L8.5 16"/>
    </svg>`,
  },
  {
    path: '/tools/pdf',
    label: 'PDF 工具',
    shortLabel: 'PDF',
    // 叠层文档：前景实线 + 背景半透明，暗示多页 / 合并 / 操作
    icon: `<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
      <rect x="7" y="2.5" width="9.5" height="12.5" rx="1.5" stroke-width="1.1" stroke-opacity="0.4"/>
      <rect x="3.5" y="5" width="9.5" height="12.5" rx="1.5" stroke-width="1.45"/>
      <path d="M6 10h5.5M6 12.5h4" stroke-width="1.2"/>
    </svg>`,
  },
]
</script>

<style scoped lang="scss">
.tools-wrap {
  display: flex;
  min-height: calc(100vh - 52px);
}

// ── Sidebar ──────────────────────────────────────────────────────────────────
.tools-sidebar {
  width: 160px;
  min-height: calc(100vh - 52px);
  flex-shrink: 0;
  border-right: 1px solid var(--color-border);
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 52px;
  align-self: flex-start;
  height: calc(100vh - 52px);

  @media (max-width: 640px) {
    display: none;
  }
}

.sidebar-nav {
  flex: 1;
  padding: 8px 0;
}

.sidebar-item {
  display: flex;
  align-items: center;
  height: 44px;
  padding-right: 12px;
  text-decoration: none;
  color: var(--color-text-secondary);
  white-space: nowrap;
  border-left: 2px solid transparent;
  transition: background $transition-fast, color $transition-fast, border-color $transition-fast;

  &:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
  }

  &.router-link-active {
    border-left-color: var(--color-primary);
    background: var(--color-primary-subtle);
    color: var(--color-primary);
  }
}

.item-icon {
  width: 46px;
  height: 44px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;

  :deep(svg) {
    width: 16px;
    height: 16px;
  }
}

.item-label {
  font-size: 13px;
  font-weight: 500;
}

.sidebar-footer {
  padding: 12px 14px 16px;
}

.footer-label {
  display: block;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

// ── Content ──────────────────────────────────────────────────────────────────
.tools-content {
  flex: 1;
  min-width: 0;
  background: var(--color-bg);
}

// ── Mobile tab bar ───────────────────────────────────────────────────────────
.tools-tabbar {
  display: none;

  @media (max-width: 640px) {
    display: flex;
    overflow-x: auto;
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    padding: 0 4px;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;

    &::-webkit-scrollbar { display: none; }
  }
}

.tabbar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 16px;
  text-decoration: none;
  color: var(--color-text-secondary);
  white-space: nowrap;
  border-bottom: 2px solid transparent;
  transition: color $transition-fast, border-color $transition-fast;

  &.router-link-active {
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
  }

  :deep(svg) {
    width: 16px;
    height: 16px;
  }
}

.tabbar-label {
  font-size: 11px;
  font-weight: 500;
}
</style>
