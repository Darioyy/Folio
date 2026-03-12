<template>
  <router-view v-slot="{ Component, route }">
    <transition name="page-fade" mode="out-in">
      <keep-alive :include="['SpaceView']">
        <component :is="Component" :key="route.meta?.keepAlive ? undefined : route.name" />
      </keep-alive>
    </transition>
  </router-view>
</template>

<script setup lang="ts">
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: #374151;
}

html.dark body {
  color: #e5e7eb;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

// Element Plus 主题覆盖
:root {
  --el-color-primary: #6366f1;
  --el-color-primary-light-3: #818cf8;
  --el-color-primary-light-5: #a5b4fc;
  --el-color-primary-light-7: #c7d2fe;
  --el-color-primary-light-8: #e0e7ff;
  --el-color-primary-light-9: #eef2ff;
  --el-color-primary-dark-2: #4f46e5;
  --el-border-radius-base: 8px;
  --el-border-radius-small: 6px;
  --el-border-radius-round: 20px;
  --el-border-radius-circle: 100%;
}

html.dark {
  --el-bg-color: #0f172a;
  --el-bg-color-page: #0f172a;
  --el-bg-color-overlay: #1e293b;
  --el-text-color-primary: #f1f5f9;
  --el-text-color-regular: #cbd5e1;
  --el-text-color-secondary: #94a3b8;
  --el-text-color-placeholder: #64748b;
  --el-border-color: #334155;
  --el-border-color-light: #334155;
  --el-border-color-lighter: #1e293b;
  --el-border-color-extra-light: #1e293b;
  --el-border-color-dark: #475569;
  --el-border-color-darker: #64748b;
  --el-fill-color-light: #1e293b;
  --el-fill-color-lighter: #0f172a;
  --el-fill-color-extra-light: #0f172a;
  --el-fill-color-dark: #334155;
  --el-fill-color-darker: #475569;
  --el-fill-color-blank: transparent;
  --el-box-shadow-light: 0 0 12px rgba(0, 0, 0, 0.72);
  --el-box-shadow-base: 0 2px 4px rgba(0, 0, 0, 0.5);
  --el-box-shadow-dark: 0 2px 8px rgba(0, 0, 0, 0.65);
}

// 通用容器
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 16px;

  @media (min-width: 640px) {
    padding: 0 24px;
  }
}

// 响应式显示
.hide-on-mobile {
  @media (max-width: 640px) {
    display: none !important;
  }
}

.show-on-mobile {
  display: none !important;

  @media (max-width: 640px) {
    display: block !important;
  }
}

// 滚动条美化
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;

  &:hover {
    background: #94a3b8;
  }
}

html.dark ::-webkit-scrollbar-thumb {
  background: #475569;

  &:hover {
    background: #64748b;
  }
}

// Element Plus 组件覆盖
.el-card {
  border-radius: 12px !important;
  border: 1px solid var(--el-border-color) !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;

  &:hover {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07) !important;
  }
}

.el-button {
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all 200ms ease !important;

  &.el-button--primary {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    border: none !important;

    &:hover {
      opacity: 0.9 !important;
      transform: translateY(-1px);
    }
  }
}

// 移动端优化
@media (max-width: 640px) {
  html {
    font-size: 14px;
  }
}

// 页面切换过渡：旧页完全淡出后新页才出现，消除黑条/白条闪烁
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.12s ease;
}
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}
</style>
