<template>
  <view class="page">
    <view v-if="loading && !customer" class="state">加载中…</view>
    <block v-else-if="customer">
      <view class="header">
        <view class="avatar">{{ avatarText }}</view>
        <view class="info">
          <view class="name-row">
            <text class="name">{{ customer.name }}</text>
            <text v-if="summary?.customer_type" class="tag" :class="`tag-${summary.customer_type}`">
              {{ typeLabel(summary.customer_type) }}
            </text>
          </view>
          <view class="phone">{{ customer.phone || '未留手机号' }}</view>
        </view>
      </view>

      <view class="summary">
        <view class="sum-cell">
          <view class="sum-value">¥{{ formatAmount(summary?.total_amount) }}</view>
          <view class="sum-label">累计消费</view>
        </view>
        <view class="sum-cell">
          <view class="sum-value">{{ summary?.cost_count || 0 }}</view>
          <view class="sum-label">总订单数</view>
        </view>
        <view class="sum-cell">
          <view class="sum-value">{{ lastVisitText }}</view>
          <view class="sum-label">上次到店</view>
        </view>
      </view>

      <view v-if="customer.note" class="section">
        <view class="section-title">备注</view>
        <view class="note">{{ customer.note }}</view>
      </view>

      <view class="section">
        <view class="section-title">名下宠物（{{ customer.pets?.length || 0 }}）</view>
        <view v-if="!customer.pets?.length" class="empty">暂无宠物档案</view>
        <view v-else class="pet-list">
          <view v-for="p in customer.pets" :key="p.id" class="pet-item">
            <view class="pet-name">{{ p.name }}</view>
            <view class="pet-meta">
              <text v-if="p.species">{{ p.species }}</text>
              <text v-if="p.breed" class="dot">·</text>
              <text v-if="p.breed">{{ p.breed }}</text>
              <text v-if="p.gender" class="dot">·</text>
              <text v-if="p.gender">{{ p.gender }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="section">
        <view class="section-title">消费记录</view>
        <view v-if="!costs.length && !loadingCosts" class="empty">暂无消费记录</view>
        <view v-else class="cost-list">
          <view v-for="c in costs" :key="c.id" class="cost-item">
            <view class="cost-main">
              <view class="cost-title">
                <text class="cost-pet">{{ c.pet_name || '—' }}</text>
                <text class="cost-cat">{{ categoryLabel(c.category_code) }}</text>
              </view>
              <view class="cost-meta">
                <text>{{ c.occurred_on }}</text>
                <text v-if="c.note" class="dot">·</text>
                <text v-if="c.note" class="cost-note">{{ c.note }}</text>
              </view>
            </view>
            <view class="cost-amount">¥{{ formatAmount(c.amount) }}</view>
          </view>
          <view v-if="hasMoreCosts" class="load-more" @click="loadMoreCosts">
            {{ loadingCosts ? '加载中…' : '加载更多' }}
          </view>
          <view v-else-if="costs.length" class="load-end">已显示全部</view>
        </view>
      </view>
    </block>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onLoad, onReachBottom } from '@dcloudio/uni-app'
import { useCategoryStore } from '@/stores/category'
import { getCustomer, getCustomerSummary } from '@/api/customers'
import { listCosts } from '@/api/costs'

const categoryStore = useCategoryStore()

const customerId = ref(null)
const customer = ref(null)
const summary = ref(null)
const costs = ref([])
const costPage = ref(1)
const costTotal = ref(0)
const costPageSize = 20
const loading = ref(false)
const loadingCosts = ref(false)

const avatarText = computed(() => (customer.value?.name || '?').slice(0, 1))
const hasMoreCosts = computed(() => costs.value.length < costTotal.value)

const lastVisitText = computed(() => {
  const v = summary.value?.last_visit_at
  if (!v) return '—'
  return String(v).slice(0, 10)
})

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

function categoryLabel(code) {
  return categoryStore.byCode(code)?.label || code
}

async function loadHeader() {
  loading.value = true
  try {
    const [c, s] = await Promise.all([
      getCustomer(customerId.value),
      getCustomerSummary(customerId.value),
      categoryStore.fetch(),
    ])
    customer.value = c
    summary.value = s
    uni.setNavigationBarTitle({ title: c.name })
  } finally {
    loading.value = false
  }
}

async function loadCosts(reset = false) {
  if (loadingCosts.value) return
  loadingCosts.value = true
  if (reset) {
    costPage.value = 1
    costs.value = []
    costTotal.value = 0
  }
  try {
    const data = await listCosts({
      customer_id: customerId.value,
      page: costPage.value,
      page_size: costPageSize,
    })
    const newItems = data.items || []
    costs.value = costPage.value === 1 ? newItems : costs.value.concat(newItems)
    costTotal.value = data.total || 0
  } finally {
    loadingCosts.value = false
  }
}

function loadMoreCosts() {
  if (!hasMoreCosts.value || loadingCosts.value) return
  costPage.value += 1
  loadCosts(false)
}

onLoad((options) => {
  customerId.value = Number(options.id)
  if (!customerId.value) {
    uni.showToast({ title: '会员 ID 缺失', icon: 'none' })
    return
  }
})

onMounted(async () => {
  if (!customerId.value) return
  await loadHeader()
  loadCosts(true)
})

onReachBottom(() => {
  loadMoreCosts()
})
</script>

<style lang="scss">
.page {
  padding: 24rpx 24rpx 60rpx;
}
.state {
  padding: 120rpx 0;
  text-align: center;
  color: #b0b4bd;
  font-size: 26rpx;
}
.header {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
}
.avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: #5b7fff;
  color: #fff;
  font-size: 44rpx;
  font-weight: 600;
  text-align: center;
  line-height: 100rpx;
  margin-right: 24rpx;
  flex-shrink: 0;
}
.info {
  flex: 1;
  min-width: 0;
}
.name-row {
  display: flex;
  align-items: center;
}
.name {
  font-size: 34rpx;
  font-weight: 600;
  color: #1f2329;
}
.tag {
  margin-left: 12rpx;
  padding: 4rpx 14rpx;
  font-size: 22rpx;
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
.phone {
  margin-top: 10rpx;
  font-size: 26rpx;
  color: #8a8f99;
}
.summary {
  display: flex;
  margin-top: 20rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 28rpx 0;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
}
.sum-cell {
  flex: 1;
  text-align: center;
  border-right: 1rpx solid #f0f1f5;
  &:last-child {
    border-right: none;
  }
}
.sum-value {
  font-size: 32rpx;
  font-weight: 600;
  color: #1f2329;
}
.sum-label {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #8a8f99;
}
.section {
  margin-top: 20rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
}
.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #1f2329;
  margin-bottom: 16rpx;
}
.note {
  font-size: 26rpx;
  color: #4a5160;
  line-height: 1.6;
}
.empty {
  padding: 40rpx 0;
  text-align: center;
  font-size: 24rpx;
  color: #b0b4bd;
}
.pet-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.pet-item {
  flex: 1 1 45%;
  background: #f5f6fa;
  border-radius: 12rpx;
  padding: 20rpx;
  min-width: 0;
}
.pet-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #1f2329;
}
.pet-meta {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #8a8f99;
}
.dot {
  margin: 0 8rpx;
}
.cost-list {
  margin-top: -8rpx;
}
.cost-item {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #f0f1f5;
  &:last-child {
    border-bottom: none;
  }
}
.cost-main {
  flex: 1;
  min-width: 0;
}
.cost-title {
  display: flex;
  align-items: center;
}
.cost-pet {
  font-size: 28rpx;
  font-weight: 500;
  color: #1f2329;
}
.cost-cat {
  margin-left: 14rpx;
  font-size: 22rpx;
  color: #5b7fff;
  background: #eef2ff;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
}
.cost-meta {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #8a8f99;
  display: flex;
  align-items: center;
  overflow: hidden;
}
.cost-note {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}
.cost-amount {
  flex-shrink: 0;
  margin-left: 16rpx;
  font-size: 30rpx;
  font-weight: 600;
  color: #1f2329;
}
.load-more,
.load-end {
  padding: 28rpx 0;
  text-align: center;
  font-size: 24rpx;
}
.load-more {
  color: #5b7fff;
}
.load-end {
  color: #b0b4bd;
}
</style>
