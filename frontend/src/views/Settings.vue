<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCategoryStore } from '@/stores/categoryStore'

const categoryStore = useCategoryStore()

const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive({ code: '', label: '', sort_order: 0 })
const formRef = ref(null)
const submitting = ref(false)

const rules = {
  code: [
    { required: true, message: '请输入 code', trigger: 'blur' },
    { pattern: /^[a-z0-9_-]{1,30}$/i, message: '只能用字母/数字/下划线/中划线，最长 30', trigger: 'blur' },
  ],
  label: [{ required: true, message: '请输入显示名', trigger: 'blur' }],
}

onMounted(() => {
  categoryStore.fetch(true)
})

function openCreate() {
  editing.value = null
  Object.assign(form, { code: '', label: '', sort_order: 0 })
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  Object.assign(form, { code: row.code, label: row.label, sort_order: row.sort_order })
  dialogVisible.value = true
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (editing.value) {
        await categoryStore.update(editing.value.code, {
          label: form.label.trim(),
          sort_order: Number(form.sort_order) || 0,
        })
        ElMessage.success('已更新')
      } else {
        await categoryStore.create({
          code: form.code.trim(),
          label: form.label.trim(),
          sort_order: Number(form.sort_order) || 0,
        })
        ElMessage.success('已新增')
      }
      dialogVisible.value = false
    } catch (err) {
      if (err?.status === 409 && err.detail?.detail === 'category_code_exists') {
        ElMessage.error(`code "${err.detail.code}" 已存在`)
      }
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除分类「${row.label}」？被花费记录引用时无法删除。`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await categoryStore.remove(row.code)
    ElMessage.success('已删除')
  } catch (err) {
    if (err?.status === 409 && err.detail?.detail === 'category_in_use') {
      ElMessage.error(`分类「${row.label}」已被花费记录引用，无法删除`)
    }
  }
}
</script>

<template>
  <div class="settings-page">
    <el-card class="card">
      <template #header>
        <div class="card-header">
          <span class="title">花费分类字典</span>
          <el-button type="primary" :icon="'Plus'" @click="openCreate">新增分类</el-button>
        </div>
      </template>

      <el-table v-loading="categoryStore.loading" :data="categoryStore.list" stripe>
        <el-table-column prop="code" label="Code" width="160" />
        <el-table-column prop="label" label="显示名" min-width="160" />
        <el-table-column prop="sort_order" label="排序" width="120" />
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <p class="hint">提示：sort_order 越小越靠前；code 不可修改，删除时若已有花费记录引用会被拒绝。</p>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑分类' : '新增分类'"
      width="420px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="Code" prop="code">
          <el-input v-model="form.code" :disabled="!!editing" maxlength="30" />
        </el-form-item>
        <el-form-item label="显示名" prop="label">
          <el-input v-model="form.label" maxlength="30" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.settings-page {
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
.hint {
  margin-top: 12px;
  color: #909399;
  font-size: 13px;
}
</style>
