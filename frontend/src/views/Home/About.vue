<template>
  <div class="about-page">
    <div class="container">
      <el-card class="about-card" shadow="never">
        <div class="about-content">
          <div class="about-avatar">
            <el-avatar :size="120" :icon="UserFilled" />
          </div>
          <div class="about-info">
            <h1>Dario</h1>
            <p class="about-bio">这是一个练手项目，用于学习全栈开发、数据库操作和服务器部署。</p>

            <div class="about-stats">
              <el-statistic title="文章" :value="stats.posts" />
              <el-statistic title="资料" :value="stats.resources" />
              <el-statistic title="媒体" :value="stats.media" />
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="tech-stack-card" shadow="never">
        <template #header>
          <h2>技术栈</h2>
        </template>
        <el-space wrap>
          <el-tag v-for="tech in techStack" :key="tech" size="large">
            {{ tech }}
          </el-tag>
        </el-space>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { UserFilled } from '@element-plus/icons-vue'
import { systemApi } from '@/api/modules/system'

const stats = ref({
  posts: 0,
  resources: 0,
  media: 0
})

const techStack = [
  'Vue 3', 'TypeScript', 'Element Plus', 'Vite',
  'Flask', 'MySQL', 'SQLAlchemy', 'Docker',
  'Nginx', 'Python', 'Pinia', 'Axios'
]

onMounted(async () => {
  try {
    const res = await systemApi.getInfo()
    stats.value = res.data.database_stats
  } catch {
    // 静默失败，使用默认值
  }
})
</script>

<style scoped lang="scss">
.about-page {
  .container {
    max-width: 800px;
  }
}

.about-card {
  margin-bottom: $spacing-lg;
}

.about-content {
  display: flex;
  gap: $spacing-xl;
  align-items: center;

  @media (max-width: $breakpoint-sm) {
    flex-direction: column;
    text-align: center;
  }
}

.about-avatar {
  flex-shrink: 0;
}

.about-info {
  flex: 1;

  h1 {
    font-size: 32px;
    margin-bottom: $spacing-sm;
  }

  .about-bio {
    color: var(--el-text-color-secondary);
    margin-bottom: $spacing-lg;
    font-size: 16px;
  }
}

.about-stats {
  display: flex;
  gap: $spacing-xl;

  @media (max-width: $breakpoint-sm) {
    justify-content: center;
  }
}

.tech-stack-card {
  h2 {
    font-size: 20px;
    margin: 0;
  }
}
</style>
