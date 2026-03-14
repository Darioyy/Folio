<template>
  <div class="app-layout" :class="{ 'is-dark': isDarkMode }">
    <AppHeader />
    <main class="app-main">
      <router-view v-slot="{ Component, route }">
        <transition name="fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>
    <AppTabBar />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppHeader from '@/components/common/AppHeader.vue'
import AppTabBar from '@/components/common/AppTabBar.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const isDarkMode = computed(() => appStore.isDarkMode)
</script>

<style scoped lang="scss">
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-main {
  flex: 1;
  padding: $spacing-lg 0;

  // 移动端底部为 TabBar 留出空间
  @media (max-width: 640px) {
    padding-bottom: calc(#{$spacing-lg} + 56px);
  }
}
</style>
