<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCustomerStore } from '@/stores/customerStore'
import { useCategoryStore } from '@/stores/categoryStore'
import * as petsApi from '@/api/pets'
import * as customersApi from '@/api/customers'
import { listCosts } from '@/api/costs'
import { listBoarding } from '@/api/boarding'
import CostFormDialog from '@/views/costs/CostFormDialog.vue'
import RechargeDialog from '@/views/customers/RechargeDialog.vue'
import PetForm from '@/components/PetForm.vue'

const props = defineProps({ id: { type: [String, Number], required: true } })
const router = useRouter()
const customerStore = useCustomerStore()
const categoryStore = useCategoryStore()

const detail = ref(null)
const summary = ref(null)
const loading = ref(false)
const editingInfo = ref(false)
const submitting = ref(false)
const customerForm = reactive({ name: '', phone: '', note: '' })
const customerFormRef = ref(null)
const customerRules = {
  name: [
    { required: true, message: '请输入客户姓名', trigger: 'blur' },
    { max: 50, message: '姓名不超过 50 字符', trigger: 'blur' },
  ],
  phone: [
    {
      validator: (_rule, value, callback) => {
        const v = (value || '').trim()
        if (!v) return callback()
        if (!/^1\d{10}$/.test(v)) {
          return callback(new Error('请输入 11 位手机号（以 1 开头）'))
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

// T-011: 消费时间线（分页加载）
const TIMELINE_PAGE_SIZE = 20
const timelineItems = ref([])
const timelineTotal = ref(0)
const timelinePage = ref(1)
const timelineLoading = ref(false)
const timelineLoaded = ref(false)
const timelineHasMore = computed(
  () => timelineItems.value.length < timelineTotal.value
)

const petDialog = ref(false)
const editingPetId = ref(null)
// P-004: 客户详情页直达新增消费
const costDialogVisible = ref(false)
// 储值充值
const rechargeVisible = ref(false)
// 寄养（在住）
const activeBoarding = ref([])
// 储值流水
const txns = ref([])
const txnTotal = ref(0)
const txnPage = ref(1)
const TXN_PAGE_SIZE = 10
const txnLoading = ref(false)
const txnHasMore = computed(() => txns.value.length < txnTotal.value)

// 余额为负 = 欠费
const isArrears = computed(() => {
  const b = Number(detail.value?.balance)
  return Number.isFinite(b) && b < 0
})

async function loadActiveBoarding() {
  try {
    const res = await listBoarding({ status: 'active', customer_id: Number(props.id) })
    activeBoarding.value = res || []
  } catch (e) {
    activeBoarding.value = []
  }
}

const speciesOptions = [
  { value: 'dog', label: '犬' },
  { value: 'cat', label: '猫' },
  { value: 'other', label: '其他' },
]
const genderOptions = [
  { value: 'male', label: '公' },
  { value: 'female', label: '母' },
  { value: 'unknown', label: '未知' },
]

async function load() {
  loading.value = true
  try {
    detail.value = await customerStore.fetchDetail(props.id)
    Object.assign(customerForm, {
      name: detail.value.name,
      phone: detail.value.phone || '',
      note: detail.value.note || '',
    })
    // T-007: 拉取客户聚合指标（失败不阻断详情页加载）
    try {
      summary.value = await customersApi.getCustomerSummary(props.id)
    } catch (err) {
      summary.value = null
    }
    // T-011: 确保分类字典已加载（用于显示分类 label），并刷新时间线第 1 页
    try {
      await categoryStore.fetch()
    } catch (err) {
      // 字典拉取失败不阻断详情页，时间线会回退显示 code
    }
    timelinePage.value = 1
    timelineItems.value = []
    timelineTotal.value = 0
    timelineLoaded.value = false
    await loadTimeline()
    // 储值流水第一页
    txnPage.value = 1
    await loadTransactions()
    // 在住寄养
    await loadActiveBoarding()
  } finally {
    loading.value = false
  }
}

async function loadTransactions() {
  if (txnLoading.value) return
  txnLoading.value = true
  try {
    const res = await customersApi.listTransactions(props.id, {
      page: txnPage.value,
      page_size: TXN_PAGE_SIZE,
    })
    const list = res?.items || []
    txns.value = txnPage.value === 1 ? list : txns.value.concat(list)
    txnTotal.value = Number(res?.total || 0)
  } catch {
    if (txnPage.value === 1) {
      txns.value = []
      txnTotal.value = 0
    }
  } finally {
    txnLoading.value = false
  }
}

async function loadMoreTxns() {
  if (!txnHasMore.value || txnLoading.value) return
  txnPage.value += 1
  await loadTransactions()
}

async function onRecharged() {
  detail.value = await customerStore.fetchDetail(props.id)
  txnPage.value = 1
  await loadTransactions()
}

async function loadTimeline() {
  if (timelineLoading.value) return
  timelineLoading.value = true
  try {
    const res = await listCosts({
      customer_id: Number(props.id),
      page: timelinePage.value,
      page_size: TIMELINE_PAGE_SIZE,
    })
    const list = res?.items || []
    if (timelinePage.value === 1) {
      timelineItems.value = list
    } else {
      timelineItems.value = timelineItems.value.concat(list)
    }
    timelineTotal.value = Number(res?.total || 0)
    timelineLoaded.value = true
  } catch (err) {
    if (timelinePage.value === 1) {
      timelineItems.value = []
      timelineTotal.value = 0
    }
  } finally {
    timelineLoading.value = false
  }
}

async function loadMoreTimeline() {
  if (!timelineHasMore.value || timelineLoading.value) return
  timelinePage.value += 1
  await loadTimeline()
}

onMounted(load)

async function saveCustomer() {
  if (!customerFormRef.value) return
  const valid = await customerFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  const payload = {
    name: customerForm.name.trim(),
    phone: customerForm.phone.trim() || null,
    note: customerForm.note || null,
  }
  try {
    await customerStore.update(props.id, payload)
    ElMessage.success('已更新')
    editingInfo.value = false
    await load()
  } catch (err) {
    if (err?.status === 409 && err.detail?.detail === 'phone_exists') {
      ElMessage.error(`手机号已绑定客户 #${err.detail.existing_id}`)
    }
  } finally {
    submitting.value = false
  }
}

function cancelEdit() {
  editingInfo.value = false
  Object.assign(customerForm, {
    name: detail.value.name,
    phone: detail.value.phone || '',
    note: detail.value.note || '',
  })
}

function openCreatePet() {
  editingPetId.value = null
  petDialog.value = true
}

function openEditPet(pet) {
  editingPetId.value = pet.id
  petDialog.value = true
}

async function onPetSaved() {
  petDialog.value = false
  await load()
}

async function deletePet(pet) {
  try {
    await ElMessageBox.confirm(
      `确定删除宠物「${pet.name}」？相关花费记录会一并删除。`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    return
  }
  await petsApi.deletePet(pet.id)
  ElMessage.success('已删除')
  await load()
}

function viewPet(pet) {
  router.push(`/pets/${pet.id}`)
}

function speciesLabel(v) {
  return speciesOptions.find((s) => s.value === v)?.label || '-'
}
function genderLabel(v) {
  return genderOptions.find((g) => g.value === v)?.label || '-'
}

// T-007: 卡片显示助手
const totalAmountDisplay = computed(() => {
  const n = summary.value?.total_amount
  if (n === undefined || n === null) return '—'
  const num = Number(n)
  if (!Number.isFinite(num)) return '—'
  return `¥${num.toFixed(2)}`
})

const lastVisitDisplay = computed(() => {
  const ts = summary.value?.last_visit_at
  if (!ts) return '—'
  return String(ts).slice(0, 10)
})

const costCountDisplay = computed(() => {
  const c = summary.value?.cost_count
  if (c === undefined || c === null) return '—'
  return String(c)
})

// 客户分层徽章（按贡献金额）
const customerTypeBadge = computed(() => {
  const t = summary.value?.customer_type
  if (t === 'supreme') return { label: '至尊VIP', type: 'danger' }
  if (t === 'svip') return { label: 'SVIP', type: 'warning' }
  if (t === 'vip') return { label: 'VIP', type: 'success' }
  if (t === 'regular') return { label: '回头客', type: 'primary' }
  if (t === 'first_visit') return { label: '新客', type: 'info' }
  return null
})

// 会员等级说明：等级名 + 折扣
const tierName = computed(() => customerTypeBadge.value?.label || '—')
const tierDiscountText = computed(() => {
  const d = Number(summary.value?.discount)
  if (!Number.isFinite(d) || d >= 100) return '暂无折扣'
  // 98 → 9.8折，90 → 9折
  const zhe = d % 10 === 0 ? String(d / 10) : (d / 10).toFixed(1)
  return `储值消费享 ${zhe} 折`
})

// T-011: 时间线展示助手
function categoryLabel(code) {
  if (!code) return '-'
  return categoryStore.list?.find?.((c) => c.code === code)?.label || code
}

function amountDisplay(v) {
  const num = Number(v)
  if (!Number.isFinite(num)) return '—'
  return `¥${num.toFixed(2)}`
}

async function onCostSaved() {
  // 刷新时间线和客户指标
  timelinePage.value = 1
  timelineItems.value = []
  timelineTotal.value = 0
  timelineLoaded.value = false
  await loadTimeline()
  try {
    summary.value = await customersApi.getCustomerSummary(props.id)
  } catch {
    summary.value = null
  }
  // 储值订单会扣余额，刷新余额和流水
  try {
    detail.value = await customerStore.fetchDetail(props.id)
  } catch {
    /* ignore */
  }
  txnPage.value = 1
  await loadTransactions()
}

// 储值展示助手
const balanceDisplay = computed(() => {
  const b = detail.value?.balance
  const n = Number(b)
  return Number.isFinite(n) ? `¥${n.toFixed(2)}` : '¥0.00'
})

const TXN_TYPE_LABEL = {
  recharge: { text: '充值', type: 'success' },
  consume: { text: '消费', type: 'danger' },
  refund: { text: '退款', type: 'warning' },
  adjust: { text: '调整', type: 'info' },
}
const CHANNEL_LABEL = { wechat: '微信', alipay: '支付宝', cash: '现金' }

function txnTypeBadge(t) {
  return TXN_TYPE_LABEL[t] || { text: t, type: 'info' }
}
function txnAmountDisplay(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return '—'
  const sign = n > 0 ? '+' : ''
  return `${sign}${n.toFixed(2)}`
}
function channelLabel(row) {
  if (row.channel) return CHANNEL_LABEL[row.channel] || row.channel
  // 消费/退款没有充值渠道，资金来源是储值余额
  if (row.type === 'consume' || row.type === 'refund') return '储值'
  return '-'
}
</script>

<template>
  <div v-loading="loading" class="customer-detail">
    <div class="back-bar">
      <el-button :icon="'ArrowLeft'" link @click="router.push('/customers')">返回客户列表</el-button>
    </div>

    <div v-if="detail" class="summary-row">
      <el-card class="summary-card" shadow="never">
        <div class="summary-label">
          会员等级
          <el-tag
            v-if="customerTypeBadge"
            :type="customerTypeBadge.type"
            size="small"
            effect="dark"
            style="margin-left: 6px;"
          >
            {{ customerTypeBadge.label }}
          </el-tag>
        </div>
        <div class="summary-value">{{ tierName }}</div>
        <div class="summary-sub">{{ tierDiscountText }}</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-label">累计消费</div>
        <div class="summary-value">{{ totalAmountDisplay }}</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-label">上次到店</div>
        <div class="summary-value">{{ lastVisitDisplay }}</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-label">总订单数</div>
        <div class="summary-value">{{ costCountDisplay }}</div>
      </el-card>
      <el-card class="summary-card balance-card" shadow="never">
        <div class="summary-label">
          储值余额
          <el-button
            size="small"
            class="recharge-btn"
            :icon="'Wallet'"
            style="margin-left: 8px;"
            @click="rechargeVisible = true"
          >充值</el-button>
        </div>
        <div class="summary-value balance-amount" :class="{ 'balance-negative': isArrears }">
          {{ balanceDisplay }}
        </div>
        <div class="summary-sub arrears-hint" v-if="isArrears">⚠️ 已欠费，建议尽快收款</div>
      </el-card>
    </div>

    <!-- 寄养中提示条 -->
    <el-card
      v-if="activeBoarding.length > 0"
      class="boarding-banner"
      shadow="never"
    >
      <div class="bd-banner-head">
        <span class="bd-banner-title">🛏️ 寄养中（{{ activeBoarding.length }}）</span>
        <el-button size="small" text type="primary" @click="router.push('/boarding')">前往寄养管理 →</el-button>
      </div>
      <div class="bd-banner-list">
        <div v-for="b in activeBoarding" :key="b.id" class="bd-banner-item" :class="{ overdue: b.is_overdue }">
          <span class="bd-banner-pet">{{ b.pet_name }}</span>
          <span class="bd-banner-meta">
            已住 <strong :class="{ 'text-over': b.is_overdue }">{{ b.days_stayed }}</strong> / {{ b.expected_days }} 天
            · 每日 ¥{{ Number(b.daily_rate).toFixed(2) }}
            · 累计已扣 ¥{{ Number(b.total_charged).toFixed(2) }}
          </span>
          <el-tag v-if="b.is_overdue" type="danger" size="small" effect="dark">超期 {{ b.overdue_days }} 天</el-tag>
        </div>
      </div>
    </el-card>

    <el-card v-if="detail" class="card">
      <template #header>
        <div class="card-header">
          <span class="title">客户信息</span>
          <div v-if="!editingInfo">
            <el-button size="small" type="primary" @click="editingInfo = true">编辑</el-button>
          </div>
          <div v-else>
            <el-button size="small" @click="cancelEdit">取消</el-button>
            <el-button size="small" type="primary" :loading="submitting" @click="saveCustomer">保存</el-button>
          </div>
        </div>
      </template>

      <el-descriptions v-if="!editingInfo" :column="2" border>
        <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ detail.name }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ detail.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ detail.note || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detail.created_at?.replace('T', ' ').slice(0, 19) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ detail.updated_at?.replace('T', ' ').slice(0, 19) }}</el-descriptions-item>
      </el-descriptions>

      <el-form v-else ref="customerFormRef" :model="customerForm" :rules="customerRules" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="customerForm.name" maxlength="50" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="customerForm.phone" maxlength="11" placeholder="选填，11 位手机号" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="customerForm.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="detail" class="card">
      <template #header>
        <div class="card-header">
          <span class="title">名下宠物（{{ detail.pets?.length || 0 }}）</span>
          <el-button size="small" type="primary" :icon="'Plus'" @click="openCreatePet">新增宠物</el-button>
        </div>
      </template>

      <el-table :data="detail.pets || []" stripe empty-text="还没有宠物，点右上角新增" @row-click="viewPet">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名字" min-width="120" />
        <el-table-column label="种类" width="100">
          <template #default="{ row }">{{ speciesLabel(row.species) }}</template>
        </el-table-column>
        <el-table-column prop="breed" label="品种" min-width="120">
          <template #default="{ row }">{{ row.breed || '-' }}</template>
        </el-table-column>
        <el-table-column label="性别" width="80">
          <template #default="{ row }">{{ genderLabel(row.gender) }}</template>
        </el-table-column>
        <el-table-column prop="birthday" label="生日" width="120">
          <template #default="{ row }">{{ row.birthday || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center">
          <template #default="{ row }">
            <el-button size="small" @click.stop="viewPet(row)">详情</el-button>
            <el-button size="small" type="primary" @click.stop="openEditPet(row)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="deletePet(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="detail" class="card">
      <template #header>
        <div class="card-header">
          <span class="title">消费时间线<span class="title-count">（共 {{ timelineTotal }} 条）</span></span>
          <el-button size="small" type="primary" :icon="'Plus'" @click="costDialogVisible = true">
            新增服务
          </el-button>
        </div>
      </template>

      <div v-if="timelineLoaded && timelineItems.length === 0" class="timeline-empty">
        该客户还没有消费记录
      </div>

      <el-timeline v-else class="timeline">
        <el-timeline-item
          v-for="cost in timelineItems"
          :key="cost.id"
          :timestamp="cost.occurred_on"
          placement="top"
        >
          <div class="timeline-row">
            <span class="timeline-pet">{{ cost.pet_name || `宠物#${cost.pet_id}` }}</span>
            <el-tag size="small" type="info" effect="plain">{{ categoryLabel(cost.category_code) }}</el-tag>
            <span class="timeline-amount">{{ amountDisplay(cost.amount) }}</span>
          </div>
          <div v-if="cost.note" class="timeline-note">{{ cost.note }}</div>
        </el-timeline-item>
      </el-timeline>

      <div v-if="timelineHasMore" class="timeline-more">
        <el-button :loading="timelineLoading" @click="loadMoreTimeline">加载更多</el-button>
      </div>
    </el-card>

    <el-card v-if="detail" class="card">
      <template #header>
        <div class="card-header">
          <span class="title">储值流水<span class="title-count">（共 {{ txnTotal }} 条）</span></span>
          <el-button size="small" class="recharge-btn" :icon="'Wallet'" @click="rechargeVisible = true">充值</el-button>
        </div>
      </template>

      <div v-if="!txnLoading && txns.length === 0" class="timeline-empty">
        还没有储值记录，点右上角充值
      </div>

      <el-table v-else :data="txns" stripe>
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="txnTypeBadge(row.type).type" size="small" effect="plain">
              {{ txnTypeBadge(row.type).text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            <span :class="Number(row.amount) >= 0 ? 'txn-plus' : 'txn-minus'">
              {{ txnAmountDisplay(row.amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="赠送" width="90">
          <template #default="{ row }">
            {{ Number(row.bonus_amount) > 0 ? `+${Number(row.bonus_amount).toFixed(2)}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="折扣优惠" width="100">
          <template #default="{ row }">
            <span :class="{ 'txn-minus': Number(row.discount_amount) > 0 }">
              {{ Number(row.discount_amount) > 0 ? `省 ${Number(row.discount_amount).toFixed(2)}` : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="变动后余额" width="120">
          <template #default="{ row }">¥{{ Number(row.balance_after).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="渠道" width="90">
          <template #default="{ row }">{{ channelLabel(row) }}</template>
        </el-table-column>
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ String(row.created_at).replace('T', ' ').slice(0, 19) }}</template>
        </el-table-column>
      </el-table>

      <div v-if="txnHasMore" class="timeline-more">
        <el-button :loading="txnLoading" @click="loadMoreTxns">加载更多</el-button>
      </div>
    </el-card>

    <PetForm
      v-model="petDialog"
      :edit-id="editingPetId"
      :default-customer-id="Number(id)"
      @success="onPetSaved"
    />

    <!-- P-004: 客户详情页直达新增消费 -->
    <CostFormDialog
      v-model="costDialogVisible"
      :initial-customer-id="Number(id)"
      @saved="onCostSaved"
    />

    <!-- 储值充值 -->
    <RechargeDialog
      v-model="rechargeVisible"
      :customer-id="Number(id)"
      :customer-name="detail?.name || ''"
      @success="onRecharged"
    />
  </div>
</template>

<style scoped>
.customer-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.back-bar {
  display: flex;
}
.summary-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}
.summary-card {
  border-radius: 12px;
}
.balance-card .balance-amount {
  color: var(--el-color-success, #67c23a);
}
.balance-card .balance-amount.balance-negative {
  color: var(--danger, #FF6B6B);
}
.arrears-hint {
  color: var(--danger, #FF6B6B) !important;
  font-weight: 600;
}
/* 寄养中提示条 */
.boarding-banner {
  margin-bottom: 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  border-left: 4px solid var(--primary);
}
.bd-banner-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.bd-banner-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}
.bd-banner-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bd-banner-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg);
  border-radius: 8px;
  flex-wrap: wrap;
}
.bd-banner-item.overdue {
  background: color-mix(in srgb, var(--danger) 8%, transparent);
}
.bd-banner-pet {
  font-weight: 600;
  color: var(--text-primary);
}
.bd-banner-meta {
  font-size: 13px;
  color: var(--text-secondary);
}
.bd-banner-meta .text-over {
  color: var(--danger);
}
/* 充值按钮：金色调，呼应「钱」的语义 */
.recharge-btn {
  background: linear-gradient(135deg, #f5b939 0%, #f08b32 100%);
  border: none;
  color: #fff;
  font-weight: 600;
}
.recharge-btn:hover,
.recharge-btn:focus {
  background: linear-gradient(135deg, #f6c356 0%, #f49a4c 100%);
  color: #fff;
}
.txn-plus {
  color: var(--el-color-success, #67c23a);
  font-weight: 600;
}
.txn-minus {
  color: var(--el-color-danger, #f56c6c);
  font-weight: 600;
}
.summary-card :deep(.el-card__body) {
  padding: 16px 20px;
}
.summary-label {
  font-size: 13px;
  color: var(--el-text-color-secondary, #909399);
  margin-bottom: 6px;
}
.summary-value {
  font-size: 22px;
  font-weight: 600;
  color: var(--el-text-color-primary, #303133);
}
.summary-sub {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-color-warning, #e6a23c);
}
.card {
  border-radius: 12px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-header .title {
  font-size: 16px;
  font-weight: 600;
}
.card-header .title-count {
  font-size: 13px;
  font-weight: 400;
  color: var(--el-text-color-secondary, #909399);
  margin-left: 4px;
}
.timeline {
  padding-left: 4px;
}
.timeline-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.timeline-pet {
  font-weight: 600;
  color: var(--el-text-color-primary, #303133);
}
.timeline-amount {
  font-weight: 600;
  color: var(--el-color-danger, #f56c6c);
  margin-left: auto;
}
.timeline-note {
  margin-top: 4px;
  font-size: 13px;
  color: var(--el-text-color-secondary, #909399);
  white-space: pre-wrap;
  word-break: break-word;
}
.timeline-empty {
  padding: 16px 0;
  text-align: center;
  color: var(--el-text-color-secondary, #909399);
}
.timeline-more {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}
.el-table :deep(.el-table__row) {
  cursor: pointer;
}
</style>
