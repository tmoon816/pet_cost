<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  HomeFilled,
  Money,
  TrendCharts,
  Setting,
  User,
  List,
  Search,
  UserFilled,
  Expand,
  Fold
} from '@element-plus/icons-vue'
import { useCategoryStore } from './stores/categoryStore'
import { search as searchApi } from './api/search'

const router = useRouter()
const route = useRoute()
const categoryStore = useCategoryStore()
const activeMenu = ref('')

// 响应式侧边栏
const MOBILE_BP = 768
const isSidebarCollapsed = ref(window.innerWidth < MOBILE_BP)

function handleResize() {
  isSidebarCollapsed.value = window.innerWidth < MOBILE_BP
}
function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}
function closeSidebar() {
  if (window.innerWidth < MOBILE_BP) isSidebarCollapsed.value = true
}

// 搜索状态
const searchQuery = ref('')
const searchResults = ref([])
const searchPopoverVisible = ref(false)
const searchLoading = ref(false)
let debounceTimer = null

const menuItems = [
  { path: '/dashboard',  title: '营业概览',     icon: HomeFilled },
  { path: '/customers',  title: '会员/客户档案', icon: UserFilled },
  { path: '/bills',      title: '服务订单',     icon: Money },
  { path: '/pets',       title: '宠物档案',     icon: User },
  { path: '/categories', title: '服务项目',     icon: List },
  { path: '/budget',     title: '经营预算',     icon: TrendCharts },
  { path: '/settings',   title: '系统设置',     icon: Setting }
]

const handleMenuSelect = (path) => {
  router.push(path)
}

// 分组建模
const groupResults = () => {
  const typeMap = { customer: '客户', pet: '宠物', cost: '账单' }
  const groups = []
  for (const r of searchResults.value) {
    const last = groups[groups.length - 1]
    if (last && last.label === typeMap[r.type]) {
      last.items.push(r)
    } else {
      groups.push({ label: typeMap[r.type], items: [r] })
    }
  }
  return groups
}

const doSearch = async () => {
  const q = searchQuery.value.trim()
  if (!q) {
    searchResults.value = []
    searchPopoverVisible.value = false
    return
  }
  searchLoading.value = true
  try {
    const res = await searchApi(q)
    searchResults.value = res.results || []
    searchPopoverVisible.value = true
  } catch {
    searchResults.value = []
  } finally {
    searchLoading.value = false
  }
}

const onSearchInput = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(doSearch, 300)
}

const onSearchKeyup = (e) => {
  if (e.key === 'Enter' && searchResults.value.length > 0) {
    router.push(searchResults.value[0].url)
    closeSearch()
  }
}

const onResultClick = (item) => {
  router.push(item.url)
  closeSearch()
}

const closeSearch = () => {
  searchPopoverVisible.value = false
  searchQuery.value = ''
  searchResults.value = []
}

// 路由变化时关闭搜索面板
watch(() => route.path, () => {
  closeSearch()
})

onMounted(() => {
  // 初始化活跃菜单
  activeMenu.value = route.path
  // 预加载分类数据（兼容旧名会在 store 里别名为 fetchCategories）
  categoryStore.fetch?.(true) ?? categoryStore.fetchCategories?.(true)

  // 监听路由变化更新活跃菜单
  router.afterEach((to) => {
    activeMenu.value = to.path
    closeSidebar()
  })

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="app-container">
    <el-container style="height: 100vh;">
      <!-- 移动端侧边栏遮罩 -->
      <div v-if="!isSidebarCollapsed" class="sidebar-overlay" @click="closeSidebar"></div>
      <!-- 侧边导航 -->
      <el-aside
        :width="isSidebarCollapsed ? '0px' : '240px'"
        class="sidebar"
        :class="{ collapsed: isSidebarCollapsed }"
        style="background: var(--card); border-right: 1px solid var(--border);"
      >
        <div class="sidebar-header">
          <div class="logo">
            <span class="paw-icon">🐾</span>
            <span class="logo-text">宠物店管家</span>
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
          <div class="header-left" style="display: flex; align-items: center; gap: 12px;">
            <el-button
              class="hamburger-btn"
              :icon="isSidebarCollapsed ? Expand : Fold"
              text
              @click="toggleSidebar"
            />
            <h1 style="font-size: 18px; font-weight: 600; margin: 0;">{{ menuItems.find(item => item.path === activeMenu)?.title || '宠物店管理系统' }}</h1>
          </div>
          <div class="header-right" style="display: flex; align-items: center; gap: 16px;">
            <div class="search-wrapper">
              <el-input
                v-model="searchQuery"
                placeholder="搜索账单、宠物、客户..."
                style="width: 300px;"
                :prefix-icon="Search"
                :loading="searchLoading"
                @input="onSearchInput"
                @keyup="onSearchKeyup"
                @blur="closeSearch"
              />
              <div v-if="searchPopoverVisible" class="search-dropdown">
                <template v-if="searchResults.length === 0">
                  <div class="search-empty">无匹配结果</div>
                </template>
                <template v-else>
                  <div v-for="group in groupResults()" :key="group.label" class="search-group">
                    <div class="search-group-title">{{ group.label }}</div>
                    <div
                      v-for="item in group.items"
                      :key="`${item.type}-${item.id}`"
                      class="search-item"
                      @mousedown.prevent="onResultClick(item)"
                    >
                      <span class="search-item-icon">{{ item.type === 'customer' ? '👤' : item.type === 'pet' ? '🐾' : '💰' }}</span>
                      <div class="search-item-body">
                        <div class="search-item-title">{{ item.title }}</div>
                        <div class="search-item-subtitle">{{ item.subtitle }}</div>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
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

/* 搜索下拉面板 */
.search-wrapper {
  position: relative;
}
.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  max-height: 420px;
  overflow-y: auto;
  z-index: 1000;
}
.search-empty {
  padding: 24px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
}
.search-group-title {
  padding: 8px 16px 4px;
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.search-group:first-child .search-group-title {
  padding-top: 12px;
}
.search-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.15s;
}
.search-item:hover {
  background: var(--bg);
}
.search-item:last-child {
  border-radius: 0 0 8px 8px;
}
.search-item-icon {
  font-size: 18px;
  flex-shrink: 0;
}
.search-item-body {
  overflow: hidden;
}
.search-item-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.search-item-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 1440px) {
  .el-main {
    padding: 16px;
  }
}

/* 响应式侧边栏 */
.hamburger-btn {
  display: none;
  font-size: 20px;
}
.sidebar {
  transition: width 0.3s ease;
  overflow: hidden;
  flex-shrink: 0;
}
.sidebar.collapsed {
  width: 0 !important;
  min-width: 0 !important;
  border-right: none !important;
}
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 998;
}

@media (max-width: 767px) {
  .hamburger-btn {
    display: inline-flex;
  }
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 999;
  }
  .sidebar.collapsed {
    transform: translateX(-100%);
  }
  .sidebar-overlay {
    display: block;
  }
}
</style>
