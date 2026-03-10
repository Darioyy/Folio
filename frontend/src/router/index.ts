import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  // 前台页面
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Home/index.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'about',
        name: 'About',
        component: () => import('@/views/Home/About.vue'),
        meta: { title: '关于我' }
      },
      {
        path: 'posts',
        name: 'Posts',
        component: () => import('@/views/Posts/index.vue'),
        meta: { title: '文章列表' }
      },
      {
        path: 'posts/:id',
        name: 'PostDetail',
        component: () => import('@/views/Posts/Detail.vue'),
        meta: { title: '文章详情' }
      },
      {
        path: 'plaza',
        name: 'Plaza',
        component: () => import('@/views/Plaza/index.vue'),
        meta: { title: '公共大厅' }
      }
    ]
  },

  // 个人工作台
  {
    path: '/hub',
    name: 'Hub',
    component: () => import('@/views/Hub/index.vue'),
    meta: { title: '个人工作台', requiresAuth: true, hideInMenu: true },
    redirect: '/hub/private',
    children: [
      {
        path: 'private',
        name: 'HubPrivate',
        component: () => import('@/views/Hub/PrivateFiles.vue'),
        meta: { title: '私有文件库', requiresAuth: true }
      },
      {
        path: 'published',
        name: 'HubPublished',
        component: () => import('@/views/Hub/PublishedFiles.vue'),
        meta: { title: '公共发布区', requiresAuth: true }
      }
    ]
  },

  // 个人中心（独立页面）
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile/index.vue'),
    meta: { title: '个人中心', requiresAuth: true }
  },

  // 用户主页（公开访问）
  {
    path: '/u/:username',
    name: 'UserProfile',
    component: () => import('@/views/UserProfile/index.vue'),
    meta: { title: '用户主页' }
  },

  // 关注列表
  {
    path: '/follows/:username/:type',
    name: 'FollowList',
    component: () => import('@/views/FollowList/index.vue'),
    meta: { title: '关注列表' }
  },

  // 认证页面
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Auth/Login.vue'),
    meta: { title: '登录', hideInMenu: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Auth/Register.vue'),
    meta: { title: '注册', hideInMenu: true }
  },

  // 后台管理
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/Admin/index.vue'),
    meta: { title: '后台管理', requiresAuth: true, requiresAdmin: true, hideInMenu: true },
    redirect: '/admin/users',
    children: [
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/Admin/Users.vue'),
        meta: { title: '用户管理', requiresAdmin: true }
      },
      {
        path: 'posts',
        name: 'AdminPosts',
        component: () => import('@/views/Admin/Posts.vue'),
        meta: { title: '文章管理', requiresAdmin: true }
      },
      {
        path: 'media',
        name: 'AdminMedia',
        component: () => import('@/views/Admin/Media.vue'),
        meta: { title: '媒体管理', requiresAdmin: true }
      },
      {
        path: 'resources',
        name: 'AdminResources',
        component: () => import('@/views/Admin/Resources.vue'),
        meta: { title: '资源管理', requiresAdmin: true }
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('@/views/Admin/Categories.vue'),
        meta: { title: '分类管理', requiresAdmin: true }
      }
    ]
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '404', hideInMenu: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const title = to.meta.title as string

  // 设置页面标题
  if (title) {
    document.title = `${title} - My Blog`
  }

  // 需要登录的页面
  if (to.meta.requiresAuth) {
    // 如果本地有用户信息，验证 session 是否仍然有效
    if (userStore.isLoggedIn) {
      try {
        // 通过调用 /me 接口验证 session
        await userStore.refreshUser()
      } catch {
        // session 过期，跳转到登录页
        next({
          name: 'Login',
          query: { redirect: to.fullPath }
        })
        return
      }
    } else {
      next({
        name: 'Login',
        query: { redirect: to.fullPath }
      })
      return
    }
  }

  // 需要管理员权限的页面
  if (to.meta.requiresAdmin && !userStore.isAdminOrRoot) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router
