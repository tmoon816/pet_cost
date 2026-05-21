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
  background-color: #f5f7fa;
}
.header-menu {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background-color: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
.header-title {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.header-title h2 {
  margin: 0;
  color: #409eff;
  font-size: 20px;
}
.main-content {
  padding: 80px 20px 40px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>
