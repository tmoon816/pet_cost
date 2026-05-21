<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { useCategoryStore } from '@/stores/categoryStore'
import { listCosts, deleteCost } from '@/api/costs'
import BillForm from '@/components/BillForm.vue'

const categoryStore = useCategoryStore()
const list = ref([])
const total = ref(0)
const pagination = ref({
  page: 1,
  pageSize: 20
})
const filter = ref({
  keyword: '',
  category: '',
  pet: '',
  dateRange: []
})
const loading = ref(false)
const dialogVisible = ref(false)
const editId = ref(null)

const fetchList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
      keyword: filter.value.keyword || undefined,
      category: filter.value.category || undefined,
      pet: filter.value.pet || undefined
    }
    if (filter.value.dateRange && filter.value.dateRange.length === 2) {
      params.start = filter.value.dateRange[0]
      params.end = filter.value.dateRange[1]
    }
    // 模拟数据
    setTimeout(() => {
      list.value = [
        { id: 1, date: '2024-05-20', category: '食品', pet: '旺财', amount: 168, note: '渴望猫粮', payType: '微信支付', type: '支出' },
        { id: 2, date: '2024-05-18', category: '医疗', pet: '年糕', amount: 320, note: '疫苗接种', payType: '支付宝', type: '支出' },
        { id: 3, date: '2024-05-15', category: '美容', pet: '旺财', amount: 180, note: '洗澡剪毛', payType: '微信支付', type: '支出' },
        { id: 4, date: '2024-05-10', category: '用品', pet: '年糕', amount: 89, note: '猫砂', payType: '支付宝', type: '支出' },
        { id: 5, date: '2024-05-08', category: '玩具', pet: '旺财', amount: 59.9, note: '飞盘', payType: '微信支付', type: '支出' },
        { id: 6, date: '2024-05-05', category: '保险', pet: '年糕', amount: 299, note: '宠物医疗险', payType: '支付宝', type: '支出' }
      ]
      total.value = 6
      loading.value = false
    }, 500)
  } catch (e) {
    loading.value = false
    ElMessage.error('获取账单列表失败')
  }
}

const resetFilter = () => {
  filter.value = {
    keyword: '',
    category: '',
    pet: '',
    dateRange: []
  }
  pagination.value.page = 1
  fetchList()
}

const handleAdd = () => {
  editId.value = null
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editId.value = row.id
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除该账单吗？删除后无法恢复！`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteCost(row.id)
      ElMessage.success('删除成功')
      fetchList()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const handleFormSuccess = () => {
  dialogVisible.value = false
  fetchList()
}

const formatAmount = (row) => {
  return row.type === '收入' ? `+¥${row.amount.toFixed(2)}` : `-¥${row.amount.toFixed(2)}`
}

const amountClass = (row) => {
  return row.type === '收入' ? 'text-success' : 'text-danger'
}

onMounted(() => {
  categoryStore.fetchCategories()
  fetchList()
})
</script>

<template>
  <div class="bill-list-page">
    <el-card shadow="hover" class="filter-card">
      <template #header>
        <div class="card-header">
          <span>筛选查询</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增账单
          </el-button>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-input
            v-model="filter.keyword"
            placeholder="搜索备注/宠物/金额"
            @keyup.enter="fetchList"
            @clear="fetchList"
            clearable
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-select
            v-model="filter.category"
            placeholder="选择消费分类"
            clearable
            @change="fetchList"
          >
            <el-option
              v-for="category in categoryStore.categories"
              :key="category.code"
              :label="category.label"
              :value="category.code"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-input
            v-model="filter.pet"
            placeholder="搜索宠物名称"
            @keyup.enter="fetchList"
            @clear="fetchList"
            clearable
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-date-picker
            v-model="filter.dateRange"
            type="daterange"
            placeholder="选择日期范围"
            value-format="YYYY-MM-DD"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%;"
            @change="fetchList"
          />
        </el-col>
      </el-row>
      <div style="margin-top: 16px;">
        <el-button @click="fetchList">查询</el-button>
        <el-button @click="resetFilter">重置</el-button>
      </div>
    </el-card>

    <el-card shadow="hover" class="list-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>账单列表</span>
          <div style="color: var(--text-muted); font-size: 14px; font-weight: normal; display: flex; gap: 20px;">
            <span>共 {{ total }} 条记录</span>
            <span>总支出：¥ {{ list.reduce((sum, item) => sum + item.amount, 0).toFixed(2) }}</span>
          </div>
        </div>
      </template>

      <div v-if="list.length === 0 && !loading" class="empty-state">
        <div style="font-size: 64px; margin-bottom: 20px;">📝</div>
        <p class="empty-title">暂无账单记录</p>
        <p class="empty-desc">点击右上角「新增账单」按钮添加第一条记录吧~</p>
        <el-button type="primary" @click="handleAdd" style="margin-top: 20px;">
          <el-icon><Plus /></el-icon>
          立即新增
        </el-button>
      </div>

      <el-table
        v-else
        :data="list"
        border
        stripe
        style="width: 100%;"
        v-loading="loading"
      >
        <el-table-column prop="date" label="日期" width="120" sortable />
        <el-table-column prop="type" label="类型" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.type === '收入' ? 'success' : 'danger'" size="small">
              {{ scope.row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column prop="pet" label="所属宠物" width="100" />
        <el-table-column label="金额" width="120" align="right">
          <template #default="scope">
            <span :class="amountClass(scope.row)" style="font-weight: 600;">
              {{ formatAmount(scope.row) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="payType" label="支付方式" width="120" />
        <el-table-column prop="note" label="备注" show-overflow-tooltip />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="handleEdit(scope.row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap" style="margin-top: 20px; text-align: right;" v-if="total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </el-card>

    <BillForm
      v-model="dialogVisible"
      :edit-id="editId"
      @success="handleFormSuccess"
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
  color: var(--text-muted);
}
.empty-title {
  font-size: 18px;
  font-weight: 500;
  margin: 20px 0 10px;
  color: var(--text-secondary);
}
.empty-desc {
  font-size: 14px;
  color: var(--text-muted);
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
