<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import EChart from '@/components/EChart.vue'
import {
  getSummary,
  getCashflow,
  getByCategory,
  getByMonth,
  getByDay,
  getByPet,
  getCustomerAcquisition,
  getDormantCustomers,
  getTopCustomers,
} from '@/api/stats'
import { listCosts } from '@/api/costs'
import { useCategoryStore } from '@/stores/categoryStore'

const router = useRouter()
const categoryStore = useCategoryStore()

// ECharts 调色板。值与 style.css :root 中 --primary/--success/--info/--purple/
// --orange/--warning/--danger/--text-muted 保持一致。
const chartPalette = [
  '#FFA62B', // primary
  '#82C91E', // success
  '#4DABF7', // info
  '#9775FA', // purple
  '#FF922B', // orange
  '#AE886A', // warning
  '#FF6B6B', // danger
  '#ADB5BD', // muted
]

const now = new Date()
const defaultStart = new Date(now.getFullYear(), now.getMonth(), 1)
const defaultEnd = new Date()
const dateRange = ref([defaultStart, defaultEnd])
const dateRangeKey = ref(0)

function formatDate(d) {
  if (!d) return ''
  const dt = d instanceof Date ? d : new Date(d)
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
}

function getRange() {
  const [start, end] = dateRange.value || []
  return { start: formatDate(start), end: formatDate(end) }
}

// 枚举 [startStr, endStr] 之间的每一天（含端点），返回 'YYYY-MM-DD' 数组
function enumerateDays(startStr, endStr) {
  if (!startStr || !endStr) return []
  const out = []
  const cur = new Date(`${startStr}T00:00:00`)
  const last = new Date(`${endStr}T00:00:00`)
  // 防御：区间反了或日期非法时返回空，避免死循环
  if (Number.isNaN(cur.getTime()) || Number.isNaN(last.getTime()) || cur > last) return []
  // 上限保护：最多枚举约 2 年，避免极端区间生成过多点
  let guard = 0
  while (cur <= last && guard < 800) {
    out.push(formatDate(cur))
    cur.setDate(cur.getDate() + 1)
    guard++
  }
  return out
}

const monthStart = computed(() => getRange().start)
const monthEnd = computed(() => getRange().end)

// 上一周期：按当前区间天数往前对齐一段
const prevRange = computed(() => {
  const [s, e] = dateRange.value || []
  if (!s || !e) return { start: '', end: '' }
  const days = Math.floor((e - s) / 86400000) + 1
  const prevEnd = new Date(s.getTime() - 86400000)
  const prevStart = new Date(prevEnd.getTime() - (days - 1) * 86400000)
  return { start: formatDate(prevStart), end: formatDate(prevEnd) }
})

const rangeLabel = computed(() => {
  const [s, e] = dateRange.value || []
  if (!s || !e) return '本月'
  const sStr = formatDate(s)
  const eStr = formatDate(e)
  const today = new Date()
  const todayStr = formatDate(today)
  const thisMonthStart = formatDate(new Date(today.getFullYear(), today.getMonth(), 1))
  const lastMonthStart = formatDate(new Date(today.getFullYear(), today.getMonth() - 1, 1))
  const lastMonthEnd = formatDate(new Date(today.getFullYear(), today.getMonth(), 0))
  if (sStr === thisMonthStart && eStr === todayStr) return '本月'
  if (sStr === lastMonthStart && eStr === lastMonthEnd) return '上月'
  if (sStr === eStr) return sStr
  return `${sStr} ~ ${eStr}`
})

const greetingHour = now.getHours()
const greeting = computed(() => {
  if (greetingHour < 6) return '深夜好'
  if (greetingHour < 11) return '早上好'
  if (greetingHour < 13) return '中午好'
  if (greetingHour < 18) return '下午好'
  return '晚上好'
})
const todayLabel = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`

const summary = ref({ total_amount: 0, record_count: 0, customer_count: 0, pet_count: 0 })
const prevSummary = ref({ total_amount: 0, record_count: 0, customer_count: 0, pet_count: 0 })
// T-030: 今日营业固定卡片，与日期选择器解耦
const todayStats = ref({ total_amount: 0, record_count: 0, cash_in: 0 })
const todayDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
const categoryStats = ref([])
const monthStats = ref([])
const revenueTrend = ref([])
const petStats = ref([])
const recentBills = ref([])
const acquisition = ref({ new_customers: 0, returning_customers: 0, total: 0 })
const dormantList = ref([])
const dormantDays = ref(90)
const topCustomers = ref([])
const customerInsightTab = ref('top')

// 客户名脱敏：保留姓氏首字，其余用 * 替换（如 张伟→张*，王小明→王**）
function maskName(name) {
  const chars = [...(name || '')]
  if (chars.length === 0) return '—'
  if (chars.length === 1) return chars[0]
  return chars[0] + '*'.repeat(chars.length - 1)
}

const loading = ref({
  summary: false,
  category: false,
  month: false,
  revenueTrend: false,
  pet: false,
  bills: false,
  acquisition: false,
  dormant: false,
  topCustomers: false,
  today: false,
})

const moneyFmt = new Intl.NumberFormat('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const intFmt = new Intl.NumberFormat('zh-CN')
function formatMoney(n) { return `¥${moneyFmt.format(Number(n) || 0)}` }
function formatInt(n) { return intFmt.format(Number(n) || 0) }
function rankMedal(rank) {
  if (rank === 1) return '🥇'
  if (rank === 2) return '🥈'
  if (rank === 3) return '🥉'
  return `${rank}`
}

// 环比：上期 0 时显示「新增」/「—」
function computeDelta(curr, prev) {
  const c = Number(curr) || 0
  const p = Number(prev) || 0
  if (p === 0) {
    if (c === 0) return { sign: 'flat', text: '持平' }
    return { sign: 'up', text: '新增' }
  }
  const pct = ((c - p) / p) * 100
  if (Math.abs(pct) < 0.1) return { sign: 'flat', text: '持平' }
  return {
    sign: pct >= 0 ? 'up' : 'down',
    text: `${pct >= 0 ? '↑' : '↓'} ${Math.abs(pct).toFixed(1)}%`,
  }
}

const deltaTotal = computed(() => computeDelta(summary.value.total_amount, prevSummary.value.total_amount))
const deltaRecord = computed(() => computeDelta(summary.value.record_count, prevSummary.value.record_count))
const deltaCustomer = computed(() => computeDelta(summary.value.customer_count, prevSummary.value.customer_count))
const deltaPet = computed(() => computeDelta(summary.value.pet_count, prevSummary.value.pet_count))

const fetchSummary = async () => {
  loading.value.summary = true
  try {
    const [curr, prev] = await Promise.all([
      getSummary({ start: monthStart.value, end: monthEnd.value }),
      prevRange.value.start
        ? getSummary({ start: prevRange.value.start, end: prevRange.value.end })
        : Promise.resolve({ total_amount: 0, record_count: 0, customer_count: 0, pet_count: 0 }),
    ])
    summary.value = {
      total_amount: Number(curr.total_amount || 0),
      record_count: Number(curr.record_count || 0),
      customer_count: Number(curr.customer_count || 0),
      pet_count: Number(curr.pet_count || 0),
    }
    prevSummary.value = {
      total_amount: Number(prev.total_amount || 0),
      record_count: Number(prev.record_count || 0),
      customer_count: Number(prev.customer_count || 0),
      pet_count: Number(prev.pet_count || 0),
    }
  } catch (e) {
    summary.value = { total_amount: 0, record_count: 0, customer_count: 0, pet_count: 0 }
    prevSummary.value = { total_amount: 0, record_count: 0, customer_count: 0, pet_count: 0 }
  } finally {
    loading.value.summary = false
  }
}

const fetchCategoryStats = async () => {
  loading.value.category = true
  try {
    const res = await getByCategory({ start: monthStart.value, end: monthEnd.value })
    categoryStats.value = (res || [])
      .map((item) => ({ type: item.label || item.category, value: Number(item.total || 0), count: Number(item.count || 0) }))
      .filter((d) => d.value > 0)
  } catch (e) {
    categoryStats.value = []
  } finally {
    loading.value.category = false
  }
}

const fetchMonthStats = async () => {
  loading.value.month = true
  try {
    const res = await getByMonth()
    monthStats.value = (res || [])
      .map((item) => ({ month: item.month, 营业额: Number(item.total || 0) }))
      .sort((a, b) => a.month.localeCompare(b.month))
  } catch (e) {
    monthStats.value = []
  } finally {
    loading.value.month = false
  }
}

// 各 KPI 卡片下方的迷你趋势：按天聚合，跟随顶部日期区间动态变化
// 区间内每一天都补齐（无消费补 0），保证任意区间都是一条连续曲线
const fetchRevenueTrend = async () => {
  loading.value.revenueTrend = true
  try {
    const res = await getByDay({ start: monthStart.value, end: monthEnd.value })
    const byDay = new Map((res || []).map((item) => [item.day, item]))
    revenueTrend.value = enumerateDays(monthStart.value, monthEnd.value).map((day) => {
      const item = byDay.get(day) || {}
      return {
        day,
        营业额: Number(item.total || 0),
        订单数: Number(item.record_count || 0),
        活跃会员: Number(item.customer_count || 0),
        服务宠物: Number(item.pet_count || 0),
      }
    })
  } catch (e) {
    revenueTrend.value = []
  } finally {
    loading.value.revenueTrend = false
  }
}

const fetchPetStats = async () => {
  loading.value.pet = true
  try {
    const res = await getByPet({ start: monthStart.value, end: monthEnd.value, limit: 8 })
    petStats.value = (res || [])
      .map((item) => ({ pet: item.pet_name || `宠物 #${item.pet_id}`, 消费: Number(item.total || 0) }))
      .sort((a, b) => b.消费 - a.消费)
  } catch (e) {
    petStats.value = []
  } finally {
    loading.value.pet = false
  }
}

const fetchRecentBills = async () => {
  loading.value.bills = true
  try {
    const res = await listCosts({ page: 1, page_size: 5 })
    recentBills.value = (res.items || []).map((item) => ({
      id: item.id,
      date: item.occurred_on,
      category: categoryStore.list.find((c) => c.code === item.category_code)?.label || item.category_code,
      pet: item.pet_name || `宠物 #${item.pet_id}`,
      amount: Number(item.amount || 0),
      note: item.note || '',
    }))
  } catch (e) {
    recentBills.value = []
  } finally {
    loading.value.bills = false
  }
}

const fetchAcquisition = async () => {
  loading.value.acquisition = true
  try {
    const res = await getCustomerAcquisition({ year: now.getFullYear(), month: now.getMonth() + 1 })
    acquisition.value = {
      new_customers: Number(res.new_customers || 0),
      returning_customers: Number(res.returning_customers || 0),
      total: Number(res.total || 0),
    }
  } catch (e) {
    acquisition.value = { new_customers: 0, returning_customers: 0, total: 0 }
  } finally {
    loading.value.acquisition = false
  }
}

const fetchDormantCustomers = async () => {
  loading.value.dormant = true
  try {
    const res = await getDormantCustomers({ days: dormantDays.value, limit: 10 })
    dormantList.value = (res || []).map((item) => ({
      customer_id: Number(item.customer_id),
      customer_name: item.customer_name,
      phone: item.phone || '',
      last_visit_at: item.last_visit_at,
      days_since: Number(item.days_since || 0),
    }))
  } catch (e) {
    dormantList.value = []
  } finally {
    loading.value.dormant = false
  }
}

const fetchTopCustomers = async () => {
  loading.value.topCustomers = true
  try {
    const res = await getTopCustomers({ limit: 10, start: monthStart.value, end: monthEnd.value })
    topCustomers.value = (res || []).map((item) => ({
      rank: item.rank,
      customer_id: item.customer_id,
      customer_name: item.customer_name,
      total_amount: Number(item.total_amount || 0),
      order_count: Number(item.order_count || 0),
    }))
  } catch (e) {
    topCustomers.value = []
  } finally {
    loading.value.topCustomers = false
  }
}

// T-030: 今日营业额，与下方日期选择器完全解耦，仅在 mount 时拉一次
const fetchToday = async () => {
  loading.value.today = true
  try {
    const [res, cf] = await Promise.all([
      getSummary({ start: todayDate, end: todayDate }),
      getCashflow({ start: todayDate, end: todayDate }),
    ])
    todayStats.value = {
      total_amount: Number(res.total_amount || 0),
      record_count: Number(res.record_count || 0),
      cash_in: Number(cf.total_cash_in || 0),
    }
  } catch (e) {
    todayStats.value = { total_amount: 0, record_count: 0, cash_in: 0 }
  } finally {
    loading.value.today = false
  }
}

const goToTodayBills = () => {
  router.push({ path: '/bills', query: { start: todayDate, end: todayDate } })
}

const fetchAllData = () => {
  fetchSummary()
  fetchCategoryStats()
  fetchMonthStats()
  fetchRevenueTrend()
  fetchPetStats()
  fetchRecentBills()
  fetchAcquisition()
  fetchDormantCustomers()
  fetchTopCustomers()
  fetchToday()
}

function defaultMonthRange() {
  const t = new Date()
  return [new Date(t.getFullYear(), t.getMonth(), 1), t]
}

function onDateChange(val) {
  if (!val || !val[0] || !val[1]) {
    dateRange.value = defaultMonthRange()
  }
  dateRangeKey.value++
  fetchSummary()
  fetchCategoryStats()
  fetchRevenueTrend()
  fetchPetStats()
  fetchRecentBills()
  fetchTopCustomers()
}

const goToCustomer = (id) => {
  router.push({ name: 'customer-detail', params: { id } })
}

async function copyPhone(phone) {
  try {
    await navigator.clipboard.writeText(phone)
    ElMessage.success('手机号已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

const acquisitionDisplay = computed(() => {
  const { new_customers, returning_customers, total } = acquisition.value
  if (!total) return { newPct: '—', returnPct: '—', newRatio: 0, returnRatio: 0 }
  return {
    newPct: `${Math.round((new_customers / total) * 100)}%`,
    returnPct: `${Math.round((returning_customers / total) * 100)}%`,
    newRatio: (new_customers / total) * 100,
    returnRatio: (returning_customers / total) * 100,
  }
})

// 迷你 sparkline 工厂：四个 KPI 卡片共用，差异仅在指标字段、主色、tooltip 文案/格式
// 数据源跟随顶部日期区间（revenueTrend），与底部「全量历史」趋势图解耦
function makeSparkConfig({ field, color, label, fmt }) {
  const days = revenueTrend.value.map((d) => d.day)
  const data = revenueTrend.value.map((d) => d[field])
  const rgba = (a) => {
    const c = color.replace('#', '')
    const r = parseInt(c.slice(0, 2), 16)
    const g = parseInt(c.slice(2, 4), 16)
    const b = parseInt(c.slice(4, 6), 16)
    return `rgba(${r}, ${g}, ${b}, ${a})`
  }
  return {
    grid: { left: 0, right: 0, top: 4, bottom: 0 },
    xAxis: { type: 'category', show: false, boundaryGap: false, data: days },
    yAxis: { type: 'value', show: false, scale: true },
    tooltip: {
      trigger: 'axis',
      confine: true,
      appendToBody: true,
      axisPointer: { type: 'line', lineStyle: { color, width: 1, type: 'dashed' } },
      formatter: (params) => `${params[0].name}<br/>${label}: ${fmt(params[0].value)}`,
    },
    series: [{
      type: 'line',
      smooth: true,
      showSymbol: false,
      symbol: 'circle',
      symbolSize: 6,
      emphasis: { focus: 'series', itemStyle: { color, borderColor: '#fff', borderWidth: 2 } },
      lineStyle: { color, width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: rgba(0.32) },
            { offset: 1, color: rgba(0) },
          ],
        },
      },
      data,
    }],
  }
}

const revenueSparkConfig = computed(() =>
  makeSparkConfig({ field: '营业额', color: chartPalette[0], label: '营业额', fmt: formatMoney }))
const recordSparkConfig = computed(() =>
  makeSparkConfig({ field: '订单数', color: chartPalette[4], label: '订单数', fmt: formatInt }))
const customerSparkConfig = computed(() =>
  makeSparkConfig({ field: '活跃会员', color: chartPalette[2], label: '活跃会员', fmt: formatInt }))
const petSparkConfig = computed(() =>
  makeSparkConfig({ field: '服务宠物', color: chartPalette[3], label: '服务宠物', fmt: formatInt }))

const pieConfig = computed(() => ({
  color: chartPalette,
  tooltip: { trigger: 'item', formatter: (p) => `${p.name}: ${formatMoney(p.value)} (${p.percent}%)` },
  legend: { bottom: 0, type: 'scroll', icon: 'circle', textStyle: { color: '#6C757D', fontSize: 12 } },
  series: [{
    type: 'pie',
    radius: ['54%', '74%'],
    avoidLabelOverlap: true,
    itemStyle: { borderColor: '#fff', borderWidth: 2 },
    label: { formatter: '{b}\n{d}%', color: '#6C757D', fontSize: 12 },
    data: categoryStats.value.map((d) => ({ name: d.type, value: d.value })),
  }],
}))

const monthBarConfig = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => `${params[0].name}<br/>营业额: ${formatMoney(params[0].value)}`,
  },
  grid: { left: 56, right: 16, top: 12, bottom: 36 },
  xAxis: {
    type: 'category',
    data: monthStats.value.map((d) => d.month),
    axisLine: { lineStyle: { color: '#E9ECEF' } },
    axisTick: { show: false },
    axisLabel: { color: '#6C757D', fontSize: 12 },
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    splitLine: { lineStyle: { color: '#F1F3F5' } },
    axisLabel: { color: '#ADB5BD', fontSize: 12 },
  },
  series: [{
    type: 'bar',
    barMaxWidth: 28,
    itemStyle: {
      borderRadius: [6, 6, 0, 0],
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: '#FFA62B' },
          { offset: 1, color: '#FFD085' },
        ],
      },
    },
    data: monthStats.value.map((d) => d['营业额']),
  }],
}))

const petBarConfig = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    formatter: (params) => `${params[0].name}<br/>消费: ${formatMoney(params[0].value)}`,
  },
  grid: { left: 90, right: 80, top: 12, bottom: 24 },
  xAxis: { type: 'value', axisLine: { show: false }, splitLine: { lineStyle: { color: '#F1F3F5' } }, axisLabel: { color: '#ADB5BD', fontSize: 12 } },
  yAxis: { type: 'category', data: [...petStats.value].reverse().map((d) => d.pet), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#6C757D', fontSize: 12 } },
  series: [{
    type: 'bar',
    barMaxWidth: 14,
    itemStyle: { color: chartPalette[1], borderRadius: [0, 6, 6, 0] },
    label: { show: true, position: 'right', formatter: (p) => formatMoney(p.value), color: '#6C757D', fontSize: 12 },
    data: [...petStats.value].reverse().map((d) => d['消费']),
  }],
}))

onMounted(async () => {
  await categoryStore.fetch(true).catch(() => {})
  fetchAllData()
})

const dateShortcuts = [
  { text: '今天', value: () => [new Date(), new Date()] },
  { text: '本周', value: () => {
    const d = new Date()
    const start = new Date(d.getFullYear(), d.getMonth(), d.getDate() - d.getDay() + 1)
    return [start, d]
  }},
  { text: '本月', value: () => [new Date(now.getFullYear(), now.getMonth(), 1), new Date()] },
  { text: '上月', value: () => {
    const start = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    const end = new Date(now.getFullYear(), now.getMonth(), 0)
    return [start, end]
  }},
  { text: '近30天', value: () => [new Date(now.getTime() - 30 * 86400000), new Date()] },
  { text: '近90天', value: () => [new Date(now.getTime() - 90 * 86400000), new Date()] },
]
</script>

<template>
  <div class="dashboard-page" :key="dateRangeKey">
    <!-- 页面头：标题 + 欢迎语 + chip + 日期条 + 爪印水印 -->
    <div class="page-header">
      <div class="page-title-block">
        <div class="page-title-row">
          <h2>营业概览</h2>
          <span class="page-chip">{{ rangeLabel }}</span>
        </div>
        <p class="page-subtitle">{{ greeting }}，老板。今天是 {{ todayLabel }}，看看店铺的状况吧 ✨</p>
      </div>
      <div class="page-header-right">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="~"
          start-placeholder="开始"
          end-placeholder="结束"
          :shortcuts="dateShortcuts"
          :default-value="[defaultStart, defaultEnd]"
          @change="onDateChange"
          size="default"
          class="header-datepicker"
        />
      </div>
      <svg class="paw-watermark" viewBox="0 0 64 64" aria-hidden="true">
        <ellipse cx="20" cy="20" rx="5" ry="7" />
        <ellipse cx="32" cy="14" rx="5" ry="7" />
        <ellipse cx="44" cy="20" rx="5" ry="7" />
        <ellipse cx="13" cy="34" rx="4" ry="5.5" />
        <ellipse cx="51" cy="34" rx="4" ry="5.5" />
        <path d="M22 38c-3.5 0-7 4-7 9.5 0 6 5 9 10 9s10-3 10-9c0-5.5-3.5-9.5-7-9.5-2 0-3 1-3 1s-1-1-3-1z" />
      </svg>
    </div>

    <!-- T-030: 今日营业固定小卡（与下方日期选择器解耦，专给打烊对账用） -->
    <el-card shadow="hover" class="today-card" v-loading="loading.today">
      <div class="today-row">
        <div class="today-cell">
          <div class="today-label">
            今日营业额
            <el-tooltip placement="top" effect="dark">
              <template #content>
                按「服务发生」统计：当天所有消费订单（现金 + 储值），<br/>
                不含充值（充值是预收款，等消费时才计营业额，避免重复计）。
              </template>
              <span class="today-info">?</span>
            </el-tooltip>
          </div>
          <div class="today-value">{{ formatMoney(todayStats.total_amount) }}</div>
        </div>
        <div class="today-divider"></div>
        <div class="today-cell">
          <div class="today-label">
            今日实收
            <el-tooltip placement="top" effect="dark">
              <template #content>
                按「现金流入」统计：当天充值本金（不含赠送）+ 现金消费，<br/>
                反映今天实际进账多少钱。储值消费不计（充值时已计）。
              </template>
              <span class="today-info">?</span>
            </el-tooltip>
          </div>
          <div class="today-value today-cash">{{ formatMoney(todayStats.cash_in) }}</div>
        </div>
        <div class="today-divider"></div>
        <div class="today-cell">
          <div class="today-label">今日订单数</div>
          <div class="today-value">{{ formatInt(todayStats.record_count) }}</div>
        </div>
        <div class="today-cell today-meta">
          <span class="today-tag">{{ todayDate }}</span>
          <el-button type="primary" plain size="small" @click="goToTodayBills">查看明细 →</el-button>
        </div>
      </div>
    </el-card>

    <!-- KPI 卡片：图标容器 + label + 大数字 + 环比 chip + (营业额) sparkline -->
    <el-row :gutter="16">
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card kpi-revenue" v-loading="loading.summary">
          <div class="kpi-head">
            <div class="kpi-icon tint-primary">💰</div>
            <span class="kpi-label">营业额</span>
          </div>
          <div class="kpi-value">{{ formatMoney(summary.total_amount) }}</div>
          <div class="kpi-foot">
            <span class="delta" :class="`delta-${deltaTotal.sign}`">{{ deltaTotal.text }}</span>
            <span class="delta-hint">vs 上一周期</span>
          </div>
          <div class="kpi-spark" v-if="revenueTrend.length > 1">
            <EChart :option="revenueSparkConfig" />
          </div>
          <div class="kpi-spark-placeholder" v-else></div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card" v-loading="loading.summary">
          <div class="kpi-head">
            <div class="kpi-icon tint-orange">📋</div>
            <span class="kpi-label">订单数</span>
          </div>
          <div class="kpi-value">{{ formatInt(summary.record_count) }}</div>
          <div class="kpi-foot">
            <span class="delta" :class="`delta-${deltaRecord.sign}`">{{ deltaRecord.text }}</span>
            <span class="delta-hint">vs 上一周期</span>
          </div>
          <div class="kpi-spark" v-if="revenueTrend.length > 1">
            <EChart :option="recordSparkConfig" />
          </div>
          <div class="kpi-spark-placeholder" v-else></div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card" v-loading="loading.summary">
          <div class="kpi-head">
            <div class="kpi-icon tint-info">👥</div>
            <span class="kpi-label">活跃会员</span>
          </div>
          <div class="kpi-value">{{ formatInt(summary.customer_count) }}</div>
          <div class="kpi-foot">
            <span class="delta" :class="`delta-${deltaCustomer.sign}`">{{ deltaCustomer.text }}</span>
            <span class="delta-hint">vs 上一周期</span>
          </div>
          <div class="kpi-spark" v-if="revenueTrend.length > 1">
            <EChart :option="customerSparkConfig" />
          </div>
          <div class="kpi-spark-placeholder" v-else></div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card" v-loading="loading.summary">
          <div class="kpi-head">
            <div class="kpi-icon tint-purple">🐾</div>
            <span class="kpi-label">服务宠物</span>
          </div>
          <div class="kpi-value">{{ formatInt(summary.pet_count) }}</div>
          <div class="kpi-foot">
            <span class="delta" :class="`delta-${deltaPet.sign}`">{{ deltaPet.text }}</span>
            <span class="delta-hint">vs 上一周期</span>
          </div>
          <div class="kpi-spark" v-if="revenueTrend.length > 1">
            <EChart :option="petSparkConfig" />
          </div>
          <div class="kpi-spark-placeholder" v-else></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 客户洞察行 -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" v-loading="loading.acquisition" class="full-h-card">
          <template #header>
            <div class="card-head">
              <strong>新客 vs 回头客</strong>
              <span class="card-head-hint">本月</span>
            </div>
          </template>
          <div class="acq-block">
            <!-- 比例条 -->
            <div class="ratio-bar">
              <div class="ratio-seg ratio-new" :style="{ width: `${acquisitionDisplay.newRatio}%` }"></div>
              <div class="ratio-seg ratio-return" :style="{ width: `${acquisitionDisplay.returnRatio}%` }"></div>
            </div>
            <div class="ratio-legend">
              <span class="legend-item"><span class="legend-dot dot-info"></span>新客 {{ acquisitionDisplay.newPct }}</span>
              <span class="legend-item"><span class="legend-dot dot-success"></span>回头 {{ acquisitionDisplay.returnPct }}</span>
            </div>
            <!-- 三段数字 -->
            <div class="kv-list">
              <div class="kv-row">
                <span class="kv-key">新客</span>
                <span class="kv-val">{{ acquisition.new_customers }}</span>
              </div>
              <div class="kv-row">
                <span class="kv-key">回头客</span>
                <span class="kv-val">{{ acquisition.returning_customers }}</span>
              </div>
              <div class="kv-row">
                <span class="kv-key">活跃总数（去重）</span>
                <span class="kv-val">{{ acquisition.total }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card shadow="hover" class="full-h-card">
          <template #header>
            <div class="insight-tabs-header">
              <el-tabs v-model="customerInsightTab" class="insight-tabs">
                <el-tab-pane label="高价值客户 TOP 10" name="top" />
                <el-tab-pane label="久未到店预警" name="dormant" />
              </el-tabs>
              <el-select
                v-if="customerInsightTab === 'dormant'"
                v-model="dormantDays"
                size="small"
                style="width: 120px;"
                @change="fetchDormantCustomers"
              >
                <el-option :value="30" label="≥ 30 天" />
                <el-option :value="60" label="≥ 60 天" />
                <el-option :value="90" label="≥ 90 天" />
                <el-option :value="180" label="≥ 180 天" />
              </el-select>
            </div>
          </template>

          <!-- 久未到店 -->
          <div v-show="customerInsightTab === 'dormant'" v-loading="loading.dormant">
            <el-table v-if="dormantList.length > 0" :data="dormantList" size="small" style="width: 100%;">
              <el-table-column prop="customer_name" label="客户" min-width="140">
                <template #default="{ row }">
                  <span class="name-link" @click="goToCustomer(row.customer_id)">
                    {{ maskName(row.customer_name) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="last_visit_at" label="最后到店" width="120" />
              <el-table-column label="距今" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.days_since >= 180 ? 'danger' : 'warning'" effect="plain" size="small">
                    {{ row.days_since }} 天
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="联系" min-width="170">
                <template #default="{ row }">
                  <template v-if="row.phone">
                    <span class="phone-masked">{{ row.phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') }}</span>
                    <el-button type="primary" link size="small" style="margin-left: 6px;" @click="copyPhone(row.phone)">复制</el-button>
                  </template>
                  <span v-else class="text-muted">—</span>
                </template>
              </el-table-column>
              <el-table-column label="" width="60" align="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="goToCustomer(row.customer_id)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div class="empty-state" v-else>
              <div class="empty-emoji">🐱</div>
              <p class="empty-title">所有老客都最近回来过</p>
              <p class="empty-hint">没有需要召回的客户，店铺关系维护得不错</p>
            </div>
          </div>

          <!-- Top10 -->
          <div v-show="customerInsightTab === 'top'" v-loading="loading.topCustomers">
            <el-table v-if="topCustomers.length > 0" :data="topCustomers" size="small" style="width: 100%;">
              <el-table-column label="" width="60" align="center">
                <template #default="{ row }">
                  <span class="rank-medal" :class="{ top3: row.rank <= 3 }">{{ rankMedal(row.rank) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="customer_name" label="客户" min-width="140">
                <template #default="{ row }">
                  <span class="name-link" @click="goToCustomer(row.customer_id)">
                    {{ maskName(row.customer_name) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column :label="`消费（${rangeLabel}）`" width="160">
                <template #default="{ row }">
                  <span class="top-amount">{{ formatMoney(row.total_amount) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="order_count" label="订单" width="80" align="center" />
              <el-table-column label="" width="60" align="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="goToCustomer(row.customer_id)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div class="empty-state" v-else>
              <div class="empty-emoji">📊</div>
              <p class="empty-title">暂无消费数据</p>
              <p class="empty-hint">客户消费产生后会自动排名</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表行 1 -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" v-loading="loading.category">
          <template #header>
            <div class="card-head"><strong>服务项目营收占比</strong><span class="card-head-hint">{{ rangeLabel }}</span></div>
          </template>
          <div style="height: 300px;" v-if="categoryStats.length > 0"><EChart :option="pieConfig" /></div>
          <div class="empty-state" v-else>
            <div class="empty-emoji">🍰</div>
            <p class="empty-title">暂无消费数据</p>
            <p class="empty-hint">本期没有产生服务订单</p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" v-loading="loading.pet">
          <template #header>
            <div class="card-head"><strong>消费宠物 TOP 8</strong><span class="card-head-hint">{{ rangeLabel }}</span></div>
          </template>
          <div style="height: 300px;" v-if="petStats.length > 0"><EChart :option="petBarConfig" /></div>
          <div class="empty-state" v-else>
            <div class="empty-emoji">🐶</div>
            <p class="empty-title">暂无宠物消费数据</p>
            <p class="empty-hint">本期没有宠物到店服务</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表行 2 -->
    <el-row :gutter="16" style="margin-top: 16px; margin-bottom: 8px;">
      <el-col :xs="24" :lg="14">
        <el-card shadow="hover" v-loading="loading.month">
          <template #header>
            <div class="card-head"><strong>月度营业额趋势</strong><span class="card-head-hint">全量历史</span></div>
          </template>
          <div style="height: 300px;" v-if="monthStats.length > 0"><EChart :option="monthBarConfig" /></div>
          <div class="empty-state" v-else>
            <div class="empty-emoji">📈</div>
            <p class="empty-title">暂无月度数据</p>
            <p class="empty-hint">至少积累一个月数据后展示</p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="10">
        <el-card shadow="hover" v-loading="loading.bills">
          <template #header>
            <div class="card-head"><strong>最近订单</strong><span class="card-head-hint">最新 5 笔</span></div>
          </template>
          <div v-if="recentBills.length > 0" class="recent-bills">
            <div v-for="bill in recentBills" :key="bill.id" class="bill-item">
              <div class="bill-left">
                <div class="bill-info">
                  <el-tag size="small" effect="plain">{{ bill.category }}</el-tag>
                  <span class="bill-pet">{{ bill.pet }}</span>
                </div>
                <div class="bill-meta">
                  <span>{{ bill.date }}</span>
                  <span v-if="bill.note" class="bill-note">· {{ bill.note }}</span>
                </div>
              </div>
              <div class="bill-amount">{{ formatMoney(bill.amount) }}</div>
            </div>
          </div>
          <div class="empty-state" v-else>
            <div class="empty-emoji">🧾</div>
            <p class="empty-title">暂无订单</p>
            <p class="empty-hint">第一笔订单还在路上</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
/* ---- 页面头 ---- */
.page-header {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;
  overflow: hidden;
}
.page-title-block {
  min-width: 0;
}
.page-title-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.page-title-row h2 {
  margin: 0;
  font-size: 22px;
  letter-spacing: -0.3px;
}
.page-chip {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary) 14%, transparent);
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
.page-subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--text-muted);
}
.page-header-right {
  flex-shrink: 0;
  z-index: 1;
}
.header-datepicker { width: 280px; }

/* 爪印水印：跟随页面头放右侧，作为品牌点缀 */
.paw-watermark {
  position: absolute;
  top: -10px;
  right: 320px;
  width: 88px;
  height: 88px;
  fill: var(--primary);
  opacity: 0.06;
  transform: rotate(-12deg);
  pointer-events: none;
}

/* ---- 卡片公共头 ---- */
.card-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.card-head strong { font-size: 14px; color: var(--text-primary); }
.card-head-hint { color: var(--text-muted); font-size: 12px; font-weight: 400; }

/* ---- KPI 卡片 ---- */
.kpi-card :deep(.el-card__body) {
  padding: 18px 20px 14px;
}
.kpi-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.kpi-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.tint-primary { background: color-mix(in srgb, var(--primary) 14%, transparent); }
.tint-success { background: color-mix(in srgb, var(--success) 14%, transparent); }
.tint-info    { background: color-mix(in srgb, var(--info) 14%, transparent); }
.tint-purple  { background: color-mix(in srgb, var(--purple) 14%, transparent); }
.tint-orange  { background: color-mix(in srgb, var(--orange) 14%, transparent); }

.kpi-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}
.kpi-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  letter-spacing: -0.5px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-foot {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
}
.delta {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.delta-up   { background: color-mix(in srgb, var(--success) 14%, transparent); color: var(--success); }
.delta-down { background: color-mix(in srgb, var(--danger) 14%, transparent);  color: var(--danger); }
.delta-flat { background: var(--bg-secondary); color: var(--text-muted); }
.delta-hint { color: var(--text-muted); }

.kpi-spark {
  height: 36px;
  margin: 6px -8px -4px;
}
.kpi-spark-placeholder { height: 36px; margin-top: 6px; }

/* ---- 客户洞察行 ---- */
.full-h-card { height: 100%; }
.full-h-card :deep(.el-card__body) {
  height: calc(100% - 57px);
  display: flex;
  flex-direction: column;
}

/* 比例条 */
.acq-block { display: flex; flex-direction: column; gap: 16px; flex: 1; }
.ratio-bar {
  display: flex;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--bg-secondary);
}
.ratio-seg { transition: width 0.4s ease; }
.ratio-seg.ratio-new    { background: var(--info); }
.ratio-seg.ratio-return { background: var(--success); }
.ratio-legend {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}
.legend-item { display: inline-flex; align-items: center; gap: 6px; }
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.dot-success { background: var(--success); }
.dot-info    { background: var(--info); }

/* k/v 行 */
.kv-list {
  display: flex;
  flex-direction: column;
  flex: 1;
  justify-content: center;
}
.kv-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}
.kv-row:last-child { border-bottom: none; }
.kv-key { font-size: 13px; color: var(--text-secondary); }
.kv-val {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}

/* ---- Tabs 头 ---- */
.insight-tabs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.insight-tabs { flex: 1; }
.insight-tabs :deep(.el-tabs__header) { margin: 0; }
.insight-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }

.rank-medal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}
.rank-medal.top3 {
  font-size: 18px;
  color: inherit;
}
.top-amount {
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
.name-link {
  color: var(--text-primary);
  cursor: pointer;
}
.name-link:hover {
  text-decoration: underline;
  text-underline-offset: 2px;
}
.phone-masked {
  font-family: 'Menlo', 'Monaco', monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

/* ---- 最近订单 ---- */
.recent-bills { display: flex; flex-direction: column; }
.bill-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  gap: 12px;
}
.bill-item:first-child { padding-top: 4px; }
.bill-item:last-child { padding-bottom: 0; border-bottom: none; }
.bill-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}
.bill-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.bill-pet { font-size: 14px; color: var(--text-primary); font-weight: 500; }
.bill-meta {
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  gap: 4px;
  align-items: center;
}
.bill-note {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}
.bill-amount {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

/* ---- 空状态：emoji + 标题 + 提示 ---- */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 240px;
  color: var(--text-muted);
}
.empty-emoji {
  font-size: 56px;
  line-height: 1;
  opacity: 0.85;
  margin-bottom: 4px;
  filter: saturate(0.95);
}
.empty-title {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}
.empty-hint {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}
.text-muted { color: var(--text-muted); }

/* ---- T-030: 今日营业固定小卡 ---- */
.today-card {
  margin-bottom: 16px;
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--primary) 6%, var(--bg-card, #fff)),
    var(--bg-card, #fff));
  border: 1px solid color-mix(in srgb, var(--primary) 18%, transparent);
}
.today-card :deep(.el-card__body) { padding: 14px 20px; }
.today-row {
  display: flex;
  align-items: center;
  gap: 28px;
}
.today-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.today-cell.today-meta {
  margin-left: auto;
  flex-direction: row;
  align-items: center;
  gap: 12px;
}
.today-label {
  font-size: 12px;
  color: var(--text-muted);
}
.today-info {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  margin-left: 4px;
  border-radius: 50%;
  background: var(--bg-secondary);
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 700;
  cursor: help;
  vertical-align: middle;
}
.today-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}
.today-value.today-cash {
  color: var(--success);
}
.today-tag {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary) 12%, transparent);
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.today-divider {
  width: 1px;
  height: 36px;
  background: var(--border);
}
@media (max-width: 767px) {
  .today-row { flex-wrap: wrap; gap: 14px; }
  .today-divider { display: none; }
  .today-cell.today-meta { width: 100%; margin-left: 0; justify-content: space-between; }
}

@media (max-width: 1440px) {
  .header-datepicker { width: 240px; }
  .paw-watermark { right: 280px; }
  .kpi-value { font-size: 22px; }
}
@media (max-width: 767px) {
  .page-header { flex-direction: column; align-items: stretch; }
  .header-datepicker { width: 100%; }
  .paw-watermark { display: none; }
}
</style>
