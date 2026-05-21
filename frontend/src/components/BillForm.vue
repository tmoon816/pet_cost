<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { createCost, updateCost, getCost } from '@/api/costs'
import { useCategoryStore } from '@/stores/categoryStore'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  editId: {
    type: Number,
    default: null
  },
  defaultPetId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])
const categoryStore = useCategoryStore()

const formRef = ref()
const form = ref({
  type: '支出',
  petId: props.defaultPetId || '',
  categoryCode: '',
  amount: '',
  occurredOn: new Date(),
  note: '',
  payType: '微信支付'
})

const rules = {
  petId: [
    { required: true, message: '请输入宠物ID', trigger: 'blur' },
    { type: 'number', min: 1, message: '请输入有效的宠物ID', trigger: 'blur' }
  ],
  categoryCode: [
    { required: true, message: '请选择消费分类', trigger: 'blur' }
  ],
  amount: [
    { required: true, message: '请输入花费金额', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '金额必须大于0', trigger: 'blur' }
  ],
  occurredOn: [
    { required: true, message: '请选择发生日期', trigger: 'blur' }
  ]
}

const payTypes = ['微信支付', '支付宝', '现金', '银行卡', '其他']
const loading = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const resetForm = () => {
  form.value = {
    type: '支出',
    petId: props.defaultPetId || '',
    categoryCode: '',
    amount: '',
    occurredOn: new Date(),
    note: '',
    payType: '微信支付'
  }
  formRef.value?.resetFields()
}

onMounted(() => {
  if (categoryStore.categories.length === 0) {
    categoryStore.fetchCategories()
  }
})

watch(() => visible.value, (val) => {
  if (!val) {
    resetForm()
  } else if (props.editId) {
    fetchCost()
  }
})

watch(() => props.defaultPetId, (val) => {
  form.value.petId = val
}, { immediate: true })

const fetchCost = async () => {
  try {
    const data = await getCost(props.editId)
    form.value = {
      type: data.type || '支出',
      petId: data.petId,
      categoryCode: data.categoryCode,
      amount: parseFloat(data.amount),
      occurredOn: new Date(data.occurredOn),
      note: data.note || '',
      payType: data.payType || '微信支付'
    }
  } catch (e) {
    ElMessage.error('获取账单信息失败')
    visible.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const submitData = { ...form.value }
      if (!submitData.note) delete submitData.note

      if (props.editId) {
        await updateCost(props.editId, submitData)
        ElMessage.success('更新成功')
      } else {
        await createCost(submitData)
        ElMessage.success('创建成功')
      }
      emit('success')
      visible.value = false
    } catch (e) {
      const detail = e?.response?.data?.detail
      if (detail === '所属宠物不存在') {
        ElMessage.error('该宠物ID不存在，请检查后重试')
      } else if (detail === '分类不存在') {
        ElMessage.error('该花费分类不存在，请检查后重试')
      } else {
        ElMessage.error(detail || '操作失败')
      }
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="editId ? '编辑账单' : '新增账单'"
    width="550px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      style="padding-right: 24px;"
    >
      <el-form-item label="类型" prop="type">
        <el-radio-group v-model="form.type">
          <el-radio label="支出">支出</el-radio>
          <el-radio label="收入">收入</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="宠物ID" prop="petId">
        <el-input-number
          v-model.number="form.petId"
          placeholder="请输入宠物ID"
          :min="1"
          style="width: 100%;"
          :disabled="defaultPetId"
        />
      </el-form-item>
      <el-form-item label="分类" prop="categoryCode">
        <el-select
          v-model="form.categoryCode"
          placeholder="请选择消费分类"
          style="width: 100%;"
          v-loading="categoryStore.loading"
        >
          <el-option
            v-for="item in categoryStore.categories"
            :key="item.code"
            :label="item.label"
            :value="item.code"
          />
        </el-select>
      </el-form-item>
      <el-row :gutter="20">
        <el-col span="12">
          <el-form-item label="金额" prop="amount">
            <el-input
              v-model.number="form.amount"
              type="number"
              placeholder="请输入金额"
              step="0.01"
              prefix-icon="¥"
            />
          </el-form-item>
        </el-col>
        <el-col span="12">
          <el-form-item label="支付方式">
            <el-select v-model="form.payType" placeholder="请选择支付方式" style="width: 100%;">
              <el-option v-for="type in payTypes" :key="type" :label="type" :value="type" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="发生日期" prop="occurredOn">
        <el-date-picker
          v-model="form.occurredOn"
          type="date"
          placeholder="请选择发生日期"
          style="width: 100%;"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
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
