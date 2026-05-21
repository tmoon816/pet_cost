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
      <el-menu-item :index="menu.name" v-for="menu in menus" :key="menu.name" class="nav-item">
        <el-icon :size="20"><component :is="menu.icon" /></el-icon>
        <span class="nav-text">{{ menu.label }}</span>
      </el-menu-item>
      <div class="header-title">
        <h2>🐾 宠物花费管理系统</h2>
      </div>
    </el-menu>

    <!-- 主内容区 -->
    <div class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" :key="$route.path" />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<style scoped>
/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

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
  padding: 0 20px;
}
.nav-item {
  padding: 0 20px !important;
}
.nav-text {
  margin-left: 8px;
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
  padding: 90px 24px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .header-menu {
    padding: 0 10px;
  }
  .nav-text {
    display: none;
  }
  .nav-item {
    padding: 0 15px !important;
  }
  .header-title h2 {
    font-size: 18px;
  }
  .main-content {
    padding: 80px 16px 40px;
  }
}
</style>
