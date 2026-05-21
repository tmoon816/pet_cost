<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { listBudgets, createBudget, updateBudget, deleteBudget } from '@/api/budgets'
import { useCategoryStore } from '@/stores/categoryStore'
import { listPets } from '@/api/pets'

const categoryStore = useCategoryStore()

// 默认当前年月，不再硬编码 2024-05
const now = new Date()
const currentMonth = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)

const loading = ref(false)
const pets = ref([])

// 所有预算的原始数据（[{id,type,target_id,year,month,amount,spent,remaining,overspent,...}]）
const budgets = ref([])

// 派生：三类
const globalBudget = computed(() => budgets.value.find((b) => b.type === 'global') || null)
const petBudgets = computed(() => budgets.value.filter((b) => b.type === 'pet'))
const categoryBudgets = computed(() => budgets.value.filter((b) => b.type === 'category'))

// 总预算卡片
const totalBudget = computed(() => Number(globalBudget.value?.amount || 0))
const usedAmount = computed(() => Number(globalBudget.value?.spent || 0))
const remainAmount = computed(() => Number(globalBudget.value?.remaining || 0))
const usageRate = computed(() => {
  if (!totalBudget.value) return 0
  return Number(((usedAmount.value / totalBudget.value) * 100).toFixed(1))
})
const isOverBudget = computed(() => !!globalBudget.value?.overspent)
const isWarning = computed(() => !isOverBudget.value && usageRate.value >= 80)

const petNameOf = (target_id) =>
  pets.value.find((p) => String(p.id) === String(target_id))?.name || `宠物 #${target_id}`
const categoryLabelOf = (target_id) =>
  categoryStore.list.find((c) => c.code === target_id)?.label || target_id

function statusOf(b) {
  if (!b.amount || Number(b.amount) <= 0) return 'normal'
  const rate = (Number(b.spent) / Number(b.amount)) * 100
  if (b.overspent) return 'danger'
  if (rate >= 80) return 'warning'
  return 'normal'
}
function rateOf(b) {
  const amount = Number(b.amount || 0)
  if (amount <= 0) return 0
  return Number(((Number(b.spent || 0) / amount) * 100).toFixed(1))
}
function statusColor(status) {
  switch (status) {
    case 'danger': return '#f56c6c'
    case 'warning': return '#e6a23c'
    default: return '#67c23a'
  }
}

async function fetchBudgetData() {
  loading.value = true
  try {
    const [year, month] = currentMonth.value.split('-').map(Number)
    const [budgetsRes, petsRes] = await Promise.all([
      listBudgets({ year, month }),
      listPets({ page: 1, page_size: 100 })
    ])
    await categoryStore.fetch(true)
    budgets.value = Array.isArray(budgetsRes) ? budgetsRes : []
    pets.value = petsRes?.items || []
  } catch (e) {
    budgets.value = []
    pets.value = []
  } finally {
    loading.value = false
  }
}

function handleMonthChange() {
  fetchBudgetData()
}

// ============ 弹窗 ============
const dialogVisible = ref(false)
const dialogMode = ref('create') // create | edit
const dialogType = ref('global') // global | pet | category
const editingId = ref(null)
const form = ref({
  target_id: null,
  amount: '',
})

function openCreate(type) {
  dialogMode.value = 'create'
  dialogType.value = type
  editingId.value = null
  form.value = { target_id: null, amount: '' }
  dialogVisible.value = true
}
function openEdit(item) {
  dialogMode.value = 'edit'
  dialogType.value = item.type
  editingId.value = item.id
  form.value = {
    target_id: item.target_id,
    amount: Number(item.amount)
  }
  dialogVisible.value = true
}

async function submitDialog() {
  const amountNum = Number(form.value.amount)
  if (!amountNum || amountNum <= 0) {
    ElMessage.warning('预算金额必须大于 0')
    return
  }
  if (dialogType.value !== 'global' && !form.value.target_id) {
    ElMessage.warning(dialogType.value === 'pet' ? '请选择宠物' : '请选择服务项目')
    return
  }
  const [year, month] = currentMonth.value.split('-').map(Number)
  try {
    if (dialogMode.value === 'edit') {
      // 后端只允许 PATCH amount
      await updateBudget(editingId.value, { amount: String(amountNum.toFixed(2)) })
      ElMessage.success('已更新')
    } else {
      await createBudget({
        type: dialogType.value,
        target_id: dialogType.value === 'global' ? null : String(form.value.target_id),
        year,
        month,
        amount: String(amountNum.toFixed(2))
      })
      ElMessage.success('已新增')
    }
    dialogVisible.value = false
    await fetchBudgetData()
  } catch (e) {
    // 拦截器兜底
  }
}

async function handleDelete(item) {
  try {
    await ElMessageBox.confirm(
      `确定要删除该预算（${item.type}/${item.target_id || '全店'}）？`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await deleteBudget(item.id)
    ElMessage.success('已删除')
    await fetchBudgetData()
  } catch (e) {
    // 拦截器兜底
  }
}

onMounted(() => {
  categoryStore.fetch(true)
  fetchBudgetData()
})
</script>

<template>
  <div class="budget-page">
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
      <h2 style="margin: 0; font-size: 24px;">经营预算</h2>
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
        <el-date-picker
          v-model="currentMonth"
          type="month"
          value-format="YYYY-MM"
          placeholder="选择月份"
          style="width: 160px;"
          @change="handleMonthChange"
        />
        <el-button type="primary" :disabled="!!globalBudget" @click="openCreate('global')">
          <el-icon><Plus /></el-icon>
          营收目标
        </el-button>
        <el-button type="primary" @click="openCreate('pet')">
          <el-icon><Plus /></el-icon>
          单宠物预警
        </el-button>
        <el-button type="primary" @click="openCreate('category')">
          <el-icon><Plus /></el-icon>
          服务项目目标
        </el-button>
      </div>
    </div>

    <!-- 全店营收目标 -->
    <el-card shadow="hover" class="total-budget-card" v-loading="loading">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <strong>{{ currentMonth }} 全店营收目标</strong>
          <div v-if="globalBudget" :class="['budget-status', isOverBudget ? 'danger' : isWarning ? 'warning' : 'normal']">
            {{ isOverBudget ? '已超目标' : isWarning ? '即将达成' : '进度正常' }}
          </div>
        </div>
      </template>
      <div v-if="!globalBudget" class="empty-block">
        <div style="font-size: 48px;">🎯</div>
        <p style="color: #909399; margin: 8px 0;">尚未设置本月全店营收目标</p>
        <el-button type="primary" @click="openCreate('global')">立即设置</el-button>
      </div>
      <div v-else>
        <div class="budget-stats">
          <div class="stat-item">
            <p class="label">营收目标</p>
            <p class="value">¥ {{ totalBudget.toFixed(2) }}</p>
          </div>
          <div class="stat-item">
            <p class="label">本月已营收</p>
            <p class="value text-danger">¥ {{ usedAmount.toFixed(2) }}</p>
          </div>
          <div class="stat-item">
            <p class="label">距离目标</p>
            <p class="value" :class="remainAmount < 0 ? 'text-danger' : 'text-success'">¥ {{ remainAmount.toFixed(2) }}</p>
          </div>
          <div class="stat-item">
            <p class="label">完成率</p>
            <p class="value" :class="isOverBudget ? 'text-danger' : isWarning ? 'text-warning' : 'text-success'">{{ usageRate }}%</p>
          </div>
        </div>
        <div class="progress-wrap">
          <el-progress
            :percentage="Math.min(usageRate, 100)"
            :color="statusColor(isOverBudget ? 'danger' : isWarning ? 'warning' : 'normal')"
            :show-text="false"
            striped
          />
          <p class="progress-text">完成 {{ usageRate }}%</p>
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px;">
          <el-button size="small" @click="openEdit(globalBudget)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(globalBudget)">删除</el-button>
        </div>
      </div>
    </el-card>

    <!-- 单宠物消费预警 -->
    <el-card shadow="hover" style="margin-top: 20px;" v-loading="loading">
      <template #header>
        <strong>单宠物消费预警</strong>
        <span style="margin-left: 8px; font-size: 12px; color: #909399;">针对长期寄养/疗养客户的累计消费预警</span>
      </template>
      <div v-if="petBudgets.length === 0" class="empty-block">
        <div style="font-size: 40px;">🐾</div>
        <p style="color: #909399;">本月暂无单宠物预警</p>
      </div>
      <div v-else class="budget-list">
        <div v-for="item in petBudgets" :key="item.id" class="budget-item">
          <div class="item-header">
            <div class="item-name">🐾 {{ petNameOf(item.target_id) }}</div>
            <div>
              <el-button size="small" @click="openEdit(item)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(item)">删除</el-button>
            </div>
          </div>
          <div class="item-stats">
            <div><span class="stat-label">预警额度：</span><span class="stat-value">¥{{ Number(item.amount).toFixed(2) }}</span></div>
            <div><span class="stat-label">已消费：</span><span class="stat-value text-danger">¥{{ Number(item.spent).toFixed(2) }}</span></div>
            <div><span class="stat-label">剩余：</span><span class="stat-value" :class="Number(item.remaining) < 0 ? 'text-danger' : 'text-success'">¥{{ Number(item.remaining).toFixed(2) }}</span></div>
            <div><span class="stat-label">已达：</span><span class="stat-value" :style="{ color: statusColor(statusOf(item)) }">{{ rateOf(item) }}%</span></div>
          </div>
          <el-progress :percentage="Math.min(rateOf(item), 100)" :color="statusColor(statusOf(item))" :show-text="false" style="margin-top: 12px;" />
        </div>
      </div>
    </el-card>

    <!-- 服务项目营收目标 -->
    <el-card shadow="hover" style="margin-top: 20px;" v-loading="loading">
      <template #header>
        <strong>服务项目营收目标</strong>
      </template>
      <div v-if="categoryBudgets.length === 0" class="empty-block">
        <div style="font-size: 40px;">📊</div>
        <p style="color: #909399;">本月暂无分项目标</p>
      </div>
      <div v-else class="budget-grid">
        <div v-for="item in categoryBudgets" :key="item.id" class="category-budget-card">
          <div class="card-header">
            <h4>{{ categoryLabelOf(item.target_id) }}</h4>
            <div>
              <el-button size="small" @click="openEdit(item)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(item)">删除</el-button>
            </div>
          </div>
          <div class="card-body">
            <div class="amount-info">
              <div class="amount-item"><span class="amount-label">目标</span><span class="amount-value">¥{{ Number(item.amount).toFixed(2) }}</span></div>
              <div class="amount-item"><span class="amount-label">已达</span><span class="amount-value text-danger">¥{{ Number(item.spent).toFixed(2) }}</span></div>
              <div class="amount-item"><span class="amount-label">剩余</span><span class="amount-value" :class="Number(item.remaining) < 0 ? 'text-danger' : 'text-success'">¥{{ Number(item.remaining).toFixed(2) }}</span></div>
            </div>
            <el-progress :percentage="Math.min(rateOf(item), 100)" :color="statusColor(statusOf(item))" :show-text="false" style="margin-top: 12px;" />
            <p class="rate-text" :style="{ color: statusColor(statusOf(item)) }">完成率：{{ rateOf(item) }}%</p>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 预算表单弹窗（真正调接口） -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'edit' ? '编辑预算' : (dialogType === 'global' ? '新增全店营收目标' : dialogType === 'pet' ? '新增单宠物预警' : '新增服务项目目标')"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px" style="padding-right: 24px;">
        <el-form-item label="生效月份">
          <el-date-picker v-model="currentMonth" type="month" value-format="YYYY-MM" :disabled="dialogMode === 'edit'" style="width: 100%;" />
          <div style="font-size: 12px; color: #909399; margin-top: 4px;" v-if="dialogMode === 'edit'">编辑模式下月份不可修改，如需切换月份请删除后重建</div>
        </el-form-item>
        <el-form-item v-if="dialogType === 'pet'" label="所属宠物">
          <el-select v-model="form.target_id" placeholder="请选择宠物" filterable :disabled="dialogMode === 'edit'" style="width: 100%;">
            <el-option v-for="p in pets" :key="p.id" :label="`#${p.id} · ${p.name}`" :value="String(p.id)" />
          </el-select>
        </el-form-item>
        <el-form-item v-else-if="dialogType === 'category'" label="所属项目">
          <el-select v-model="form.target_id" placeholder="请选择服务项目" :disabled="dialogMode === 'edit'" style="width: 100%;">
            <el-option v-for="c in categoryStore.list" :key="c.code" :label="c.label" :value="c.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="预算金额">
          <el-input-number v-model="form.amount" :min="0.01" :step="100" :precision="2" style="width: 100%;" placeholder="请输入金额" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDialog">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.total-budget-card { padding: 0; }
.budget-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  color: white;
}
.budget-status.danger { background: #f56c6c; }
.budget-status.warning { background: #e6a23c; }
.budget-status.normal { background: #67c23a; }
.budget-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  margin-bottom: 16px;
}
.stat-item .label { margin: 0 0 8px 0; color: #909399; font-size: 14px; }
.stat-item .value { margin: 0; font-size: 22px; font-weight: 700; color: #303133; }
.text-danger { color: #f56c6c; }
.text-warning { color: #e6a23c; }
.text-success { color: #67c23a; }
.progress-wrap { margin-top: 8px; }
.progress-text { margin: 6px 0 0 0; text-align: center; color: #909399; font-size: 13px; }
.budget-list { display: flex; flex-direction: column; gap: 16px; }
.budget-item {
  padding: 16px;
  background: #f6f8fa;
  border-radius: 10px;
}
.item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.item-name { font-size: 16px; font-weight: 600; color: #303133; }
.item-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-label { font-size: 13px; color: #909399; }
.stat-value { font-size: 15px; font-weight: 600; margin-left: 4px; }
.budget-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.category-budget-card { background: #f6f8fa; border-radius: 10px; padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.card-header h4 { margin: 0; font-size: 16px; font-weight: 600; color: #303133; }
.amount-info { display: flex; flex-direction: column; gap: 6px; }
.amount-item { display: flex; justify-content: space-between; }
.amount-label { font-size: 13px; color: #909399; }
.amount-value { font-size: 15px; font-weight: 600; }
.rate-text { margin: 6px 0 0 0; text-align: right; font-size: 13px; font-weight: 500; }
.empty-block { text-align: center; padding: 32px 0; }
@media (max-width: 768px) {
  .budget-stats, .item-stats { grid-template-columns: repeat(2, 1fr); }
  .budget-grid { grid-template-columns: 1fr; }
}
</style>
