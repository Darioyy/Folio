<template>
  <footer class="app-footer">
    <div class="container footer-container">
      <div class="footer-content">
        <div class="footer-brand">
          <h3>Folio</h3>
          <p>私有云存储 + 内容分享社区</p>
        </div>
        <div class="footer-links">
          <div class="footer-section">
            <h4>产品</h4>
            <a href="#features">功能介绍</a>
            <a href="#pricing">价格</a>
          </div>
          <div class="footer-section">
            <h4>支持</h4>
            <a href="#help">帮助中心</a>
            <a href="#contact">联系我们</a>
          </div>
          <div class="footer-section">
            <h4>法律</h4>
            <router-link to="/privacy">隐私政策</router-link>
            <a href="#terms">服务条款</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>&copy; {{ currentYear }} Folio. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>

<style scoped lang="scss">
.app-footer {
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color);
  padding: $spacing-2xl 0 $spacing-lg;
  margin-top: auto;

  html.dark & {
    background: $dark-bg-secondary;
    border-top-color: $dark-border;
  }
}

.footer-container {
  max-width: $container-lg;
  margin: 0 auto;
  padding: 0 $spacing-lg;
}

.footer-content {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: $spacing-xl;
  margin-bottom: $spacing-xl;

  @media (max-width: $breakpoint-md) {
    grid-template-columns: 1fr;
  }
}

.footer-brand {
  h3 {
    font-size: 24px;
    font-weight: 700;
    margin: 0 0 $spacing-sm 0;
    background: linear-gradient(135deg, #5a67d8 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  p {
    color: var(--el-text-color-secondary);
    margin: 0;
    font-size: 14px;
  }
}

.footer-links {
  display: flex;
  gap: $spacing-xl;

  @media (max-width: $breakpoint-sm) {
    flex-direction: column;
    gap: $spacing-lg;
  }
}

.footer-section {
  h4 {
    font-size: 14px;
    font-weight: 600;
    margin: 0 0 $spacing-md 0;
    color: var(--el-text-color-primary);
  }

  a {
    display: block;
    color: var(--el-text-color-secondary);
    text-decoration: none;
    font-size: 14px;
    margin-bottom: $spacing-sm;
    transition: color $transition-base;

    &:hover {
      color: #5a67d8;
    }
  }
}

.footer-bottom {
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  padding-top: $spacing-lg;
  border-top: 1px solid var(--el-border-color);

  p {
    margin: 0;
  }
}
</style>
