<template>
  <div class="favorites-tab">
    <div v-if="collectionsLoading && collectionFiles.length === 0" class="posts-grid">
      <el-skeleton v-for="i in 6" :key="i" animated :rows="3" />
    </div>
    <div v-else-if="collectionFiles.length > 0" class="posts-grid">
      <PostCard v-for="post in collectionFiles" :key="post.id" :post="post" />
    </div>
    <el-empty v-else description="还没有收藏的博文" :image-size="80" />
    <div v-if="collectionsHasMore" class="load-more">
      <el-button text :loading="collectionsLoadingMore" @click="loadMoreCollections">加载更多</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onActivated } from 'vue'
import PostCard from '@/components/business/PostCard.vue'
import { useCollections } from '@/composables/useCollections'

const {
  collectionFiles, collectionsLoading, collectionsLoadingMore, collectionsHasMore,
  loadCollections, loadMoreCollections,
} = useCollections()

onMounted(() => loadCollections(true))
onActivated(() => loadCollections(true))
</script>

<style scoped lang="scss">
.favorites-tab {
  padding: $spacing-lg 0;
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
}

.load-more {
  display: flex;
  justify-content: center;
  padding-top: $spacing-sm;
}

@media (max-width: 900px) {
  .posts-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 560px) {
  .posts-grid { grid-template-columns: 1fr; }
}
</style>
