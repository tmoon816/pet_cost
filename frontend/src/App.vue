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
  ArrowDown,
  Wallet,
  House,
  QuestionFilled
} from '@element-plus/icons-vue'
import { useCategoryStore } from './stores/categoryStore'
import { useAuthStore } from './stores/authStore'
import { search as searchApi } from './api/search'
import { getBoardingAlerts } from './api/boarding'

const router = useRouter()
const route = useRoute()
const categoryStore = useCategoryStore()
const authStore = useAuthStore()
const activeMenu = ref('')

const isPublicRoute = computed(() => !!route.meta.public)
const userInitial = computed(() => (authStore.username || '?').charAt(0).toUpperCase())

// 使用帮助文档抽屉
const docVisible = ref(false)
const activeDocSection = ref('intro')
const docSections = [
  { key: 'intro', title: '系统概览', icon: '🏠' },
  { key: 'customer', title: '会员与宠物', icon: '👤' },
  { key: 'order', title: '服务订单', icon: '🧾' },
  { key: 'recharge', title: '套餐充值与储值', icon: '💳' },
  { key: 'boarding', title: '寄养管理', icon: '🛏️' },
  { key: 'revenue', title: '营业额口径', icon: '📊' },
  { key: 'settings', title: '系统设置', icon: '⚙️' },
  { key: 'faq', title: '常见问题', icon: '❓' },
]
function openDocSection(key) {
  activeDocSection.value = key
  const el = document.getElementById(`doc-${key}`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// 寄养提醒（顶部铃铛）
const alerts = ref([])
async function loadAlerts() {
  try {
    const res = await getBoardingAlerts()
    alerts.value = res || []
  } catch {
    alerts.value = []
  }
}
function goAlert(a) {
  router.push({ name: 'customer-detail', params: { id: a.customer_id } })
}

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
  { path: '/recharge',   title: '套餐充值',     icon: Wallet },
  { path: '/boarding',   title: '寄养管理',     icon: House },
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
  // 加载寄养提醒（铃铛角标）
  loadAlerts()

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
            <button class="icon-btn" aria-label="使用帮助" @click="docVisible = true">
              <el-icon :size="18"><QuestionFilled /></el-icon>
            </button>
            <el-popover
              placement="bottom-end"
              :width="320"
              trigger="click"
              popper-class="notify-popover"
              @show="loadAlerts"
            >
              <template #reference>
                <button class="icon-btn" aria-label="通知">
                  <el-icon :size="18"><Bell /></el-icon>
                  <span v-if="alerts.length > 0" class="notify-badge">{{ alerts.length > 99 ? '99+' : alerts.length }}</span>
                </button>
              </template>
              <div v-if="alerts.length === 0" class="notify-empty">
                <div class="notify-empty-emoji">🔕</div>
                <p class="notify-empty-title">暂无新通知</p>
                <p class="notify-empty-hint">店铺有重要事件时会出现在这里</p>
              </div>
              <div v-else class="notify-list">
                <div class="notify-list-header">
                  <span>寄养提醒</span>
                  <span class="notify-count">{{ alerts.length }} 条</span>
                </div>
                <div
                  v-for="(a, i) in alerts"
                  :key="i"
                  class="notify-item"
                  @click="goAlert(a)"
                >
                  <span class="notify-item-icon">{{ a.type === 'overdue' ? '⏰' : '⚠️' }}</span>
                  <div class="notify-item-body">
                    <div class="notify-item-title">{{ a.type === 'overdue' ? '寄养超期' : '余额欠费' }}</div>
                    <div class="notify-item-text">{{ a.message }}</div>
                  </div>
                </div>
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

    <!-- 使用帮助文档抽屉 -->
    <el-drawer
      v-model="docVisible"
      title="使用帮助 · 操作指南"
      direction="rtl"
      size="640px"
      class="doc-drawer"
    >
      <div class="doc-layout">
        <!-- 左侧目录 -->
        <nav class="doc-nav">
          <button
            v-for="s in docSections"
            :key="s.key"
            class="doc-nav-item"
            :class="{ on: activeDocSection === s.key }"
            @click="openDocSection(s.key)"
          >
            <span class="doc-nav-icon">{{ s.icon }}</span>{{ s.title }}
          </button>
        </nav>

        <!-- 右侧内容 -->
        <div class="doc-content">
          <section id="doc-intro" class="doc-sec">
            <h3>🏠 系统概览</h3>
            <p>这是一套面向宠物店的管理系统，核心围绕「会员 → 宠物 → 服务订单 → 储值」展开。左侧菜单是主要功能入口：</p>
            <ul>
              <li><b>营业概览</b>：看店铺整体经营数据（营业额、订单、会员趋势）。</li>
              <li><b>会员/客户档案</b>：管理客户资料、储值余额、消费记录。</li>
              <li><b>服务订单</b>：日常开单记账（洗护、医疗、寄养等）。</li>
              <li><b>套餐充值</b>：给会员办理储值卡充值。</li>
              <li><b>寄养管理</b>：长期寄养按天自动扣费。</li>
              <li><b>服务项目 / 经营预算 / 系统设置</b>：基础配置与目标管理。</li>
            </ul>
          </section>

          <section id="doc-customer" class="doc-sec">
            <h3>👤 会员与宠物</h3>
            <p>先建客户，再在客户名下添加宠物。订单和寄养都挂在宠物上，扣费时自动找到所属客户的钱包。</p>
            <ul>
              <li>支持按姓名/手机号搜索，也支持批量导入客户。</li>
              <li>客户详情页能看到：累计消费、储值余额、储值流水、名下宠物。</li>
              <li>会员分层（VIP/SVIP/至尊）按「贡献金额」自动计算，可在系统设置里调阈值和折扣。</li>
            </ul>
          </section>

          <section id="doc-order" class="doc-sec">
            <h3>🧾 服务订单</h3>
            <p>每一笔到店服务都记一条订单。开单时选择支付方式：</p>
            <ul>
              <li><b>现金</b>：客户当场付钱，不动储值余额。</li>
              <li><b>储值扣款</b>：从会员卡余额里扣，享会员折扣；余额不足会被拒绝（寄养除外）。</li>
            </ul>
            <p class="doc-tip">💡 删除/修改储值订单会自动退回或重扣余额，保证账目一致。</p>
          </section>

          <section id="doc-recharge" class="doc-sec">
            <h3>💳 套餐充值与储值</h3>
            <p>在「套餐充值」页选套餐 + 选会员即可充值，到账 = 实付本金 + 赠送金额，赠品记入流水备注。</p>
            <ul>
              <li>套餐内容（价格、赠送、赠品、卖点）都能在<b>系统设置 → 充值套餐配置</b>里自定义。</li>
              <li>充值后余额立即到账，可在客户详情的储值流水查看。</li>
              <li>标「推荐」的套餐会在充值页高亮并默认选中。</li>
            </ul>
            <p class="doc-tip">⚠️ 充值是「预收款」：钱进了卡里但还没消费。详见下方「营业额口径」。</p>
          </section>

          <section id="doc-boarding" class="doc-sec">
            <h3>🛏️ 寄养管理</h3>
            <p>适合长期寄养/疗养。建单时设入住日、约定天数、每日价，系统<b>每天自动扣一笔寄养费</b>（走储值）。</p>
            <ul>
              <li><b>自动补扣</b>：软件每次启动会把没扣的天数一次性补齐，关机几天也不漏。</li>
              <li><b>超期继续扣</b>：超过约定天数仍未退房，照常按天扣并在铃铛提醒。</li>
              <li><b>可欠费</b>：余额扣光后继续扣成负数（欠费），铃铛会提醒。</li>
              <li><b>退房</b>：办理退房时结清到退房前一天，退房当天不计费。</li>
            </ul>
            <p class="doc-tip">💡 顶部🔔铃铛会汇总「寄养超期」和「余额欠费」提醒。</p>
          </section>

          <section id="doc-revenue" class="doc-sec">
            <h3>📊 营业额口径（重要）</h3>
            <p>为避免「同一笔钱算两遍」，请理解钱的两个阶段：</p>
            <ul>
              <li><b>充值</b>：客户把钱充进卡 —— 这是预收款。</li>
              <li><b>消费</b>：客户用卡里的钱消费（储值扣款）—— 这才是服务发生。</li>
            </ul>
            <p>当前「营业额/今日营业」按<b>服务发生</b>统计：所有消费订单（现金 + 储值）计入营业额，<b>充值本身不计入营业额</b>，否则充值时算一次、消费时再算一次会重复。</p>
            <p>营业概览顶部同时提供两个数字，对照看更清楚：</p>
            <ul>
              <li><b>今日营业额</b>：今天发生的消费（服务）总额。</li>
              <li><b>今日实收</b>：今天实际进账的现金 = 充值本金（不含赠送）+ 现金消费。反映"今天到底收了多少钱"。</li>
            </ul>
            <p class="doc-tip">💡 充值当天进「今日实收」，客户日后用储值消费进「营业额」，两个口径各看各的，互不重复。</p>
          </section>

          <section id="doc-settings" class="doc-sec">
            <h3>⚙️ 系统设置</h3>
            <ul>
              <li><b>会员分层 & 折扣</b>：设定 VIP/SVIP/至尊的达标金额和折扣率。</li>
              <li><b>服务项目字典</b>：维护开单时可选的服务分类及默认价。</li>
              <li><b>充值套餐配置</b>：增删改充值套餐，每个小项（价格/赠送/赠品/卖点/角标/推荐/启用）都可配。</li>
            </ul>
          </section>

          <section id="doc-faq" class="doc-sec">
            <h3>❓ 常见问题</h3>
            <p><b>Q：充值的钱为什么没进营业额？</b><br/>A：充值是预收款，等客户消费时才计入营业额，避免重复计算。</p>
            <p><b>Q：寄养扣费在哪看？</b><br/>A：每天的寄养费会作为「寄养」分类的订单出现在服务订单和客户储值流水里。</p>
            <p><b>Q：余额能为负吗？</b><br/>A：普通开单余额不足会被拒绝；只有寄养允许扣成负数（欠费），并会提醒。</p>
            <p><b>Q：关机几天寄养费会漏扣吗？</b><br/>A：不会。每次启动会自动补扣欠下的天数，且不会重复扣。</p>
          </section>
        </div>
      </div>
    </el-drawer>
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

/* 铃铛角标 + 通知列表 */
.notify-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--danger);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  box-shadow: 0 0 0 2px var(--card);
}
.notify-list { max-height: 360px; overflow-y: auto; }
.notify-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 6px 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border);
}
.notify-count { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.notify-item {
  display: flex;
  gap: 10px;
  padding: 10px 6px;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.15s;
}
.notify-item:hover { background: var(--bg); }
.notify-item-icon { font-size: 18px; flex-shrink: 0; }
.notify-item-body { overflow: hidden; }
.notify-item-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.notify-item-text {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  margin-top: 2px;
}

/* ---- 使用帮助文档抽屉 ---- */
.doc-layout {
  display: flex;
  gap: 16px;
  height: 100%;
}
.doc-nav {
  flex: 0 0 150px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: sticky;
  top: 0;
  align-self: flex-start;
}
.doc-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  text-align: left;
  padding: 9px 12px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}
.doc-nav-item:hover { background: var(--bg); color: var(--text-primary); }
.doc-nav-item.on {
  background: color-mix(in srgb, var(--primary) 12%, transparent);
  color: var(--primary);
  font-weight: 600;
}
.doc-nav-icon { font-size: 15px; }
.doc-content {
  flex: 1;
  overflow-y: auto;
  padding-right: 6px;
}
.doc-sec {
  padding-bottom: 22px;
  margin-bottom: 22px;
  border-bottom: 1px dashed var(--border);
}
.doc-sec:last-child { border-bottom: none; }
.doc-sec h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 10px;
}
.doc-sec p {
  font-size: 13.5px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 8px;
}
.doc-sec ul {
  margin: 0 0 8px;
  padding-left: 18px;
}
.doc-sec li {
  font-size: 13.5px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 4px;
}
.doc-sec b { color: var(--text-primary); }
.doc-tip {
  background: var(--bg);
  border-left: 3px solid var(--primary);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px !important;
  margin-top: 6px;
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
