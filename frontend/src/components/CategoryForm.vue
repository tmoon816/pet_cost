<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { createCategory, updateCategory, getCategory } from '@/api/categories'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  editCode: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const form = ref({
  code: '',
  label: '',
  sortOrder: 1,
  icon: '',
  status: true
})

const rules = {
  code: [
    { required: true, message: '请输入分类编码', trigger: 'blur' },
    { min: 1, max: 30, message: '编码长度在1到30个字符', trigger: 'blur' },
    { pattern: /^[a-z0-9_]+$/, message: '编码只能包含小写字母、数字和下划线', trigger: 'blur' }
  ],
  label: [
    { required: true, message: '请输入显示名称', trigger: 'blur' },
    { min: 1, max: 30, message: '名称长度在1到30个字符', trigger: 'blur' }
  ],
  sortOrder: [
    { type: 'number', min: 0, message: '排序值必须大于等于0', trigger: 'blur' }
  ]
}

const iconOptions = ['🥫', '🏥', '💇', '🧻', '🎾', '🛡️', '🏠', '📦', '🍖', '💊', '🧼', '🎁', '🐶', '🐱', '🐹', '🐰']
const loading = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const resetForm = () => {
  form.value = {
    code: '',
    label: '',
    sortOrder: 1,
    icon: '',
    status: true
  }
  formRef.value?.resetFields()
}

watch(() => visible.value, (val) => {
  if (!val) {
    resetForm()
  } else if (props.editCode) {
    fetchCategory()
  }
})

const fetchCategory = async () => {
  try {
    const data = await getCategory(props.editCode)
    form.value = {
      code: data.code,
      label: data.label,
      sortOrder: data.sortOrder || 1,
      icon: data.icon || '',
      status: data.status !== false
    }
  } catch (e) {
    ElMessage.error('获取分类信息失败')
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
      if (!submitData.icon) delete submitData.icon

      if (props.editCode) {
        // 编辑时不能修改编码
        const { code, ...updateData } = submitData
        await updateCategory(props.editCode, updateData)
        ElMessage.success('更新成功')
      } else {
        await createCategory(submitData)
        ElMessage.success('创建成功')
      }
      emit('success')
      visible.value = false
    } catch (e) {
      if (e?.response?.data?.detail === 'category_code_exists') {
        ElMessage.error('该分类编码已存在')
      } else {
        ElMessage.error(e?.response?.data?.detail || '操作失败')
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
    :title="editCode ? '编辑分类' : '新增分类'"
    width="550px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      style="padding-right: 24px;"
    >
      <el-form-item label="分类编码" prop="code">
        <el-input
          v-model="form.code"
          placeholder="请输入分类编码（英文小写，如food）"
          :disabled="editCode"
        />
        <div v-if="!editCode" style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
          编码只能包含小写字母、数字和下划线，创建后无法修改
        </div>
      </el-form-item>
      <el-form-item label="显示名称" prop="label">
        <el-input v-model="form.label" placeholder="请输入显示名称（中文，如食品）" />
      </el-form-item>
      <el-form-item label="图标">
        <el-select v-model="form.icon" placeholder="请选择分类图标" style="width: 100%;">
          <el-option v-for="icon in iconOptions" :key="icon" :label="icon" :value="icon">
            <span style="font-size: 20px;">{{ icon }}</span> {{ icon }}
          </el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="排序" prop="sortOrder">
        <el-input-number
          v-model.number="form.sortOrder"
          :min="0"
          style="width: 100%;"
          placeholder="数值越小排序越靠前"
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-switch
          v-model="form.status"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        {{ editCode ? '保存修改' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>
