<template>
  <view class="page">
    <!-- 1. 搜会员 -->
    <view class="section">
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

      <view class="cust-label">{{ keyword ? '搜索结果' : '最近会员' }}</view>

      <scroll-view scroll-x class="cust-scroll" enable-flex>
        <view
          v-for="c in customers"
          :key="c.id"
          class="cust-chip"
          :class="{ active: selectedCustomer?.id === c.id }"
          @click="selectCustomer(c)"
        >
          <view class="cust-name">{{ c.name }}</view>
          <view class="cust-phone">{{ c.phone || '—' }}</view>
        </view>
        <view v-if="!customers.length && !loadingCustomers" class="empty-tip">
          {{ keyword ? '没找到匹配的会员' : '暂无最近会员' }}
        </view>
      </scroll-view>
    </view>

    <!-- 2. 选宠物 -->
    <view v-if="selectedCustomer" class="section">
      <view class="label">选择宠物</view>
      <view class="chip-grid">
        <view
          v-for="p in pets"
          :key="p.id"
          class="chip"
          :class="{ active: form.pet_id === p.id }"
          @click="form.pet_id = p.id"
        >
          {{ p.name }}<text v-if="p.species" class="chip-sub"> · {{ p.species }}</text>
        </view>
        <view v-if="!pets.length && !loadingPets" class="empty-tip">
          该会员暂无宠物档案
        </view>
      </view>
    </view>

    <!-- 3. 选项目 -->
    <view v-if="selectedCustomer && pets.length" class="section">
      <view class="label">选择项目</view>
      <view class="chip-grid">
        <view
          v-for="c in categories"
          :key="c.code"
          class="chip"
          :class="{ active: form.category_code === c.code }"
          @click="form.category_code = c.code"
        >
          {{ c.label }}
        </view>
      </view>
    </view>

    <!-- 4. 金额/日期/备注 -->
    <view v-if="selectedCustomer && pets.length" class="section">
      <view class="form-row">
        <text class="label">金额</text>
        <input
          class="form-input amount"
          v-model="form.amount"
          type="digit"
          placeholder="0.00"
          placeholder-class="ph"
        />
        <text class="suffix">元</text>
      </view>

      <view class="form-row">
        <text class="label">日期</text>
        <picker mode="date" :value="form.occurred_on" @change="onDateChange">
          <view class="form-input picker">{{ form.occurred_on }}</view>
        </picker>
      </view>

      <view class="form-row col">
        <text class="label">备注</text>
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
      <button class="btn" :loading="submitting" :disabled="!canSubmit" @click="onSubmit">
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
  // 进入页面时重新拉一次最近会员，避免数据过时
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
    // request 已弹 toast
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  // 保留客户和宠物，方便连续给同一只宠物开多单
  form.category_code = ''
  form.amount = ''
  form.note = ''
  form.occurred_on = todayStr()
}
</script>

<style lang="scss">
.page {
  padding: 24rpx 24rpx 160rpx;
}
.section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
}
.label {
  font-size: 26rpx;
  color: #4a5160;
  font-weight: 500;
}
.search-bar {
  position: relative;
  background: #f5f6fa;
  border-radius: 12rpx;
  height: 76rpx;
  display: flex;
  align-items: center;
  padding: 0 24rpx;
}
.search-input {
  flex: 1;
  height: 76rpx;
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
.cust-label {
  margin: 24rpx 0 16rpx;
  font-size: 24rpx;
  color: #8a8f99;
}
.cust-scroll {
  white-space: nowrap;
  display: flex;
}
.cust-chip {
  display: inline-block;
  min-width: 200rpx;
  padding: 16rpx 24rpx;
  margin-right: 16rpx;
  background: #f5f6fa;
  border-radius: 12rpx;
  border: 2rpx solid transparent;
  &.active {
    background: #eef2ff;
    border-color: #5b7fff;
  }
}
.cust-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #1f2329;
}
.cust-phone {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #8a8f99;
}
.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 16rpx;
}
.chip {
  padding: 14rpx 28rpx;
  background: #f5f6fa;
  border-radius: 999rpx;
  font-size: 26rpx;
  color: #4a5160;
  border: 2rpx solid transparent;
  &.active {
    background: #eef2ff;
    color: #5b7fff;
    border-color: #5b7fff;
  }
}
.chip-sub {
  font-size: 22rpx;
  color: #8a8f99;
}
.empty-tip {
  width: 100%;
  text-align: center;
  color: #b0b4bd;
  font-size: 24rpx;
  padding: 24rpx 0;
}
.form-row {
  display: flex;
  align-items: center;
  margin-top: 20rpx;
  &.col {
    flex-direction: column;
    align-items: stretch;
  }
  .label {
    width: 100rpx;
    flex-shrink: 0;
  }
}
.form-input {
  flex: 1;
  height: 72rpx;
  line-height: 72rpx;
  background: #f5f6fa;
  border-radius: 10rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  &.picker {
    color: #1f2329;
  }
}
.amount {
  font-size: 32rpx;
  font-weight: 500;
}
.suffix {
  margin-left: 12rpx;
  color: #8a8f99;
}
.form-textarea {
  margin-top: 12rpx;
  width: 100%;
  min-height: 120rpx;
  background: #f5f6fa;
  border-radius: 10rpx;
  padding: 16rpx 20rpx;
  font-size: 26rpx;
  box-sizing: border-box;
}
.submit-wrap {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 20rpx 24rpx calc(20rpx + env(safe-area-inset-bottom));
  background: #f5f6fa;
}
.btn {
  height: 88rpx;
  line-height: 88rpx;
  background: #5b7fff;
  color: #fff;
  border-radius: 12rpx;
  font-size: 32rpx;
  &[disabled] {
    background: #c4cdee;
    color: #fff;
  }
}
</style>
