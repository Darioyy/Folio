<template>
  <router-view v-slot="{ Component, route }">
    <transition name="page-fade">
      <keep-alive :include="['SpaceView']">
        <component :is="Component" :key="route.meta?.keepAlive ? undefined : route.name" />
      </keep-alive>
    </transition>
  </router-view>
</template>

<script setup lang="ts">
</script>

<style>
/* ─── Element Plus 主题变量覆盖 ─── */
:root {
  --el-color-primary: #5a67d8;
  --el-color-primary-light-3: #8b95e2;
  --el-color-primary-light-5: #acb3ec;
  --el-color-primary-light-7: #cdd1f5;
  --el-color-primary-light-8: #dde1f9;
  --el-color-primary-light-9: #eeeffe;
  --el-color-primary-dark-2: #4a56c5;
  --el-border-radius-base: 6px;
  --el-border-radius-small: 4px;
  --el-border-radius-round: 9999px;
  --el-border-radius-circle: 100%;
}

html.dark {
  --el-bg-color: #1c1f26;
  --el-bg-color-page: #141720;
  --el-bg-color-overlay: #1c1f26;
  --el-text-color-primary: #e8eaf0;
  --el-text-color-regular: #b0b8cc;
  --el-text-color-secondary: #8b93a7;
  --el-text-color-placeholder: #6b7280;
  --el-border-color: #2d3242;
  --el-border-color-light: #252a35;
  --el-border-color-lighter: #1e2230;
  --el-border-color-extra-light: #1a1e2a;
  --el-border-color-dark: #3a4060;
  --el-border-color-darker: #4a5070;
  --el-fill-color-light: #252a35;
  --el-fill-color-lighter: #1c1f26;
  --el-fill-color-extra-light: #141720;
  --el-fill-color-dark: #2d3242;
  --el-fill-color-darker: #3a4060;
  --el-fill-color-blank: transparent;
  --el-box-shadow-light: 0 0 0 1px rgba(255, 255, 255, 0.06);
  --el-box-shadow-base: 0 2px 12px rgba(0, 0, 0, 0.4);
  --el-box-shadow-dark: 0 4px 20px rgba(0, 0, 0, 0.5);
}

/* ─── 应用容器 ─── */
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ─── 页面切换过渡（旧页淡出后新页才出现，消除闪烁） ─── */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.12s ease;
}
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}
</style>
