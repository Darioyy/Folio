<template>
  <div class="resources-page">
    <div class="container">
      <div class="page-header">
        <h1>学习资料</h1>
      </div>

      <el-empty v-if="resources.length === 0 && !loading" description="暂无资料" />

      <div v-else class="resources-grid">
        <el-card
          v-for="resource in resources"
          :key="resource.id"
          class="resource-card"
          shadow="hover"
        >
          <div class="resource-icon">📄</div>
          <h3 class="resource-title">{{ resource.title }}</h3>
          <p v-if="resource.description" class="resource-description">
            {{ resource.description }}
          </p>
          <div class="resource-meta">
            <span>{{ formatFileSize(resource.file_size) }}</span>
            <span>{{ resource.download_count }} 次下载</span>
          </div>
          <el-button
            type="primary"
            :icon="Download"
            @click="downloadResource(resource.id)"
          >
            下载
          </el-button>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { resourcesApi } from '@/api/modules/resources'
import { formatFileSize } from '@/utils/format'

const resources = ref<any[]>([])
const loading = ref(false)

async function loadResources() {
  loading.value = true
  try {
    const res = await resourcesApi.getList({ limit: 50 })
    resources.value = res.data || []
  } catch {
    resources.value = []
  } finally {
    loading.value = false
  }
}

function downloadResource(id: number) {
  // 新窗口打开下载链接
  window.open(resourcesApi.getDownloadUrl(id), '_blank')
}

onMounted(() => {
  loadResources()
})
</script>

<style scoped lang="scss">
.resources-page {
  .page-header {
    margin-bottom: $spacing-lg;
  }
}

.resources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: $spacing-lg;
}

.resource-card {
  text-align: center;

  :deep(.el-card__body) {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: $spacing-sm;
  }
}

.resource-icon {
  font-size: 48px;
}

.resource-title {
  font-size: 16px;
  margin: 0;
}

.resource-description {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  min-height: 40px;
}

.resource-meta {
  display: flex;
  gap: $spacing-md;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
</style>
