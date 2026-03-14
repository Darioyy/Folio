<template>
  <div class="follow-list-page" :class="{ 'is-dark': isDarkMode }">
    <AppHeader />

    <div class="page-header">
      <el-button :icon="Back" @click="goBack" circle text />
      <h1 class="page-title">
        {{ isOwnProfile ? '我的' : `${username}的` }}
        {{ type === 'followers' ? '粉丝' : '关注' }}
      </h1>
    </div>

    <div class="follow-container">
      <!-- 标签切换 -->
      <el-tabs v-if="isOwnProfile" v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="粉丝" name="followers">
          <div class="tab-content">
            <FollowUserList
              :users="followers"
              :loading="loading"
              :is-own-list="isOwnProfile"
              @follow-change="handleFollowChange"
            />
          </div>
        </el-tab-pane>
        <el-tab-pane label="关注" name="following">
          <div class="tab-content">
            <FollowUserList
              :users="following"
              :loading="loading"
              :is-own-list="isOwnProfile"
              @follow-change="handleFollowChange"
            />
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- 单个类型列表 -->
      <div v-else class="single-list">
        <FollowUserList
          :users="currentUserList"
          :loading="loading"
          :show-follow-button="!isOwnProfile"
          :is-own-list="isOwnProfile"
          @follow-change="handleFollowChange"
        />
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore && !loading" class="load-more">
        <el-button @click="loadMore" :loading="loadingMore">
          加载更多
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back } from '@element-plus/icons-vue'
import AppHeader from '@/components/common/AppHeader.vue'
import FollowUserList from '@/components/business/FollowUserList.vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { usersApi } from '@/api/modules/users'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()
const isDarkMode = computed(() => appStore.isDarkMode)

const type = ref<'followers' | 'following'>('followers')
const username = ref('')
const activeTab = ref('followers')
const userId = ref<number | null>(null)

const followers = ref<any[]>([])
const following = ref<any[]>([])

const loading = ref(false)
const loadingMore = ref(false)
const currentPage = ref(1)
const totalPages = ref(0)

const isOwnProfile = computed(() => {
  return userStore.isLoggedIn && userStore.currentUser?.username === username.value
})

const currentUserList = computed(() => {
  return type.value === 'followers' ? followers.value : following.value
})

const hasMore = computed(() => {
  return totalPages.value > currentPage.value
})

// 加载列表数据
async function loadList(reset = true) {
  if (userId.value === null) {
    // 先获取用户 ID
    try {
      const userRes = await usersApi.getUserByUsername(username.value)
      userId.value = userRes.data.id
    } catch (error) {
      ElMessage.error('获取用户信息失败')
      return
    }
  }

  if (reset) {
    currentPage.value = 1
  }

  loading.value = reset
  if (!reset) loadingMore.value = true

  try {
    let res
    if (type.value === 'followers') {
      res = await usersApi.getUserFollowers(userId.value, currentPage.value, 20)
      const newData = res.data.items || []
      followers.value = reset ? newData : [...followers.value, ...newData]
      totalPages.value = res.data.pages || 0
    } else {
      res = await usersApi.getUserFollowing(userId.value, currentPage.value, 20)
      const newData = res.data.items || []
      following.value = reset ? newData : [...following.value, ...newData]
      totalPages.value = res.data.pages || 0
    }
  } catch (error: any) {
    console.error('加载列表失败:', error)
    ElMessage.error(error.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 加载更多
function loadMore() {
  currentPage.value++
  loadList(false)
}

// 标签切换
function handleTabChange(tabName: string) {
  type.value = tabName as 'followers' | 'following'
  loadList()
}

// 关注状态变化
async function handleFollowChange(user: any, isFollowing: boolean) {
  const list = type.value === 'followers' ? followers.value : following.value
  const item = list.find(u => u.id === user.id)
  if (item) {
    item.is_following = isFollowing
    // 更新粉丝数
    if (isFollowing) {
      if (item.followers_count !== undefined) item.followers_count++
    } else {
      if (item.followers_count !== undefined) item.followers_count--
    }
  }
}

// 返回
function goBack() {
  router.back()
}

onMounted(async () => {
  username.value = route.params.username as string || userStore.currentUser?.username || ''
  type.value = route.params.type as 'followers' | 'following' || 'followers'
  activeTab.value = type.value

  // 先获取用户 ID
  try {
    const userRes = await usersApi.getUserByUsername(username.value)
    userId.value = userRes.data.id
    loadList()
  } catch (error) {
    ElMessage.error('获取用户信息失败')
  }
})
</script>

<style scoped lang="scss">
.follow-list-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f9fafb;

  html.dark & {
    background: #141720;
  }
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 32px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);

  .page-title {
    font-size: 20px;
    font-weight: 600;
    margin: 0;
    color: var(--el-text-color-primary);
  }
}

.follow-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
  width: 100%;
  flex: 1;
}

.tab-content {
  padding-top: 16px;
}

.single-list {
  padding-top: 16px;
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 24px 0 0;
}

:deep(.el-tabs) {
  .el-tabs__content {
    min-height: 400px;
  }
}
</style>
