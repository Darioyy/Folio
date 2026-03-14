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
        path: 'privacy',
        name: 'Privacy',
        component: () => import('@/views/Home/Privacy.vue'),
        meta: { title: '隐私政策' }
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
        path: 'blog',
        name: 'Blog',
        component: () => import('@/views/Blog/index.vue'),
        meta: { title: '博客' }
      },
      {
        path: 'post/create',
        name: 'PostCreate',
        component: () => import('@/views/Blog/Editor.vue'),
        meta: { title: '写博文', requiresAuth: true }
      },
      {
        path: 'post/:id/edit',
        name: 'PostEdit',
        component: () => import('@/views/Blog/Editor.vue'),
        meta: { title: '编辑博文', requiresAuth: true }
      },
      {
        path: 'post/:id',
        name: 'BlogPostDetail',
        component: () => import('@/views/Blog/Detail.vue'),
        meta: { title: '博文详情' }
      },
      {
        path: 'post/:id/moderation',
        name: 'PostHideInfo',
        component: () => import('@/views/Blog/HideInfo.vue'),
        meta: { title: '博文隐藏详情', requiresAuth: true }
      },
      {
        path: 'plaza',
        redirect: '/blog'
      },
      {
        path: 'following',
        name: 'Following',
        component: () => import('@/views/Following/index.vue'),
        meta: { title: '关注', requiresAuth: true }
      }
    ]
  },

  // 我的空间
  {
    path: '/space',
    name: 'Space',
    component: () => import('@/views/Space/index.vue'),
    meta: { title: '我的空间', requiresAuth: true, hideInMenu: true }
  },

  // 账户设置
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings/index.vue'),
    meta: { title: '账户设置', requiresAuth: true, hideInMenu: true }
  },

  // 旧路由重定向（向后兼容）
  { path: '/hub', redirect: '/space' },
  { path: '/hub/private', redirect: '/space' },
  { path: '/hub/published', redirect: '/space' },
  { path: '/profile', redirect: '/space' },

  // 用户主页（公开访问）
  {
    path: '/u/:username',
    name: 'UserProfile',
    component: () => import('@/views/UserProfile/index.vue'),
    meta: { title: '用户主页' }
  },

  // 文件详情页（公开访问，私有文件登录后验证）
  {
    path: '/file/:id',
    name: 'FileDetail',
    component: () => import('@/views/File/index.vue'),
    meta: { title: '文件详情' }
  },

  // 搜索结果页
  {
    path: '/search',
    name: 'Search',
    component: () => import('@/views/Search/index.vue'),
    meta: { title: '搜索' }
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
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/Admin/Dashboard.vue'),
        meta: { title: '数据概览', requiresAdmin: true }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/Admin/Users.vue'),
        meta: { title: '用户管理', requiresAdmin: true }
      },
      {
        path: 'blog',
        name: 'AdminBlog',
        component: () => import('@/views/Admin/Blog.vue'),
        meta: { title: '博客管理', requiresAdmin: true }
      },
      { path: 'posts', redirect: '/admin/blog' },
      {
        path: 'content',
        name: 'AdminContent',
        component: () => import('@/views/Admin/Content.vue'),
        meta: { title: '内容管理', requiresRoot: true }
      },
      {
        path: 'site',
        name: 'AdminSite',
        component: () => import('@/views/Admin/Site.vue'),
        meta: { title: '站点设置', requiresRoot: true }
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/Admin/Settings.vue'),
        meta: { title: '系统设置', requiresRoot: true }
      },
      {
        path: 'review',
        name: 'AdminReview',
        component: () => import('@/views/Admin/Review.vue'),
        meta: { title: '审核中心', requiresAdmin: true }
      },
      // 旧路由重定向
      { path: 'feedback', redirect: { path: '/admin/review', query: { tab: 'feedback' } } },
      { path: 'reports', redirect: '/admin/review' },
      // 旧路由重定向
      { path: 'media', redirect: '/admin/content' },
      { path: 'resources', redirect: '/admin/content' }
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
    document.title = `${title} - Folio`
  }

  // 已登录用户访问登录/注册页（无 redirect 参数，即非 session 过期跳转）时直接去首页
  if ((to.name === 'Login' || to.name === 'Register') && userStore.isLoggedIn && !to.query.redirect) {
    next({ name: 'Home' })
    return
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

  // 需要 Root 权限的页面
  if (to.meta.requiresRoot && !userStore.isRoot) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router
