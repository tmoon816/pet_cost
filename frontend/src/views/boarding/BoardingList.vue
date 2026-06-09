<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, House } from '@element-plus/icons-vue'
import * as boardingApi from '@/api/boarding'
import * as customersApi from '@/api/customers'

const activeTab = ref('active')
const loading = ref(false)
const orders = ref([])

const moneyFmt = new Intl.NumberFormat('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
function formatMoney(n) { return `¥${moneyFmt.format(Number(n) || 0)}` }

// 创建对话框
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const form = reactive({
  customer_id: null,
  pet_id: null,
  check_in_date: new Date(),
  expected_days: 7,
  daily_rate: 50,
  note: '',
})
const customerOptions = ref([])
const customerLoading = ref(false)
const petOptions = ref([])

const rules = {
  pet_id: [{ required: true, message: '请选择宠物', trigger: 'change' }],
  check_in_date: [{ required: true, message: '请选择入住日期', trigger: 'change' }],
  expected_days: [{ required: true, message: '请输入约定天数', trigger: 'blur' }],
  daily_rate: [{ required: true, message: '请输入每日价格', trigger: 'blur' }],
}

const estimatedTotal = computed(() => Number(form.expected_days || 0) * Number(form.daily_rate || 0))

const fetchOrders = async () => {
  loading.value = true
  try {
    const res = await boardingApi.listBoarding({ status: activeTab.value })
    orders.value = res || []
  } catch (e) {
    orders.value = []
  } finally {
    loading.value = false
  }
}

const loadCustomers = async (query) => {
  customerLoading.value = true
  try {
    const data = await customersApi.listCustomers({ q: query || undefined, page: 1, page_size: 50 })
    customerOptions.value = data.items || []
  } catch (e) {
    customerOptions.value = []
  } finally {
    customerLoading.value = false
  }
}

const onCustomerChange = async (cid) => {
  form.pet_id = null
  petOptions.value = []
  if (!cid) return
  try {
    const detail = await customersApi.getCustomer(cid)
    petOptions.value = detail.pets || []
  } catch (e) {
    petOptions.value = []
  }
}

function formatDateForApi(d) {
  if (!d) return ''
  const dt = d instanceof Date ? d : new Date(d)
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
}

function openCreate() {
  Object.assign(form, {
    customer_id: null, pet_id: null, check_in_date: new Date(),
    expected_days: 7, daily_rate: 50, note: '',
  })
  petOptions.value = []
  dialogVisible.value = true
}

const submit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await boardingApi.createBoarding({
        pet_id: form.pet_id,
        check_in_date: formatDateForApi(form.check_in_date),
        expected_days: Number(form.expected_days),
        daily_rate: Number(form.daily_rate).toFixed(2),
        note: form.note || undefined,
      })
      ElMessage.success('寄养单已创建，开始按天计费')
      dialogVisible.value = false
      activeTab.value = 'active'
      await fetchOrders()
    } catch (e) {
      /* http 拦截器已提示 */
    } finally {
      submitting.value = false
    }
  })
}

const onClose = async (row) => {
  try {
    const { value } = await ElMessageBox.prompt(
      `「${row.pet_name}」退房日期（退房当天不计费）`,
      '办理退房',
      {
        confirmButtonText: '确认退房',
        cancelButtonText: '取消',
        inputType: 'date',
        inputValue: formatDateForApi(new Date()),
        inputValidator: (v) => (v ? true : '请选择退房日期'),
      }
    )
    const res = await boardingApi.closeBoarding(row.id, { check_out_date: value })
    // 退房后若客户欠费，醒目提示收款
    const bal = Number(res.customer_balance)
    if (Number.isFinite(bal) && bal < 0) {
      await ElMessageBox.alert(
        `该客户储值余额为 ¥${bal.toFixed(2)}，已欠费 ¥${Math.abs(bal).toFixed(2)}。\n请在退房时向客户收清欠款（可到客户详情页充值补足）。`,
        '⚠️ 请收取欠款',
        { confirmButtonText: '知道了', type: 'warning' }
      )
    } else {
      ElMessage.success('已退房并结清费用')
    }
    await fetchOrders()
  } catch (e) {
    if (e !== 'cancel') {
      const detail = e?.response?.data?.detail
      if (detail === 'checkout_before_checkin') ElMessage.error('退房日不能早于入住日')
    }
  }
}

const onDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除「${row.pet_name}」的寄养单？将一并删除其按天扣费记录（不自动退余额）。`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    return
  }
  await boardingApi.deleteBoarding(row.id)
  ElMessage.success('已删除')
  await fetchOrders()
}

const onSettle = async () => {
  loading.value = true
  try {
    const res = await boardingApi.settleBoarding()
    ElMessage.success(`结算完成：处理 ${res.orders_processed} 单，新扣 ${res.days_charged} 天`)
    await fetchOrders()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function switchTab(tab) {
  activeTab.value = tab
  fetchOrders()
}

onMounted(() => {
  fetchOrders()
  loadCustomers()
})
</script>

<template>
  <div class="boarding-page">
    <header class="bd-header">
      <div class="bd-header-text">
        <h2>寄养管理</h2>
        <p>按天自动扣费，超期持续计费并提醒，余额不足可欠费 🏠</p>
      </div>
      <div class="bd-header-actions">
        <el-button :icon="Refresh" @click="onSettle">立即结算</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建寄养单</el-button>
      </div>
    </header>

    <div class="bd-tabs">
      <button class="bd-tab" :class="{ on: activeTab === 'active' }" @click="switchTab('active')">在住</button>
      <button class="bd-tab" :class="{ on: activeTab === 'closed' }" @click="switchTab('closed')">已退房</button>
    </div>

    <div class="bd-list" v-loading="loading">
      <div v-if="orders.length === 0" class="bd-empty">
        <div class="empty-emoji">🐾</div>
        <p class="empty-title">{{ activeTab === 'active' ? '当前没有在住寄养' : '暂无已退房记录' }}</p>
        <p class="empty-hint" v-if="activeTab === 'active'">点击右上角「新建寄养单」开始</p>
      </div>

      <div
        v-for="o in orders"
        :key="o.id"
        class="bd-card"
        :class="{ overdue: o.is_overdue, arrears: o.customer_balance < 0 }"
      >
        <div class="bd-card-main">
          <div class="bd-pet">
            <span class="bd-pet-icon"><el-icon><House /></el-icon></span>
            <div>
              <div class="bd-pet-name">{{ o.pet_name }}</div>
              <div class="bd-owner">{{ o.customer_name }}</div>
            </div>
          </div>

          <div class="bd-tags">
            <el-tag v-if="o.is_overdue" type="danger" effect="dark" size="small">
              超期 {{ o.overdue_days }} 天
            </el-tag>
            <el-tag v-else-if="o.status === 'active'" type="success" effect="plain" size="small">在住</el-tag>
            <el-tag v-else type="info" effect="plain" size="small">已退房</el-tag>
            <el-tag v-if="o.customer_balance < 0" type="danger" effect="plain" size="small">
              欠费 {{ formatMoney(Math.abs(o.customer_balance)) }}
            </el-tag>
          </div>
        </div>

        <div class="bd-stats">
          <div class="bd-stat">
            <span class="bd-stat-label">入住日</span>
            <span class="bd-stat-val">{{ o.check_in_date }}</span>
          </div>
          <div class="bd-stat">
            <span class="bd-stat-label">已住 / 约定</span>
            <span class="bd-stat-val">
              <strong :class="{ 'text-over': o.is_overdue }">{{ o.days_stayed }}</strong> / {{ o.expected_days }} 天
            </span>
          </div>
          <div class="bd-stat">
            <span class="bd-stat-label">每日</span>
            <span class="bd-stat-val">{{ formatMoney(o.daily_rate) }}</span>
          </div>
          <div class="bd-stat">
            <span class="bd-stat-label">累计已扣</span>
            <span class="bd-stat-val accent">{{ formatMoney(o.total_charged) }}</span>
          </div>
          <div class="bd-stat">
            <span class="bd-stat-label">结算至</span>
            <span class="bd-stat-val">{{ o.settled_through || '—' }}</span>
          </div>
          <div class="bd-stat" v-if="o.status === 'closed'">
            <span class="bd-stat-label">退房日</span>
            <span class="bd-stat-val">{{ o.check_out_date }}</span>
          </div>
        </div>

        <div class="bd-actions" v-if="o.status === 'active'">
          <el-button size="small" type="primary" @click="onClose(o)">办理退房</el-button>
          <el-button size="small" type="danger" plain @click="onDelete(o)">删除</el-button>
        </div>
        <div class="bd-actions" v-else>
          <el-button size="small" type="danger" plain @click="onDelete(o)">删除</el-button>
        </div>
      </div>
    </div>

    <!-- 新建寄养单 -->
    <el-dialog v-model="dialogVisible" title="新建寄养单" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <el-form-item label="客户">
          <el-select
            v-model="form.customer_id"
            filterable remote clearable
            :remote-method="loadCustomers"
            :loading="customerLoading"
            placeholder="搜索姓名 / 手机号"
            style="width: 100%"
            @change="onCustomerChange"
          >
            <el-option
              v-for="c in customerOptions"
              :key="c.id"
              :label="c.phone ? `${c.name}（${c.phone}）` : c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="宠物" prop="pet_id">
          <el-select
            v-model="form.pet_id"
            placeholder="先选客户，再选其名下宠物"
            :disabled="!form.customer_id"
            style="width: 100%"
          >
            <el-option v-for="p in petOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="入住日期" prop="check_in_date">
          <el-date-picker
            v-model="form.check_in_date"
            type="date"
            placeholder="选择入住日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="约定天数" prop="expected_days">
              <el-input-number v-model="form.expected_days" :min="1" :max="3650" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="每日价格" prop="daily_rate">
              <el-input-number v-model="form.daily_rate" :min="1" :precision="2" :step="10" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <div class="bd-estimate">
          约定期内预计：<strong>{{ formatMoney(estimatedTotal) }}</strong>
          （{{ form.expected_days }} 天 × {{ formatMoney(form.daily_rate) }}）
        </div>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="2" maxlength="200" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">创建并开始计费</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.boarding-page { max-width: 1180px; margin: 0 auto; }

.bd-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}
.bd-header-text h2 { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.bd-header-text p { margin: 6px 0 0; color: var(--text-secondary); font-size: 14px; }

.bd-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}
.bd-tab {
  height: 36px;
  padding: 0 20px;
  border: 1px solid var(--border);
  background: var(--card);
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.18s ease;
}
.bd-tab:hover { border-color: var(--primary); color: var(--primary); }
.bd-tab.on { background: var(--primary); border-color: var(--primary); color: #fff; }

.bd-list { display: flex; flex-direction: column; gap: 14px; min-height: 160px; }
.bd-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 4px solid var(--success);
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: box-shadow 0.18s ease;
}
.bd-card:hover { box-shadow: 0 8px 22px rgba(0,0,0,0.07); }
.bd-card.overdue { border-left-color: var(--danger); }
.bd-card.arrears:not(.overdue) { border-left-color: var(--warning); }

.bd-card-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.bd-pet { display: flex; align-items: center; gap: 12px; }
.bd-pet-icon {
  width: 42px; height: 42px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--primary) 14%, transparent);
  color: var(--primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
}
.bd-pet-name { font-size: 16px; font-weight: 700; color: var(--text-primary); }
.bd-owner { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
.bd-tags { display: flex; gap: 6px; flex-wrap: wrap; }

.bd-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 12px;
  padding: 14px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.bd-stat { display: flex; flex-direction: column; gap: 4px; }
.bd-stat-label { font-size: 12px; color: var(--text-muted); }
.bd-stat-val { font-size: 14px; color: var(--text-primary); font-weight: 500; }
.bd-stat-val.accent { color: var(--primary); font-weight: 700; }
.bd-stat-val .text-over { color: var(--danger); }

.bd-actions { display: flex; justify-content: flex-end; gap: 8px; }

.bd-empty { text-align: center; padding: 48px; }
.empty-emoji { font-size: 46px; }
.empty-title { margin: 10px 0 2px; font-weight: 600; color: var(--text-secondary); }
.empty-hint { margin: 0; font-size: 13px; color: var(--text-muted); }

.bd-estimate {
  margin: -6px 0 16px;
  padding: 10px 14px;
  background: var(--bg);
  border-radius: 10px;
  font-size: 13px;
  color: var(--text-secondary);
}
.bd-estimate strong { color: var(--primary); font-size: 15px; }
</style>
