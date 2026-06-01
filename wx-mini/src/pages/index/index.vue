<template>
  <view class="page">
    <!-- Hero：奶油暖白卡，不堆渐变 -->
    <view class="hero">
      <view class="hero-greet">
        <text class="greet">{{ greet }}</text>
        <text class="date">{{ today }} · {{ weekday }}</text>
      </view>

      <view class="hero-amount">
        <text class="amount-label">今日流水</text>
        <view class="amount-value">
          <text class="amount-currency">¥</text>
          <text class="amount-num">{{ totalAmount }}</text>
        </view>
      </view>

      <view class="hero-stats">
        <view class="hero-stat">
          <text class="stat-num">{{ recordCount }}</text>
          <text class="stat-label">今日单数</text>
        </view>
        <view class="hero-stat-divider"></view>
        <view class="hero-stat">
          <text class="stat-num">¥{{ avgAmount }}</text>
          <text class="stat-label">客单价</text>
        </view>
      </view>
    </view>

    <!-- 今日订单 -->
    <view class="section">
      <view class="section-head">
        <view class="title-wrap">
          <text class="section-title">今日订单</text>
          <text v-if="costs.length" class="title-badge">{{ costs.length }}</text>
        </view>
        <text v-if="costs.length" class="section-action" @click="goBill">+ 开新单</text>
      </view>

      <view v-if="loading && !costs.length" class="state">加载中…</view>

      <view v-else-if="!costs.length" class="empty">
        <view class="empty-emoji">📋</view>
        <view class="empty-title">今天还没开单</view>
        <view class="empty-action" @click="goBill">+ 去开第一单</view>
      </view>

      <view v-else class="list">
        <view v-for="c in costs" :key="c.id" class="item">
          <view
            class="item-icon"
            :style="{ background: catTheme(c.category_code).bg, color: catTheme(c.category_code).fg }"
          >
            {{ catTheme(c.category_code).emoji }}
          </view>
          <view class="item-main">
            <view class="item-title">
              <text class="pet">{{ c.pet_name || '—' }}</text>
              <text class="cat">· {{ categoryLabel(c.category_code) }}</text>
            </view>
            <view v-if="c.note" class="item-note">{{ c.note }}</view>
          </view>
          <view class="amount">¥{{ formatAmount(c.amount) }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/category'
import { getSummary } from '@/api/stats'
import { listCosts } from '@/api/costs'

const auth = useAuthStore()
const categoryStore = useCategoryStore()

const today = ref('')
const weekday = ref('')
const summary = ref({ total_amount: 0, record_count: 0 })
const costs = ref([])
const loading = ref(false)

const greet = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早上好'
  if (h < 13) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const recordCount = computed(() => summary.value.record_count || 0)
const totalAmount = computed(() => formatAmount(summary.value.total_amount))
const avgAmount = computed(() => {
  const n = Number(summary.value.record_count || 0)
  if (!n) return '0.00'
  return formatAmount(Number(summary.value.total_amount || 0) / n)
})

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function weekdayStr() {
  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][new Date().getDay()]
}

function formatAmount(v) {
  const n = Number(v || 0)
  if (Number.isNaN(n)) return '0.00'
  return n.toFixed(2)
}

function categoryLabel(code) {
  return categoryStore.byCode(code)?.label || code
}

const CAT_THEME = {
  grooming: { bg: '#FFF4E5', fg: '#E68A00', emoji: '✂️' },
  medical: { bg: '#FFEEEE', fg: '#E03131', emoji: '🏥' },
  food: { bg: '#FFF8E1', fg: '#B8860B', emoji: '🍖' },
  toy: { bg: '#FFEFE0', fg: '#D9480F', emoji: '🎾' },
  boarding: { bg: '#E7F3FB', fg: '#1C7ED6', emoji: '🏠' },
  training: { bg: '#F1ECFF', fg: '#7048E8', emoji: '🐕' },
  retail: { bg: '#F4F9E6', fg: '#5DA716', emoji: '🛍️' },
  other: { bg: '#F1F3F5', fg: '#6C757D', emoji: '📦' },
}
function catTheme(code) {
  return CAT_THEME[code] || CAT_THEME.other
}

function goBill() {
  uni.switchTab({ url: '/pages/bill/bill' })
}

async function loadAll() {
  if (loading.value) return
  loading.value = true
  today.value = todayStr()
  weekday.value = weekdayStr()
  try {
    const [s, list] = await Promise.all([
      getSummary({ start: today.value, end: today.value }),
      listCosts({ start: today.value, end: today.value, page: 1, page_size: 100 }),
      categoryStore.fetch(),
    ])
    summary.value = s
    costs.value = list.items || []
  } catch (e) {
    /* request 已弹 toast */
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!auth.isLogin) {
    uni.reLaunch({ url: '/pages/login/login' })
    return
  }
  loadAll()
})

onShow(() => {
  if (auth.isLogin) loadAll()
})

onPullDownRefresh(async () => {
  await loadAll()
  uni.stopPullDownRefresh()
})
</script>

<style lang="scss">
.page {
  padding: 24rpx 24rpx 60rpx;
}

/* ===== Hero —— 奶油暖白，主色克制点缀 ===== */
.hero {
  background: #FFFAF2;
  border: 1rpx solid #FFE4BD;
  border-radius: 24rpx;
  padding: 32rpx 32rpx 28rpx;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04);
}
.hero-greet {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.greet {
  font-size: 28rpx;
  font-weight: 600;
  color: #212529;
}
.date {
  font-size: 22rpx;
  color: #ADB5BD;
}
.hero-amount {
  margin-top: 24rpx;
}
.amount-label {
  font-size: 24rpx;
  color: #6C757D;
  letter-spacing: 1rpx;
}
.amount-value {
  margin-top: 10rpx;
  display: flex;
  align-items: baseline;
}
.amount-currency {
  font-size: 36rpx;
  font-weight: 500;
  color: #FFA62B;
  margin-right: 6rpx;
}
.amount-num {
  font-size: 76rpx;
  font-weight: 700;
  color: #212529;
  letter-spacing: -1rpx;
  line-height: 1;
}
.hero-stats {
  margin-top: 28rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid #FFE4BD;
  display: flex;
  align-items: center;
}
.hero-stat {
  flex: 1;
  text-align: center;
}
.hero-stat-divider {
  width: 1rpx;
  height: 48rpx;
  background: #FFE4BD;
}
.stat-num {
  font-size: 30rpx;
  font-weight: 600;
  color: #212529;
}
.stat-label {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #6C757D;
}

/* ===== Section ===== */
.section {
  margin-top: 24rpx;
  background: #FFFFFF;
  border: 1rpx solid #E9ECEF;
  border-radius: 24rpx;
  padding: 24rpx 24rpx 8rpx;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04), 0 1rpx 2rpx rgba(33, 37, 41, 0.03);
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4rpx 0 16rpx;
}
.title-wrap {
  display: flex;
  align-items: center;
}
.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #212529;
}
.title-badge {
  margin-left: 12rpx;
  padding: 2rpx 14rpx;
  font-size: 22rpx;
  color: #FFA62B;
  background: #FFF4E5;
  border-radius: 999rpx;
  font-weight: 500;
}
.section-action {
  font-size: 26rpx;
  color: #FFA62B;
  font-weight: 500;
  padding: 4rpx 8rpx;
}

.state {
  padding: 60rpx 0;
  text-align: center;
  color: #ADB5BD;
  font-size: 26rpx;
}
.empty {
  padding: 60rpx 0 80rpx;
  text-align: center;
}
.empty-emoji {
  font-size: 72rpx;
  opacity: 0.6;
}
.empty-title {
  margin-top: 20rpx;
  font-size: 28rpx;
  color: #6C757D;
}
.empty-action {
  margin-top: 20rpx;
  display: inline-block;
  font-size: 26rpx;
  color: #FFA62B;
  padding: 14rpx 32rpx;
  background: #FFF4E5;
  border-radius: 999rpx;
  font-weight: 500;
}

/* ===== 列表 ===== */
.list {
  margin: -4rpx -8rpx 0;
}
.item {
  display: flex;
  align-items: center;
  padding: 20rpx 8rpx;
  border-radius: 12rpx;
  &:active {
    background: #F8F9FA;
  }
}
.item-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 16rpx;
  font-size: 32rpx;
  text-align: center;
  line-height: 72rpx;
  margin-right: 20rpx;
  flex-shrink: 0;
}
.item-main {
  flex: 1;
  min-width: 0;
}
.item-title {
  display: flex;
  align-items: baseline;
  font-size: 28rpx;
  color: #212529;
}
.pet {
  font-weight: 500;
}
.cat {
  margin-left: 8rpx;
  font-size: 24rpx;
  color: #6C757D;
}
.item-note {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #ADB5BD;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.amount {
  flex-shrink: 0;
  margin-left: 16rpx;
  font-size: 30rpx;
  font-weight: 600;
  color: #212529;
}
</style>
