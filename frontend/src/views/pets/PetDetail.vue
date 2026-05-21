<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as petsApi from '@/api/pets'
import * as costsApi from '@/api/costs'
import { useCategoryStore } from '@/stores/categoryStore'
import CostFormDialog from '@/views/costs/CostFormDialog.vue'

const props = defineProps({ id: { type: [String, Number], required: true } })
const router = useRouter()
const categoryStore = useCategoryStore()

const pet = ref(null)
const customerName = ref('')
const loading = ref(false)
const editingInfo = ref(false)
const submitting = ref(false)
const petForm = reactive({ name: '', species: '', breed: '', gender: '', birthday: null, note: '' })

const costs = ref([])
const costsTotal = ref(0)
const page = ref(1)
const pageSize = ref(20)
const costsLoading = ref(false)

const costDialog = ref(false)
const editingCost = ref(null)

const speciesOptions = [
  { value: 'dog', label: '犬' },
  { value: 'cat', label: '猫' },
  { value: 'other', label: '其他' },
]
const genderOptions = [
  { value: 'male', label: '公' },
  { value: 'female', label: '母' },
  { value: 'unknown', label: '未知' },
]

async function loadPet() {
  loading.value = true
  try {
    pet.value = await petsApi.getPet(props.id)
    Object.assign(petForm, {
      name: pet.value.name,
      species: pet.value.species || '',
      breed: pet.value.breed || '',
      gender: pet.value.gender || '',
      birthday: pet.value.birthday || null,
      note: pet.value.note || '',
    })
    try {
      const customersApi = await import('@/api/customers')
      const c = await customersApi.getCustomer(pet.value.customer_id)
      customerName.value = c.name
    } catch {
      customerName.value = ''
    }
  } finally {
    loading.value = false
  }
}

async function loadCosts() {
  costsLoading.value = true
  try {
    const data = await costsApi.listCosts({
      pet_id: props.id,
      page: page.value,
      page_size: pageSize.value,
    })
    costs.value = data.items
    costsTotal.value = data.total
  } finally {
    costsLoading.value = false
  }
}

onMounted(async () => {
  await categoryStore.fetch().catch(() => {})
  await loadPet()
  await loadCosts()
})

async function savePet() {
  submitting.value = true
  const payload = {
    name: petForm.name.trim(),
    species: petForm.species || null,
    breed: petForm.breed?.trim() || null,
    gender: petForm.gender || null,
    birthday: petForm.birthday || null,
    note: petForm.note || null,
  }
  try {
    await petsApi.updatePet(props.id, payload)
    ElMessage.success('已更新')
    editingInfo.value = false
    await loadPet()
  } finally {
    submitting.value = false
  }
}

function cancelEdit() {
  editingInfo.value = false
  Object.assign(petForm, {
    name: pet.value.name,
    species: pet.value.species || '',
    breed: pet.value.breed || '',
    gender: pet.value.gender || '',
    birthday: pet.value.birthday || null,
    note: pet.value.note || '',
  })
}

function openCreateCost() {
  editingCost.value = null
  costDialog.value = true
}

function openEditCost(row) {
  editingCost.value = row
  costDialog.value = true
}

async function deleteCost(row) {
  try {
    await ElMessageBox.confirm('确定删除该花费记录？', '确认删除', { type: 'warning' })
  } catch {
    return
  }
  await costsApi.deleteCost(row.id)
  ElMessage.success('已删除')
  if (costs.value.length === 1 && page.value > 1) page.value -= 1
  await loadCosts()
}

function onCostSaved() {
  loadCosts()
}

function speciesLabel(v) {
  return speciesOptions.find((s) => s.value === v)?.label || '-'
}
function genderLabel(v) {
  return genderOptions.find((g) => g.value === v)?.label || '-'
}

const totalAmount = computed(() => {
  const sum = costs.value.reduce((acc, x) => acc + Number(x.amount), 0)
  return sum.toFixed(2)
})

function onPageChange(p) {
  page.value = p
  loadCosts()
}
</script>

<template>
  <div v-loading="loading" class="pet-detail">
    <div class="back-bar">
      <el-button :icon="'ArrowLeft'" link @click="router.back()">返回</el-button>
    </div>

    <el-card v-if="pet" class="card">
      <template #header>
        <div class="card-header">
          <span class="title">
            宠物信息
            <span v-if="customerName" class="owner">
              · 主人
              <el-link type="primary" @click="router.push(`/customers/${pet.customer_id}`)">
                {{ customerName }}
              </el-link>
            </span>
          </span>
          <div v-if="!editingInfo">
            <el-button size="small" type="primary" @click="editingInfo = true">编辑</el-button>
          </div>
          <div v-else>
            <el-button size="small" @click="cancelEdit">取消</el-button>
            <el-button size="small" type="primary" :loading="submitting" @click="savePet">保存</el-button>
          </div>
        </div>
      </template>

      <el-descriptions v-if="!editingInfo" :column="2" border>
        <el-descriptions-item label="名字">{{ pet.name }}</el-descriptions-item>
        <el-descriptions-item label="种类">{{ speciesLabel(pet.species) }}</el-descriptions-item>
        <el-descriptions-item label="品种">{{ pet.breed || '-' }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ genderLabel(pet.gender) }}</el-descriptions-item>
        <el-descriptions-item label="生日">{{ pet.birthday || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ pet.note || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-form v-else :model="petForm" label-width="80px">
        <el-form-item label="名字">
          <el-input v-model="petForm.name" />
        </el-form-item>
        <el-form-item label="种类">
          <el-select v-model="petForm.species" placeholder="可选" clearable style="width: 100%">
            <el-option v-for="s in speciesOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="品种">
          <el-input v-model="petForm.breed" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="petForm.gender" placeholder="可选" clearable style="width: 100%">
            <el-option v-for="g in genderOptions" :key="g.value" :label="g.label" :value="g.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="生日">
          <el-date-picker v-model="petForm.birthday" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="petForm.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="card">
      <template #header>
        <div class="card-header">
          <span class="title">花费记录（共 {{ costsTotal }} 条 · 当前页合计 ¥{{ totalAmount }}）</span>
          <el-button size="small" type="primary" :icon="'Plus'" @click="openCreateCost">新增花费</el-button>
        </div>
      </template>

      <el-table v-loading="costsLoading" :data="costs" stripe empty-text="该宠物暂无花费记录">
        <el-table-column prop="occurred_on" label="日期" width="120" />
        <el-table-column label="分类" width="120">
          <template #default="{ row }">{{ categoryStore.labelOf(row.category_code) }}</template>
        </el-table-column>
        <el-table-column label="金额" width="140">
          <template #default="{ row }">¥ {{ Number(row.amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.note || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEditCost(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCost(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :total="costsTotal"
          :page-size="pageSize"
          :current-page="page"
          @current-change="onPageChange"
        />
      </div>
    </el-card>

    <CostFormDialog
      v-model="costDialog"
      :initial-pet-id="pet?.id"
      :editing="editingCost"
      :lock-pet="!editingCost"
      @saved="onCostSaved"
    />
  </div>
</template>

<style scoped>
.pet-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card {
  border-radius: 12px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-header .title {
  font-size: 16px;
  font-weight: 600;
}
.owner {
  margin-left: 8px;
  font-weight: normal;
  color: #606266;
}
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
