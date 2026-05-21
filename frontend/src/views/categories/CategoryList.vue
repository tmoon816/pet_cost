<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElSwitch } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { listCategories, createCategory, updateCategory, deleteCategory } from '@/api/categories'
import CategoryForm from '@/components/CategoryForm.vue'

const categories = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editCode = ref(null)

const categoryIcons = {
  '食品': '🥫',
  '医疗': '🏥',
  '美容': '💇',
  '用品': '🧻',
  '玩具': '🎾',
  '保险': '🛡️',
  '寄养': '🏠',
  '其他': '📦'
}

const fetchCategories = async () => {
  loading.value = true
  try {
    const res = await listCategories()
    categories.value = res.map(item => ({
      ...item,
      icon: item.icon || categoryIcons[item.label] || '📦',
      totalUsed: Number(item.totalUsed || 0)
    })).sort((a, b) => a.sortOrder - b.sortOrder)
  } catch (e) {
    ElMessage.error('获取分类列表失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  editCode.value = null
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editCode.value = row.code
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除分类「${row.label}」吗？如果该分类已被花费记录使用则无法删除！`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteCategory(row.code)
      ElMessage.success('删除成功')
      fetchCategories()
    } catch (e) {
      ElMessage.error('该分类已被使用，无法删除')
    }
  }).catch(() => {})
}

const handleStatusChange = async (row, status) => {
  try {
    await updateCategory(row.code, { status })
    ElMessage.success(`已${status ? '启用' : '禁用'}分类`)
  } catch (e) {
    ElMessage.error('状态修改失败')
    row.status = !status
  }
}

const handleFormSuccess = () => {
  dialogVisible.value = false
  fetchCategories()
}

onMounted(() => {
  fetchCategories()
})
</script>

<template>
  <div class="category-list-page">
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h2 style="margin: 0; font-size: 24px;">消费分类</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增分类
      </el-button>
    </div>

    <div class="category-grid" v-loading="loading">
      <div v-if="categories.length === 0 && !loading" class="empty-state">
        <div style="font-size: 64px; margin-bottom: 20px;">🏷️</div>
        <p class="empty-title">暂无分类</p>
        <p class="empty-desc">点击右上角「新增分类」按钮添加第一个分类吧~</p>
        <el-button type="primary" @click="handleAdd" style="margin-top: 20px;">
          <el-icon><Plus /></el-icon>
          立即新增
        </el-button>
      </div>

      <el-card
        v-for="category in categories"
        :key="category.code"
        shadow="hover"
        class="category-card"
        :class="{ disabled: !category.status }"
      >
        <div class="category-header">
          <div class="category-icon">{{ category.icon }}</div>
          <div class="category-info">
            <h3>{{ category.label }}</h3>
            <p class="category-code">编码：{{ category.code }}</p>
          </div>
          <div class="category-status">
            <el-switch
              v-model="category.status"
              @change="handleStatusChange(category, $event)"
              :active-text="category.status ? '已启用' : '已禁用'"
              inline-prompt
            />
          </div>
        </div>
        <div class="category-stats">
          <div class="stat-item">
            <span class="label">总消费</span>
            <span class="value text-danger">¥ {{ category.totalUsed.toFixed(2) }}</span>
          </div>
          <div class="stat-item">
            <span class="label">排序</span>
            <span class="value">{{ category.sortOrder }}</span>
          </div>
        </div>
        <div class="category-actions">
          <el-button size="small" @click="handleEdit(category)" :disabled="!category.status">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(category)">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </el-card>
    </div>

    <CategoryForm
      v-model="dialogVisible"
      :edit-code="editCode"
      @success="handleFormSuccess"
    />
  </div>
</template>

<style scoped>
.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
.category-card {
  transition: all 0.2s ease;
}
.category-card.disabled {
  opacity: 0.6;
  background: var(--bg-secondary) !important;
}
.category-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.category-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: rgba(74, 222, 128, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
}
.category-info {
  flex: 1;
}
.category-info h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  color: var(--text-primary);
}
.category-code {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}
.category-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-item .label {
  font-size: 12px;
  color: var(--text-muted);
}
.stat-item .value {
  font-size: 16px;
  font-weight: 600;
}
.category-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 20px;
  color: var(--text-muted);
}
.empty-title {
  font-size: 18px;
  font-weight: 500;
  margin: 20px 0 10px;
  color: var(--text-secondary);
}
.empty-desc {
  font-size: 14px;
  color: var(--text-muted);
}
@media (max-width: 768px) {
  .category-grid {
    grid-template-columns: 1fr;
  }
}
</style>
