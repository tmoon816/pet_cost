<template>
  <view class="page">
    <!-- 渐变 hero 卡 -->
    <view class="hero">
      <view class="hero-blob hero-blob-1"></view>
      <view class="hero-blob hero-blob-2"></view>

      <view class="hero-top">
        <view class="hero-greet">{{ greet }}</view>
        <view class="hero-date">{{ today }} · {{ weekday }}</view>
      </view>

      <view class="hero-amount-label">今日流水</view>
      <view class="hero-amount">
        <text class="amt-currency">¥</text>
        <text class="amt-num">{{ totalAmount }}</text>
      </view>

      <view class="hero-stats">
        <view class="hero-stat">
          <view class="hero-stat-num">{{ recordCount }}</view>
          <view class="hero-stat-label">今日单数</view>
        </view>
        <view class="hero-stat-divider"></view>
        <view class="hero-stat">
          <view class="hero-stat-num">¥{{ avgAmount }}</view>
          <view class="hero-stat-label">客单价</view>
        </view>
      </view>
    </view>

    <!-- 今日订单 -->
    <view class="section">
      <view class="section-head">
        <view class="section-title-wrap">
          <text class="section-title">今日订单</text>
          <text v-if="costs.length" class="section-badge">{{ costs.length }}</text>
        </view>
        <text v-if="costs.length" class="section-action" @click="goBill">+ 开新单</text>
      </view>

      <view v-if="loading && !costs.length" class="state">加载中…</view>
      <view v-else-if="!costs.length" class="empty">
        <view class="empty-emoji">🐾</view>
        <view class="empty-title">今天还没有开单</view>
        <view class="empty-tip" @click="goBill">点这里去开第一单</view>
      </view>

      <view v-else class="list">
        <view v-for="c in costs" :key="c.id" class="item">
          <view class="item-icon" :style="{ background: catColor(c.category_code).bg, color: catColor(c.category_code).fg }">
            {{ catEmoji(c.category_code) }}
          </view>
          <view class="item-main">
            <view class="item-title">
              <text class="pet">{{ c.pet_name || '—' }}</text>
              <text class="cat">{{ categoryLabel(c.category_code) }}</text>
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
  grooming: { bg: '#EEF0FF', fg: '#5B5BF2', emoji: '✂️' },
  medical: { bg: '#FEE2E2', fg: '#EF4444', emoji: '🏥' },
  food: { bg: '#FEF3C7', fg: '#F59E0B', emoji: '🍖' },
  toy: { bg: '#FFEDD5', fg: '#FB923C', emoji: '🎾' },
  boarding: { bg: '#E0F2FE', fg: '#0EA5E9', emoji: '🏠' },
  training: { bg: '#F3E8FF', fg: '#A855F7', emoji: '🐕' },
  retail: { bg: '#D1FAE5', fg: '#10B981', emoji: '🛍️' },
  other: { bg: '#F1F5F9', fg: '#64748B', emoji: '📦' },
}
function catColor(code) {
  return CAT_THEME[code] || CAT_THEME.other
}
function catEmoji(code) {
  return catColor(code).emoji
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

/* ===== Hero ===== */
.hero {
  position: relative;
  background: linear-gradient(135deg, #5B5BF2 0%, #8B5CF6 100%);
  border-radius: 32rpx;
  padding: 36rpx 36rpx 28rpx;
  color: #fff;
  overflow: hidden;
  box-shadow: 0 14rpx 40rpx rgba(91, 91, 242, 0.3);
}
.hero-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(40rpx);
  opacity: 0.5;
  pointer-events: none;
}
.hero-blob-1 {
  width: 280rpx;
  height: 280rpx;
  background: #C084FC;
  top: -80rpx;
  right: -80rpx;
}
.hero-blob-2 {
  width: 220rpx;
  height: 220rpx;
  background: #F472B6;
  bottom: -100rpx;
  left: -60rpx;
}
.hero-top {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.hero-greet {
  font-size: 30rpx;
  font-weight: 500;
}
.hero-date {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.78);
}
.hero-amount-label {
  position: relative;
  margin-top: 36rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.78);
  letter-spacing: 1rpx;
}
.hero-amount {
  position: relative;
  margin-top: 12rpx;
  display: flex;
  align-items: baseline;
}
.amt-currency {
  font-size: 36rpx;
  font-weight: 500;
  margin-right: 6rpx;
  color: rgba(255, 255, 255, 0.92);
}
.amt-num {
  font-size: 80rpx;
  font-weight: 700;
  letter-spacing: -1rpx;
  line-height: 1;
}
.hero-stats {
  position: relative;
  margin-top: 36rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
}
.hero-stat {
  flex: 1;
  text-align: center;
}
.hero-stat-divider {
  width: 1rpx;
  height: 60rpx;
  background: rgba(255, 255, 255, 0.18);
}
.hero-stat-num {
  font-size: 32rpx;
  font-weight: 600;
}
.hero-stat-label {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.78);
}

/* ===== Section ===== */
.section {
  margin-top: 32rpx;
  background: #fff;
  border-radius: 28rpx;
  padding: 28rpx 28rpx 12rpx;
  box-shadow: 0 6rpx 20rpx rgba(15, 23, 42, 0.04);
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}
.section-title-wrap {
  display: flex;
  align-items: center;
}
.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #0F172A;
}
.section-badge {
  margin-left: 16rpx;
  padding: 2rpx 14rpx;
  font-size: 22rpx;
  color: #5B5BF2;
  background: #EEF0FF;
  border-radius: 999rpx;
}
.section-action {
  font-size: 26rpx;
  color: #5B5BF2;
  padding: 4rpx 8rpx;
}

.state {
  padding: 60rpx 0;
  text-align: center;
  color: #94A3B8;
  font-size: 26rpx;
}
.empty {
  padding: 60rpx 0 80rpx;
  text-align: center;
}
.empty-emoji {
  font-size: 80rpx;
}
.empty-title {
  margin-top: 20rpx;
  font-size: 28rpx;
  color: #475569;
}
.empty-tip {
  margin-top: 16rpx;
  display: inline-block;
  font-size: 24rpx;
  color: #5B5BF2;
  padding: 12rpx 28rpx;
  background: #EEF0FF;
  border-radius: 999rpx;
}

/* ===== List ===== */
.list {
  margin: 8rpx -12rpx 0;
}
.item {
  display: flex;
  align-items: center;
  padding: 20rpx 12rpx;
  border-radius: 16rpx;
  &:active {
    background: #F8F9FC;
  }
}
.item-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
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
  align-items: center;
  font-size: 28rpx;
  color: #0F172A;
}
.pet {
  font-weight: 500;
}
.cat {
  margin-left: 14rpx;
  font-size: 22rpx;
  color: #64748B;
}
.item-note {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #94A3B8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.amount {
  flex-shrink: 0;
  margin-left: 16rpx;
  font-size: 30rpx;
  font-weight: 600;
  color: #0F172A;
}
</style>
