<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { createPet, updatePet, getPet } from '@/api/pets'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  editId: {
    type: Number,
    default: null
  },
  defaultCustomerId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const form = ref({
  customerId: props.defaultCustomerId || '',
  name: '',
  species: '',
  breed: '',
  gender: '',
  birthday: null,
  weight: '',
  healthRecord: '',
  note: ''
})

const rules = {
  customerId: [
    { required: true, message: '请输入所属客户ID', trigger: 'blur' },
    { type: 'number', min: 1, message: '请输入有效的客户ID', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入宠物名称', trigger: 'blur' },
    { min: 1, max: 50, message: '名称长度在1到50个字符', trigger: 'blur' }
  ]
}

const genderOptions = [
  { label: '公', value: '公' },
  { label: '母', value: '母' },
  { label: '未知', value: '未知' }
]
const speciesOptions = [
  { label: '狗', value: '狗' },
  { label: '猫', value: '猫' },
  { label: '仓鼠', value: '仓鼠' },
  { label: '兔子', value: '兔子' },
  { label: '鹦鹉', value: '鹦鹉' },
  { label: '其他', value: '其他' }
]
const loading = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const resetForm = () => {
  form.value = {
    customerId: props.defaultCustomerId || '',
    name: '',
    species: '',
    breed: '',
    gender: '',
    birthday: null,
    weight: '',
    healthRecord: '',
    note: ''
  }
  formRef.value?.resetFields()
}

watch(() => visible.value, (val) => {
  if (!val) {
    resetForm()
  } else if (props.editId) {
    fetchPet()
  }
})

watch(() => props.defaultCustomerId, (val) => {
  form.value.customerId = val
}, { immediate: true })

const fetchPet = async () => {
  try {
    const data = await getPet(props.editId)
    form.value = {
      customerId: data.customerId,
      name: data.name,
      species: data.species || '',
      breed: data.breed || '',
      gender: data.gender || '',
      birthday: data.birthday ? new Date(data.birthday) : null,
      weight: data.weight || '',
      healthRecord: data.healthRecord || '',
      note: data.note || ''
    }
  } catch (e) {
    ElMessage.error('获取宠物信息失败')
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
      // 清理空字段
      Object.keys(submitData).forEach(key => {
        if (!submitData[key] && submitData[key] !== 0) delete submitData[key]
      })

      if (props.editId) {
        await updatePet(props.editId, submitData)
        ElMessage.success('更新成功')
      } else {
        await createPet(submitData)
        ElMessage.success('创建成功')
      }
      emit('success')
      visible.value = false
    } catch (e) {
      ElMessage.error(e?.response?.data?.detail || '操作失败')
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
      <el-form-item label="所属客户ID" prop="customerId">
        <el-input-number
          v-model.number="form.customerId"
          placeholder="请输入客户ID"
          :min="1"
          style="width: 100%;"
          :disabled="defaultCustomerId"
        />
      </el-form-item>
      <el-form-item label="宠物名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入宠物名称" />
      </el-form-item>
      <el-row :gutter="20">
        <el-col span="12">
          <el-form-item label="物种">
            <el-select v-model="form.species" placeholder="请选择物种" style="width: 100%;">
              <el-option
                v-for="item in speciesOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col span="12">
          <el-form-item label="品种">
            <el-input v-model="form.breed" placeholder="请输入品种" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col span="12">
          <el-form-item label="性别">
            <el-select v-model="form.gender" placeholder="请选择性别" style="width: 100%;">
              <el-option
                v-for="item in genderOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col span="12">
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
      <el-form-item label="体重">
        <el-input v-model="form.weight" placeholder="请输入体重，如：12kg" />
      </el-form-item>
      <el-form-item label="健康记录">
        <el-input
          v-model="form.healthRecord"
          type="textarea"
          placeholder="请输入健康记录，如：疫苗已接种，无过敏史等"
          :rows="2"
        />
      </el-form-item>
      <el-form-item label="备注">
        <el-input
          v-model="form.note"
          type="textarea"
          placeholder="请输入备注信息（可选）"
          :rows="2"
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
