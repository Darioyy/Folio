<template>
  <div class="hub-layout">
    <!-- 顶部栏 -->
    <div class="hub-header">
      <div class="header-left">
        <h1 class="page-title">
          <el-icon :size="24"><FolderOpened /></el-icon>
          我的工作台
        </h1>
      </div>
      <div class="header-right">
        <!-- 暗黑模式切换 -->
        <el-button
          :icon="isDarkMode ? Sunny : Moon"
          circle
          text
          @click="toggleDarkMode"
          class="theme-toggle"
        />

        <!-- 用户菜单 -->
        <el-dropdown trigger="click">
          <div class="user-dropdown-trigger">
            <UserAvatar :src="avatarUrl" :user="userStore.currentUser" :size="36" />
            <span class="user-name-display">{{ displayName }}</span>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="goToHome">
                <el-icon><HomeFilled /></el-icon>
                首页
              </el-dropdown-item>
              <el-dropdown-item @click="goToProfile">
                <el-icon><User /></el-icon>
                个人中心
              </el-dropdown-item>
              <el-dropdown-item v-if="userStore.isAdminOrRoot" @click="goToAdmin">
                <el-icon><Setting /></el-icon>
                后台管理
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <el-container class="hub-container">
      <!-- 左侧导航栏 -->
      <el-aside width="240px" class="hub-aside">
        <el-menu
          :default-active="activeMenu"
          router
          class="hub-menu"
        >
          <el-menu-item index="/hub/private">
            <el-icon><Lock /></el-icon>
            <span>私有文件库</span>
          </el-menu-item>
          <el-menu-item index="/hub/published">
            <el-icon><Share /></el-icon>
            <span>公共发布区</span>
          </el-menu-item>
        </el-menu>

        <!-- 存储配额卡片 -->
        <div v-if="storageInfo" class="storage-card">
          <div class="storage-header">
            <span class="storage-label">存储空间</span>
            <el-tag :type="getStorageTagType()" size="small">
              {{ storageInfo.storage_percentage }}%
            </el-tag>
          </div>
          <div class="storage-bar">
            <div
              class="storage-fill"
              :style="{ width: storageInfo.storage_percentage + '%' }"
            ></div>
          </div>
          <div class="storage-text">
            <span>{{ formatSize(storageInfo.storage_used) }}</span>
            <span>/ {{ formatSize(storageInfo.storage_quota) }}</span>
          </div>
        </div>
        <el-skeleton v-else :rows="3" animated />
      </el-aside>

      <!-- 内容区 -->
      <el-main class="hub-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { FolderOpened, Lock, Share, Sunny, Moon, HomeFilled, User, Setting, SwitchButton } from '@element-plus/icons-vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/modules/auth'
import { hubApi } from '@/api/modules/hub'
import type { StorageInfo } from '@/api/modules/hub'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const storageInfo = ref<StorageInfo | null>(null)

const activeMenu = computed(() => route.path)
const isDarkMode = computed(() => appStore.isDarkMode)

// 头像 URL
const avatarUrl = computed(() => {
  const user = userStore.currentUser
  if (user?.avatar) {
    const baseUrl = authApi.getAvatarUrl()
    const timestamp = new Date(user.updated_at).getTime()
    return `${baseUrl}?t=${timestamp}`
  }
  return undefined
})

// 显示名称（优先显示昵称）
const displayName = computed(() => {
  const user = userStore.currentUser
  return user?.nickname || user?.username || ''
})

// 获取存储标签类型
function getStorageTagType(): 'success' | 'warning' | 'danger' | 'info' {
  if (!storageInfo.value) return 'info'
  const percentage = storageInfo.value.storage_percentage
  if (percentage >= 90) return 'danger'
  if (percentage >= 70) return 'warning'
  return 'success'
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// 加载存储配额
async function loadStorageInfo() {
  try {
    const res = await hubApi.getStorageInfo()
    storageInfo.value = res.data
  } catch (error) {
    console.error('加载存储配额失败:', error)
  }
}

function toggleDarkMode() {
  appStore.toggleDarkMode()
}

function goToHome() {
  router.push({ name: 'Home' })
}

function goToProfile() {
  router.push({ name: 'Profile' })
}

function goToAdmin() {
  router.push({ name: 'Admin' })
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userStore.logout()
    router.push({ name: 'Home' })
  } catch {
    // 取消退出
  }
}

onMounted(() => {
  loadStorageInfo()
})
</script>

<style scoped lang="scss">
.hub-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f9fafb;

  html.dark & {
    background: #0f172a;
  }

  :deep(.el-container) {
    flex: 1;
  }
}

.hub-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 64px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  html.dark & {
    background: #1e293b;
    border-bottom-color: #334155;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 20px;
      font-weight: 600;
      margin: 0;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .theme-toggle {
    color: var(--el-text-color-secondary);

    &:hover {
      color: #6366f1;
      background: rgba(99, 102, 241, 0.08);
    }
  }

  .user-dropdown-trigger {
    cursor: pointer;
    padding: 6px 12px;
    border-radius: 12px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 8px;

    &:hover {
      background: rgba(99, 102, 241, 0.08);
    }
  }

  .user-name-display {
    font-size: 14px;
    font-weight: 500;
    color: var(--el-text-color-secondary);
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.hub-container {
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

// 左侧边栏
.hub-aside {
  background: transparent;
  padding: 24px 0 24px 24px;

  .hub-menu {
    border-right: none;
    background: transparent;

    .el-menu-item {
      margin-bottom: 8px;
      border-radius: 12px;
      padding: 0 16px;
      height: 48px;
      line-height: 48px;
      font-size: 14px;
      color: var(--el-text-color-regular);

      &:hover {
        background: #ffffff;
        color: #6366f1;

        html.dark & {
          background: #1e293b;
        }
      }

      &.is-active {
        background: #ffffff;
        color: #6366f1;
        font-weight: 500;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

        html.dark & {
          background: #1e293b;
        }
      }

      .el-icon {
        margin-right: 8px;
        font-size: 18px;
      }
    }
  }

  .storage-card {
    margin-top: 24px;
    padding: 20px;
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

    html.dark & {
      background: #1e293b;
    }

    .storage-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;

      .storage-label {
        font-size: 14px;
        font-weight: 500;
        color: var(--el-text-color-primary);
      }
    }

    .storage-bar {
      height: 6px;
      background: #f3f4f6;
      border-radius: 3px;
      overflow: hidden;
      margin-bottom: 12px;

      html.dark & {
        background: #334155;
      }

      .storage-fill {
        height: 100%;
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
        transition: width 0.3s ease;
        border-radius: 3px;
      }
    }

    .storage-text {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: var(--el-text-color-secondary);

      span:first-child {
        font-weight: 500;
        color: var(--el-text-color-primary);
      }
    }
  }
}

// 主内容区
.hub-main {
  padding: 24px 32px;
  overflow-y: auto;
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
