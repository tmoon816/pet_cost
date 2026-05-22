<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import { useCategoryStore } from '@/stores/categoryStore'
import { listCosts, deleteCost, exportCosts } from '@/api/costs'
import * as customersApi from '@/api/customers'
import * as petsApi from '@/api/pets'
import CostFormDialog from '@/views/costs/CostFormDialog.vue'

const categoryStore = useCategoryStore()

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)

// 筛选
const customerOptions = ref([])
const petOptions = ref([])
const customerLoading = ref(false)
const filterCustomer = ref(null)
const filterPet = ref(null)
const filterCategory = ref(null)
const dateRange = ref(null)

const pageTotalAmount = computed(() =>
  items.value.reduce((s, item) => s + Number(item.amount || 0), 0).toFixed(2)
)

const categoryLabel = (code) =>
  categoryStore.list?.find?.((c) => c.code === code)?.label || code || '-'

async function loadCustomers(query) {
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

async function loadPets(customerId) {
  if (!customerId) {
    petOptions.value = []
    return
  }
  try {
    const data = await petsApi.listPets({ customer_id: customerId, page: 1, page_size: 100 })
    petOptions.value = data.items || []
  } catch (e) {
    petOptions.value = []
  }
}

watch(filterCustomer, async (newId) => {
  await loadPets(newId)
  if (!petOptions.value.some((p) => p.id === filterPet.value)) {
    filterPet.value = null
  }
})

async function fetchList() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterCustomer.value) params.customer_id = filterCustomer.value
    if (filterPet.value) params.pet_id = filterPet.value
    if (filterCategory.value) params.category = filterCategory.value
    if (dateRange.value && dateRange.value.length === 2) {
      params.start = dateRange.value[0]
      params.end = dateRange.value[1]
    }
    const res = await listCosts(params)
    items.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 1
  fetchList()
}
function resetFilters() {
  filterCustomer.value = null
  filterPet.value = null
  filterCategory.value = null
  dateRange.value = null
  page.value = 1
  fetchList()
}
function onPageChange(p) {
  page.value = p
  fetchList()
}

function handleAdd() {
  editing.value = null
  dialogVisible.value = true
}

function formatDateStr(d) {
  if (!d) return ''
  const dt = d instanceof Date ? d : new Date(d)
  return `${dt.getFullYear()}${String(dt.getMonth() + 1).padStart(2, '0')}${String(dt.getDate()).padStart(2, '0')}`
}

async function handleExport() {
  try {
    const params = {}
    if (filterCustomer.value) params.customer_id = filterCustomer.value
    if (filterPet.value) params.pet_id = filterPet.value
    if (filterCategory.value) params.category = filterCategory.value
    if (dateRange.value?.[0]) params.start = formatDateStr(dateRange.value[0])
    if (dateRange.value?.[1]) params.end = formatDateStr(dateRange.value[1])
    const blob = await exportCosts(params)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `costs_${formatDateStr(new Date())}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出完成')
  } catch {
    ElMessage.error('导出失败')
  }
}
function handleEdit(row) {
  editing.value = row
  dialogVisible.value = true
}
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除该订单吗？删除后无法恢复。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await deleteCost(row.id)
    ElMessage.success('已删除')
    if (items.value.length === 1 && page.value > 1) page.value -= 1
    await fetchList()
  } catch (e) {
    // 拦截器兜底
  }
}
function onSaved() {
  dialogVisible.value = false
  fetchList()
}

onMounted(async () => {
  await Promise.all([
    categoryStore.fetch?.().catch?.(() => {}) ?? categoryStore.fetchCategories?.().catch?.(() => {}),
    loadCustomers(''),
  ])
  await fetchList()
})
</script>

<template>
  <div class="bill-list-page">
    <el-card shadow="hover" class="filter-card">
      <template #header>
        <div class="card-header">
          <span>筛选 / 查询</span>
          <div style="display: flex; gap: 8px;">
            <el-button @click="handleExport">
              <el-icon><Download /></el-icon>
              导出 CSV
            </el-button>
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              新增订单
            </el-button>
          </div>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-select
            v-model="filterCustomer"
            filterable
            remote
            clearable
            :remote-method="loadCustomers"
            :loading="customerLoading"
            placeholder="按客户筛选"
            style="width: 100%;"
          >
            <el-option
              v-for="c in customerOptions"
              :key="c.id"
              :label="`${c.name}${c.phone ? ' · ' + c.phone : ''}`"
              :value="c.id"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-select
            v-model="filterPet"
            clearable
            placeholder="按宠物筛选"
            :disabled="!filterCustomer"
            style="width: 100%;"
          >
            <el-option
              v-for="p in petOptions"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-select
            v-model="filterCategory"
            clearable
            placeholder="按服务项目筛选"
            style="width: 100%;"
          >
            <el-option
              v-for="c in categoryStore.list || categoryStore.categories || []"
              :key="c.code"
              :label="c.label"
              :value="c.code"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%;"
          />
        </el-col>
      </el-row>
      <div style="margin-top: 16px;">
        <el-button type="primary" @click="applyFilters">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <el-card shadow="hover" class="list-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>服务订单流水</span>
          <div style="color: var(--text-muted, #909399); font-size: 14px; font-weight: normal; display: flex; gap: 20px;">
            <span>共 {{ total }} 条</span>
            <span>当前页合计：¥ {{ pageTotalAmount }}</span>
          </div>
        </div>
      </template>

      <div v-if="items.length === 0 && !loading" class="empty-state">
        <div style="font-size: 64px; margin-bottom: 20px;">📋</div>
        <p class="empty-title">暂无服务订单</p>
        <p class="empty-desc">点击右上角「新增订单」按钮添加第一条记录</p>
        <el-button type="primary" @click="handleAdd" style="margin-top: 20px;">
          <el-icon><Plus /></el-icon>
          立即新增
        </el-button>
      </div>

      <el-table
        v-else
        :data="items"
        border
        stripe
        style="width: 100%;"
        v-loading="loading"
      >
        <el-table-column prop="occurred_on" label="日期" width="120" sortable />
        <el-table-column label="服务项目" width="150">
          <template #default="{ row }">{{ categoryLabel(row.category_code) }}</template>
        </el-table-column>
        <el-table-column label="所属宠物" width="140">
          <template #default="{ row }">
            {{ row.pet_name || `宠物 #${row.pet_id}` }}
          </template>
        </el-table-column>
        <el-table-column label="金额" width="140" align="right">
          <template #default="{ row }">
            <span class="text-danger" style="font-weight: 600;">
              ¥ {{ Number(row.amount).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="备注" show-overflow-tooltip>
          <template #default="{ row }">{{ row.note || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap" style="margin-top: 20px; text-align: right;" v-if="total > 0">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchList"
          @current-change="onPageChange"
        />
      </div>
    </el-card>

    <CostFormDialog
      v-model="dialogVisible"
      :editing="editing"
      @saved="onSaved"
    />
  </div>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-muted, #909399);
}
.empty-title {
  font-size: 18px;
  font-weight: 500;
  margin: 20px 0 10px;
  color: var(--text-secondary, #606266);
}
.empty-desc {
  font-size: 14px;
  color: var(--text-muted, #909399);
}
.text-danger {
  color: #f56c6c;
}
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  .card-header .el-button {
    width: 100%;
  }
}
</style>
