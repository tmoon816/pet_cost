<template>
  <view class="page">
    <!-- 步骤指示 -->
    <view class="steps">
      <view class="step" :class="{ active: !!selectedCustomer, done: !!selectedCustomer }">
        <view class="step-dot">1</view>
        <view class="step-label">会员</view>
      </view>
      <view class="step-line" :class="{ active: !!selectedCustomer }"></view>
      <view class="step" :class="{ active: !!form.pet_id, done: !!form.pet_id }">
        <view class="step-dot">2</view>
        <view class="step-label">宠物</view>
      </view>
      <view class="step-line" :class="{ active: !!form.pet_id }"></view>
      <view class="step" :class="{ active: !!form.category_code }">
        <view class="step-dot">3</view>
        <view class="step-label">项目</view>
      </view>
      <view class="step-line" :class="{ active: !!form.category_code }"></view>
      <view class="step" :class="{ active: canSubmit }">
        <view class="step-dot">4</view>
        <view class="step-label">金额</view>
      </view>
    </view>

    <!-- 1. 搜会员 -->
    <view class="section">
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

      <view class="cust-label">{{ keyword ? '搜索结果' : '最近会员' }}</view>

      <scroll-view scroll-x class="cust-scroll" enable-flex>
        <view
          v-for="c in customers"
          :key="c.id"
          class="cust-chip"
          :class="{ active: selectedCustomer?.id === c.id }"
          @click="selectCustomer(c)"
        >
          <view class="cust-avatar">{{ (c.name || '?').slice(0, 1) }}</view>
          <view class="cust-info">
            <view class="cust-name">{{ c.name }}</view>
            <view class="cust-phone">{{ c.phone || '—' }}</view>
          </view>
        </view>
        <view v-if="!customers.length && !loadingCustomers" class="empty-tip">
          {{ keyword ? '没找到匹配的会员' : '暂无最近会员' }}
        </view>
      </scroll-view>
    </view>

    <!-- 2. 选宠物 -->
    <view v-if="selectedCustomer" class="section">
      <view class="section-title">选择宠物</view>
      <view class="chip-grid">
        <view
          v-for="p in pets"
          :key="p.id"
          class="pet-chip"
          :class="{ active: form.pet_id === p.id }"
          @click="form.pet_id = p.id"
        >
          <text class="pet-emoji">{{ petEmoji(p.species) }}</text>
          <view class="pet-info">
            <view class="pet-name">{{ p.name }}</view>
            <view v-if="p.species" class="pet-sub">{{ p.species }}</view>
          </view>
        </view>
        <view v-if="!pets.length && !loadingPets" class="empty-tip">
          该会员暂无宠物档案
        </view>
      </view>
    </view>

    <!-- 3. 选项目 -->
    <view v-if="selectedCustomer && pets.length" class="section">
      <view class="section-title">选择项目</view>
      <view class="cat-grid">
        <view
          v-for="c in categories"
          :key="c.code"
          class="cat-chip"
          :class="{ active: form.category_code === c.code }"
          :style="form.category_code === c.code ? { background: catTheme(c.code).bg, color: catTheme(c.code).fg, 'border-color': catTheme(c.code).fg } : {}"
          @click="form.category_code = c.code"
        >
          <text class="cat-emoji">{{ catTheme(c.code).emoji }}</text>
          <text class="cat-label">{{ c.label }}</text>
        </view>
      </view>
    </view>

    <!-- 4. 金额/日期/备注 -->
    <view v-if="selectedCustomer && pets.length" class="section">
      <view class="amount-row">
        <text class="amount-label">金额</text>
        <view class="amount-input-wrap">
          <text class="amount-prefix">¥</text>
          <input
            class="amount-input"
            v-model="form.amount"
            type="digit"
            placeholder="0.00"
            placeholder-class="amount-ph"
          />
        </view>
      </view>

      <view class="form-row">
        <text class="form-label">日期</text>
        <picker mode="date" :value="form.occurred_on" @change="onDateChange">
          <view class="form-input picker">
            {{ form.occurred_on }}
            <text class="form-arrow">›</text>
          </view>
        </picker>
      </view>

      <view class="form-row col">
        <text class="form-label">备注</text>
        <textarea
          class="form-textarea"
          v-model="form.note"
          placeholder="选填"
          placeholder-class="ph"
          maxlength="200"
        />
      </view>
    </view>

    <!-- 5. 提交 -->
    <view v-if="selectedCustomer && pets.length" class="submit-wrap">
      <button class="btn-primary" :loading="submitting" :disabled="!canSubmit" @click="onSubmit">
        提交开单
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/category'
import { listCustomers, listRecentCustomers } from '@/api/customers'
import { listPets } from '@/api/pets'
import { createCost } from '@/api/costs'

const auth = useAuthStore()
const categoryStore = useCategoryStore()

const keyword = ref('')
const customers = ref([])
const loadingCustomers = ref(false)
const selectedCustomer = ref(null)
const pets = ref([])
const loadingPets = ref(false)
const submitting = ref(false)
let searchTimer = null

const categories = computed(() => categoryStore.list)

const form = reactive({
  pet_id: null,
  category_code: '',
  amount: '',
  occurred_on: todayStr(),
  note: '',
})

const canSubmit = computed(() => {
  return (
    !!form.pet_id &&
    !!form.category_code &&
    !!form.amount &&
    Number(form.amount) > 0 &&
    !!form.occurred_on
  )
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

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(() => {
  if (!auth.isLogin) {
    uni.reLaunch({ url: '/pages/login/login' })
    return
  }
  categoryStore.fetch()
  loadRecent()
})

onShow(() => {
  if (auth.isLogin && !keyword.value) loadRecent()
})

async function loadRecent() {
  loadingCustomers.value = true
  try {
    customers.value = await listRecentCustomers(8)
  } catch (e) {
    customers.value = []
  } finally {
    loadingCustomers.value = false
  }
}

function onKeywordChange() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(onSearch, 300)
}

async function onSearch() {
  if (!keyword.value.trim()) {
    loadRecent()
    return
  }
  loadingCustomers.value = true
  try {
    const data = await listCustomers({
      q: keyword.value.trim(),
      page: 1,
      page_size: 20,
    })
    customers.value = data.items || []
  } catch (e) {
    customers.value = []
  } finally {
    loadingCustomers.value = false
  }
}

function clearKeyword() {
  keyword.value = ''
  loadRecent()
}

async function selectCustomer(c) {
  selectedCustomer.value = c
  form.pet_id = null
  pets.value = []
  loadingPets.value = true
  try {
    const data = await listPets({ customer_id: c.id, page: 1, page_size: 50 })
    pets.value = data.items || []
    if (pets.value.length === 1) {
      form.pet_id = pets.value[0].id
    }
  } finally {
    loadingPets.value = false
  }
}

function onDateChange(e) {
  form.occurred_on = e.detail.value
}

async function onSubmit() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    await createCost({
      pet_id: form.pet_id,
      category_code: form.category_code,
      amount: form.amount,
      occurred_on: form.occurred_on,
      note: form.note || null,
    })
    uni.showToast({ title: '开单成功', icon: 'success' })
    resetForm()
  } catch (e) {
    /* request 已弹 toast */
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  form.category_code = ''
  form.amount = ''
  form.note = ''
  form.occurred_on = todayStr()
}
</script>

<style lang="scss">
.page {
  padding: 24rpx 24rpx 200rpx;
}

/* ===== 步骤指示 ===== */
.steps {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 28rpx;
  padding: 24rpx 28rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 6rpx 20rpx rgba(15, 23, 42, 0.04);
}
.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}
.step-dot {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: #F1F3F9;
  color: #94A3B8;
  font-size: 24rpx;
  font-weight: 600;
  text-align: center;
  line-height: 48rpx;
  transition: all 0.2s;
}
.step.active .step-dot,
.step.done .step-dot {
  background: linear-gradient(135deg, #5B5BF2 0%, #8B5CF6 100%);
  color: #fff;
  box-shadow: 0 4rpx 12rpx rgba(91, 91, 242, 0.4);
}
.step-label {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #94A3B8;
}
.step.active .step-label,
.step.done .step-label {
  color: #5B5BF2;
  font-weight: 500;
}
.step-line {
  flex: 1;
  height: 4rpx;
  background: #F1F3F9;
  margin: 0 16rpx;
  margin-bottom: 32rpx;
  border-radius: 4rpx;
}
.step-line.active {
  background: linear-gradient(90deg, #5B5BF2 0%, #8B5CF6 100%);
}

/* ===== Section ===== */
.section {
  background: #fff;
  border-radius: 28rpx;
  padding: 28rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 6rpx 20rpx rgba(15, 23, 42, 0.04);
}
.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 20rpx;
}

/* ===== 搜索 ===== */
.search-bar {
  display: flex;
  align-items: center;
  background: #F1F3F9;
  border-radius: 16rpx;
  height: 80rpx;
  padding: 0 24rpx;
}
.search-icon {
  font-size: 26rpx;
  margin-right: 12rpx;
  opacity: 0.6;
}
.search-input {
  flex: 1;
  height: 80rpx;
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
.cust-label {
  margin: 24rpx 0 16rpx;
  font-size: 22rpx;
  color: #94A3B8;
  letter-spacing: 1rpx;
}
.cust-scroll {
  white-space: nowrap;
  display: flex;
}
.cust-chip {
  display: inline-flex;
  align-items: center;
  min-width: 240rpx;
  padding: 16rpx 20rpx;
  margin-right: 16rpx;
  background: #F8F9FC;
  border-radius: 20rpx;
  border: 2rpx solid transparent;
  transition: all 0.15s;
  &.active {
    background: linear-gradient(135deg, #EEF0FF 0%, #F3E8FF 100%);
    border-color: #5B5BF2;
    box-shadow: 0 4rpx 12rpx rgba(91, 91, 242, 0.18);
  }
}
.cust-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #fff;
  color: #5B5BF2;
  font-size: 28rpx;
  font-weight: 600;
  text-align: center;
  line-height: 64rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
}
.cust-chip.active .cust-avatar {
  background: linear-gradient(135deg, #5B5BF2 0%, #8B5CF6 100%);
  color: #fff;
}
.cust-info {
  min-width: 0;
}
.cust-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #0F172A;
}
.cust-phone {
  margin-top: 4rpx;
  font-size: 22rpx;
  color: #94A3B8;
}
.empty-tip {
  width: 100%;
  text-align: center;
  color: #94A3B8;
  font-size: 24rpx;
  padding: 32rpx 0;
}

/* ===== 宠物芯片 ===== */
.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.pet-chip {
  display: flex;
  align-items: center;
  padding: 16rpx 24rpx;
  background: #F8F9FC;
  border-radius: 18rpx;
  border: 2rpx solid transparent;
  transition: all 0.15s;
  &.active {
    background: linear-gradient(135deg, #EEF0FF 0%, #F3E8FF 100%);
    border-color: #5B5BF2;
  }
}
.pet-emoji {
  font-size: 36rpx;
  margin-right: 14rpx;
}
.pet-info {
  display: flex;
  flex-direction: column;
}
.pet-name {
  font-size: 26rpx;
  font-weight: 500;
  color: #0F172A;
}
.pet-sub {
  margin-top: 2rpx;
  font-size: 20rpx;
  color: #94A3B8;
}

/* ===== 项目网格 ===== */
.cat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
}
.cat-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx 8rpx;
  background: #F8F9FC;
  border-radius: 18rpx;
  border: 2rpx solid transparent;
  transition: all 0.15s;
}
.cat-emoji {
  font-size: 40rpx;
}
.cat-label {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #475569;
}
.cat-chip.active .cat-label {
  font-weight: 600;
}

/* ===== 金额输入 ===== */
.amount-row {
  display: flex;
  flex-direction: column;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #F1F3F9;
}
.amount-label {
  font-size: 24rpx;
  color: #94A3B8;
  letter-spacing: 1rpx;
}
.amount-input-wrap {
  display: flex;
  align-items: baseline;
  margin-top: 12rpx;
}
.amount-prefix {
  font-size: 36rpx;
  color: #5B5BF2;
  font-weight: 500;
  margin-right: 8rpx;
}
.amount-input {
  flex: 1;
  font-size: 60rpx;
  font-weight: 700;
  color: #0F172A;
  letter-spacing: -1rpx;
  height: 80rpx;
}
.amount-ph {
  color: #CBD5E1;
}

/* ===== 通用表单 ===== */
.form-row {
  display: flex;
  align-items: center;
  margin-top: 24rpx;
  &.col {
    flex-direction: column;
    align-items: stretch;
  }
}
.form-label {
  width: 100rpx;
  flex-shrink: 0;
  font-size: 26rpx;
  color: #475569;
}
.form-input {
  flex: 1;
  height: 80rpx;
  line-height: 80rpx;
  background: #F1F3F9;
  border-radius: 14rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: #0F172A;
  &.picker {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
.form-arrow {
  color: #CBD5E1;
  font-size: 32rpx;
}
.form-textarea {
  margin-top: 14rpx;
  width: 100%;
  min-height: 140rpx;
  background: #F1F3F9;
  border-radius: 14rpx;
  padding: 20rpx 24rpx;
  font-size: 26rpx;
  box-sizing: border-box;
}

/* ===== 提交按钮 ===== */
.submit-wrap {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 20rpx 24rpx calc(20rpx + env(safe-area-inset-bottom));
  background: rgba(246, 247, 251, 0.92);
  backdrop-filter: blur(20rpx);
}
.btn-primary {
  height: 96rpx;
  line-height: 96rpx;
  background: linear-gradient(135deg, #5B5BF2 0%, #8B5CF6 100%);
  color: #fff;
  border-radius: 20rpx;
  font-size: 32rpx;
  font-weight: 500;
  letter-spacing: 2rpx;
  box-shadow: 0 12rpx 28rpx rgba(91, 91, 242, 0.4);
  border: none;
  &::after {
    border: none;
  }
  &[disabled] {
    background: #CBD5E1;
    color: #fff;
    box-shadow: none;
  }
}
</style>
