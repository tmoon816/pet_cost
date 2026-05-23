<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCustomerStore } from '@/stores/customerStore'
import * as customersApi from '@/api/customers'
import CustomerImportDialog from '@/views/customers/CustomerImportDialog.vue'

const router = useRouter()
const store = useCustomerStore()

const searchInput = ref('')
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const form = reactive({ name: '', phone: '', note: '' })
const formRef = ref(null)

const rules = {
  name: [
    { required: true, message: '请输入客户姓名', trigger: 'blur' },
    { max: 50, message: '姓名不超过 50 字符', trigger: 'blur' },
  ],
  phone: [
    {
      validator: (_rule, value, callback) => {
        const v = (value || '').trim()
        if (!v) return callback()
        if (!/^1\d{10}$/.test(v)) {
          return callback(new Error('请输入 11 位手机号（以 1 开头）'))
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

// debounce 300ms实时搜索：输入变动 300ms 后触发查询；清空后恢复全部
let searchTimer = null
function triggerSearch() {
  const next = searchInput.value.trim()
  if (next === store.q) return
  store.setQuery(next)
  store.fetchList()
}
watch(searchInput, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(triggerSearch, 300)
})
onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer)
})

onMounted(async () => {
  searchInput.value = store.q
  await store.fetchList()
})

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

// T-015：按「累计消费」排序切换。连击：默认 → desc → asc → 默认。
function toggleSortByAmount() {
  if (store.sortBy !== 'total_amount') {
    store.setSort('total_amount') // desc
  } else if (store.sortDir === 'desc') {
    store.setSort('total_amount') // asc
  } else {
    store.setSort(null) // 恢复默认
  }
  store.fetchList()
}

async function handleExport() {
  try {
    const blob = await customersApi.exportCustomers({
      q: store.q || undefined,
      sort_by: store.sortBy || undefined,
      sort_dir: store.sortBy ? store.sortDir : undefined,
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const d = new Date()
    a.download = `customers_${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出完成')
  } catch {
    ElMessage.error('导出失败')
  }
}
const amountSortLabel = computed(() => {
  if (store.sortBy !== 'total_amount') return '按金额排序'
  return store.sortDir === 'desc' ? '金额 ↓' : '金额 ↑'
})
function formatAmount(v) {
  const n = Number(v || 0)
  return Number.isFinite(n) ? n.toFixed(2) : '0.00'
}

// P-006: 客户类型徽标。后端给 customer_type，没有就根据 has_cost 兜底为新/老客二分。
function customerTagLabel(type, hasCost) {
  if (type === 'vip') return 'VIP'
  if (type === 'returning') return '回头客'
  if (type === 'first_visit') return '新客'
  return hasCost ? '回头客' : '新客'
}
function customerTagType(type, hasCost) {
  if (type === 'vip') return 'warning'
  if (type === 'returning') return 'success'
  if (type === 'first_visit') return 'info'
  return hasCost ? 'success' : 'info'
}
</script>

<template>
  <div class="customer-list">
    <div class="toolbar">
      <el-input
        v-model="searchInput"
        placeholder="搜姓名 / 手机号（实时）"
        clearable
        class="search"
        :prefix-icon="'Search'"
      />
      <el-button @click="toggleSortByAmount">{{ amountSortLabel }}</el-button>
      <el-button @click="importDialogVisible = true">
        <el-icon><Upload /></el-icon>
        批量导入
      </el-button>
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon>
        导出 CSV
      </el-button>
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
      <el-table-column label="类型" width="110" align="center">
        <template #header>
          <span class="header-with-tip">
            类型
            <el-tooltip placement="top">
              <template #content>
                按消费记录条数划分：<br />
                · 新客 = 0 条<br />
                · 回头客 = 1 ~ 4 条<br />
                · VIP = ≥ 5 条
              </template>
              <el-icon class="tip-icon"><InfoFilled /></el-icon>
            </el-tooltip>
          </span>
        </template>
        <template #default="{ row }">
          <el-tag
            :type="customerTagType(row.customer_type, row.has_cost)"
            size="small"
            effect="plain"
          >
            {{ customerTagLabel(row.customer_type, row.has_cost) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="手机号" min-width="140">
        <template #default="{ row }">{{ row.phone || '-' }}</template>
      </el-table-column>
      <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ row.note || '-' }}</template>
      </el-table-column>
      <el-table-column label="累计消费" width="140" align="right">
        <template #default="{ row }">
          <span style="color: #f56c6c; font-weight: 600;">¥ {{ formatAmount(row.total_amount) }}</span>
        </template>
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
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" maxlength="11" placeholder="选填，11 位手机号" />
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

    <CustomerImportDialog
      v-model="importDialogVisible"
      @imported="store.fetchList()"
    />
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
.header-with-tip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.tip-icon {
  color: var(--text-muted, #909399);
  cursor: help;
  font-size: 14px;
}
.tip-icon:hover {
  color: var(--primary, #5a8dee);
}
</style>
