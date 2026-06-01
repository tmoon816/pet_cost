<template>
  <view class="page">
    <!-- 进度条：填充式，更直观 -->
    <view class="progress">
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: progressPercent + '%' }"></view>
      </view>
      <view class="progress-meta">
        <text class="progress-label">{{ currentStepLabel }}</text>
        <text class="progress-count">{{ completedCount }}/4</text>
      </view>
    </view>

    <!-- 1. 会员 -->
    <view class="section">
      <view class="section-head">
        <text class="section-title">
          <text class="step-num">1</text>
          会员
          <text v-if="selectedCustomer" class="section-check">✓</text>
        </text>
      </view>

      <!-- 已选会员卡片 -->
      <view v-if="selectedCustomer" class="selected-card" @click="resetCustomer">
        <view class="sel-avatar" :style="{ background: avatarBg(selectedCustomer.name) }">
          {{ (selectedCustomer.name || '?').slice(0, 1) }}
        </view>
        <view class="sel-info">
          <view class="sel-name">{{ selectedCustomer.name }}</view>
          <view class="sel-phone">{{ selectedCustomer.phone || '未留手机号' }}</view>
        </view>
        <text class="sel-switch">切换 ›</text>
      </view>

      <!-- 搜索 + 最近会员 -->
      <block v-else>
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
            @click="selectCustomer(c)"
          >
            <view class="cust-avatar" :style="{ background: avatarBg(c.name) }">
              {{ (c.name || '?').slice(0, 1) }}
            </view>
            <view class="cust-info">
              <view class="cust-name">{{ c.name }}</view>
              <view class="cust-phone">{{ c.phone || '—' }}</view>
            </view>
          </view>
          <view v-if="!customers.length && !loadingCustomers" class="empty-tip">
            {{ keyword ? '没找到匹配的会员' : '暂无最近会员，搜手机号试试' }}
          </view>
        </scroll-view>
      </block>
    </view>

    <!-- 2. 宠物 -->
    <view v-if="selectedCustomer" class="section">
      <view class="section-head">
        <text class="section-title">
          <text class="step-num">2</text>
          宠物
          <text v-if="form.pet_id" class="section-check">✓</text>
        </text>
      </view>
      <view class="pet-grid">
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

    <!-- 3. 项目 -->
    <view v-if="selectedCustomer && pets.length" class="section">
      <view class="section-head">
        <text class="section-title">
          <text class="step-num">3</text>
          项目
          <text v-if="form.category_code" class="section-check">✓</text>
        </text>
      </view>
      <view class="cat-grid">
        <view
          v-for="c in categories"
          :key="c.code"
          class="cat-chip"
          :class="{ active: form.category_code === c.code }"
          @click="form.category_code = c.code"
        >
          <view
            class="cat-icon"
            :style="form.category_code === c.code
              ? { background: catTheme(c.code).fg, color: '#fff' }
              : { background: catTheme(c.code).bg, color: catTheme(c.code).fg }"
          >
            {{ catTheme(c.code).emoji }}
          </view>
          <text class="cat-label">{{ c.label }}</text>
        </view>
      </view>
    </view>

    <!-- 4. 金额 / 日期 / 备注 -->
    <view v-if="selectedCustomer && pets.length" class="section">
      <view class="section-head">
        <text class="section-title">
          <text class="step-num">4</text>
          金额
          <text v-if="form.amount && Number(form.amount) > 0" class="section-check">✓</text>
        </text>
      </view>

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

      <!-- 快捷金额 -->
      <view class="quick-amounts">
        <view
          v-for="q in quickAmounts"
          :key="q"
          class="quick-chip"
          :class="{ active: Number(form.amount) === q }"
          @click="form.amount = String(q)"
        >
          ¥{{ q }}
        </view>
      </view>

      <!-- 日期 -->
      <view class="date-row">
        <text class="date-label">日期</text>
        <view class="date-options">
          <view
            class="date-opt"
            :class="{ active: form.occurred_on === todayValue }"
            @click="form.occurred_on = todayValue"
          >
            今天
          </view>
          <view
            class="date-opt"
            :class="{ active: form.occurred_on === yesterdayValue }"
            @click="form.occurred_on = yesterdayValue"
          >
            昨天
          </view>
          <picker mode="date" :value="form.occurred_on" @change="onDateChange">
            <view
              class="date-opt"
              :class="{ active: form.occurred_on !== todayValue && form.occurred_on !== yesterdayValue }"
            >
              {{ form.occurred_on !== todayValue && form.occurred_on !== yesterdayValue
                  ? form.occurred_on.slice(5)
                  : '其他' }}
            </view>
          </picker>
        </view>
      </view>

      <!-- 备注 -->
      <view class="note-wrap">
        <textarea
          class="note-input"
          v-model="form.note"
          placeholder="备注（选填）"
          placeholder-class="ph"
          maxlength="200"
        />
      </view>
    </view>

    <!-- 提交栏：带实时预览 -->
    <view v-if="selectedCustomer && pets.length" class="submit-wrap">
      <view class="submit-preview">
        <view v-if="canSubmit" class="preview-line">
          <text class="preview-pet">{{ selectedPetName }}</text>
          <text class="preview-cat">· {{ selectedCategoryLabel }}</text>
        </view>
        <view v-else class="preview-tip">
          {{ nextHint }}
        </view>
        <view v-if="canSubmit" class="preview-amount">¥{{ form.amount }}</view>
      </view>
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
const quickAmounts = [50, 80, 100, 150, 200, 300]

const form = reactive({
  pet_id: null,
  category_code: '',
  amount: '',
  occurred_on: todayStr(),
  note: '',
})

const todayValue = computed(() => todayStr())
const yesterdayValue = computed(() => {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

const completedCount = computed(() => {
  let n = 0
  if (selectedCustomer.value) n++
  if (form.pet_id) n++
  if (form.category_code) n++
  if (form.amount && Number(form.amount) > 0) n++
  return n
})

const progressPercent = computed(() => (completedCount.value / 4) * 100)

const currentStepLabel = computed(() => {
  if (!selectedCustomer.value) return '第 1 步：选择会员'
  if (!form.pet_id) return '第 2 步：选择宠物'
  if (!form.category_code) return '第 3 步：选择项目'
  if (!form.amount || Number(form.amount) <= 0) return '第 4 步：填写金额'
  return '可以提交了'
})

const nextHint = computed(() => {
  if (!form.pet_id) return '请选择宠物'
  if (!form.category_code) return '请选择项目'
  if (!form.amount || Number(form.amount) <= 0) return '请填写金额'
  return ''
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

const selectedPetName = computed(() => {
  return pets.value.find((p) => p.id === form.pet_id)?.name || ''
})

const selectedCategoryLabel = computed(() => {
  return categoryStore.byCode(form.category_code)?.label || ''
})

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

const AVATAR_BG = ['#FFA62B', '#1C7ED6', '#5DA716', '#7048E8', '#E03131', '#D9480F']
function avatarBg(name) {
  if (!name) return AVATAR_BG[0]
  let h = 0
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return AVATAR_BG[h % AVATAR_BG.length]
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
  if (auth.isLogin && !keyword.value && !selectedCustomer.value) loadRecent()
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

function resetCustomer() {
  selectedCustomer.value = null
  form.pet_id = null
  pets.value = []
  loadRecent()
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
  padding: 24rpx 24rpx 240rpx;
}

/* ===== 进度条 ===== */
.progress {
  background: #FFFFFF;
  border: 1rpx solid #E9ECEF;
  border-radius: 20rpx;
  padding: 20rpx 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04);
}
.progress-track {
  height: 8rpx;
  background: #F1F3F5;
  border-radius: 999rpx;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #FFA62B 0%, #FFBD5C 100%);
  border-radius: 999rpx;
  transition: width 0.3s ease;
}
.progress-meta {
  margin-top: 14rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.progress-label {
  font-size: 24rpx;
  color: #6C757D;
  font-weight: 500;
}
.progress-count {
  font-size: 22rpx;
  color: #FFA62B;
  font-weight: 600;
}

/* ===== Section ===== */
.section {
  background: #FFFFFF;
  border: 1rpx solid #E9ECEF;
  border-radius: 24rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04), 0 1rpx 2rpx rgba(33, 37, 41, 0.03);
}
.section-head {
  margin-bottom: 18rpx;
}
.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #212529;
  display: flex;
  align-items: center;
}
.step-num {
  display: inline-block;
  width: 36rpx;
  height: 36rpx;
  line-height: 36rpx;
  text-align: center;
  background: #FFF4E5;
  color: #FFA62B;
  border-radius: 50%;
  font-size: 22rpx;
  font-weight: 700;
  margin-right: 12rpx;
}
.section-check {
  margin-left: 12rpx;
  color: #5DA716;
  font-size: 26rpx;
  font-weight: 700;
}

/* ===== 已选会员卡片 ===== */
.selected-card {
  display: flex;
  align-items: center;
  background: #FFFAF2;
  border: 1rpx solid #FFE4BD;
  border-radius: 18rpx;
  padding: 22rpx 24rpx;
  &:active {
    background: #FFF4E5;
  }
}
.sel-avatar {
  width: 76rpx;
  height: 76rpx;
  border-radius: 18rpx;
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 600;
  text-align: center;
  line-height: 76rpx;
  margin-right: 20rpx;
  flex-shrink: 0;
}
.sel-info {
  flex: 1;
  min-width: 0;
}
.sel-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #212529;
}
.sel-phone {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #6C757D;
}
.sel-switch {
  flex-shrink: 0;
  font-size: 24rpx;
  color: #FFA62B;
  font-weight: 500;
}

/* ===== 搜索 ===== */
.search-bar {
  display: flex;
  align-items: center;
  background: #F8F9FA;
  border: 1rpx solid #E9ECEF;
  border-radius: 14rpx;
  height: 76rpx;
  padding: 0 24rpx;
}
.search-icon {
  font-size: 26rpx;
  margin-right: 12rpx;
  opacity: 0.5;
}
.search-input {
  flex: 1;
  height: 76rpx;
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
.cust-label {
  margin: 24rpx 0 12rpx;
  font-size: 22rpx;
  color: #ADB5BD;
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
  padding: 14rpx 18rpx;
  margin-right: 12rpx;
  background: #F8F9FA;
  border: 1rpx solid #E9ECEF;
  border-radius: 16rpx;
  &:active {
    background: #FFF4E5;
    border-color: #FFA62B;
  }
}
.cust-avatar {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  color: #FFFFFF;
  font-size: 24rpx;
  font-weight: 600;
  text-align: center;
  line-height: 56rpx;
  margin-right: 14rpx;
  flex-shrink: 0;
}
.cust-info {
  min-width: 0;
}
.cust-name {
  font-size: 26rpx;
  font-weight: 500;
  color: #212529;
}
.cust-phone {
  margin-top: 4rpx;
  font-size: 22rpx;
  color: #ADB5BD;
}
.empty-tip {
  width: 100%;
  text-align: center;
  color: #ADB5BD;
  font-size: 24rpx;
  padding: 32rpx 0;
}

/* ===== 宠物 ===== */
.pet-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}
.pet-chip {
  display: flex;
  align-items: center;
  padding: 16rpx 22rpx;
  background: #F8F9FA;
  border: 2rpx solid transparent;
  border-radius: 14rpx;
  transition: all 0.15s;
  &.active {
    background: #FFF4E5;
    border-color: #FFA62B;
  }
}
.pet-emoji {
  font-size: 36rpx;
  margin-right: 12rpx;
}
.pet-info {
  display: flex;
  flex-direction: column;
}
.pet-name {
  font-size: 26rpx;
  font-weight: 500;
  color: #212529;
}
.pet-sub {
  margin-top: 2rpx;
  font-size: 20rpx;
  color: #ADB5BD;
}

/* ===== 项目 ===== */
.cat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12rpx;
}
.cat-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 18rpx 8rpx;
  background: #FFFFFF;
  border: 2rpx solid #F1F3F5;
  border-radius: 14rpx;
  transition: all 0.15s;
  &.active {
    background: #FFF4E5;
    border-color: #FFA62B;
  }
}
.cat-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  font-size: 30rpx;
  text-align: center;
  line-height: 64rpx;
  transition: all 0.15s;
}
.cat-label {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #6C757D;
}
.cat-chip.active .cat-label {
  color: #212529;
  font-weight: 600;
}

/* ===== 金额 ===== */
.amount-input-wrap {
  display: flex;
  align-items: baseline;
  padding: 8rpx 0 16rpx;
  border-bottom: 2rpx solid #F1F3F5;
}
.amount-prefix {
  font-size: 36rpx;
  color: #FFA62B;
  font-weight: 500;
  margin-right: 8rpx;
}
.amount-input {
  flex: 1;
  font-size: 60rpx;
  font-weight: 700;
  color: #212529;
  letter-spacing: -1rpx;
  height: 80rpx;
}
.amount-ph {
  color: #DEE2E6;
}
.quick-amounts {
  margin-top: 20rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}
.quick-chip {
  padding: 12rpx 24rpx;
  background: #F8F9FA;
  border: 1rpx solid #E9ECEF;
  border-radius: 999rpx;
  font-size: 24rpx;
  color: #6C757D;
  font-weight: 500;
  transition: all 0.15s;
  &.active {
    background: #FFA62B;
    border-color: #FFA62B;
    color: #FFFFFF;
  }
  &:active {
    background: #FFF4E5;
  }
}

/* ===== 日期 ===== */
.date-row {
  display: flex;
  align-items: center;
  margin-top: 28rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid #F1F3F5;
}
.date-label {
  width: 80rpx;
  flex-shrink: 0;
  font-size: 26rpx;
  color: #6C757D;
}
.date-options {
  flex: 1;
  display: flex;
  gap: 12rpx;
}
.date-opt {
  flex: 1;
  height: 64rpx;
  line-height: 64rpx;
  text-align: center;
  background: #F8F9FA;
  border: 1rpx solid #E9ECEF;
  border-radius: 12rpx;
  font-size: 24rpx;
  color: #6C757D;
  &.active {
    background: #FFF4E5;
    border-color: #FFA62B;
    color: #FFA62B;
    font-weight: 600;
  }
}

/* ===== 备注 ===== */
.note-wrap {
  margin-top: 20rpx;
}
.note-input {
  width: 100%;
  min-height: 100rpx;
  background: #F8F9FA;
  border: 1rpx solid #E9ECEF;
  border-radius: 12rpx;
  padding: 18rpx 22rpx;
  font-size: 26rpx;
  box-sizing: border-box;
}

/* ===== 提交栏（带预览） ===== */
.submit-wrap {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 16rpx 24rpx calc(20rpx + env(safe-area-inset-bottom));
  background: rgba(248, 249, 250, 0.96);
  border-top: 1rpx solid #E9ECEF;
}
.submit-preview {
  display: flex;
  align-items: center;
  padding: 8rpx 4rpx 14rpx;
}
.preview-line {
  flex: 1;
  min-width: 0;
  font-size: 24rpx;
  color: #6C757D;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-pet {
  font-weight: 600;
  color: #212529;
}
.preview-cat {
  margin-left: 6rpx;
}
.preview-tip {
  flex: 1;
  font-size: 24rpx;
  color: #ADB5BD;
}
.preview-amount {
  flex-shrink: 0;
  margin-left: 16rpx;
  font-size: 32rpx;
  font-weight: 700;
  color: #FFA62B;
}
.btn-primary {
  height: 92rpx;
  line-height: 92rpx;
  background: #FFA62B;
  color: #FFFFFF;
  border-radius: 16rpx;
  font-size: 32rpx;
  font-weight: 500;
  letter-spacing: 4rpx;
  border: none;
  &::after {
    border: none;
  }
  &:active {
    background: #F5940F;
  }
  &[disabled] {
    background: #E9ECEF;
    color: #ADB5BD;
  }
}
</style>
