<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Pie, Bar } from '@ant-design/charts'
import { getSummary, getByCategory, getByMonth, getByPet, getCustomerAcquisition, getDormantCustomers } from '@/api/stats'
import { listCosts } from '@/api/costs'
import { useCategoryStore } from '@/stores/categoryStore'

const router = useRouter()
const categoryStore = useCategoryStore()

// 日期范围选择器
const now = new Date()
const defaultStart = new Date(now.getFullYear(), now.getMonth(), 1)
const defaultEnd = new Date()
const dateRange = ref([defaultStart, defaultEnd])
const dateRangeKey = ref(0) // 强制刷新 key

function formatDate(d) {
  if (!d) return ''
  const dt = d instanceof Date ? d : new Date(d)
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
}

function getRange() {
  const [start, end] = dateRange.value || []
  return { start: formatDate(start), end: formatDate(end) }
}

const monthStart = computed(() => getRange().start)
const monthEnd = computed(() => getRange().end)

// 卡片 - 全部用后端 stats/summary 实有字段
const summary = ref({
  total_amount: 0,
  record_count: 0,
  customer_count: 0,
  pet_count: 0
})

const categoryStats = ref([])
const monthStats = ref([])
const petStats = ref([])
const recentBills = ref([])
// T-009: 本月新客 vs 回头客
const acquisition = ref({ new_customers: 0, returning_customers: 0, total: 0 })
// T-010: 久未到店老客预警
const dormantList = ref([])
const dormantDays = ref(90)
const loading = ref({ summary: false, category: false, month: false, pet: false, bills: false, acquisition: false, dormant: false })

const fetchSummary = async () => {
  loading.value.summary = true
  try {
    const res = await getSummary({ start: monthStart.value, end: monthEnd.value })
    summary.value = {
      total_amount: Number(res.total_amount || 0),
      record_count: Number(res.record_count || 0),
      customer_count: Number(res.customer_count || 0),
      pet_count: Number(res.pet_count || 0)
    }
  } catch (e) {
    summary.value = { total_amount: 0, record_count: 0, customer_count: 0, pet_count: 0 }
  } finally {
    loading.value.summary = false
  }
}

const fetchCategoryStats = async () => {
  loading.value.category = true
  try {
    const res = await getByCategory({ start: monthStart.value, end: monthEnd.value })
    categoryStats.value = (res || []).map((item) => ({
      type: item.label || item.category,
      value: Number(item.total || 0),
      count: Number(item.count || 0)
    })).filter((d) => d.value > 0)
  } catch (e) {
    categoryStats.value = []
  } finally {
    loading.value.category = false
  }
}

const fetchMonthStats = async () => {
  loading.value.month = true
  try {
    // 不传 start/end，拿全量月份趋势
    const res = await getByMonth()
    monthStats.value = (res || []).map((item) => ({
      month: item.month,
      营业额: Number(item.total || 0)
    })).sort((a, b) => a.month.localeCompare(b.month))
  } catch (e) {
    monthStats.value = []
  } finally {
    loading.value.month = false
  }
}

const fetchPetStats = async () => {
  loading.value.pet = true
  try {
    const res = await getByPet({ start: monthStart.value, end: monthEnd.value, limit: 8 })
    petStats.value = (res || []).map((item) => ({
      pet: item.pet_name || `宠物 #${item.pet_id}`,
      消费: Number(item.total || 0)
    })).sort((a, b) => b.消费 - a.消费)
  } catch (e) {
    petStats.value = []
  } finally {
    loading.value.pet = false
  }
}

const fetchRecentBills = async () => {
  loading.value.bills = true
  try {
    const res = await listCosts({ page: 1, page_size: 5 })
    recentBills.value = (res.items || []).map((item) => ({
      id: item.id,
      date: item.occurred_on,
      category: categoryStore.list.find((c) => c.code === item.category_code)?.label || item.category_code,
      pet: item.pet_name || `宠物 #${item.pet_id}`,
      amount: Number(item.amount || 0),
      note: item.note || ''
    }))
  } catch (e) {
    recentBills.value = []
  } finally {
    loading.value.bills = false
  }
}

const fetchAllData = () => {
  fetchSummary()
  fetchCategoryStats()
  fetchMonthStats()
  fetchPetStats()
  fetchRecentBills()
  fetchAcquisition()
  fetchDormantCustomers()
}

function onDateChange() {
  dateRangeKey.value++
  fetchSummary()
  fetchCategoryStats()
  fetchPetStats()
  fetchRecentBills()
}

const fetchDormantCustomers = async () => {
  loading.value.dormant = true
  try {
    const res = await getDormantCustomers({ days: dormantDays.value, limit: 10 })
    dormantList.value = (res || []).map((item) => ({
      customer_id: Number(item.customer_id),
      customer_name: item.customer_name,
      last_visit_at: item.last_visit_at,
      days_since: Number(item.days_since || 0),
    }))
  } catch (e) {
    dormantList.value = []
  } finally {
    loading.value.dormant = false
  }
}

const goToCustomer = (id) => {
  router.push({ name: 'customer-detail', params: { id } })
}

const fetchAcquisition = async () => {
  loading.value.acquisition = true
  try {
    const res = await getCustomerAcquisition({
      year: now.getFullYear(),
      month: now.getMonth() + 1,
    })
    acquisition.value = {
      new_customers: Number(res.new_customers || 0),
      returning_customers: Number(res.returning_customers || 0),
      total: Number(res.total || 0),
    }
  } catch (e) {
    acquisition.value = { new_customers: 0, returning_customers: 0, total: 0 }
  } finally {
    loading.value.acquisition = false
  }
}

const acquisitionDisplay = computed(() => {
  const { new_customers, returning_customers, total } = acquisition.value
  if (!total) {
    return { newPct: '—', returnPct: '—' }
  }
  return {
    newPct: `${Math.round((new_customers / total) * 100)}%`,
    returnPct: `${Math.round((returning_customers / total) * 100)}%`,
  }
})

const pieConfig = computed(() => ({
  data: categoryStats.value,
  angleField: 'value',
  colorField: 'type',
  radius: 0.8,
  label: { type: 'outer', content: '{name}: {percentage:.1%}' },
  legend: true
}))

const monthBarConfig = computed(() => ({
  data: monthStats.value,
  xField: 'month',
  yField: '营业额',
  color: '#FFA62B',
  tooltip: {
    formatter: (datum) => ({ name: datum.month, value: `¥${datum.营业额.toFixed(2)}` })
  }
}))

const petBarConfig = computed(() => ({
  data: petStats.value,
  xField: '消费',
  yField: 'pet',
  color: '#82C91E',
  legend: false,
  label: {
    position: 'right',
    formatter: (datum) => `¥${datum.消费.toFixed(2)}`
  }
}))

onMounted(async () => {
  await categoryStore.fetch(true).catch(() => {})
  fetchAllData()
})

const dateShortcuts = [
  { text: '今天', value: () => [new Date(), new Date()] },
  { text: '本周', value: () => {
    const d = new Date()
    const start = new Date(d.getFullYear(), d.getMonth(), d.getDate() - d.getDay() + 1)
    return [start, d]
  }},
  { text: '本月', value: () => [new Date(now.getFullYear(), now.getMonth(), 1), new Date()] },
  { text: '上月', value: () => {
    const start = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    const end = new Date(now.getFullYear(), now.getMonth(), 0)
    return [start, end]
  }},
  { text: '近30天', value: () => [new Date(now.getTime() - 30 * 86400000), new Date()] },
  { text: '近90天', value: () => [new Date(now.getTime() - 90 * 86400000), new Date()] },
]
</script>

<template>
  <div class="dashboard-page" :key="dateRangeKey">
    <!-- 日期范围选择器 -->
    <div class="date-range-bar">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        :shortcuts="dateShortcuts"
        :default-value="[defaultStart, defaultEnd]"
        @change="onDateChange"
        style="width: 320px;"
      />
    </div>
    <!-- 顶部统计卡片 - 全部用后端 stats/summary 真字段 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.summary">
          <div class="stat-icon" style="background: rgba(74, 222, 128, 0.12); color: #67c23a;">💰</div>
          <div class="stat-content">
            <p class="stat-label">本月营业额</p>
            <p class="stat-value">¥ {{ summary.total_amount.toFixed(2) }}</p>
            <p class="stat-change text-muted">店铺本月客户消费累计</p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.summary">
          <div class="stat-icon" style="background: rgba(253, 186, 116, 0.12); color: #e6a23c;">📋</div>
          <div class="stat-content">
            <p class="stat-label">本月订单数</p>
            <p class="stat-value">{{ summary.record_count }}</p>
            <p class="stat-change text-muted">本月成交服务订单</p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.summary">
          <div class="stat-icon" style="background: rgba(59, 130, 246, 0.12); color: #409eff;">👥</div>
          <div class="stat-content">
            <p class="stat-label">本月活跃会员</p>
            <p class="stat-value">{{ summary.customer_count }}</p>
            <p class="stat-change text-muted">本月有消费的会员</p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.summary">
          <div class="stat-icon" style="background: rgba(167, 139, 250, 0.12); color: #a78bfa;">🐾</div>
          <div class="stat-content">
            <p class="stat-label">服务宠物数</p>
            <p class="stat-value">{{ summary.pet_count }}</p>
            <p class="stat-change text-muted">本月被服务过的宠物</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- T-009: 本月新客 vs 回头客 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover" v-loading="loading.acquisition">
          <template #header><strong>本月新客 vs 回头客</strong></template>
          <div class="acquisition-row">
            <div class="acquisition-cell new">
              <div class="acquisition-label">新客</div>
              <div class="acquisition-value">{{ acquisition.new_customers }}</div>
              <div class="acquisition-pct">{{ acquisitionDisplay.newPct }}</div>
            </div>
            <div class="acquisition-cell returning">
              <div class="acquisition-label">回头客</div>
              <div class="acquisition-value">{{ acquisition.returning_customers }}</div>
              <div class="acquisition-pct">{{ acquisitionDisplay.returnPct }}</div>
            </div>
            <div class="acquisition-cell total">
              <div class="acquisition-label">本月活跃总数</div>
              <div class="acquisition-value">{{ acquisition.total }}</div>
              <div class="acquisition-pct text-muted">去重客户数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- T-010: 3 个月未到店老客预警列表 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover" v-loading="loading.dormant">
          <template #header>
            <div class="dormant-header">
              <strong>久未到店老客预警（≥ {{ dormantDays }} 天）</strong>
              <el-select
                v-model="dormantDays"
                size="small"
                style="width: 130px;"
                @change="fetchDormantCustomers"
              >
                <el-option :value="30" label="≥ 30 天" />
                <el-option :value="60" label="≥ 60 天" />
                <el-option :value="90" label="≥ 90 天" />
                <el-option :value="180" label="≥ 180 天" />
              </el-select>
            </div>
          </template>
          <el-table
            v-if="dormantList.length > 0"
            :data="dormantList"
            size="small"
            stripe
            style="width: 100%;"
          >
            <el-table-column prop="customer_name" label="客户名" min-width="160" />
            <el-table-column prop="last_visit_at" label="最后到店日期" width="160" />
            <el-table-column label="距今天数" width="120">
              <template #default="{ row }">
                <el-tag :type="row.days_since >= 180 ? 'danger' : 'warning'" effect="plain">
                  {{ row.days_since }} 天
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="goToCustomer(row.customer_id)">
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="empty-chart" style="height: 120px;" v-else>
            <p>暂无久未到店老客 🎉</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" v-loading="loading.category">
          <template #header><strong>服务项目营收占比（本月）</strong></template>
          <div style="height: 320px;" v-if="categoryStats.length > 0">
            <Pie v-bind="pieConfig" />
          </div>
          <div class="empty-chart" v-else><p>暂无消费数据</p></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" v-loading="loading.pet">
          <template #header><strong>本月消费宠物 TOP 8</strong></template>
          <div style="height: 320px;" v-if="petStats.length > 0">
            <Bar v-bind="petBarConfig" />
          </div>
          <div class="empty-chart" v-else><p>暂无宠物消费数据</p></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :lg="14">
        <el-card shadow="hover" v-loading="loading.month">
          <template #header><strong>月度营业额趋势（全量）</strong></template>
          <div style="height: 320px;" v-if="monthStats.length > 0">
            <Bar v-bind="monthBarConfig" />
          </div>
          <div class="empty-chart" v-else><p>暂无月度数据</p></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="10">
        <el-card shadow="hover" v-loading="loading.bills">
          <template #header><strong>最近订单</strong></template>
          <div v-if="recentBills.length > 0" class="recent-bills">
            <div v-for="bill in recentBills" :key="bill.id" class="bill-item">
              <div class="bill-left">
                <div class="bill-date">{{ bill.date }}</div>
                <div class="bill-info">
                  <el-tag size="small">{{ bill.category }}</el-tag>
                  <span class="bill-pet">{{ bill.pet }}</span>
                  <span v-if="bill.note" class="bill-note">{{ bill.note }}</span>
                </div>
              </div>
              <div class="bill-right">
                <div class="bill-amount">¥{{ bill.amount.toFixed(2) }}</div>
              </div>
            </div>
          </div>
          <div class="empty-chart" v-else><p>暂无订单</p></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  min-height: 120px;
}
.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
.stat-content .stat-label { margin: 0 0 6px 0; color: #909399; font-size: 13px; }
.stat-content .stat-value { margin: 0; font-size: 26px; font-weight: 700; color: #303133; }
.stat-content .stat-change { margin: 6px 0 0 0; font-size: 12px; }
.text-muted { color: #909399; }
.empty-chart {
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 14px;
}
.recent-bills { display: flex; flex-direction: column; gap: 10px; }
.bill-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f6f8fa;
  border-radius: 8px;
}
.bill-left { display: flex; flex-direction: column; gap: 4px; }
.bill-date { font-size: 12px; color: #909399; }
.bill-info { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.bill-pet { font-size: 13px; color: #606266; }
.bill-note { font-size: 12px; color: #909399; }
.bill-right { text-align: right; }
.bill-amount { font-size: 16px; font-weight: 700; color: #f56c6c; }
/* T-009: 本月新客 vs 回头客 */
.acquisition-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.acquisition-cell {
  padding: 16px 20px;
  border-radius: 10px;
  background: #fafafa;
  text-align: center;
}
.acquisition-cell.new { background: rgba(64, 158, 255, 0.08); }
.acquisition-cell.returning { background: rgba(103, 194, 58, 0.08); }
.acquisition-cell.total { background: rgba(144, 147, 153, 0.08); }
.acquisition-label { font-size: 13px; color: #909399; margin-bottom: 8px; }
.acquisition-value { font-size: 28px; font-weight: 700; color: #303133; }
.acquisition-pct { font-size: 13px; color: #606266; margin-top: 4px; }
/* T-010: 久未到店老客预警 */
.dormant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.date-range-bar {
  margin-bottom: 8px;
}
@media (max-width: 1440px) {
  .stat-card { flex-direction: column; text-align: center; gap: 10px; min-height: 140px; }
}
</style>
