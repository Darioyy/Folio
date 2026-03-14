<template>
  <div class="home-page">
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title" aria-label="Folio">
          <span
            v-for="(char, i) in 'Folio'.split('')"
            :key="i"
            class="hero-char"
            :style="{ '--d': i }"
            aria-hidden="true"
          >{{ char }}</span>
        </h1>
        <p class="hero-subtitle">私有云存储 · 轻博客社区</p>
        <div class="hero-actions">
          <el-button
            size="large"
            class="btn-cta"
            @click="router.push('/blog')"
          >
            探索发现
          </el-button>
          <el-button
            v-if="!userStore.isLoggedIn"
            size="large"
            class="btn-outline"
            @click="router.push({ name: 'Login' })"
          >
            立即开始
          </el-button>
          <el-button
            v-else
            size="large"
            class="btn-outline"
            @click="router.push('/space')"
          >
            进入空间
          </el-button>
        </div>
      </div>

      <!-- 底部导航链接 -->
      <div class="hero-foot">
        <router-link to="/about">关于网站</router-link>
        <span>·</span>
        <router-link to="/privacy">隐私条款</router-link>
        <span>·</span>
        <button class="foot-feedback-btn" @click="showFeedback = true">反馈</button>
        <span>·</span>
        <span>© {{ year }} Folio</span>
      </div>
    </section>

    <FeedbackModal v-model="showFeedback" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import FeedbackModal from '@/components/business/FeedbackModal.vue'

const router = useRouter()
const userStore = useUserStore()
const showFeedback = ref(false)
const year = new Date().getFullYear()
</script>

<style scoped lang="scss">
.home-page {
  // 抵消 .app-main 的上下 padding，让 hero 真正贴边填满视口
  margin-top: -$spacing-lg;
  margin-bottom: -$spacing-lg;
}

.hero-section {
  width: 100%;
  height: calc(100vh - 52px);
  min-height: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  // 底部留白使视觉重心上移约 5%
  padding-bottom: 10%;
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
  font-size: clamp(68px, 10vw, 96px);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 0.95;
  margin: 0 0 $spacing-lg;

  @media (max-width: $breakpoint-sm) {
    font-size: clamp(52px, 15vw, 68px);
  }
}

// 每个字母独立承载渐变+剪切，避免父子 opacity 冲突导致文字消失
.hero-char {
  display: inline-block;
  opacity: 0;
  transform: translateY(20px);
  background: linear-gradient(160deg, #fff 0%, rgba(255, 255, 255, 0.80) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 2px 10px rgba(255, 255, 255, 0.22));
  animation: char-enter 0.65s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: calc(var(--d) * 80ms + 120ms);
}

@keyframes char-enter {
  to { opacity: 1; transform: translateY(0); }
}

.hero-subtitle {
  font-size: $font-xl;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 400;
  margin: 0 0 $spacing-xl;

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

// 底部导航链接条
.hero-foot {
  position: absolute;
  bottom: 20px;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  z-index: 1;

  a, .foot-feedback-btn {
    color: inherit;
    text-decoration: none;
    background: none;
    border: none;
    cursor: pointer;
    font-size: inherit;
    padding: 0;
    font-family: inherit;
    transition: color 0.15s;

    &:hover { color: rgba(255, 255, 255, 0.85); }
  }

  @media (max-width: $breakpoint-sm) {
    bottom: 76px; // 移动端避开 TabBar（56px）
    font-size: 11px;
    gap: 7px;
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
