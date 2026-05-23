<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { createPet, updatePet, getPet } from '@/api/pets'
import { listCustomers, getCustomer } from '@/api/customers'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  editId: { type: Number, default: null },
  defaultCustomerId: { type: Number, default: null }
})
const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const form = ref({
  customer_id: props.defaultCustomerId || null,
  name: '',
  species: '',
  breed: '',
  gender: '',
  birthday: null,
  note: ''
})

const rules = {
  customer_id: [
    { required: true, message: '请选择主人', trigger: 'change' },
    { type: 'number', min: 1, message: '请选择有效的主人', trigger: 'change' }
  ],
  name: [
    { required: true, message: '请输入宠物名称', trigger: 'blur' },
    { min: 1, max: 50, message: '名称长度在1到50个字符', trigger: 'blur' }
  ]
}

const speciesOptions = [
  { label: '犬', value: 'dog' },
  { label: '猫', value: 'cat' },
  { label: '仓鼠', value: 'hamster' },
  { label: '兔子', value: 'rabbit' },
  { label: '鹦鹉', value: 'bird' },
  { label: '其他', value: 'other' }
]
const genderOptions = [
  { label: '公', value: 'male' },
  { label: '母', value: 'female' },
  { label: '未知', value: 'unknown' }
]

const loading = ref(false)
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 主人远程搜索：el-select remote。结果带姓名 + 手机号便于识别。
// editId / defaultCustomerId 场景下需要预先把当前主人塞进去，否则 select 显示空白。
const customerOptions = ref([])
const customerSearchLoading = ref(false)

async function searchCustomers(q) {
  customerSearchLoading.value = true
  try {
    const res = await listCustomers({ q: q || undefined, page: 1, page_size: 20 })
    customerOptions.value = res.items.map((c) => ({
      id: c.id,
      label: c.phone ? `${c.name} · ${c.phone}` : c.name,
    }))
  } catch {
    customerOptions.value = []
  } finally {
    customerSearchLoading.value = false
  }
}

async function ensureCustomerOption(id) {
  if (!id) return
  if (customerOptions.value.some((o) => o.id === id)) return
  try {
    const c = await getCustomer(id)
    customerOptions.value.unshift({
      id: c.id,
      label: c.phone ? `${c.name} · ${c.phone}` : c.name,
    })
  } catch { /* ignore */ }
}

const resetForm = () => {
  form.value = {
    customer_id: props.defaultCustomerId || null,
    name: '',
    species: '',
    breed: '',
    gender: '',
    birthday: null,
    note: ''
  }
  customerOptions.value = []
  formRef.value?.resetFields()
}

watch(() => visible.value, async (val) => {
  if (!val) {
    resetForm()
    return
  }
  // 打开时预热一份初始客户列表，方便点开就能看到
  await searchCustomers('')
  if (props.editId) {
    await fetchPet()
  } else if (props.defaultCustomerId) {
    await ensureCustomerOption(props.defaultCustomerId)
  }
})

watch(() => props.defaultCustomerId, (val) => {
  if (val) form.value.customer_id = val
}, { immediate: true })

const fetchPet = async () => {
  try {
    const data = await getPet(props.editId)
    form.value = {
      customer_id: data.customer_id,
      name: data.name,
      species: data.species || '',
      breed: data.breed || '',
      gender: data.gender || '',
      birthday: data.birthday || null,
      note: data.note || ''
    }
    await ensureCustomerOption(data.customer_id)
  } catch (e) {
    ElMessage.error('获取宠物信息失败')
    visible.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.warning('请检查表单必填项')
      return
    }
    loading.value = true
    try {
      const payload = {
        customer_id: form.value.customer_id,
        name: form.value.name.trim(),
        species: form.value.species || null,
        breed: form.value.breed?.trim() || null,
        gender: form.value.gender || null,
        birthday: form.value.birthday || null,
        note: form.value.note || null
      }

      if (props.editId) {
        await updatePet(props.editId, payload)
        ElMessage.success('更新成功')
      } else {
        await createPet(payload)
        ElMessage.success('创建成功')
      }
      emit('success')
      visible.value = false
    } catch (e) {
      // http 拦截器已弹 ElMessage.error
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="editId ? '编辑宠物' : '新增宠物'"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      style="padding-right: 24px;"
    >
      <el-form-item label="主人" prop="customer_id">
        <el-select
          v-model="form.customer_id"
          filterable
          remote
          :remote-method="searchCustomers"
          :loading="customerSearchLoading"
          placeholder="按姓名或手机号搜索"
          clearable
          style="width: 100%;"
          :disabled="!!defaultCustomerId"
        >
          <el-option
            v-for="c in customerOptions"
            :key="c.id"
            :label="c.label"
            :value="c.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="宠物名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入宠物名称" />
      </el-form-item>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="物种">
            <el-select v-model="form.species" placeholder="请选择物种" clearable style="width: 100%;">
              <el-option
                v-for="item in speciesOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="品种">
            <el-input v-model="form.breed" placeholder="请输入品种" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="性别">
            <el-select v-model="form.gender" placeholder="请选择性别" clearable style="width: 100%;">
              <el-option
                v-for="item in genderOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="生日">
            <el-date-picker
              v-model="form.birthday"
              type="date"
              placeholder="请选择生日"
              style="width: 100%;"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="备注">
        <el-input
          v-model="form.note"
          type="textarea"
          placeholder="请输入备注信息（可选）"
          :rows="3"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        {{ editId ? '保存修改' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>
