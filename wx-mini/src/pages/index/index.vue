<template>
  <view class="page">
    <view class="header">
      <view class="title">今日营收</view>
      <view class="date">{{ today }}</view>
    </view>

    <view class="cards">
      <view class="card">
        <view class="card-label">今日单数</view>
        <view class="card-value">{{ recordCount }}</view>
      </view>
      <view class="card primary">
        <view class="card-label">今日流水</view>
        <view class="card-value">¥{{ totalAmount }}</view>
      </view>
      <view class="card">
        <view class="card-label">客单价</view>
        <view class="card-value">¥{{ avgAmount }}</view>
      </view>
    </view>

    <view class="section">
      <view class="section-head">
        <text class="section-title">今日订单</text>
        <text v-if="costs.length" class="section-count">{{ costs.length }} 单</text>
      </view>

      <view v-if="loading && !costs.length" class="state">加载中…</view>
      <view v-else-if="!costs.length" class="state">今天还没有开单</view>

      <view v-else class="list">
        <view v-for="c in costs" :key="c.id" class="item">
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
const summary = ref({ total_amount: 0, record_count: 0 })
const costs = ref([])
const loading = ref(false)

const recordCount = computed(() => summary.value.record_count || 0)
const totalAmount = computed(() => formatAmount(summary.value.total_amount))
const avgAmount = computed(() => {
  const n = Number(summary.value.record_count || 0)
  if (!n) return '—'
  return formatAmount(Number(summary.value.total_amount || 0) / n)
})

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatAmount(v) {
  const n = Number(v || 0)
  if (Number.isNaN(n)) return '0.00'
  return n.toFixed(2)
}

function categoryLabel(code) {
  return categoryStore.byCode(code)?.label || code
}

async function loadAll() {
  if (loading.value) return
  loading.value = true
  today.value = todayStr()
  try {
    const [s, list] = await Promise.all([
      getSummary({ start: today.value, end: today.value }),
      listCosts({ start: today.value, end: today.value, page: 1, page_size: 100 }),
      categoryStore.fetch(),
    ])
    summary.value = s
    costs.value = list.items || []
  } catch (e) {
    // request 已弹 toast
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
  padding: 32rpx 24rpx 60rpx;
}
.header {
  margin-bottom: 28rpx;
}
.title {
  font-size: 40rpx;
  font-weight: 600;
  color: #1f2329;
}
.date {
  margin-top: 8rpx;
  color: #8a8f99;
  font-size: 26rpx;
}
.cards {
  display: flex;
  gap: 16rpx;
}
.card {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx 16rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
  &.primary {
    background: linear-gradient(135deg, #5b7fff 0%, #7c98ff 100%);
    .card-label {
      color: rgba(255, 255, 255, 0.85);
    }
    .card-value {
      color: #fff;
    }
  }
}
.card-label {
  font-size: 22rpx;
  color: #8a8f99;
}
.card-value {
  margin-top: 14rpx;
  font-size: 36rpx;
  font-weight: 600;
  color: #1f2329;
}
.section {
  margin-top: 32rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}
.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #1f2329;
}
.section-count {
  font-size: 24rpx;
  color: #8a8f99;
}
.state {
  padding: 60rpx 0;
  text-align: center;
  color: #b0b4bd;
  font-size: 26rpx;
}
.list {
  margin-top: 8rpx;
}
.item {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #f0f1f5;
  &:last-child {
    border-bottom: none;
  }
}
.item-main {
  flex: 1;
  min-width: 0;
}
.item-title {
  display: flex;
  align-items: center;
  font-size: 28rpx;
  color: #1f2329;
}
.pet {
  font-weight: 500;
}
.cat {
  margin-left: 16rpx;
  font-size: 24rpx;
  color: #5b7fff;
  background: #eef2ff;
  padding: 4rpx 14rpx;
  border-radius: 8rpx;
}
.item-note {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #8a8f99;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.amount {
  flex-shrink: 0;
  margin-left: 16rpx;
  font-size: 30rpx;
  font-weight: 600;
  color: #1f2329;
}
</style>
