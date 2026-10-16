<template>
  <div class="settings-page">
    <AppHeader />
    <div class="settings-container">
      <div class="settings-layout">
        <!-- 左侧导航 -->
        <nav class="settings-nav">
          <div class="nav-title">账户设置</div>
          <div
            v-for="item in navItems"
            :key="item.key"
            :class="['nav-item', { active: activeSection === item.key }]"
            @click="activeSection = item.key"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            {{ item.label }}
          </div>
        </nav>

        <!-- 右侧内容 -->
        <div class="settings-content">
          <ProfileSettings v-if="activeSection === 'profile'" />
          <SecuritySettings v-else-if="activeSection === 'security'" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Edit, Lock } from '@element-plus/icons-vue'
import AppHeader from '@/components/common/AppHeader.vue'
import ProfileSettings from './Profile.vue'
import SecuritySettings from './Security.vue'

const activeSection = ref<'profile' | 'security'>('profile')

const navItems = [
  { key: 'profile' as const, label: '基本资料', icon: Edit },
  { key: 'security' as const, label: '账户安全', icon: Lock },
]
</script>

<style scoped lang="scss">
.settings-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.settings-container {
  max-width: 960px;
  margin: 0 auto;
  padding: $spacing-xl $spacing-md $spacing-3xl;
  width: 100%;
}

.settings-layout {
  display: flex;
  gap: $spacing-xl;
  align-items: flex-start;

  @media (max-width: $breakpoint-md) {
    flex-direction: column;
  }
}

.settings-nav {
  width: 200px;
  flex-shrink: 0;
  background: var(--el-bg-color);
  border-radius: $radius-lg;
  padding: $spacing-md;
  box-shadow: $shadow-sm;
  position: sticky;
  top: 80px;

  @media (max-width: $breakpoint-md) {
    width: 100%;
    position: static;
    display: flex;
    gap: $spacing-xs;
    padding: $spacing-sm;
  }
}

.nav-title {
  font-size: $font-xs;
  font-weight: 600;
  color: var(--el-text-color-placeholder);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: $spacing-xs $spacing-sm $spacing-md;

  @media (max-width: $breakpoint-md) {
    display: none;
  }
}

.nav-item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-sm $spacing-md;
  border-radius: $radius-md;
  cursor: pointer;
  font-size: $font-sm;
  color: var(--el-text-color-regular);
  transition: all $transition-fast;

  &:hover {
    background: var(--el-fill-color-light);
    color: var(--el-text-color-primary);
  }

  &.active {
    background: var(--color-primary-subtle);
    color: var(--color-primary);
    font-weight: 500;
  }

  .el-icon {
    font-size: 16px;
  }
}

.settings-content {
  flex: 1;
  min-width: 0;
}
</style>
