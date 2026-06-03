<template>
  <view class="page">
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
        <view v-if="!keyword && idx < 3" class="rank">
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

// 6 套头像底色，跟主色调和谐共处但不抢戏
const AVATAR_BG = [
  '#FFA62B', // 主色
  '#1C7ED6', // 信息蓝
  '#5DA716', // 成功绿
  '#7048E8', // 紫
  '#E03131', // 红
  '#D9480F', // 深橙
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
  if (t === 'supreme') return '至尊VIP'
  if (t === 'svip') return 'SVIP'
  if (t === 'vip') return 'VIP'
  if (t === 'regular') return '回头客'
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
  margin-bottom: 12rpx;
}
.search-bar {
  display: flex;
  align-items: center;
  background: #FFFFFF;
  border: 1rpx solid #E9ECEF;
  border-radius: 16rpx;
  height: 84rpx;
  padding: 0 28rpx;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04);
}
.search-icon {
  font-size: 28rpx;
  margin-right: 14rpx;
  opacity: 0.5;
}
.search-input {
  flex: 1;
  height: 84rpx;
  font-size: 28rpx;
  color: #212529;
}
.search-clear {
  font-size: 36rpx;
  color: #ADB5BD;
  padding: 0 8rpx;
  line-height: 1;
}
.ph {
  color: #ADB5BD;
}
.overview {
  padding: 16rpx 12rpx 12rpx;
  display: flex;
  align-items: baseline;
}
.overview-num {
  font-size: 32rpx;
  font-weight: 700;
  color: #212529;
  margin-right: 12rpx;
}
.overview-label {
  font-size: 22rpx;
  color: #ADB5BD;
}
.state,
.empty {
  padding: 120rpx 0;
  text-align: center;
}
.state {
  color: #ADB5BD;
  font-size: 26rpx;
}
.empty-emoji {
  font-size: 84rpx;
  opacity: 0.5;
}
.empty-title {
  margin-top: 24rpx;
  font-size: 28rpx;
  color: #6C757D;
}
.empty-tip {
  margin-top: 10rpx;
  font-size: 24rpx;
  color: #ADB5BD;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.card {
  position: relative;
  display: flex;
  align-items: center;
  background: #FFFFFF;
  border: 1rpx solid #E9ECEF;
  border-radius: 20rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04);
  &:active {
    background: #F8F9FA;
  }
}
.rank {
  position: absolute;
  top: 14rpx;
  right: 18rpx;
  font-size: 26rpx;
}
.avatar {
  width: 84rpx;
  height: 84rpx;
  border-radius: 20rpx;
  color: #FFFFFF;
  font-size: 34rpx;
  font-weight: 600;
  text-align: center;
  line-height: 84rpx;
  margin-right: 22rpx;
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
  font-weight: 600;
  color: #212529;
}
.tag {
  margin-left: 10rpx;
  padding: 2rpx 12rpx;
  font-size: 20rpx;
  border-radius: 8rpx;
  font-weight: 500;
}
.tag-first_visit {
  color: #1C7ED6;
  background: #E7F3FB;
}
.tag-regular {
  color: #5DA716;
  background: #F4F9E6;
}
.tag-vip {
  color: #FFFFFF;
  background: #FFA62B;
}
.tag-svip {
  color: #FFFFFF;
  background: #FF7043;
}
.tag-supreme {
  color: #FFFFFF;
  background: #E03131;
}
.sub {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #ADB5BD;
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
  font-size: 28rpx;
  font-weight: 700;
  color: #212529;
}
.amt-label {
  display: block;
  margin-top: 4rpx;
  font-size: 20rpx;
  color: #ADB5BD;
}
.load-more,
.load-end {
  padding: 32rpx 0;
  text-align: center;
  font-size: 24rpx;
  letter-spacing: 2rpx;
}
.load-more {
  color: #FFA62B;
  font-weight: 500;
}
.load-end {
  color: #DEE2E6;
}
</style>
