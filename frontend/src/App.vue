<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
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
  Fold,
  Bell,
  SwitchButton,
  ArrowDown
} from '@element-plus/icons-vue'
import { useCategoryStore } from './stores/categoryStore'
import { useAuthStore } from './stores/authStore'
import { search as searchApi } from './api/search'

const router = useRouter()
const route = useRoute()
const categoryStore = useCategoryStore()
const authStore = useAuthStore()
const activeMenu = ref('')

const isPublicRoute = computed(() => !!route.meta.public)
const userInitial = computed(() => (authStore.username || '?').charAt(0).toUpperCase())

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
const searchHistory = ref([])
let debounceTimer = null

const SEARCH_HISTORY_KEY = 'petcost.searchHistory'
const SEARCH_HISTORY_MAX = 8

function loadSearchHistory() {
  try {
    const raw = localStorage.getItem(SEARCH_HISTORY_KEY)
    const arr = raw ? JSON.parse(raw) : []
    searchHistory.value = Array.isArray(arr) ? arr.slice(0, SEARCH_HISTORY_MAX) : []
  } catch {
    searchHistory.value = []
  }
}
function pushSearchHistory(q) {
  const term = q.trim()
  if (!term) return
  const next = [term, ...searchHistory.value.filter((t) => t !== term)].slice(0, SEARCH_HISTORY_MAX)
  searchHistory.value = next
  try {
    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(next))
  } catch {
    /* quota / disabled */
  }
}
function removeSearchHistory(term) {
  const next = searchHistory.value.filter((t) => t !== term)
  searchHistory.value = next
  try {
    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(next))
  } catch {
    /* ignore */
  }
}
function clearSearchHistory() {
  searchHistory.value = []
  try {
    localStorage.removeItem(SEARCH_HISTORY_KEY)
  } catch {
    /* ignore */
  }
}

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}
function escapeRegExp(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
function highlightMatch(text, q) {
  const safe = escapeHtml(text)
  const term = (q || '').trim()
  if (!term) return safe
  const re = new RegExp(escapeRegExp(term), 'gi')
  return safe.replace(re, (m) => `<mark class="search-hit">${m}</mark>`)
}

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
    // 空输入时仍展示历史面板
    searchPopoverVisible.value = searchHistory.value.length > 0
    return
  }
  searchLoading.value = true
  try {
    const res = await searchApi(q)
    searchResults.value = res.results || []
    searchPopoverVisible.value = true
    if ((res.results || []).length > 0) pushSearchHistory(q)
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

const onSearchFocus = () => {
  if (!searchQuery.value.trim() && searchHistory.value.length > 0) {
    searchPopoverVisible.value = true
  }
}

const onHistoryClick = (term) => {
  searchQuery.value = term
  doSearch()
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
  // 加载搜索历史
  loadSearchHistory()

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

async function onLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  authStore.logout()
  router.replace({ path: '/login' })
}
</script>

<template>
  <div class="app-container">
    <!-- 登录等公共路由：仅渲染内容 -->
    <router-view v-if="isPublicRoute" />

    <el-container v-else style="height: 100vh;">
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
        <el-header class="topbar">
          <div class="header-left">
            <el-button
              class="hamburger-btn"
              :icon="isSidebarCollapsed ? Expand : Fold"
              text
              @click="toggleSidebar"
            />
            <h1 class="topbar-title">{{ menuItems.find(item => item.path === activeMenu)?.title || '宠物店管理系统' }}</h1>
          </div>
          <div class="header-right">
            <div class="search-wrapper">
              <el-input
                v-model="searchQuery"
                placeholder="搜索账单、宠物、客户..."
                class="topbar-search"
                :prefix-icon="Search"
                :loading="searchLoading"
                @input="onSearchInput"
                @keyup="onSearchKeyup"
                @focus="onSearchFocus"
                @blur="closeSearch"
              />
              <div v-if="searchPopoverVisible" class="search-dropdown">
                <template v-if="!searchQuery.trim() && searchHistory.length > 0">
                  <div class="search-history-header">
                    <span>搜索历史</span>
                    <span class="search-history-clear" @mousedown.prevent="clearSearchHistory">清空</span>
                  </div>
                  <div
                    v-for="term in searchHistory"
                    :key="term"
                    class="search-item history"
                    @mousedown.prevent="onHistoryClick(term)"
                  >
                    <span class="search-item-icon">🕐</span>
                    <div class="search-item-body">
                      <div class="search-item-title">{{ term }}</div>
                    </div>
                    <span
                      class="search-history-remove"
                      title="移除"
                      @mousedown.prevent.stop="removeSearchHistory(term)"
                    >×</span>
                  </div>
                </template>
                <template v-else-if="searchResults.length === 0">
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
                        <div class="search-item-title" v-html="highlightMatch(item.title, searchQuery)"></div>
                        <div class="search-item-subtitle" v-html="highlightMatch(item.subtitle, searchQuery)"></div>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
            <el-popover
              placement="bottom-end"
              :width="300"
              trigger="click"
              popper-class="notify-popover"
            >
              <template #reference>
                <button class="icon-btn" aria-label="通知">
                  <el-icon :size="18"><Bell /></el-icon>
                </button>
              </template>
              <div class="notify-empty">
                <div class="notify-empty-emoji">🔕</div>
                <p class="notify-empty-title">暂无新通知</p>
                <p class="notify-empty-hint">店铺有重要事件时会出现在这里</p>
              </div>
            </el-popover>
            <el-dropdown trigger="click" @command="(c) => c === 'logout' && onLogout()">
              <div class="user-chip" tabindex="0">
                <span class="user-avatar">{{ userInitial }}</span>
                <div class="user-meta">
                  <span class="user-name">{{ authStore.username || '管理员' }}</span>
                  <span class="user-role">店长</span>
                </div>
                <el-icon class="user-chip-arrow"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    <span style="margin-left: 6px;">退出登录</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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

/* ---- 顶栏 ---- */
.topbar {
  height: 64px;
  background: var(--card);
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.topbar-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 搜索胶囊 */
.topbar-search {
  width: 320px;
}
.topbar-search :deep(.el-input__wrapper) {
  background: var(--bg) !important;
  border: 1px solid transparent !important;
  border-radius: 999px !important;
  height: 38px;
  padding: 0 14px;
  transition: all 0.2s ease;
}
.topbar-search :deep(.el-input__wrapper:hover) {
  background: var(--bg-secondary) !important;
  border-color: var(--border) !important;
}
.topbar-search :deep(.el-input__wrapper.is-focus) {
  background: var(--card) !important;
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 14%, transparent) !important;
}
.topbar-search :deep(.el-input__prefix) {
  color: var(--text-muted);
  margin-right: 4px;
}

/* 通用图标按钮（铃铛） */
.icon-btn {
  width: 38px;
  height: 38px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}
.icon-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: color-mix(in srgb, var(--primary) 6%, transparent);
}

/* 用户胶囊 */
.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 40px;
  padding: 0 12px 0 4px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--card);
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
}
.user-chip:hover,
.user-chip:focus-visible {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 12%, transparent);
}
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--orange));
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 6px color-mix(in srgb, var(--primary) 35%, transparent);
}
.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}
.user-chip-arrow {
  color: var(--text-muted);
  font-size: 12px;
  margin-left: 2px;
}
.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.user-role {
  font-size: 11px;
  color: var(--text-muted);
}

/* 通知面板空状态（在 .notify-popover 全局规则里复用） */
.notify-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 16px 8px;
  gap: 6px;
}
.notify-empty-emoji {
  font-size: 38px;
  line-height: 1;
}
.notify-empty-title {
  margin: 4px 0 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}
.notify-empty-hint {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
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
  margin-top: 6px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.10);
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
  color: var(--text-muted);
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
  border-radius: 0 0 12px 12px;
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
.search-history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px 4px;
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.search-history-clear {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: none;
  letter-spacing: 0;
  cursor: pointer;
}
.search-history-clear:hover {
  color: var(--primary);
}
.search-item.history .search-history-remove {
  margin-left: auto;
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s;
}
.search-item.history:hover .search-history-remove {
  opacity: 1;
}
.search-item.history .search-history-remove:hover {
  background: var(--bg);
  color: var(--text-primary);
}
.search-hit {
  background: color-mix(in srgb, var(--primary) 22%, transparent);
  color: var(--primary);
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 600;
}

@media (max-width: 1440px) {
  .el-main {
    padding: 16px;
  }
  .topbar-search { width: 240px; }
  .user-meta { display: none; }
  .user-chip { padding: 0 4px; }
}
@media (max-width: 1024px) {
  .topbar-title { display: none; }
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
