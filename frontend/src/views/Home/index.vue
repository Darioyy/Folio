<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="container">
        <div class="hero-content">
          <h1 class="hero-title">VaultShare</h1>
          <p class="hero-subtitle">私有云存储 · 灵活分享 · 社区互动</p>
          <div class="hero-actions">
            <el-button
              v-if="!userStore.isLoggedIn"
              type="primary"
              size="large"
              @click="goToRegister"
              class="btn-hero"
            >
              立即开始
            </el-button>
            <el-button
              v-else
              type="primary"
              size="large"
              @click="goToDashboard"
              class="btn-hero"
            >
              进入工作台
            </el-button>
            <el-button
              size="large"
              @click="scrollToFeatures"
              class="btn-hero-outline"
            >
              了解更多
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="features-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">核心功能</h2>
          <p class="section-subtitle">简单、安全、高效的文件管理体验</p>
        </div>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="8" v-for="feature in features" :key="feature.title">
            <div class="feature-card">
              <div class="feature-icon" :style="{ background: feature.color }">
                <el-icon :size="32">
                  <component :is="feature.icon" />
                </el-icon>
              </div>
              <h3>{{ feature.title }}</h3>
              <p>{{ feature.description }}</p>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- Stats Section -->
    <section class="stats-section">
      <div class="container">
        <el-row :gutter="24">
          <el-col :xs="12" :sm="6" v-for="stat in stats" :key="stat.label">
            <div class="stat-item">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="container">
        <div class="cta-content">
          <h2>准备好开始了吗？</h2>
          <p>加入 VaultShare，体验全新的文件管理方式</p>
          <el-button
            v-if="!userStore.isLoggedIn"
            type="primary"
            size="large"
            @click="goToRegister"
          >
            免费注册
          </el-button>
          <el-button
            v-else
            type="primary"
            size="large"
            @click="goToDashboard"
          >
            进入工作台
          </el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  Lock, Share, ChatLineRound, TrendCharts, Files, DataAnalysis
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const features = [
  {
    icon: Lock,
    title: '私有存储',
    description: '默认私有存储，完全掌控文件访问权限，保护您的隐私安全',
    color: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'
  },
  {
    icon: Share,
    title: '灵活分享',
    description: '一键切换私有/公共，选择性分享内容给他人',
    color: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
  },
  {
    icon: ChatLineRound,
    title: '社区互动',
    description: '公共大厅分享作品，评论点赞，发现精彩内容',
    color: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
  },
  {
    icon: Files,
    title: '文件管理',
    description: '支持多种文件类型，文件夹分组管理，批量操作',
    color: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
  },
  {
    icon: TrendCharts,
    title: '数据统计',
    description: '实时查看存储使用情况，文件浏览下载统计',
    color: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
  },
  {
    icon: DataAnalysis,
    title: '管理后台',
    description: '管理员专用控制台，用户管理内容审核',
    color: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)'
  }
]

const stats = [
  { value: '100%', label: '隐私保护' },
  { value: '0', label: '广告打扰' },
  { value: '24/7', label: '随时访问' },
  { value: '∞', label: '永久存储' }
]

function goToRegister() {
  router.push({ name: 'Register' })
}

function goToDashboard() {
  router.push('/hub')
}

function scrollToFeatures() {
  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<style scoped lang="scss">
@import '@/styles/variables.scss';

.home-page {
  background: var(--el-bg-color);
}

// Hero Section
.hero-section {
  min-height: 600px;
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  color: white;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
    animation: pulse 15s ease-in-out infinite;
  }

  @media (max-width: $breakpoint-sm) {
    min-height: 500px;
    padding: $spacing-xl 0;
  }
}

@keyframes pulse {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(-25px, -25px) scale(1.1);
  }
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 700px;
  margin: 0 auto;
  animation: fadeInUp 0.6s ease-out;
}

.hero-title {
  font-size: 64px;
  font-weight: 800;
  margin: 0 0 $spacing-md 0;
  letter-spacing: -2px;

  @media (max-width: $breakpoint-sm) {
    font-size: 42px !important;
  }
}

.hero-subtitle {
  font-size: 20px;
  opacity: 0.95;
  margin: 0 0 $spacing-xl 0;
  font-weight: 400;

  @media (max-width: $breakpoint-sm) {
    font-size: 16px !important;
  }
}

.hero-actions {
  display: flex;
  gap: $spacing-md;
  justify-content: center;

  @media (max-width: $breakpoint-sm) {
    flex-direction: column;
    width: 100%;
  }
}

.btn-hero {
  padding: 14px 32px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  height: auto !important;
  border-radius: $radius-full !important;
  background: white !important;
  color: #6366f1 !important;
  border: none !important;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  }

  @media (max-width: $breakpoint-sm) {
    width: 100%;
  }
}

.btn-hero-outline {
  padding: 14px 32px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  height: auto !important;
  border-radius: $radius-full !important;
  background: transparent !important;
  color: white !important;
  border: 2px solid rgba(255, 255, 255, 0.5) !important;

  &:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    border-color: white !important;
  }

  @media (max-width: $breakpoint-sm) {
    width: 100%;
  }
}

// Features Section
.features-section {
  padding: $spacing-3xl 0;
}

.section-header {
  text-align: center;
  margin-bottom: $spacing-2xl;
}

.section-title {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 $spacing-sm 0;
  color: var(--el-text-color-primary);

  @media (max-width: $breakpoint-sm) {
    font-size: 28px !important;
  }
}

.section-subtitle {
  font-size: 18px;
  color: var(--el-text-color-secondary);
  margin: 0;

  @media (max-width: $breakpoint-sm) {
    font-size: 16px !important;
  }
}

.feature-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: $radius-xl;
  padding: $spacing-xl;
  text-align: center;
  height: 100%;
  transition: all $transition-base;

  &:hover {
    transform: translateY(-4px);
    box-shadow: $shadow-lg;
    border-color: #6366f1;
  }
}

.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: $radius-lg;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto $spacing-lg;
  color: white;
}

.feature-card {
  h3 {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 $spacing-sm 0;
    color: var(--el-text-color-primary);
  }

  p {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    line-height: 1.6;
    margin: 0;
  }
}

// Stats Section
.stats-section {
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  padding: $spacing-2xl 0;

  html.dark & {
    background: linear-gradient(135deg, $dark-bg-secondary 0%, $dark-bg-tertiary 100%);
  }
}

.stat-item {
  text-align: center;
  padding: $spacing-lg;
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: $spacing-xs;

  @media (max-width: $breakpoint-sm) {
    font-size: 28px !important;
  }
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

// CTA Section
.cta-section {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  padding: $spacing-3xl 0;
  color: white;
}

.cta-content {
  text-align: center;
  max-width: 600px;
  margin: 0 auto;

  h2 {
    font-size: 32px;
    font-weight: 700;
    margin: 0 0 $spacing-md 0;

    @media (max-width: $breakpoint-sm) {
      font-size: 24px !important;
    }
  }

  p {
    font-size: 16px;
    opacity: 0.9;
    margin: 0 0 $spacing-xl 0;

    @media (max-width: $breakpoint-sm) {
      font-size: 14px !important;
    }
  }

  .el-button {
    padding: 14px 40px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    height: auto !important;
    border-radius: $radius-full !important;
    background: white !important;
    color: #6366f1 !important;
    border: none !important;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    }
  }
}

// Animations
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
