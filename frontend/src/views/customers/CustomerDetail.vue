<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCustomerStore } from '@/stores/customerStore'
import { useCategoryStore } from '@/stores/categoryStore'
import * as petsApi from '@/api/pets'
import * as customersApi from '@/api/customers'
import { listCosts } from '@/api/costs'
import CostFormDialog from '@/views/costs/CostFormDialog.vue'

const props = defineProps({ id: { type: [String, Number], required: true } })
const router = useRouter()
const customerStore = useCustomerStore()
const categoryStore = useCategoryStore()

const detail = ref(null)
const summary = ref(null)
const loading = ref(false)
const editingInfo = ref(false)
const submitting = ref(false)
const customerForm = reactive({ name: '', phone: '', note: '' })

// T-011: 消费时间线（分页加载）
const TIMELINE_PAGE_SIZE = 20
const timelineItems = ref([])
const timelineTotal = ref(0)
const timelinePage = ref(1)
const timelineLoading = ref(false)
const timelineLoaded = ref(false)
const timelineHasMore = computed(
  () => timelineItems.value.length < timelineTotal.value
)

const petDialog = ref(false)
const editingPetId = ref(null)
const petForm = reactive({ name: '', species: '', breed: '', gender: '', birthday: null, note: '' })
const petFormRef = ref(null)
const petSubmitting = ref(false)
// P-004: 客户详情页直达新增消费
const costDialogVisible = ref(false)

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

const petRules = {
  name: [{ required: true, message: '请输入宠物名', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    detail.value = await customerStore.fetchDetail(props.id)
    Object.assign(customerForm, {
      name: detail.value.name,
      phone: detail.value.phone || '',
      note: detail.value.note || '',
    })
    // T-007: 拉取客户聚合指标（失败不阻断详情页加载）
    try {
      summary.value = await customersApi.getCustomerSummary(props.id)
    } catch (err) {
      summary.value = null
    }
    // T-011: 确保分类字典已加载（用于显示分类 label），并刷新时间线第 1 页
    try {
      await categoryStore.fetch()
    } catch (err) {
      // 字典拉取失败不阻断详情页，时间线会回退显示 code
    }
    timelinePage.value = 1
    timelineItems.value = []
    timelineTotal.value = 0
    timelineLoaded.value = false
    await loadTimeline()
  } finally {
    loading.value = false
  }
}

async function loadTimeline() {
  if (timelineLoading.value) return
  timelineLoading.value = true
  try {
    const res = await listCosts({
      customer_id: Number(props.id),
      page: timelinePage.value,
      page_size: TIMELINE_PAGE_SIZE,
    })
    const list = res?.items || []
    if (timelinePage.value === 1) {
      timelineItems.value = list
    } else {
      timelineItems.value = timelineItems.value.concat(list)
    }
    timelineTotal.value = Number(res?.total || 0)
    timelineLoaded.value = true
  } catch (err) {
    if (timelinePage.value === 1) {
      timelineItems.value = []
      timelineTotal.value = 0
    }
  } finally {
    timelineLoading.value = false
  }
}

async function loadMoreTimeline() {
  if (!timelineHasMore.value || timelineLoading.value) return
  timelinePage.value += 1
  await loadTimeline()
}

onMounted(load)

async function saveCustomer() {
  submitting.value = true
  const payload = {
    name: customerForm.name.trim(),
    phone: customerForm.phone.trim() || null,
    note: customerForm.note || null,
  }
  try {
    await customerStore.update(props.id, payload)
    ElMessage.success('已更新')
    editingInfo.value = false
    await load()
  } catch (err) {
    if (err?.status === 409 && err.detail?.detail === 'phone_exists') {
      ElMessage.error(`手机号已绑定客户 #${err.detail.existing_id}`)
    }
  } finally {
    submitting.value = false
  }
}

function cancelEdit() {
  editingInfo.value = false
  Object.assign(customerForm, {
    name: detail.value.name,
    phone: detail.value.phone || '',
    note: detail.value.note || '',
  })
}

function resetPetForm() {
  Object.assign(petForm, { name: '', species: '', breed: '', gender: '', birthday: null, note: '' })
  editingPetId.value = null
}

function openCreatePet() {
  resetPetForm()
  petDialog.value = true
}

function openEditPet(pet) {
  editingPetId.value = pet.id
  Object.assign(petForm, {
    name: pet.name,
    species: pet.species || '',
    breed: pet.breed || '',
    gender: pet.gender || '',
    birthday: pet.birthday || null,
    note: pet.note || '',
  })
  petDialog.value = true
}

async function submitPet() {
  if (!petFormRef.value) return
  await petFormRef.value.validate(async (valid) => {
    if (!valid) return
    petSubmitting.value = true
    const payload = {
      name: petForm.name.trim(),
      species: petForm.species || null,
      breed: petForm.breed?.trim() || null,
      gender: petForm.gender || null,
      birthday: petForm.birthday || null,
      note: petForm.note || null,
    }
    try {
      if (editingPetId.value) {
        await petsApi.updatePet(editingPetId.value, payload)
        ElMessage.success('已更新')
      } else {
        await petsApi.createPet({ ...payload, customer_id: Number(props.id) })
        ElMessage.success('已新增')
      }
      petDialog.value = false
      resetPetForm()
      await load()
    } finally {
      petSubmitting.value = false
    }
  })
}

async function deletePet(pet) {
  try {
    await ElMessageBox.confirm(
      `确定删除宠物「${pet.name}」？相关花费记录会一并删除。`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    return
  }
  await petsApi.deletePet(pet.id)
  ElMessage.success('已删除')
  await load()
}

function viewPet(pet) {
  router.push(`/pets/${pet.id}`)
}

function speciesLabel(v) {
  return speciesOptions.find((s) => s.value === v)?.label || '-'
}
function genderLabel(v) {
  return genderOptions.find((g) => g.value === v)?.label || '-'
}

// T-007: 卡片显示助手
const totalAmountDisplay = computed(() => {
  const n = summary.value?.total_amount
  if (n === undefined || n === null) return '—'
  const num = Number(n)
  if (!Number.isFinite(num)) return '—'
  return `¥${num.toFixed(2)}`
})

const lastVisitDisplay = computed(() => {
  const ts = summary.value?.last_visit_at
  if (!ts) return '—'
  return String(ts).slice(0, 10)
})

const costCountDisplay = computed(() => {
  const c = summary.value?.cost_count
  if (c === undefined || c === null) return '—'
  return String(c)
})

// P-006: 客户类型徽章
const customerTypeBadge = computed(() => {
  const t = summary.value?.customer_type
  if (t === 'vip') return { label: 'VIP', type: 'warning' }
  if (t === 'returning') return { label: '回头客', type: 'success' }
  if (t === 'first_visit') return { label: '新客', type: 'info' }
  return null
})

// T-011: 时间线展示助手
function categoryLabel(code) {
  if (!code) return '-'
  return categoryStore.list?.find?.((c) => c.code === code)?.label || code
}

function amountDisplay(v) {
  const num = Number(v)
  if (!Number.isFinite(num)) return '—'
  return `¥${num.toFixed(2)}`
}

async function onCostSaved() {
  // 刷新时间线和客户指标
  timelinePage.value = 1
  timelineItems.value = []
  timelineTotal.value = 0
  timelineLoaded.value = false
  await loadTimeline()
  try {
    summary.value = await customersApi.getCustomerSummary(props.id)
  } catch {
    summary.value = null
  }
}
</script>

<template>
  <div v-loading="loading" class="customer-detail">
    <div class="back-bar">
      <el-button :icon="'ArrowLeft'" link @click="router.push('/customers')">返回客户列表</el-button>
    </div>

    <div v-if="detail" class="summary-row">
      <el-card class="summary-card" shadow="never">
        <div class="summary-label">
          客户类型
          <el-tag
            v-if="customerTypeBadge"
            :type="customerTypeBadge.type"
            size="small"
            effect="dark"
            style="margin-left: 6px;"
          >
            {{ customerTypeBadge.label }}
          </el-tag>
        </div>
        <div class="summary-value">{{ detail.name }}</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-label">累计消费</div>
        <div class="summary-value">{{ totalAmountDisplay }}</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-label">上次到店</div>
        <div class="summary-value">{{ lastVisitDisplay }}</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-label">总订单数</div>
        <div class="summary-value">{{ costCountDisplay }}</div>
      </el-card>
    </div>

    <el-card v-if="detail" class="card">
      <template #header>
        <div class="card-header">
          <span class="title">客户信息</span>
          <div v-if="!editingInfo">
            <el-button size="small" type="primary" @click="editingInfo = true">编辑</el-button>
          </div>
          <div v-else>
            <el-button size="small" @click="cancelEdit">取消</el-button>
            <el-button size="small" type="primary" :loading="submitting" @click="saveCustomer">保存</el-button>
          </div>
        </div>
      </template>

      <el-descriptions v-if="!editingInfo" :column="2" border>
        <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ detail.name }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ detail.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ detail.note || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detail.created_at?.replace('T', ' ').slice(0, 19) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ detail.updated_at?.replace('T', ' ').slice(0, 19) }}</el-descriptions-item>
      </el-descriptions>

      <el-form v-else :model="customerForm" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="customerForm.name" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="customerForm.phone" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="customerForm.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="detail" class="card">
      <template #header>
        <div class="card-header">
          <span class="title">名下宠物（{{ detail.pets?.length || 0 }}）</span>
          <el-button size="small" type="primary" :icon="'Plus'" @click="openCreatePet">新增宠物</el-button>
        </div>
      </template>

      <el-table :data="detail.pets || []" stripe empty-text="还没有宠物，点右上角新增" @row-click="viewPet">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名字" min-width="120" />
        <el-table-column label="种类" width="100">
          <template #default="{ row }">{{ speciesLabel(row.species) }}</template>
        </el-table-column>
        <el-table-column prop="breed" label="品种" min-width="120">
          <template #default="{ row }">{{ row.breed || '-' }}</template>
        </el-table-column>
        <el-table-column label="性别" width="80">
          <template #default="{ row }">{{ genderLabel(row.gender) }}</template>
        </el-table-column>
        <el-table-column prop="birthday" label="生日" width="120">
          <template #default="{ row }">{{ row.birthday || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center">
          <template #default="{ row }">
            <el-button size="small" @click.stop="viewPet(row)">详情</el-button>
            <el-button size="small" type="primary" @click.stop="openEditPet(row)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="deletePet(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="detail" class="card">
      <template #header>
        <div class="card-header">
          <span class="title">消费时间线<span class="title-count">（共 {{ timelineTotal }} 条）</span></span>
          <el-button size="small" type="primary" :icon="'Plus'" @click="costDialogVisible = true">
            新增服务
          </el-button>
        </div>
      </template>

      <div v-if="timelineLoaded && timelineItems.length === 0" class="timeline-empty">
        该客户还没有消费记录
      </div>

      <el-timeline v-else class="timeline">
        <el-timeline-item
          v-for="cost in timelineItems"
          :key="cost.id"
          :timestamp="cost.occurred_on"
          placement="top"
        >
          <div class="timeline-row">
            <span class="timeline-pet">{{ cost.pet_name || `宠物#${cost.pet_id}` }}</span>
            <el-tag size="small" type="info" effect="plain">{{ categoryLabel(cost.category_code) }}</el-tag>
            <span class="timeline-amount">{{ amountDisplay(cost.amount) }}</span>
          </div>
          <div v-if="cost.note" class="timeline-note">{{ cost.note }}</div>
        </el-timeline-item>
      </el-timeline>

      <div v-if="timelineHasMore" class="timeline-more">
        <el-button :loading="timelineLoading" @click="loadMoreTimeline">加载更多</el-button>
      </div>
    </el-card>

    <el-dialog
      v-model="petDialog"
      :title="editingPetId ? '编辑宠物' : '新增宠物'"
      width="480px"
      @closed="resetPetForm"
    >
      <el-form ref="petFormRef" :model="petForm" :rules="petRules" label-width="80px">
        <el-form-item label="名字" prop="name">
          <el-input v-model="petForm.name" maxlength="50" />
        </el-form-item>
        <el-form-item label="种类">
          <el-select v-model="petForm.species" placeholder="可选" style="width: 100%" clearable>
            <el-option v-for="s in speciesOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="品种">
          <el-input v-model="petForm.breed" maxlength="50" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="petForm.gender" placeholder="可选" style="width: 100%" clearable>
            <el-option v-for="g in genderOptions" :key="g.value" :label="g.label" :value="g.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="生日">
          <el-date-picker
            v-model="petForm.birthday"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="petForm.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="petDialog = false">取消</el-button>
        <el-button type="primary" :loading="petSubmitting" @click="submitPet">保存</el-button>
      </template>
    </el-dialog>

    <!-- P-004: 客户详情页直达新增消费 -->
    <CostFormDialog
      v-model="costDialogVisible"
      :initial-customer-id="Number(id)"
      @saved="onCostSaved"
    />
  </div>
</template>

<style scoped>
.customer-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.back-bar {
  display: flex;
}
.summary-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.summary-card {
  border-radius: 12px;
}
.summary-card :deep(.el-card__body) {
  padding: 16px 20px;
}
.summary-label {
  font-size: 13px;
  color: var(--el-text-color-secondary, #909399);
  margin-bottom: 6px;
}
.summary-value {
  font-size: 22px;
  font-weight: 600;
  color: var(--el-text-color-primary, #303133);
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
.card-header .title-count {
  font-size: 13px;
  font-weight: 400;
  color: var(--el-text-color-secondary, #909399);
  margin-left: 4px;
}
.timeline {
  padding-left: 4px;
}
.timeline-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.timeline-pet {
  font-weight: 600;
  color: var(--el-text-color-primary, #303133);
}
.timeline-amount {
  font-weight: 600;
  color: var(--el-color-danger, #f56c6c);
  margin-left: auto;
}
.timeline-note {
  margin-top: 4px;
  font-size: 13px;
  color: var(--el-text-color-secondary, #909399);
  white-space: pre-wrap;
  word-break: break-word;
}
.timeline-empty {
  padding: 16px 0;
  text-align: center;
  color: var(--el-text-color-secondary, #909399);
}
.timeline-more {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}
.el-table :deep(.el-table__row) {
  cursor: pointer;
}
</style>
