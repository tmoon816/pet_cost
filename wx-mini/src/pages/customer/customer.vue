<template>
  <view class="page">
    <view class="search-bar">
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

    <view v-if="loading && !items.length" class="state">加载中…</view>
    <view v-else-if="!items.length" class="state">
      {{ keyword ? '没找到匹配的会员' : '暂无会员，去开单页选会员开始记录' }}
    </view>

    <view v-else class="list">
      <view
        v-for="c in items"
        :key="c.id"
        class="item"
        @click="goDetail(c)"
      >
        <view class="avatar">{{ avatarText(c.name) }}</view>
        <view class="main">
          <view class="name-row">
            <text class="name">{{ c.name }}</text>
            <text v-if="c.customer_type" class="tag" :class="`tag-${c.customer_type}`">
              {{ typeLabel(c.customer_type) }}
            </text>
          </view>
          <view class="sub">
            <text>{{ c.phone || '未留手机号' }}</text>
            <text v-if="c.visit_count" class="dot">·</text>
            <text v-if="c.visit_count">{{ c.visit_count }} 单</text>
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
      <view v-else class="load-end">已显示全部</view>
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

function avatarText(name) {
  return (name || '?').slice(0, 1)
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
  uni.navigateTo({
    url: `/pages/customer-detail/customer-detail?id=${c.id}`,
  })
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
.search-bar {
  position: relative;
  background: #fff;
  border-radius: 12rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  padding: 0 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
  margin-bottom: 20rpx;
}
.search-input {
  flex: 1;
  height: 80rpx;
  font-size: 28rpx;
}
.search-clear {
  font-size: 36rpx;
  color: #b0b4bd;
  padding: 0 8rpx;
  line-height: 1;
}
.ph {
  color: #b0b4bd;
}
.state {
  padding: 120rpx 0;
  text-align: center;
  color: #b0b4bd;
  font-size: 26rpx;
}
.list {
  background: #fff;
  border-radius: 16rpx;
  padding: 0 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
}
.item {
  display: flex;
  align-items: center;
  padding: 28rpx 0;
  border-bottom: 1rpx solid #f0f1f5;
  &:last-child {
    border-bottom: none;
  }
}
.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: #eef2ff;
  color: #5b7fff;
  font-size: 32rpx;
  font-weight: 600;
  text-align: center;
  line-height: 80rpx;
  margin-right: 20rpx;
  flex-shrink: 0;
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
  font-weight: 500;
  color: #1f2329;
}
.tag {
  margin-left: 12rpx;
  padding: 2rpx 12rpx;
  font-size: 20rpx;
  border-radius: 6rpx;
}
.tag-first_visit {
  color: #5b7fff;
  background: #eef2ff;
}
.tag-returning {
  color: #1ba784;
  background: #e6f6f1;
}
.tag-vip {
  color: #c47e1f;
  background: #fff4e0;
}
.sub {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #8a8f99;
  display: flex;
  align-items: center;
}
.dot {
  margin: 0 8rpx;
}
.amount {
  flex-shrink: 0;
  text-align: right;
}
.amt-num {
  font-size: 28rpx;
  font-weight: 600;
  color: #1f2329;
}
.amt-label {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: #b0b4bd;
}
.load-more,
.load-end {
  padding: 32rpx 0;
  text-align: center;
  font-size: 24rpx;
  color: #b0b4bd;
}
.load-more {
  color: #5b7fff;
}
</style>
