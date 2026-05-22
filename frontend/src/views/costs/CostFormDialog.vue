<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useCategoryStore } from '@/stores/categoryStore'
import * as petsApi from '@/api/pets'
import * as costsApi from '@/api/costs'
import * as customersApi from '@/api/customers'

function todayStr() {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  initialPetId: { type: [Number, String], default: null },
  initialCustomerId: { type: [Number, String], default: null },
  editing: { type: Object, default: null },
  lockPet: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const categoryStore = useCategoryStore()

const customers = ref([])
const recentCustomers = ref([]) // T-014: 最近 5 个有消费的客户
const customerLoading = ref(false)
const pets = ref([])
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  customer_id: null,
  pet_id: null,
  category_code: '',
  amount: '',
  occurred_on: null,
  note: '',
})

const rules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  pet_id: [{ required: true, message: '请选择宠物', trigger: 'change' }],
  category_code: [{ required: true, message: '请选择分类', trigger: 'change' }],
  amount: [
    { required: true, message: '请输入金额', trigger: 'blur' },
    {
      validator: (_, value, cb) => {
        const n = Number(value)
        if (Number.isFinite(n) && n > 0) cb()
        else cb(new Error('金额需大于 0'))
      },
      trigger: 'blur',
    },
  ],
  occurred_on: [{ required: true, message: '请选择日期', trigger: 'change' }],
}

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

async function searchCustomers(query) {
  customerLoading.value = true
  try {
    const resp = await customersApi.listCustomers({ q: query || undefined, page: 1, page_size: 50 })
    customers.value = resp.items
  } finally {
    customerLoading.value = false
  }
}

async function loadRecentCustomers() {
  // T-014：拉取最近 5 个有消费的客户用于下拉顶部快选
  try {
    const items = await customersApi.listRecentCustomers({ limit: 5 })
    recentCustomers.value = Array.isArray(items) ? items : []
  } catch {
    recentCustomers.value = []
  }
}

// T-014：合并最近 5 个 + 搜索结果，按 id 去重后最近的优先，供下拉渲染
const displayCustomers = computed(() => {
  const list = []
  const seen = new Set()
  for (const c of recentCustomers.value) {
    if (!seen.has(c.id)) {
      seen.add(c.id)
      list.push({ ...c, __recent: true })
    }
  }
  for (const c of customers.value) {
    if (!seen.has(c.id)) {
      seen.add(c.id)
      list.push({ ...c, __recent: false })
    }
  }
  return list
})

async function loadPets(customerId) {
  if (!customerId) {
    pets.value = []
    return
  }
  const resp = await petsApi.listPets({ customer_id: customerId, page: 1, page_size: 100 })
  pets.value = resp.items
}

watch(
  () => form.customer_id,
  async (newId, oldId) => {
    if (newId !== oldId) {
      await loadPets(newId)
      if (!pets.value.some((p) => p.id === form.pet_id)) {
        form.pet_id = null
      }
    }
  }
)

async function ensureCustomerInList(id) {
  if (!id) return
  if (customers.value.some((c) => c.id === id)) return
  try {
    const c = await customersApi.getCustomer(id)
    customers.value = [{ id: c.id, name: c.name, phone: c.phone }, ...customers.value]
  } catch {
    /* ignore */
  }
}

async function init() {
  await categoryStore.fetch().catch(() => {})

  if (props.editing) {
    const e = props.editing
    Object.assign(form, {
      pet_id: e.pet_id,
      category_code: e.category_code,
      amount: String(e.amount),
      occurred_on: e.occurred_on,
      note: e.note || '',
    })
    // 反查客户
    try {
      const pet = await petsApi.getPet(e.pet_id)
      form.customer_id = pet.customer_id
      await ensureCustomerInList(pet.customer_id)
      await loadPets(pet.customer_id)
    } catch {
      /* ignore */
    }
  } else if (props.initialPetId) {
    try {
      const pet = await petsApi.getPet(props.initialPetId)
      form.customer_id = pet.customer_id
      form.pet_id = pet.id
      await ensureCustomerInList(pet.customer_id)
      await loadPets(pet.customer_id)
    } catch {
      /* ignore */
    }
  } else if (props.initialCustomerId) {
    form.customer_id = Number(props.initialCustomerId)
    await ensureCustomerInList(form.customer_id)
    await loadPets(form.customer_id)
  } else {
    await searchCustomers('')
  }

  // T-014：新增场景（非编辑）下达到拉取最近 5 个客户
  if (!props.editing) {
    await loadRecentCustomers()
  }

  if (!props.editing) {
    form.occurred_on = todayStr()
  }
}

watch(visible, (v) => {
  if (v) init()
})

function reset() {
  Object.assign(form, {
    customer_id: null,
    pet_id: null,
    category_code: '',
    amount: '',
    occurred_on: null,
    note: '',
  })
  customers.value = []
  recentCustomers.value = []
  pets.value = []
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    const payload = {
      pet_id: form.pet_id,
      category_code: form.category_code,
      amount: String(form.amount),
      occurred_on: form.occurred_on,
      note: form.note?.trim() ? form.note : null,
    }
    try {
      if (props.editing) {
        await costsApi.updateCost(props.editing.id, payload)
        ElMessage.success('已更新')
      } else {
        await costsApi.createCost(payload)
        ElMessage.success('已新增')
      }
      visible.value = false
      emit('saved')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="editing ? '编辑花费' : '新增花费'"
    width="520px"
    @closed="reset"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="客户" prop="customer_id">
        <el-select
          v-model="form.customer_id"
          filterable
          remote
          :remote-method="searchCustomers"
          :loading="customerLoading"
          placeholder="搜姓名 / 手机号（顶部为最近 5 个客户）"
          style="width: 100%"
          :disabled="lockPet"
        >
          <el-option
            v-for="c in displayCustomers"
            :key="c.id"
            :label="`${c.name}${c.phone ? ' · ' + c.phone : ''}`"
            :value="c.id"
          >
            <span>{{ c.name }}{{ c.phone ? ' · ' + c.phone : '' }}</span>
            <el-tag
              v-if="c.__recent"
              size="small"
              type="success"
              effect="plain"
              style="margin-left: 8px;"
            >最近</el-tag>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="宠物" prop="pet_id">
        <el-select
          v-model="form.pet_id"
          placeholder="先选客户"
          style="width: 100%"
          :disabled="lockPet || !form.customer_id"
        >
          <el-option v-for="p in pets" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
      </el-form-item>

      <el-form-item label="分类" prop="category_code">
        <el-select v-model="form.category_code" placeholder="选择分类" style="width: 100%">
          <el-option
            v-for="c in categoryStore.list"
            :key="c.code"
            :label="c.label"
            :value="c.code"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="金额" prop="amount">
        <el-input v-model="form.amount" placeholder="单位：元，最多两位小数">
          <template #prefix>¥</template>
        </el-input>
      </el-form-item>

      <el-form-item label="发生日期" prop="occurred_on">
        <el-date-picker
          v-model="form.occurred_on"
          type="date"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="备注">
        <el-input v-model="form.note" type="textarea" :rows="2" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>
