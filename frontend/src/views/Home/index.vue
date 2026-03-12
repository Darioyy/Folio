<template>
  <div class="home-page">
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">Folio</h1>
        <p class="hero-subtitle">私有云存储 · 灵活分享 · 社区互动</p>
        <div class="hero-actions">
          <el-button
            v-if="!userStore.isLoggedIn"
            size="large"
            class="btn-cta"
            @click="router.push({ name: 'Login' })"
          >
            立即开始
          </el-button>
          <el-button
            v-else
            size="large"
            class="btn-cta"
            @click="router.push('/hub')"
          >
            进入工作台
          </el-button>
          <el-button
            size="large"
            class="btn-outline"
            @click="router.push('/plaza')"
          >
            探索大厅
          </el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
</script>

<style scoped lang="scss">
.home-page {
  // 抵消 .app-main 的上下 padding，让 hero 真正贴边填满视口
  margin-top: -$spacing-lg;
  margin-bottom: -$spacing-lg;
}

.hero-section {
  width: 100%;
  // 精确填充 header 下方可用视口，避免视觉重心偏低
  height: calc(100vh - 64px);
  min-height: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, $color-primary 0%, $color-secondary 50%, #a855f7 100%);
  position: relative;
  overflow: hidden;

  // 背景装饰光晕
  &::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, transparent 70%);
    animation: pulse 15s ease-in-out infinite;
  }
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: $spacing-xl $spacing-lg;
  animation: fadeInUp 0.6s ease-out;
}

.hero-title {
  font-size: 72px;
  font-weight: 800;
  color: #fff;
  margin: 0 0 $spacing-md;
  letter-spacing: -2px;

  @media (max-width: $breakpoint-sm) {
    font-size: 48px;
  }
}

.hero-subtitle {
  font-size: $font-xl;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 400;
  margin: 0 0 $spacing-2xl;

  @media (max-width: $breakpoint-sm) {
    font-size: $font-base;
  }
}

.hero-actions {
  display: flex;
  gap: $spacing-md;
  justify-content: center;

  @media (max-width: $breakpoint-sm) {
    flex-direction: column;
    align-items: center;
  }
}

// 主 CTA 按钮（白底紫字，首页专用）
.btn-cta {
  padding: 14px 36px !important;
  font-size: $font-base !important;
  font-weight: 600 !important;
  height: auto !important;
  border-radius: $radius-full !important;
  background: #fff !important;
  color: $color-primary !important;
  border: none !important;
  transition: transform $transition-base, box-shadow $transition-base !important;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.25) !important;
  }

  @media (max-width: $breakpoint-sm) {
    width: 200px;
  }
}

// 次按钮（透明描边）
.btn-outline {
  padding: 14px 36px !important;
  font-size: $font-base !important;
  font-weight: 600 !important;
  height: auto !important;
  border-radius: $radius-full !important;
  background: transparent !important;
  color: #fff !important;
  border: 2px solid rgba(255, 255, 255, 0.5) !important;
  transition: background $transition-fast, border-color $transition-fast !important;

  &:hover {
    background: rgba(255, 255, 255, 0.12) !important;
    border-color: #fff !important;
  }

  @media (max-width: $breakpoint-sm) {
    width: 200px;
  }
}

@keyframes pulse {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-25px, -25px) scale(1.1); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
