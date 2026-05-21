<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import * as statsApi from '@/api/stats'
import * as customersApi from '@/api/customers'

const dateRange = ref(null)
const customerId = ref(null)
const customerOptions = ref([])
const customerLoading = ref(false)

const summary = ref({ total_amount: '0.00', record_count: 0, customer_count: 0, pet_count: 0 })
const byCategory = ref([])
const byMonth = ref([])
const byPet = ref([])
const loading = ref(false)

const categoryChartRef = ref(null)
const monthChartRef = ref(null)
const petChartRef = ref(null)
let categoryChart = null
let monthChart = null
let petChart = null

const hasData = computed(() => Number(summary.value.record_count) > 0)

function windowParams() {
  const p = {}
  if (dateRange.value?.[0]) p.start = dateRange.value[0]
  if (dateRange.value?.[1]) p.end = dateRange.value[1]
  return p
}

async function fetchAll() {
  loading.value = true
  try {
    const summaryParams = { ...windowParams() }
    const petParams = { ...windowParams(), limit: 5 }
    if (customerId.value) petParams.customer_id = customerId.value
    const [s, c, m, p] = await Promise.all([
      statsApi.getSummary(summaryParams),
      statsApi.getByCategory(summaryParams),
      statsApi.getByMonth(summaryParams),
      statsApi.getByPet(petParams),
    ])
    summary.value = s
    byCategory.value = c
    byMonth.value = m
    byPet.value = p
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

async function loadCustomers(query) {
  customerLoading.value = true
  try {
    const data = await customersApi.listCustomers({ q: query || undefined, page: 1, page_size: 50 })
    customerOptions.value = data.items
  } finally {
    customerLoading.value = false
  }
}

function renderCategoryChart() {
  if (!categoryChartRef.value) return
  if (!categoryChart) categoryChart = echarts.init(categoryChartRef.value)
  categoryChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: ¥ {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}: ¥{c}' },
        emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
        data: byCategory.value.map((row) => ({
          name: row.label,
          value: Number(row.total),
        })),
      },
    ],
  })
}

function renderMonthChart() {
  if (!monthChartRef.value) return
  if (!monthChart) monthChart = echarts.init(monthChartRef.value)
  monthChart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}<br/>合计 ¥ {c}' },
    grid: { left: 60, right: 30, top: 30, bottom: 60 },
    xAxis: {
      type: 'category',
      data: byMonth.value.map((r) => r.month),
      axisLabel: { rotate: 45 },
    },
    yAxis: { type: 'value', axisLabel: { formatter: '¥{value}' } },
    series: [
      {
        name: '月度花费',
        type: 'bar',
        data: byMonth.value.map((r) => Number(r.total)),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#667eea' },
            { offset: 1, color: '#764ba2' },
          ]),
          borderRadius: [6, 6, 0, 0],
        },
      },
    ],
  })
}

function renderPetChart() {
  if (!petChartRef.value) return
  if (!petChart) petChart = echarts.init(petChartRef.value)
  petChart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}<br/>合计 ¥ {c}' },
    grid: { left: 80, right: 30, top: 20, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { formatter: '¥{value}' } },
    yAxis: {
      type: 'category',
      data: byPet.value.map((r) => r.pet_name).reverse(),
    },
    series: [
      {
        type: 'bar',
        data: byPet.value.map((r) => Number(r.total)).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#fa709a' },
            { offset: 1, color: '#fee140' },
          ]),
          borderRadius: [0, 6, 6, 0],
        },
      },
    ],
  })
}

function renderCharts() {
  renderCategoryChart()
  renderMonthChart()
  renderPetChart()
}

function resizeAll() {
  categoryChart?.resize()
  monthChart?.resize()
  petChart?.resize()
}

onMounted(async () => {
  await loadCustomers('')
  await fetchAll()
  window.addEventListener('resize', resizeAll)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeAll)
  categoryChart?.dispose()
  monthChart?.dispose()
  petChart?.dispose()
})

watch(() => customerId.value, fetchAll)

function applyWindow() {
  fetchAll()
}

function resetWindow() {
  dateRange.value = null
  customerId.value = null
  fetchAll()
}
</script>

<template>
  <div v-loading="loading" class="stats-page">
    <el-card class="filter-card">
      <div class="filter-row">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          start-placeholder="起始日期"
          end-placeholder="截止日期"
          style="width: 280px"
        />

        <el-select
          v-model="customerId"
          filterable
          remote
          clearable
          :remote-method="loadCustomers"
          :loading="customerLoading"
          placeholder="按客户筛选 Top N 宠物"
          style="width: 240px"
        >
          <el-option
            v-for="c in customerOptions"
            :key="c.id"
            :label="`${c.name}${c.phone ? ' · ' + c.phone : ''}`"
            :value="c.id"
          />
        </el-select>

        <el-button type="primary" :icon="'Search'" @click="applyWindow">查询</el-button>
        <el-button :icon="'RefreshLeft'" @click="resetWindow">重置</el-button>
      </div>
    </el-card>

    <el-row :gutter="20">
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-item">
            <div class="stats-icon total"><el-icon><Money /></el-icon></div>
            <div>
              <div class="stats-label">总花费</div>
              <div class="stats-value">¥ {{ Number(summary.total_amount).toFixed(2) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-item">
            <div class="stats-icon count"><el-icon><List /></el-icon></div>
            <div>
              <div class="stats-label">记录数</div>
              <div class="stats-value">{{ summary.record_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-item">
            <div class="stats-icon avg"><el-icon><User /></el-icon></div>
            <div>
              <div class="stats-label">客户数</div>
              <div class="stats-value">{{ summary.customer_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-item">
            <div class="stats-icon pet"><el-icon><MagicStick /></el-icon></div>
            <div>
              <div class="stats-label">宠物数</div>
              <div class="stats-value">{{ summary.pet_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div v-if="!hasData" class="empty-state">
      <el-icon size="100" color="#c0c4cc"><DataAnalysis /></el-icon>
      <p class="empty-title">该窗口无统计数据</p>
      <p class="empty-desc">换一个时间范围，或者去花费记录页加点数据吧</p>
    </div>

    <template v-else>
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :xs="24" :lg="12">
          <el-card shadow="hover" class="chart-card">
            <template #header><span>分类占比</span></template>
            <div ref="categoryChartRef" class="chart-container" />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="12">
          <el-card shadow="hover" class="chart-card">
            <template #header><span>Top 5 宠物</span></template>
            <div ref="petChartRef" class="chart-container" />
          </el-card>
        </el-col>
      </el-row>

      <el-row style="margin-top: 20px">
        <el-col :xs="24">
          <el-card shadow="hover" class="chart-card">
            <template #header><span>月度花费</span></template>
            <div ref="monthChartRef" class="chart-container" style="height: 380px" />
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<style scoped>
.stats-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.filter-card {
  border-radius: 12px;
}
.filter-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.stats-card {
  border-radius: 12px;
}
.stats-item {
  display: flex;
  align-items: center;
  padding: 4px 0;
}
.stats-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  color: #fff;
  margin-right: 16px;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.12);
}
.stats-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.stats-icon.count {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}
.stats-icon.avg {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}
.stats-icon.pet {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}
.stats-label {
  color: #606266;
  font-size: 13px;
  margin-bottom: 6px;
  font-weight: 500;
}
.stats-value {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #303133 0%, #667eea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.chart-card {
  border-radius: 12px;
}
.chart-container {
  height: 320px;
  width: 100%;
  padding: 8px 0;
}
.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  margin-top: 20px;
}
.empty-title {
  font-size: 18px;
  font-weight: 600;
  margin: 20px 0 8px;
  color: #606266;
}
.empty-desc {
  color: #909399;
}

@media (max-width: 768px) {
  .stats-value {
    font-size: 20px;
  }
  .chart-container {
    height: 260px;
  }
}
</style>
