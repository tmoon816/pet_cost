<template>
  <view class="page">
    <view v-if="loading && !customer" class="state">加载中…</view>
    <block v-else-if="customer">
      <!-- Hero：奶油暖白 -->
      <view class="hero">
        <view class="hero-top">
          <view class="hero-avatar" :style="{ background: avatarBg(customer.name) }">
            {{ avatarText }}
          </view>
          <view class="hero-id">
            <view class="name-row">
              <text class="hero-name">{{ customer.name }}</text>
              <text v-if="summary?.customer_type" class="hero-tag" :class="`tag-${summary.customer_type}`">
                {{ typeLabel(summary.customer_type) }}
              </text>
            </view>
            <view class="hero-phone">{{ customer.phone || '未留手机号' }}</view>
          </view>
        </view>

        <view class="hero-stats">
          <view class="hero-stat">
            <view class="hero-stat-num primary">¥{{ formatAmount(summary?.total_amount) }}</view>
            <view class="hero-stat-label">累计消费</view>
          </view>
          <view class="hero-stat-divider"></view>
          <view class="hero-stat">
            <view class="hero-stat-num">{{ summary?.cost_count || 0 }}</view>
            <view class="hero-stat-label">总订单数</view>
          </view>
          <view class="hero-stat-divider"></view>
          <view class="hero-stat">
            <view class="hero-stat-num">{{ lastVisitText }}</view>
            <view class="hero-stat-label">上次到店</view>
          </view>
        </view>
      </view>

      <!-- 备注 -->
      <view v-if="customer.note" class="section">
        <view class="section-title">备注</view>
        <view class="note">{{ customer.note }}</view>
      </view>

      <!-- 名下宠物 -->
      <view class="section">
        <view class="section-title">
          名下宠物
          <text class="section-count">{{ customer.pets?.length || 0 }}</text>
        </view>
        <view v-if="!customer.pets?.length" class="empty">暂无宠物档案</view>
        <view v-else class="pet-list">
          <view v-for="p in customer.pets" :key="p.id" class="pet-card">
            <view class="pet-icon">{{ petEmoji(p.species) }}</view>
            <view class="pet-info">
              <view class="pet-name">{{ p.name }}</view>
              <view class="pet-meta">
                <text v-if="p.species">{{ p.species }}</text>
                <text v-if="p.breed" class="dot">·</text>
                <text v-if="p.breed">{{ p.breed }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 消费记录 -->
      <view class="section">
        <view class="section-title">
          消费记录
          <text v-if="costTotal" class="section-count">{{ costTotal }}</text>
        </view>
        <view v-if="!costs.length && !loadingCosts" class="empty">暂无消费记录</view>
        <view v-else class="cost-list">
          <view v-for="c in costs" :key="c.id" class="cost-item">
            <view
              class="cost-icon"
              :style="{ background: catTheme(c.category_code).bg, color: catTheme(c.category_code).fg }"
            >
              {{ catTheme(c.category_code).emoji }}
            </view>
            <view class="cost-main">
              <view class="cost-title">
                <text class="cost-pet">{{ c.pet_name || '—' }}</text>
                <text class="cost-cat">· {{ categoryLabel(c.category_code) }}</text>
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
          <view v-else-if="costs.length" class="load-end">— 已显示全部 —</view>
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
  return String(v).slice(5, 10)
})

const AVATAR_BG = ['#FFA62B', '#1C7ED6', '#5DA716', '#7048E8', '#E03131', '#D9480F']
function avatarBg(name) {
  if (!name) return AVATAR_BG[0]
  let h = 0
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return AVATAR_BG[h % AVATAR_BG.length]
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

function petEmoji(species) {
  const s = (species || '').toLowerCase()
  if (s.includes('猫') || s.includes('cat')) return '🐱'
  if (s.includes('狗') || s.includes('dog') || s.includes('犬')) return '🐶'
  if (s.includes('兔')) return '🐰'
  if (s.includes('鸟') || s.includes('鹦')) return '🦜'
  if (s.includes('鱼')) return '🐠'
  if (s.includes('龟')) return '🐢'
  return '🐾'
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
  color: #ADB5BD;
  font-size: 26rpx;
}

/* ===== Hero —— 奶油暖白 ===== */
.hero {
  background: #FFFAF2;
  border: 1rpx solid #FFE4BD;
  border-radius: 24rpx;
  padding: 32rpx;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04);
}
.hero-top {
  display: flex;
  align-items: center;
}
.hero-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  color: #FFFFFF;
  font-size: 40rpx;
  font-weight: 600;
  text-align: center;
  line-height: 96rpx;
  margin-right: 24rpx;
  flex-shrink: 0;
}
.hero-id {
  flex: 1;
  min-width: 0;
}
.name-row {
  display: flex;
  align-items: center;
}
.hero-name {
  font-size: 36rpx;
  font-weight: 600;
  color: #212529;
  letter-spacing: 1rpx;
}
.hero-tag {
  margin-left: 12rpx;
  padding: 2rpx 14rpx;
  font-size: 20rpx;
  border-radius: 8rpx;
  font-weight: 500;
}
.tag-first_visit {
  color: #1C7ED6;
  background: #E7F3FB;
}
.tag-returning {
  color: #5DA716;
  background: #F4F9E6;
}
.tag-vip {
  color: #FFFFFF;
  background: #FFA62B;
}
.hero-phone {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #6C757D;
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
.hero-stat-num {
  font-size: 28rpx;
  font-weight: 700;
  color: #212529;
  &.primary {
    color: #FFA62B;
  }
}
.hero-stat-label {
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
  padding: 28rpx;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04), 0 1rpx 2rpx rgba(33, 37, 41, 0.03);
}
.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #212529;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
}
.section-count {
  margin-left: 12rpx;
  padding: 2rpx 14rpx;
  font-size: 22rpx;
  color: #FFA62B;
  background: #FFF4E5;
  border-radius: 999rpx;
  font-weight: 500;
}
.note {
  font-size: 26rpx;
  color: #6C757D;
  line-height: 1.7;
}
.empty {
  padding: 40rpx 0;
  text-align: center;
  font-size: 24rpx;
  color: #ADB5BD;
}

/* ===== 宠物 ===== */
.pet-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12rpx;
}
.pet-card {
  display: flex;
  align-items: center;
  background: #F8F9FA;
  border: 1rpx solid #E9ECEF;
  border-radius: 16rpx;
  padding: 18rpx 20rpx;
  min-width: 0;
}
.pet-icon {
  font-size: 36rpx;
  margin-right: 14rpx;
  flex-shrink: 0;
}
.pet-info {
  min-width: 0;
}
.pet-name {
  font-size: 26rpx;
  font-weight: 600;
  color: #212529;
}
.pet-meta {
  margin-top: 4rpx;
  font-size: 20rpx;
  color: #ADB5BD;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dot {
  margin: 0 6rpx;
}

/* ===== 消费记录 ===== */
.cost-list {
  margin: -8rpx -8rpx 0;
}
.cost-item {
  display: flex;
  align-items: center;
  padding: 20rpx 8rpx;
  border-radius: 12rpx;
  &:active {
    background: #F8F9FA;
  }
}
.cost-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 14rpx;
  font-size: 28rpx;
  text-align: center;
  line-height: 64rpx;
  margin-right: 18rpx;
  flex-shrink: 0;
}
.cost-main {
  flex: 1;
  min-width: 0;
}
.cost-title {
  display: flex;
  align-items: baseline;
}
.cost-pet {
  font-size: 28rpx;
  font-weight: 500;
  color: #212529;
}
.cost-cat {
  margin-left: 8rpx;
  font-size: 22rpx;
  color: #6C757D;
}
.cost-meta {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #ADB5BD;
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
  font-size: 28rpx;
  font-weight: 700;
  color: #212529;
}
.load-more,
.load-end {
  padding: 28rpx 0;
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
