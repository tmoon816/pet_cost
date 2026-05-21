<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useCategoryStore } from '@/stores/categoryStore'
import CategoryForm from '@/components/CategoryForm.vue'

const categoryStore = useCategoryStore()
const dialogVisible = ref(false)
const editCode = ref(null)

// 仅前端 derived 的 emoji 映射（不入库）
const ICON_MAP = {
  grooming: '💇',
  medical:  '🏥',
  boarding: '🏠',
  training: '🎓',
  retail:   '🛒',
  food:     '🥫',
  toy:      '🎾',
  other:    '📦'
}
const iconOf = (code) => ICON_MAP[code] || '🏷️'

const categories = computed(() => categoryStore.list || [])
const loading = computed(() => categoryStore.loading)

const handleAdd = () => {
  editCode.value = null
  dialogVisible.value = true
}
const handleEdit = (row) => {
  editCode.value = row.code
  dialogVisible.value = true
}
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除服务项目「${row.label}」吗？如果已有订单使用此分类则无法删除。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await categoryStore.remove(row.code)
    ElMessage.success('已删除')
  } catch (e) {
    // 拦截器兜底（409/404 等会弹消息）
  }
}
const handleFormSuccess = () => {
  dialogVisible.value = false
  categoryStore.fetch(true)
}

onMounted(() => {
  categoryStore.fetch(true)
})
</script>

<template>
  <div class="category-list-page">
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h2 style="margin: 0; font-size: 24px;">服务项目</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增服务项目
      </el-button>
    </div>

    <div class="category-grid" v-loading="loading">
      <div v-if="categories.length === 0 && !loading" class="empty-state">
        <div style="font-size: 64px; margin-bottom: 20px;">🏷️</div>
        <p class="empty-title">暂无服务项目</p>
        <p class="empty-desc">点击右上角「新增服务项目」按钮添加宠物店提供的服务类型</p>
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
      >
        <div class="category-header">
          <div class="category-icon">{{ iconOf(category.code) }}</div>
          <div class="category-basic">
            <h3>{{ category.label }}</h3>
            <div class="category-meta">
              <el-tag size="small" type="info">code: {{ category.code }}</el-tag>
              <el-tag size="small" effect="plain">排序 {{ category.sort_order ?? 0 }}</el-tag>
            </div>
          </div>
        </div>
        <div class="category-footer">
          <el-button size="small" type="primary" @click="handleEdit(category)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(category)">删除</el-button>
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
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.category-card {
  transition: all 0.2s ease;
}
.category-card:hover {
  transform: translateY(-2px);
}
.category-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}
.category-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary, #5a8dee), var(--primary-hover, #4a7ad4));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
}
.category-basic h3 {
  margin: 0 0 6px 0;
  font-size: 18px;
  color: var(--text-primary, #303133);
}
.category-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.category-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  border-top: 1px solid var(--border, #ebeef5);
  padding-top: 12px;
}
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 20px;
  color: var(--text-muted, #909399);
}
.empty-title {
  font-size: 18px;
  font-weight: 500;
  margin: 20px 0 10px;
  color: var(--text-secondary, #606266);
}
</style>
