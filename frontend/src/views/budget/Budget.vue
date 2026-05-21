<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'

const currentMonth = ref('2024-05')
const totalBudget = ref(4000)
const usedAmount = ref(3280.5)
const remainAmount = computed(() => totalBudget.value - usedAmount.value)
const usageRate = computed(() => (usedAmount.value / totalBudget.value * 100).toFixed(1))
const isOverBudget = computed(() => usedAmount.value >= totalBudget.value)
const isWarning = computed(() => usageRate.value >= 80 && usageRate.value < 100)

const petBudgets = ref([
  { id: 1, petName: '旺财', budget: 2000, used: 1860.5, remain: 139.5, rate: 93, status: 'warning' },
  { id: 2, petName: '年糕', budget: 2000, used: 1420, remain: 580, rate: 71, status: 'normal' }
])

const categoryBudgets = ref([
  { id: 1, category: '食品', budget: 1500, used: 1240, remain: 260, rate: 82.7, status: 'warning' },
  { id: 2, category: '医疗', budget: 1000, used: 980, remain: 20, rate: 98, status: 'danger' },
  { id: 3, category: '美容', budget: 500, used: 560, remain: -60, rate: 112, status: 'danger' },
  { id: 4, category: '用品', budget: 400, used: 320, remain: 80, rate: 80, status: 'warning' },
  { id: 5, category: '玩具', budget: 200, used: 180.5, remain: 19.5, rate: 90.25, status: 'warning' },
  { id: 6, category: '其他', budget: 400, used: 0, remain: 400, rate: 0, status: 'normal' }
])

const loading = ref(false)
const dialogVisible = ref(false)
const editId = ref(null)
const editType = ref('') // pet or category

const handleMonthChange = (val) => {
  currentMonth.value = val
  // 切换月份后重新加载数据
  fetchBudgetData()
}

const fetchBudgetData = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 500)
}

const handleAddBudget = (type) => {
  editId.value = null
  editType.value = type
  dialogVisible.value = true
}

const handleEdit = (row, type) => {
  editId.value = row.id
  editType.value = type
  dialogVisible.value = true
}

const handleDelete = (row, type) => {
  ElMessageBox.confirm(
    `确定要删除该预算设置吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    if (type === 'pet') {
      petBudgets.value = petBudgets.value.filter(item => item.id !== row.id)
    } else {
      categoryBudgets.value = categoryBudgets.value.filter(item => item.id !== row.id)
    }
    ElMessage.success('删除成功')
  }).catch(() => {})
}

const handleFormSuccess = () => {
  dialogVisible.value = false
  fetchBudgetData()
}

const getStatusColor = (status) => {
  switch (status) {
    case 'danger': return 'var(--danger)'
    case 'warning': return 'var(--warning)'
    default: return 'var(--success)'
  }
}

onMounted(() => {
  fetchBudgetData()
})
</script>

<template>
  <div class="budget-page">
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h2 style="margin: 0; font-size: 24px;">月度预算</h2>
      <div style="display: flex; gap: 12px; align-items: center;">
        <el-date-picker
          v-model="currentMonth"
          type="month"
          value-format="YYYY-MM"
          placeholder="选择月份"
          style="width: 160px;"
          @change="handleMonthChange"
        />
        <el-button type="primary" @click="handleAddBudget('pet')">
          <el-icon><Plus /></el-icon>
          宠物预算
        </el-button>
        <el-button type="primary" @click="handleAddBudget('category')">
          <el-icon><Plus /></el-icon>
          分类预算
        </el-button>
      </div>
    </div>

    <!-- 总预算卡片 -->
    <el-card shadow="hover" class="total-budget-card" v-loading="loading">
      <div class="budget-header">
        <h3>{{ currentMonth }} 总预算</h3>
        <div :class="['budget-status', isOverBudget ? 'danger' : isWarning ? 'warning' : 'normal']">
          {{ isOverBudget ? '已超支' : isWarning ? '即将超支' : '正常' }}
        </div>
      </div>
      <div class="budget-stats">
        <div class="stat-item">
          <p class="label">总预算</p>
          <p class="value">¥ {{ totalBudget.toFixed(2) }}</p>
        </div>
        <div class="stat-item">
          <p class="label">已使用</p>
          <p class="value text-danger">¥ {{ usedAmount.toFixed(2) }}</p>
        </div>
        <div class="stat-item">
          <p class="label">剩余</p>
          <p class="value" :class="remainAmount < 0 ? 'text-danger' : 'text-success'">¥ {{ remainAmount.toFixed(2) }}</p>
        </div>
        <div class="stat-item">
          <p class="label">使用率</p>
          <p class="value" :class="isOverBudget ? 'text-danger' : isWarning ? 'text-warning' : 'text-success'">{{ usageRate }}%</p>
        </div>
      </div>
      <div class="progress-wrap">
        <el-progress
          :percentage="Number(usageRate)"
          :color="isOverBudget ? '#ef4444' : isWarning ? '#f97316' : '#4ade80'"
          :show-text="false"
          striped
        />
        <p class="progress-text">已使用 {{ usageRate }}%，剩余可用 ¥{{ remainAmount.toFixed(2) }}</p>
      </div>
    </el-card>

    <!-- 宠物预算 -->
    <el-card shadow="hover" title="宠物预算分配" style="margin-top: 20px;" v-loading="loading">
      <div class="budget-list">
        <div v-for="item in petBudgets" :key="item.id" class="budget-item">
          <div class="item-header">
            <div class="item-name">🐾 {{ item.petName }}</div>
            <div class="item-actions">
              <el-button size="small" @click="handleEdit(item, 'pet')">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(item, 'pet')">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
          <div class="item-stats">
            <div>
              <span class="stat-label">预算：</span>
              <span class="stat-value">¥{{ item.budget.toFixed(2) }}</span>
            </div>
            <div>
              <span class="stat-label">已用：</span>
              <span class="stat-value text-danger">¥{{ item.used.toFixed(2) }}</span>
            </div>
            <div>
              <span class="stat-label">剩余：</span>
              <span class="stat-value" :class="item.remain < 0 ? 'text-danger' : 'text-success'">¥{{ item.remain.toFixed(2) }}</span>
            </div>
            <div>
              <span class="stat-label">使用率：</span>
              <span class="stat-value" :style="{ color: getStatusColor(item.status) }">{{ item.rate }}%</span>
            </div>
          </div>
          <el-progress
            :percentage="item.rate"
            :color="getStatusColor(item.status)"
            :show-text="false"
            style="margin-top: 12px;"
          />
        </div>
      </div>
    </el-card>

    <!-- 分类预算 -->
    <el-card shadow="hover" title="分类预算分配" style="margin-top: 20px;" v-loading="loading">
      <div class="budget-grid">
        <div v-for="item in categoryBudgets" :key="item.id" class="category-budget-card">
          <div class="card-header">
            <h4>{{ item.category }}</h4>
            <div class="card-actions">
              <el-button size="small" @click="handleEdit(item, 'category')">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(item, 'category')">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <div class="card-body">
            <div class="amount-info">
              <div class="amount-item">
                <span class="amount-label">预算</span>
                <span class="amount-value">¥{{ item.budget.toFixed(2) }}</span>
              </div>
              <div class="amount-item">
                <span class="amount-label">已用</span>
                <span class="amount-value text-danger">¥{{ item.used.toFixed(2) }}</span>
              </div>
              <div class="amount-item">
                <span class="amount-label">剩余</span>
                <span class="amount-value" :class="item.remain < 0 ? 'text-danger' : 'text-success'">¥{{ item.remain.toFixed(2) }}</span>
              </div>
            </div>
            <el-progress
              :percentage="item.rate"
              :color="getStatusColor(item.status)"
              :show-text="false"
              style="margin-top: 12px;"
            />
            <p class="rate-text" :style="{ color: getStatusColor(item.status) }">使用率：{{ item.rate }}%</p>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 预算表单弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editId ? '编辑预算' : '新增预算'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-width="80px" style="padding-right: 24px;">
        <el-form-item label="预算类型">
          <el-radio-group v-model="editType" disabled>
            <el-radio label="pet">宠物预算</el-radio>
            <el-radio label="category">分类预算</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="editType === 'pet'" label="所属宠物">
          <el-select placeholder="选择宠物" style="width: 100%;">
            <el-option label="旺财" value="1" />
            <el-option label="年糕" value="2" />
          </el-select>
        </el-form-item>
        <el-form-item v-else label="所属分类">
          <el-select placeholder="选择分类" style="width: 100%;">
            <el-option label="食品" value="food" />
            <el-option label="医疗" value="medical" />
            <el-option label="美容" value="beauty" />
          </el-select>
        </el-form-item>
        <el-form-item label="预算金额">
          <el-input-number v-model="totalBudget" :min="0" step="0.01" style="width: 100%;" placeholder="请输入预算金额" />
        </el-form-item>
        <el-form-item label="生效月份">
          <el-date-picker
            v-model="currentMonth"
            type="month"
            value-format="YYYY-MM"
            placeholder="选择生效月份"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleFormSuccess">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.total-budget-card {
  padding: 24px;
}
.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.budget-header h3 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary);
}
.budget-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  color: white;
}
.budget-status.danger {
  background: var(--danger);
}
.budget-status.warning {
  background: var(--warning);
}
.budget-status.normal {
  background: var(--success);
}
.budget-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}
.stat-item .label {
  margin: 0 0 8px 0;
  color: var(--text-muted);
  font-size: 14px;
}
.stat-item .value {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}
.progress-wrap {
  margin-top: 16px;
}
.progress-text {
  margin: 8px 0 0 0;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}
.budget-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.budget-item {
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: 12px;
}
.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.item-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
.item-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 12px;
}
.stat-label {
  font-size: 14px;
  color: var(--text-muted);
}
.stat-value {
  font-size: 16px;
  font-weight: 600;
  margin-left: 4px;
}
.budget-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
.category-budget-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.card-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
.amount-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}
.amount-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.amount-label {
  font-size: 14px;
  color: var(--text-muted);
}
.amount-value {
  font-size: 16px;
  font-weight: 600;
}
.rate-text {
  margin: 8px 0 0 0;
  text-align: right;
  font-size: 14px;
  font-weight: 500;
}
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  .page-header .el-button {
    width: 100%;
  }
  .budget-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .item-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .budget-grid {
    grid-template-columns: 1fr;
  }
}
</style>
