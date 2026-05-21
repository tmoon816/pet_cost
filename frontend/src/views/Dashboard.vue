<script setup>
import { ref, onMounted, computed } from 'vue'
import { Pie, Bar } from '@ant-design/charts'
import { getSummary, getByCategory, getByMonth, getByPet } from '@/api/stats'
import { listCosts } from '@/api/costs'
import { useCategoryStore } from '@/stores/categoryStore'

const categoryStore = useCategoryStore()
const dateRange = ref([])
const summary = ref({
  totalExpense: 3280.5,
  totalIncome: 0,
  budgetRemain: 719.5,
  monthChange: -12.3
})
const categoryStats = ref([])
const monthStats = ref([])
const petStats = ref([])
const recentBills = ref([])
const loading = ref({
  summary: false,
  category: false,
  month: false,
  pet: false,
  bills: false
})

const fetchSummary = async () => {
  loading.value.summary = true
  try {
    const res = await getSummary()
    summary.value = {
      totalExpense: Number(res.currentMonthAmount || 0),
      totalIncome: 0, // 接口暂时没有收入字段
      budgetRemain: Number(res.budgetRemain || 0),
      monthChange: Number(res.monthChange || 0)
    }
  } catch (e) {
    console.error('获取统计信息失败', e)
  } finally {
    loading.value.summary = false
  }
}

const fetchCategoryStats = async () => {
  loading.value.category = true
  try {
    const res = await getByCategory()
    categoryStats.value = res.map(item => ({
      type: categoryStore.categories.find(c => c.code === item.categoryCode)?.label || item.categoryCode,
      value: Number(item.totalAmount || 0),
      count: item.count || 0
    }))
  } catch (e) {
    console.error('获取分类统计失败', e)
  } finally {
    loading.value.category = false
  }
}

const fetchMonthStats = async () => {
  loading.value.month = true
  try {
    const res = await getByMonth()
    monthStats.value = res.map(item => ({
      month: `${item.month.toString().padStart(2, '0')}月`,
      花费: Number(item.totalAmount || 0),
      记录数: item.count || 0
    })).sort((a, b) => a.month.localeCompare(b.month))
  } catch (e) {
    console.error('获取月度统计失败', e)
  } finally {
    loading.value.month = false
  }
}

const fetchPetStats = async () => {
  loading.value.pet = true
  try {
    const res = await getByPet()
    petStats.value = res.map(item => ({
      pet: item.petName || `宠物${item.petId}`,
      花费: Number(item.totalAmount || 0),
      记录数: item.count || 0
    })).sort((a, b) => b.花费 - a.花费)
  } catch (e) {
    console.error('获取宠物统计失败', e)
  } finally {
    loading.value.pet = false
  }
}

const fetchRecentBills = async () => {
  loading.value.bills = true
  try {
    const res = await listCosts({ pageSize: 4, page: 1 })
    recentBills.value = res.items.map(item => ({
      id: item.id,
      date: item.occurredOn,
      category: categoryStore.categories.find(c => c.code === item.categoryCode)?.label || item.categoryCode,
      pet: item.petName || `宠物${item.petId}`,
      amount: Number(item.amount || 0),
      note: item.note || '',
      payType: item.payType || '其他'
    }))
  } catch (e) {
    console.error('获取最近账单失败', e)
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
}

const pieConfig = computed(() => ({
  data: categoryStats.value,
  angleField: 'value',
  colorField: 'type',
  radius: 0.8,
  color: ['#FFA62B', '#82C91E', '#9775FA', '#FF6B6B', '#4DABF7'],
  label: {
    type: 'outer',
    content: '{name}: {percentage:.1%}',
    style: {
      fontSize: 12,
      fill: 'var(--text-secondary)'
    }
  },
  interactions: [
    { type: 'pie-legend-active' },
    { type: 'element-active' }
  ],
  legend: {
    itemName: {
      style: {
        fill: 'var(--text-secondary)'
      }
    }
  }
}))

const monthBarConfig = computed(() => ({
  data: monthStats.value,
  xField: 'month',
  yField: '花费',
  seriesField: 'month',
  color: '#FFA62B',
  label: {
    style: {
      fill: 'var(--text-muted)'
    }
  },
  tooltip: {
    formatter: (datum) => {
      return { name: datum.month, value: `¥${datum.花费.toFixed(2)} / ${datum.记录数}条` }
    }
  },
  xAxis: {
    label: {
      style: {
        fill: 'var(--text-secondary)'
      }
    }
  },
  yAxis: {
    label: {
      style: {
        fill: 'var(--text-secondary)'
      }
    }
  }
}))

const petBarConfig = computed(() => ({
  data: petStats.value,
  xField: '花费',
  yField: 'pet',
  seriesField: 'pet',
  color: ['#82C91E'],
  legend: false,
  label: {
    position: 'right',
    style: {
      fill: 'var(--text-muted)'
    },
    formatter: (datum) => `¥${datum.花费.toFixed(2)}`
  },
  xAxis: {
    label: {
      style: {
        fill: 'var(--text-secondary)'
      }
    }
  },
  yAxis: {
    label: {
      style: {
        fill: 'var(--text-secondary)'
      }
    }
  }
}))

onMounted(() => {
  categoryStore.fetchCategories()
  fetchAllData()
})
</script>

<template>
  <div class="dashboard-page">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.summary">
          <div class="stat-icon" style="background: rgba(74, 222, 128, 0.1); color: var(--primary);">
            💰
          </div>
          <div class="stat-content">
            <p class="stat-label">本月总支出</p>
            <p class="stat-value">¥ {{ summary.totalExpense.toFixed(2) }}</p>
            <p class="stat-change" :class="summary.monthChange < 0 ? 'down' : 'up'">
              {{ summary.monthChange > 0 ? '↑' : '↓' }} {{ Math.abs(summary.monthChange) }}% 较上月
            </p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.summary">
          <div class="stat-icon" style="background: rgba(253, 186, 116, 0.1); color: var(--secondary);">
            📥
          </div>
          <div class="stat-content">
            <p class="stat-label">本月收入</p>
            <p class="stat-value">¥ {{ summary.totalIncome.toFixed(2) }}</p>
            <p class="stat-change text-muted">暂无收入记录</p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.summary">
          <div class="stat-icon" style="background: rgba(59, 130, 246, 0.1); color: var(--info);">
            📊
          </div>
          <div class="stat-content">
            <p class="stat-label">预算剩余</p>
            <p class="stat-value">¥ {{ summary.budgetRemain.toFixed(2) }}</p>
            <p class="stat-change text-muted">本月总预算 ¥4000</p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.summary">
          <div class="stat-icon" style="background: rgba(167, 139, 250, 0.1); color: #a78bfa;">
            🐾
          </div>
          <div class="stat-content">
            <p class="stat-label">宠物数量</p>
            <p class="stat-value">{{ petStats.length }}只</p>
            <p class="stat-change text-muted">共{{ monthStats.reduce((sum, item) => sum + item.记录数, 0) }}条记录</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" title="分类消费占比" v-loading="loading.category">
          <div style="height: 320px;" v-if="categoryStats.length > 0">
            <Pie v-bind="pieConfig" />
          </div>
          <div class="empty-chart" v-else>
            <p>暂无消费数据</p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" title="宠物支出排行" v-loading="loading.pet">
          <div style="height: 320px;" v-if="petStats.length > 0">
            <Bar v-bind="petBarConfig" />
          </div>
          <div class="empty-chart" v-else>
            <p>暂无宠物消费数据</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :lg="14">
        <el-card shadow="hover" title="月度消费趋势" v-loading="loading.month">
          <div style="height: 320px;" v-if="monthStats.length > 0">
            <Bar v-bind="monthBarConfig" />
          </div>
          <div class="empty-chart" v-else>
            <p>暂无月度数据</p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="10">
        <el-card shadow="hover" title="近期账单" v-loading="loading.bills">
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
            <div class="bill-paytype text-muted">{{ bill.payType }}</div>
            </div>
          </div>
        </div>
        <div class="empty-chart" v-else>
          <p>暂无账单</p>
        </div>
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
  font-weight: bold;
}
.stat-content .stat-label {
  margin: 0 0 8px 0;
  color: var(--text-muted);
  font-size: 14px;
}
.stat-content .stat-value {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}
.stat-content .stat-change {
  margin: 6px 0 0 0;
  font-size: 12px;
  font-weight: 500;
}
.stat-change.up {
  color: var(--danger);
}
.stat-change.down {
  color: var(--success);
}
.empty-chart {
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 14px;
}
.recent-bills {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.bill-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}
.bill-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.bill-date {
  font-size: 12px;
  color: var(--text-muted);
}
.bill-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.bill-pet {
  font-size: 14px;
  color: var(--text-secondary);
}
.bill-note {
  font-size: 13px;
  color: var(--text-muted);
}
.bill-right {
  text-align: right;
}
.bill-amount {
  font-size: 16px;
  font-weight: 700;
  color: var(--danger);
}
.bill-paytype {
  font-size: 12px;
}
@media (max-width: 1440px) {
  .stat-card {
    flex-direction: column;
    text-align: center;
    gap: 12px;
    min-height: 140px;
  }
}
</style>
