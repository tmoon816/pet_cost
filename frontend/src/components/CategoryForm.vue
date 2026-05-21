<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useCategoryStore } from '@/stores/categoryStore'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  editCode: { type: String, default: null }
})
const emit = defineEmits(['update:modelValue', 'success'])

const categoryStore = useCategoryStore()
const formRef = ref()
const form = ref({
  code: '',
  label: '',
  sort_order: 0
})
const loading = ref(false)

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
  sort_order: [
    { type: 'number', min: 0, message: '排序值必须大于等于0', trigger: 'blur' }
  ]
}

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const resetForm = () => {
  form.value = { code: '', label: '', sort_order: 0 }
  formRef.value?.resetFields()
}

const fetchCategory = () => {
  // 直接从 store 取（list 接口已加载），避免单独的 getCategory 调用
  const target = categoryStore.list.find((c) => c.code === props.editCode)
  if (!target) {
    ElMessage.error('未找到该分类，请刷新页面后重试')
    visible.value = false
    return
  }
  form.value = {
    code: target.code,
    label: target.label,
    sort_order: target.sort_order ?? 0
  }
}

watch(() => visible.value, (val) => {
  if (!val) {
    resetForm()
  } else if (props.editCode) {
    fetchCategory()
  }
})

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.warning('请检查表单必填项')
      return
    }
    loading.value = true
    try {
      if (props.editCode) {
        // 编辑只能改 label / sort_order，code 是主键
        await categoryStore.update(props.editCode, {
          label: form.value.label.trim(),
          sort_order: Number(form.value.sort_order) || 0
        })
        ElMessage.success('更新成功')
      } else {
        await categoryStore.create({
          code: form.value.code.trim(),
          label: form.value.label.trim(),
          sort_order: Number(form.value.sort_order) || 0
        })
        ElMessage.success('创建成功')
      }
      emit('success')
      visible.value = false
    } catch (e) {
      // 拦截器兜底
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="editCode ? '编辑服务项目' : '新增服务项目'"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      style="padding-right: 24px;"
    >
      <el-form-item label="编码" prop="code">
        <el-input
          v-model="form.code"
          placeholder="英文小写，如 grooming"
          :disabled="!!editCode"
        />
        <div v-if="!editCode" style="font-size: 12px; color: #909399; margin-top: 4px;">
          仅小写字母/数字/下划线；创建后不可修改
        </div>
      </el-form-item>
      <el-form-item label="显示名称" prop="label">
        <el-input v-model="form.label" placeholder="中文显示名，如 洗护美容" />
      </el-form-item>
      <el-form-item label="排序" prop="sort_order">
        <el-input-number
          v-model.number="form.sort_order"
          :min="0"
          style="width: 100%;"
          placeholder="数值越小越靠前"
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
