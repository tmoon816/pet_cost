<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { createPet, updatePet, getPet } from '@/api/pets'

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
    { required: true, message: '请输入所属客户ID', trigger: 'blur' },
    { type: 'number', min: 1, message: '请输入有效的客户ID', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入宠物名称', trigger: 'blur' },
    { min: 1, max: 50, message: '名称长度在1到50个字符', trigger: 'blur' }
  ]
}

// 物种/性别选项：value 用英文 code，与 CustomerDetail/PetDetail 已有约定一致
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
      // payload 与后端 PetCreate / PetUpdate schema 完全一致（snake_case）
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
      // http 拦截器已弹 ElMessage.error，这里不再重复
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
      <el-form-item label="所属客户ID" prop="customer_id">
        <el-input-number
          v-model.number="form.customer_id"
          placeholder="请输入客户ID"
          :min="1"
          style="width: 100%;"
          :disabled="!!defaultCustomerId"
        />
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
