<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCustomerStore } from '@/stores/customerStore'

const router = useRouter()
const store = useCustomerStore()

const searchInput = ref('')
const dialogVisible = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const form = reactive({ name: '', phone: '', note: '' })
const formRef = ref(null)

const rules = {
  name: [{ required: true, message: '请输入客户姓名', trigger: 'blur' }],
}

onMounted(async () => {
  searchInput.value = store.q
  await store.fetchList()
})

async function onSearch() {
  store.setQuery(searchInput.value.trim())
  await store.fetchList()
}

function onPageChange(p) {
  store.setPage(p)
  store.fetchList()
}

function resetForm() {
  Object.assign(form, { name: '', phone: '', note: '' })
  editingId.value = null
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, { name: row.name, phone: row.phone || '', note: row.note || '' })
  dialogVisible.value = true
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    const payload = { name: form.name.trim(), phone: form.phone.trim() || null, note: form.note || null }
    try {
      if (editingId.value) {
        await store.update(editingId.value, payload)
        ElMessage.success('已更新')
      } else {
        await store.create(payload)
        ElMessage.success('已新增')
      }
      dialogVisible.value = false
      resetForm()
      await store.fetchList()
    } catch (err) {
      if (err?.status === 409 && err.detail?.detail === 'phone_exists') {
        const existingId = err.detail.existing_id
        try {
          await ElMessageBox.confirm(
            `该手机号已绑定客户 #${existingId}，是否查看？`,
            '手机号冲突',
            { confirmButtonText: '查看', cancelButtonText: '取消', type: 'warning' }
          )
          dialogVisible.value = false
          router.push(`/customers/${existingId}`)
        } catch {
          /* user cancelled */
        }
      } else if (err?.status !== undefined) {
        ElMessage.error('保存失败')
      }
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除客户「${row.name}」？关联的宠物和花费记录会一并删除。`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    return
  }
  await store.remove(row.id)
  ElMessage.success('已删除')
  if (store.items.length === 1 && store.page > 1) store.setPage(store.page - 1)
  await store.fetchList()
}

function viewDetail(row) {
  router.push(`/customers/${row.id}`)
}
</script>

<template>
  <div class="customer-list">
    <div class="toolbar">
      <el-input
        v-model="searchInput"
        placeholder="搜姓名 / 手机号"
        clearable
        class="search"
        :prefix-icon="'Search'"
        @keyup.enter="onSearch"
        @clear="onSearch"
      />
      <el-button type="primary" @click="onSearch">搜索</el-button>
      <div class="grow" />
      <el-button type="primary" :icon="'Plus'" @click="openCreate">新增客户</el-button>
    </div>

    <el-table
      v-loading="store.loading"
      :data="store.items"
      stripe
      class="table"
      empty-text="暂无客户，点右上角新增"
      @row-click="viewDetail"
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="姓名" min-width="120" />
      <el-table-column prop="phone" label="手机号" min-width="140">
        <template #default="{ row }">{{ row.phone || '-' }}</template>
      </el-table-column>
      <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ row.note || '-' }}</template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 19) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button size="small" @click.stop="viewDetail(row)">详情</el-button>
          <el-button size="small" type="primary" @click.stop="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click.stop="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="store.total"
        :page-size="store.pageSize"
        :current-page="store.page"
        @current-change="onPageChange"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑客户' : '新增客户'"
      width="480px"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" maxlength="50" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" maxlength="20" placeholder="选填，应用层校验唯一" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="3" />
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
.customer-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}
.toolbar .search {
  width: 280px;
}
.toolbar .grow {
  flex: 1;
}
.table :deep(.el-table__row) {
  cursor: pointer;
}
.pagination {
  display: flex;
  justify-content: flex-end;
}
</style>
