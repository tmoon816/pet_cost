<script setup>
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCostStore } from '@/stores/costStore'
import { useCategoryStore } from '@/stores/categoryStore'
import * as customersApi from '@/api/customers'
import * as petsApi from '@/api/pets'
import CostFormDialog from '@/views/costs/CostFormDialog.vue'

const store = useCostStore()
const categoryStore = useCategoryStore()

const customerOptions = ref([])
const petOptions = ref([])
const customerLoading = ref(false)
const dateRange = ref(null)
const filterCustomer = ref(null)
const filterPet = ref(null)
const filterCategory = ref(null)

const dialogVisible = ref(false)
const editing = ref(null)

async function loadCustomers(query) {
  customerLoading.value = true
  try {
    const data = await customersApi.listCustomers({ q: query || undefined, page: 1, page_size: 50 })
    customerOptions.value = data.items
  } finally {
    customerLoading.value = false
  }
}

async function loadPets(customerId) {
  if (!customerId) {
    petOptions.value = []
    return
  }
  const data = await petsApi.listPets({ customer_id: customerId, page: 1, page_size: 100 })
  petOptions.value = data.items
}

watch(filterCustomer, async (newId) => {
  await loadPets(newId)
  if (!petOptions.value.some((p) => p.id === filterPet.value)) {
    filterPet.value = null
  }
})

async function applyFilters() {
  store.setFilters({
    customer_id: filterCustomer.value || null,
    pet_id: filterPet.value || null,
    category: filterCategory.value || null,
    start: dateRange.value?.[0] || null,
    end: dateRange.value?.[1] || null,
  })
  await store.fetchList()
}

function resetFilters() {
  filterCustomer.value = null
  filterPet.value = null
  filterCategory.value = null
  dateRange.value = null
  store.resetFilters()
  store.fetchList()
}

onMounted(async () => {
  await Promise.all([categoryStore.fetch().catch(() => {}), loadCustomers('')])
  await store.fetchList()
})

function onPageChange(p) {
  store.setPage(p)
  store.fetchList()
}

function openCreate() {
  editing.value = null
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  dialogVisible.value = true
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该花费记录？', '确认删除', { type: 'warning' })
  } catch {
    return
  }
  await store.remove(row.id)
  ElMessage.success('已删除')
  if (store.items.length === 1 && store.page > 1) store.setPage(store.page - 1)
  await store.fetchList()
}

function onSaved() {
  store.fetchList()
}
</script>

<template>
  <div class="cost-list">
    <el-card class="filter-card">
      <div class="filter-row">
        <el-select
          v-model="filterCustomer"
          filterable
          remote
          clearable
          :remote-method="loadCustomers"
          :loading="customerLoading"
          placeholder="按客户筛选"
          style="width: 200px"
        >
          <el-option
            v-for="c in customerOptions"
            :key="c.id"
            :label="`${c.name}${c.phone ? ' · ' + c.phone : ''}`"
            :value="c.id"
          />
        </el-select>

        <el-select
          v-model="filterPet"
          clearable
          placeholder="按宠物筛选"
          :disabled="!filterCustomer"
          style="width: 180px"
        >
          <el-option v-for="p in petOptions" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>

        <el-select v-model="filterCategory" clearable placeholder="按分类筛选" style="width: 160px">
          <el-option v-for="c in categoryStore.list" :key="c.code" :label="c.label" :value="c.code" />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          start-placeholder="起始日期"
          end-placeholder="截止日期"
          style="width: 280px"
        />

        <el-button type="primary" :icon="'Search'" @click="applyFilters">查询</el-button>
        <el-button :icon="'RefreshLeft'" @click="resetFilters">重置</el-button>

        <div class="grow" />
        <el-button type="primary" :icon="'Plus'" @click="openCreate">新增花费</el-button>
      </div>
    </el-card>

    <el-table v-loading="store.loading" :data="store.items" stripe empty-text="无符合条件的花费记录">
      <el-table-column prop="occurred_on" label="日期" width="120" />
      <el-table-column label="分类" width="120">
        <template #default="{ row }">{{ categoryStore.labelOf(row.category_code) }}</template>
      </el-table-column>
      <el-table-column label="金额" width="140">
        <template #default="{ row }">¥ {{ Number(row.amount).toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="宠物" min-width="100">
        <template #default="{ row }">
          <el-link type="primary" @click="$router.push(`/pets/${row.pet_id}`)">
            #{{ row.pet_id }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ row.note || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="center">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="store.total"
        :page-size="store.pageSize"
        :current-page="store.page"
        @current-change="onPageChange"
      />
    </div>

    <CostFormDialog v-model="dialogVisible" :editing="editing" @saved="onSaved" />
  </div>
</template>

<style scoped>
.cost-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.filter-card {
  border-radius: 12px;
}
.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}
.filter-row .grow {
  flex: 1;
}
.pagination {
  display: flex;
  justify-content: flex-end;
}
</style>
