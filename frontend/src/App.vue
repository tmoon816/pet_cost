<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  HomeFilled,
  Money,
  TrendCharts,
  Setting,
  Pet,
  List,
  Search
} from '@element-plus/icons-vue'
import { useCategoryStore } from './stores/categoryStore'

const router = useRouter()
const route = useRoute()
const categoryStore = useCategoryStore()
const activeMenu = ref('')

const menuItems = [
  {
    path: '/dashboard',
    title: '数据大盘',
    icon: HomeFilled
  },
  {
    path: '/bills',
    title: '收支账单',
    icon: Money
  },
  {
    path: '/pets',
    title: '宠物档案',
    icon: Pet
  },
  {
    path: '/categories',
    title: '消费分类',
    icon: List
  },
  {
    path: '/budget',
    title: '月度预算',
    icon: TrendCharts
  },
  {
    path: '/settings',
    title: '系统设置',
    icon: Setting
  }
]

const handleMenuSelect = (path) => {
  router.push(path)
}

onMounted(() => {
  // 初始化活跃菜单
  activeMenu.value = route.path
  // 预加载分类数据
  categoryStore.fetchCategories()

  // 监听路由变化更新活跃菜单
  router.afterEach((to) => {
    activeMenu.value = to.path
  })
})
</script>

<template>
  <div class="app-container">
    <el-container style="height: 100vh;">
      <!-- 侧边导航 -->
      <el-aside width="240px" style="background: var(--card); border-right: 1px solid var(--border);">
        <div class="sidebar-header">
          <div class="logo">
            <span class="paw-icon">🐾</span>
            <span class="logo-text">宠物账本</span>
          </div>
        </div>
        <el-menu
          :default-active="activeMenu"
          background-color="transparent"
          text-color="var(--text-secondary)"
          active-text-color="white"
          @select="handleMenuSelect"
        >
          <el-menu-item
            v-for="item in menuItems"
            :key="item.path"
            :index="item.path"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container direction="vertical">
        <!-- 顶部导航栏 -->
        <el-header style="height: 64px; background: var(--card); border-bottom: 1px solid var(--border); padding: 0 24px; display: flex; align-items: center; justify-content: space-between;">
          <div class="header-left">
            <h1 style="font-size: 18px; font-weight: 600; margin: 0;">{{ menuItems.find(item => item.path === activeMenu)?.title || '宠物花费管理系统' }}</h1>
          </div>
          <div class="header-right" style="display: flex; align-items: center; gap: 16px;">
            <el-input
              placeholder="搜索账单、宠物、客户..."
              style="width: 300px;"
              :prefix-icon="Search"
            />
            <div class="user-avatar" style="width: 40px; height: 40px; border-radius: 50%; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; cursor: pointer;">
              贾
            </div>
          </div>
        </el-header>

        <!-- 主内容区域 -->
        <el-main style="background: var(--bg); padding: 24px; overflow-y: auto; max-width: 1920px; margin: 0 auto; width: 100%;">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
}
.sidebar-header {
  height: 64px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 20px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo .paw-icon {
  font-size: 24px;
  color: var(--primary);
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}
.header-left h1 {
  color: var(--text-primary);
}
@media (max-width: 1440px) {
  .el-main {
    padding: 16px;
  }
}
</style>
