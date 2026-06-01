<template>
  <view class="page">
    <view v-if="loading && !customer" class="state">加载中…</view>
    <block v-else-if="customer">
      <!-- 渐变 hero 卡 -->
      <view class="hero">
        <view class="hero-blob"></view>

        <view class="hero-top">
          <view class="hero-avatar">{{ avatarText }}</view>
          <view class="hero-id">
            <view class="hero-name">{{ customer.name }}</view>
            <view class="hero-phone">{{ customer.phone || '未留手机号' }}</view>
          </view>
          <text v-if="summary?.customer_type" class="hero-tag" :class="`tag-${summary.customer_type}`">
            {{ typeLabel(summary.customer_type) }}
          </text>
        </view>

        <view class="hero-stats">
          <view class="hero-stat">
            <view class="hero-stat-num">¥{{ formatAmount(summary?.total_amount) }}</view>
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
                <text v-if="p.gender" class="dot">·</text>
                <text v-if="p.gender">{{ p.gender }}</text>
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
            <view class="cost-icon" :style="{ background: catTheme(c.category_code).bg, color: catTheme(c.category_code).fg }">
              {{ catTheme(c.category_code).emoji }}
            </view>
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
  color: #94A3B8;
  font-size: 26rpx;
}

/* ===== Hero ===== */
.hero {
  position: relative;
  background: linear-gradient(135deg, #5B5BF2 0%, #8B5CF6 100%);
  border-radius: 32rpx;
  padding: 36rpx;
  color: #fff;
  overflow: hidden;
  box-shadow: 0 14rpx 40rpx rgba(91, 91, 242, 0.3);
}
.hero-blob {
  position: absolute;
  width: 320rpx;
  height: 320rpx;
  background: #C084FC;
  border-radius: 50%;
  filter: blur(40rpx);
  opacity: 0.45;
  top: -100rpx;
  right: -100rpx;
  pointer-events: none;
}
.hero-top {
  position: relative;
  display: flex;
  align-items: center;
}
.hero-avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(20rpx);
  font-size: 44rpx;
  font-weight: 600;
  text-align: center;
  line-height: 100rpx;
  margin-right: 24rpx;
  flex-shrink: 0;
}
.hero-id {
  flex: 1;
  min-width: 0;
}
.hero-name {
  font-size: 36rpx;
  font-weight: 600;
  letter-spacing: 1rpx;
}
.hero-phone {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.78);
}
.hero-tag {
  flex-shrink: 0;
  padding: 6rpx 18rpx;
  font-size: 22rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
  font-weight: 500;
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
  height: 56rpx;
  background: rgba(255, 255, 255, 0.18);
}
.hero-stat-num {
  font-size: 30rpx;
  font-weight: 700;
}
.hero-stat-label {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.78);
}

/* ===== Section ===== */
.section {
  margin-top: 24rpx;
  background: #fff;
  border-radius: 28rpx;
  padding: 28rpx;
  box-shadow: 0 6rpx 20rpx rgba(15, 23, 42, 0.04);
}
.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
}
.section-count {
  margin-left: 14rpx;
  padding: 2rpx 14rpx;
  font-size: 22rpx;
  color: #5B5BF2;
  background: #EEF0FF;
  border-radius: 999rpx;
  font-weight: 500;
}
.note {
  font-size: 26rpx;
  color: #475569;
  line-height: 1.7;
}
.empty {
  padding: 40rpx 0;
  text-align: center;
  font-size: 24rpx;
  color: #94A3B8;
}

/* ===== 宠物 ===== */
.pet-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
}
.pet-card {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #F8F9FC 0%, #EEF0FF 100%);
  border-radius: 20rpx;
  padding: 20rpx;
  min-width: 0;
}
.pet-icon {
  font-size: 40rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
}
.pet-info {
  min-width: 0;
}
.pet-name {
  font-size: 26rpx;
  font-weight: 600;
  color: #0F172A;
}
.pet-meta {
  margin-top: 6rpx;
  font-size: 20rpx;
  color: #94A3B8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dot {
  margin: 0 6rpx;
}

/* ===== 消费记录 ===== */
.cost-list {
  margin: -8rpx -12rpx 0;
}
.cost-item {
  display: flex;
  align-items: center;
  padding: 20rpx 12rpx;
  border-radius: 16rpx;
  &:active {
    background: #FAFBFE;
  }
}
.cost-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  font-size: 32rpx;
  text-align: center;
  line-height: 72rpx;
  margin-right: 20rpx;
  flex-shrink: 0;
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
  color: #0F172A;
}
.cost-cat {
  margin-left: 14rpx;
  font-size: 22rpx;
  color: #64748B;
}
.cost-meta {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #94A3B8;
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
  font-weight: 700;
  color: #5B5BF2;
}
.load-more,
.load-end {
  padding: 28rpx 0;
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
