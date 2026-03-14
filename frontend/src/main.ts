import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

import App from './App.vue'
import router from './router'
import '@/assets/styles/index.scss'   // 保留旧系统（提供 .fade-enter-active 等 Vue 过渡类）
import '@/styles/global.scss'          // 新样式系统：加载全部 CSS 自定义属性
import { useAppStore } from '@/stores/app'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 初始化暗黑模式状态（与 index.html 内联脚本已设的 class 同步）
useAppStore().initDarkMode()

app.mount('#app')
