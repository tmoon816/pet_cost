<script setup>
import { onMounted } from 'vue'
import { useCostStore } from '@/stores/costStore'
import { useRouter, useRoute } from 'vue-router'

const store = useCostStore()
const router = useRouter()
const route = useRoute()

const activeMenu = () => route.name

const menus = [
  { name: 'home', label: '花费记录', icon: 'List' },
  { name: 'stats', label: '统计分析', icon: 'DataAnalysis' },
  { name: 'settings', label: '设置', icon: 'Setting' }
]

onMounted(() => {
  store.initData()
})
</script>

<template>
  <div class="app-container">
    <!-- 顶部导航 -->
    <el-menu :default-active="activeMenu()" mode="horizontal" router class="header-menu">
      <el-menu-item :index="menu.name" v-for="menu in menus" :key="menu.name">
        <el-icon><component :is="menu.icon" /></el-icon>
        <span>{{ menu.label }}</span>
      </el-menu-item>
      <div class="header-title">
        <h2>🐾 宠物花费管理系统</h2>
      </div>
    </el-menu>

    <!-- 主内容区 -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  background: transparent;
}
.header-menu {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}
.header-title {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.header-title h2 {
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 22px;
  font-weight: 700;
}
.main-content {
  padding: 90px 20px 50px;
  max-width: 1400px;
  margin: 0 auto;
}
</style>
