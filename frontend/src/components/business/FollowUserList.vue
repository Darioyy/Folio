<template>
  <div class="follow-user-list">
    <div v-if="loading && users.length === 0" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else class="user-list">
      <div
        v-for="user in users"
        :key="user.id"
        class="user-item"
      >
        <!-- 用户信息 -->
        <div class="user-info" @click="goToUserProfile(user.username)">
          <el-avatar :src="getAvatarUrl(user)" :size="48">
            {{ getDisplayName(user) }}
          </el-avatar>
          <div class="user-details">
            <div class="user-name">
              {{ user.nickname || user.username }}
              <el-tag v-if="user.is_root === 1 || user.is_root === true" type="danger" size="small">ROOT</el-tag>
              <el-tag v-else-if="user.is_admin === 1 || user.is_admin === true" type="warning" size="small">ADMIN</el-tag>
              <el-tag v-if="user.is_mutual && props.isOwnList" type="success" size="small">互相关注</el-tag>
            </div>
            <div class="user-meta">
              <span>{{ user.followers_count || 0 }} 粉丝</span>
              <span>{{ user.following_count || 0 }} 关注</span>
            </div>
            <p v-if="user.signature" class="user-signature">{{ user.signature }}</p>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="user-actions">
          <el-button
            v-if="showFollowButton && !isOwnUser(user)"
            :type="user.is_following ? 'default' : 'primary'"
            :loading="followLoading === user.id"
            size="small"
            @click="handleFollow(user)"
          >
            {{ user.is_following ? '已关注' : '关注' }}
          </el-button>
          <el-button
            v-if="isOwnUser(user)"
            size="small"
            disabled
          >
            自己
          </el-button>
        </div>
      </div>
    </div>

    <el-empty v-if="!loading && users.length === 0" description="暂无数据" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { usersApi } from '@/api/modules/users'

interface User {
  id: number
  username: string
  nickname?: string
  avatar?: string
  signature?: string
  followers_count?: number
  following_count?: number
  is_admin?: number | boolean
  is_root?: number | boolean
  is_following?: boolean
  is_mutual?: boolean
}

interface Props {
  users: User[]
  loading?: boolean
  showFollowButton?: boolean
  isOwnList?: boolean  // true = viewer is the profile owner
}

interface Emits {
  (e: 'followChange', user: User, isFollowing: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  showFollowButton: true,
  isOwnList: false
})

const emit = defineEmits<Emits>()

const router = useRouter()
const userStore = useUserStore()
const followLoading = ref<number | null>(null)

// 获取头像 URL - 统一使用后端端点
function getAvatarUrl(user: User): string | undefined {
  if (user.username) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    return `${baseUrl}/users/username/${user.username}/avatar/view`
  }
  return undefined
}

// 获取显示名称
function getDisplayName(user: User): string {
  return user.nickname?.[0] || user.username[0] || '?'
}

// 是否是当前用户
function isOwnUser(user: User): boolean {
  return userStore.currentUser?.id === user.id
}

// 关注/取消关注
async function handleFollow(user: User) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }

  followLoading.value = user.id
  try {
    if (user.is_following) {
      await usersApi.unfollowUser(user.id)
      user.is_following = false
      emit('followChange', user, false)
      ElMessage.success('已取消关注')
    } else {
      await usersApi.followUser(user.id)
      user.is_following = true
      emit('followChange', user, true)
      ElMessage.success('关注成功')
    }
  } catch (error: any) {
    console.error('关注操作失败:', error)
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    followLoading.value = null
  }
}

// 跳转到用户主页
function goToUserProfile(username: string) {
  router.push({ name: 'UserProfile', params: { username } })
}
</script>

<style scoped lang="scss">
.follow-user-list {
  .loading-state {
    padding: 20px;
  }
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;

  html.dark & {
    background: #1c1f26;
    border-color: #2d3242;
  }

  &:hover {
    border-color: #5a67d8;
    box-shadow: 0 2px 8px rgba(90, 103, 216, 0.1);

    html.dark & {
      border-color: #8b5cf6;
    }
  }
}

.user-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.user-details {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin: 0 0 4px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-meta {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  display: flex;
  gap: 12px;
  margin: 0 0 4px 0;
}

.user-signature {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-actions {
  flex-shrink: 0;
}

// 响应式
@media (max-width: 768px) {
  .user-item {
    padding: 12px;
  }

  .user-meta {
    gap: 8px;
    font-size: 12px;
  }
}
</style>
