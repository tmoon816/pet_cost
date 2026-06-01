<template>
  <view class="page">
    <!-- 顶部搜索 -->
    <view class="top">
      <view class="search-bar">
        <text class="search-icon">🔍</text>
        <input
          class="search-input"
          v-model="keyword"
          placeholder="搜索姓名 / 手机号"
          placeholder-class="ph"
          confirm-type="search"
          @confirm="onSearch"
          @input="onKeywordChange"
        />
        <text v-if="keyword" class="search-clear" @click="clearKeyword">×</text>
      </view>
    </view>

    <!-- 概览条 -->
    <view v-if="!keyword && total > 0" class="overview">
      <text class="overview-num">{{ total }}</text>
      <text class="overview-label">位会员 · 按累计消费排序</text>
    </view>

    <view v-if="loading && !items.length" class="state">加载中…</view>
    <view v-else-if="!items.length" class="empty">
      <view class="empty-emoji">🐶</view>
      <view class="empty-title">{{ keyword ? '没找到匹配的会员' : '暂无会员' }}</view>
      <view v-if="!keyword" class="empty-tip">去开单页选会员开始记录</view>
    </view>

    <view v-else class="list">
      <view
        v-for="(c, idx) in items"
        :key="c.id"
        class="card"
        @click="goDetail(c)"
      >
        <view class="rank" v-if="!keyword && idx < 3" :class="`rank-${idx + 1}`">
          {{ ['🥇', '🥈', '🥉'][idx] }}
        </view>

        <view class="avatar" :style="{ background: avatarBg(c.name) }">
          {{ (c.name || '?').slice(0, 1) }}
        </view>

        <view class="main">
          <view class="name-row">
            <text class="name">{{ c.name }}</text>
            <text v-if="c.customer_type" class="tag" :class="`tag-${c.customer_type}`">
              {{ typeLabel(c.customer_type) }}
            </text>
          </view>
          <view class="sub">
            <text class="phone">{{ c.phone || '未留手机号' }}</text>
            <text v-if="c.visit_count" class="dot">·</text>
            <text v-if="c.visit_count" class="visits">{{ c.visit_count }} 单</text>
          </view>
        </view>

        <view class="amount">
          <text class="amt-num">¥{{ formatAmount(c.total_amount) }}</text>
          <text class="amt-label">累计</text>
        </view>
      </view>

      <view v-if="hasMore" class="load-more" @click="loadMore">
        {{ loading ? '加载中…' : '加载更多' }}
      </view>
      <view v-else class="load-end">— 已显示全部 —</view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { useAuthStore } from '@/stores/auth'
import { listCustomers } from '@/api/customers'

const auth = useAuthStore()

const keyword = ref('')
const items = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)
let searchTimer = null

const hasMore = computed(() => items.value.length < total.value)

const AVATAR_BG = [
  'linear-gradient(135deg, #5B5BF2 0%, #8B5CF6 100%)',
  'linear-gradient(135deg, #FB923C 0%, #F472B6 100%)',
  'linear-gradient(135deg, #10B981 0%, #34D399 100%)',
  'linear-gradient(135deg, #0EA5E9 0%, #38BDF8 100%)',
  'linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)',
  'linear-gradient(135deg, #EC4899 0%, #F472B6 100%)',
]
function avatarBg(name) {
  if (!name) return AVATAR_BG[0]
  let h = 0
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return AVATAR_BG[h % AVATAR_BG.length]
}

function formatAmount(v) {
  const n = Number(v || 0)
  if (Number.isNaN(n)) return '0.00'
  return n.toFixed(2)
}

function typeLabel(t) {
  if (t === 'vip') return 'VIP'
  if (t === 'returning') return '回头客'
  return '新客'
}

async function load(reset = false) {
  if (loading.value) return
  loading.value = true
  if (reset) {
    page.value = 1
    items.value = []
    total.value = 0
  }
  try {
    const data = await listCustomers({
      q: keyword.value.trim() || undefined,
      sort_by: 'total_amount',
      sort_dir: 'desc',
      page: page.value,
      page_size: pageSize,
    })
    const newItems = data.items || []
    items.value = page.value === 1 ? newItems : items.value.concat(newItems)
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

function onKeywordChange() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => load(true), 300)
}

function onSearch() {
  load(true)
}

function clearKeyword() {
  keyword.value = ''
  load(true)
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  page.value += 1
  load(false)
}

function goDetail(c) {
  uni.navigateTo({ url: `/pages/customer-detail/customer-detail?id=${c.id}` })
}

onMounted(() => {
  if (!auth.isLogin) {
    uni.reLaunch({ url: '/pages/login/login' })
    return
  }
  load(true)
})

onShow(() => {
  if (auth.isLogin && items.value.length) load(true)
})

onPullDownRefresh(async () => {
  await load(true)
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  loadMore()
})
</script>

<style lang="scss">
.page {
  padding: 24rpx 24rpx 60rpx;
}
.top {
  margin-bottom: 16rpx;
}
.search-bar {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 20rpx;
  height: 88rpx;
  padding: 0 28rpx;
  box-shadow: 0 6rpx 20rpx rgba(15, 23, 42, 0.05);
}
.search-icon {
  font-size: 28rpx;
  margin-right: 14rpx;
  opacity: 0.6;
}
.search-input {
  flex: 1;
  height: 88rpx;
  font-size: 28rpx;
  color: #0F172A;
}
.search-clear {
  font-size: 36rpx;
  color: #94A3B8;
  padding: 0 8rpx;
  line-height: 1;
}
.ph {
  color: #94A3B8;
}
.overview {
  padding: 20rpx 12rpx 8rpx;
  display: flex;
  align-items: baseline;
}
.overview-num {
  font-size: 36rpx;
  font-weight: 700;
  color: #0F172A;
  margin-right: 12rpx;
}
.overview-label {
  font-size: 22rpx;
  color: #94A3B8;
}
.state,
.empty {
  padding: 120rpx 0;
  text-align: center;
}
.state {
  color: #94A3B8;
  font-size: 26rpx;
}
.empty-emoji {
  font-size: 96rpx;
}
.empty-title {
  margin-top: 24rpx;
  font-size: 28rpx;
  color: #475569;
}
.empty-tip {
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #94A3B8;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}
.card {
  position: relative;
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
  &:active {
    background: #FAFBFE;
  }
}
.rank {
  position: absolute;
  top: 16rpx;
  right: 20rpx;
  font-size: 28rpx;
}
.avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
  color: #fff;
  font-size: 36rpx;
  font-weight: 600;
  text-align: center;
  line-height: 88rpx;
  margin-right: 24rpx;
  flex-shrink: 0;
  box-shadow: 0 6rpx 16rpx rgba(91, 91, 242, 0.18);
}
.main {
  flex: 1;
  min-width: 0;
}
.name-row {
  display: flex;
  align-items: center;
}
.name {
  font-size: 30rpx;
  font-weight: 600;
  color: #0F172A;
}
.tag {
  margin-left: 12rpx;
  padding: 2rpx 14rpx;
  font-size: 20rpx;
  border-radius: 8rpx;
  font-weight: 500;
}
.tag-first_visit {
  color: #5B5BF2;
  background: #EEF0FF;
}
.tag-returning {
  color: #10B981;
  background: #D1FAE5;
}
.tag-vip {
  color: #B45309;
  background: #FEF3C7;
}
.sub {
  margin-top: 10rpx;
  font-size: 24rpx;
  color: #94A3B8;
  display: flex;
  align-items: center;
}
.dot {
  margin: 0 8rpx;
}
.amount {
  flex-shrink: 0;
  text-align: right;
  margin-left: 16rpx;
}
.amt-num {
  font-size: 30rpx;
  font-weight: 700;
  color: #5B5BF2;
}
.amt-label {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: #94A3B8;
}
.load-more,
.load-end {
  padding: 32rpx 0;
  text-align: center;
  font-size: 24rpx;
  letter-spacing: 2rpx;
}
.load-more {
  color: #5B5BF2;
}
.load-end {
  color: #CBD5E1;
}
</style>
