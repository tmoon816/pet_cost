<script setup>
import { ref, reactive, computed } from 'vue'
import { useCostStore } from '@/stores/costStore'
import { ElMessage, ElMessageBox } from 'element-plus'

const store = useCostStore()

const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const loading = ref(false)

// 筛选条件
const filter = reactive({
  pet: '',
  type: '',
  dateRange: []
})

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 表单数据
const form = reactive({
  date: new Date().toISOString().substring(0, 10),
  pet: '',
  type: '',
  amount: '',
  remark: ''
})

// 表单校验规则
const rules = {
  date: [{ required: true, message: '请选择日期', trigger: 'blur' }],
  pet: [{ required: true, message: '请选择宠物', trigger: 'change' }],
  type: [{ required: true, message: '请选择花费类型', trigger: 'change' }],
  amount: [
    { required: true, message: '请输入金额', trigger: 'blur' },
    { type: 'number', message: '金额必须是数字', trigger: 'blur', transform: v => parseFloat(v) }
  ]
}

// 过滤后的数据
const filteredList = computed(() => {
  let list = store.sortedCostList
  
  // 按宠物筛选
  if (filter.pet) {
    list = list.filter(item => item.pet === filter.pet)
  }
  
  // 按类型筛选
  if (filter.type) {
    list = list.filter(item => item.type === filter.type)
  }
  
  // 按日期范围筛选
  if (filter.dateRange && filter.dateRange.length === 2) {
    const start = filter.dateRange[0]
    const end = filter.dateRange[1]
    list = list.filter(item => item.date >= start && item.date <= end)
  }
  
  pagination.total = list.length
  return list
})

// 分页后的数据
const pageList = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredList.value.slice(start, end)
})

// 打开新增对话框
const handleAdd = () => {
  isEdit.value = false
  currentId.value = null
  Object.assign(form, {
    date: new Date().toISOString().substring(0, 10),
    pet: '',
    type: '',
    amount: '',
    remark: ''
  })
  dialogVisible.value = true
}

// 打开编辑对话框
const handleEdit = (row) => {
  isEdit.value = true
  currentId.value = row.id
  Object.assign(form, row)
  dialogVisible.value = true
}

// 删除花费
const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除这条花费记录吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    store.deleteCost(row.id)
    ElMessage.success('删除成功')
  }).catch(() => {})
}

// 提交表单
const handleSubmit = (formEl) => {
  if (!formEl) return
  formEl.validate((valid) => {
    if (valid) {
      loading.value = true
      const data = {
        ...form,
        amount: parseFloat(form.amount)
      }
      
      if (isEdit.value) {
        store.updateCost(currentId.value, data)
        ElMessage.success('修改成功')
      } else {
        store.addCost(data)
        ElMessage.success('添加成功')
      }
      
      dialogVisible.value = false
      loading.value = false
    }
  })
}

// 重置筛选
const handleResetFilter = () => {
  filter.pet = ''
  filter.type = ''
  filter.dateRange = []
  pagination.currentPage = 1
}

// 格式化金额
const formatAmount = (row) => {
  return `¥ ${row.amount.toFixed(2)}`
}
</script>

<template>
  <div class="cost-list-page">
    <el-card shadow="hover" class="filter-card">
      <template #header>
        <div class="card-header">
          <span>筛选条件</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="8" :md="6">
          <el-select v-model="filter.pet" placeholder="选择宠物" clearable style="width: 100%">
            <el-option :label="pet" :value="pet" v-for="pet in store.petList" :key="pet" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="8" :md="6">
          <el-select v-model="filter.type" placeholder="花费类型" clearable style="width: 100%">
            <el-option :label="type" :value="type" v-for="type in store.costTypeList" :key="type" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="8" :md="6">
          <el-date-picker
            v-model="filter.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-col>
        <el-col :xs="24" :sm="24" :md="6" style="text-align: right">
          <el-button @click="handleResetFilter" style="margin-right: 10px">重置</el-button>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            添加花费
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="hover" class="list-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>花费记录</span>
          <span style="color: #909399; font-size: 14px; font-weight: normal">
            总花费：¥ {{ store.totalCost }}
          </span>
        </div>
      </template>
      <el-table :data="pageList" border stripe style="width: 100%">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="pet" label="宠物" width="100" />
        <el-table-column prop="type" label="花费类型" width="120" />
        <el-table-column prop="amount" label="金额" width="120" :formatter="formatAmount" />
        <el-table-column prop="remark" label="备注" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap" style="margin-top: 20px; text-align: right">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑花费' : '添加花费'"
      width="500px"
      :before-close="() => dialogVisible = false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="日期" prop="date">
          <el-date-picker v-model="form.date" type="date" style="width: 100%" />
        </el-form-item>
        <el-form-item label="宠物" prop="pet">
          <el-select v-model="form.pet" placeholder="请选择宠物" style="width: 100%">
            <el-option :label="pet" :value="pet" v-for="pet in store.petList" :key="pet" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择花费类型" style="width: 100%">
            <el-option :label="type" :value="type" v-for="type in store.costTypeList" :key="type" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input v-model="form.amount" placeholder="请输入金额" prefix-icon="RMB" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-card {
  margin-bottom: 20px;
}
</style>
