<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { listPets, deletePet } from '@/api/pets'
import PetForm from '@/components/PetForm.vue'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const customerFilter = ref(null)
const loading = ref(false)
const dialogVisible = ref(false)
const editId = ref(null)

// 物种 code → 中文 label / emoji（前端 derived，不入库）
const SPECIES_MAP = {
  dog:     { label: '犬',   emoji: '🐶' },
  cat:     { label: '猫',   emoji: '🐱' },
  hamster: { label: '仓鼠', emoji: '🐹' },
  rabbit:  { label: '兔子', emoji: '🐰' },
  bird:    { label: '鹦鹉', emoji: '🦜' },
  other:   { label: '其他', emoji: '🐾' }
}
const GENDER_MAP = {
  male:    '公',
  female:  '母',
  unknown: '未知'
}

const speciesLabel = (code) => SPECIES_MAP[code]?.label || code || '-'
const speciesEmoji = (code) => SPECIES_MAP[code]?.emoji || '🐾'
const genderLabel  = (code) => GENDER_MAP[code] || '-'

// 年龄计算：空生日返回 '-'，避免 NaN
const computeAge = (birthday) => {
  if (!birthday) return '-'
  const ms = new Date() - new Date(birthday)
  if (isNaN(ms)) return '-'
  const years = Math.floor(ms / (1000 * 60 * 60 * 24 * 365))
  return years >= 0 ? `${years} 岁` : '-'
}

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (customerFilter.value) params.customer_id = customerFilter.value
    const res = await listPets(params)
    // 后端返 Page{items,total}，必须取 items
    list.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    // http 拦截器已 ElMessage.error 兜底
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  editId.value = null
  dialogVisible.value = true
}
const handleEdit = (row) => {
  editId.value = row.id
  dialogVisible.value = true
}
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除宠物「${row.name}」吗？该宠物名下的所有服务订单会一并删除，无法恢复。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await deletePet(row.id)
    ElMessage.success('已删除')
    // 删完当前页若空则回退一页
    if (list.value.length === 1 && page.value > 1) page.value -= 1
    await fetchList()
  } catch (e) {
    // 拦截器兜底
  }
}
const handleViewDetail = (row) => router.push(`/pets/${row.id}`)
const handleFormSuccess = () => {
  dialogVisible.value = false
  fetchList()
}
const onPageChange = (p) => {
  page.value = p
  fetchList()
}
const resetFilter = () => {
  customerFilter.value = null
  page.value = 1
  fetchList()
}

onMounted(() => fetchList())
</script>

<template>
  <div class="pet-list-page">
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; gap: 16px; flex-wrap: wrap;">
      <h2 style="margin: 0; font-size: 24px;">客户宠物档案</h2>
      <div style="display: flex; gap: 12px; align-items: center;">
        <el-input-number
          v-model="customerFilter"
          placeholder="按客户ID筛选"
          :min="1"
          :controls="false"
          style="width: 160px;"
          @change="() => { page = 1; fetchList() }"
        />
        <el-button @click="resetFilter">重置</el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增宠物
        </el-button>
      </div>
    </div>

    <div class="pet-grid" v-loading="loading">
      <div v-if="list.length === 0 && !loading" class="empty-state">
        <div style="font-size: 80px; margin-bottom: 20px;">🐾</div>
        <p class="empty-title">暂无宠物档案</p>
        <p class="empty-desc">点击右上角「新增宠物」按钮添加第一只宠物</p>
        <el-button type="primary" @click="handleAdd" style="margin-top: 20px;">
          <el-icon><Plus /></el-icon>
          立即新增
        </el-button>
      </div>

      <el-card
        v-for="pet in list"
        :key="pet.id"
        shadow="hover"
        class="pet-card"
      >
        <div class="pet-header">
          <div class="pet-avatar">{{ speciesEmoji(pet.species) }}</div>
          <div class="pet-basic">
            <h3>{{ pet.name }}</h3>
            <div class="pet-tag">
              <el-tag size="small" type="info">
                {{ speciesLabel(pet.species) }}<span v-if="pet.breed"> · {{ pet.breed }}</span>
              </el-tag>
            </div>
          </div>
        </div>
        <div class="pet-info-grid">
          <div class="info-item">
            <label>客户ID</label>
            <span>#{{ pet.customer_id }}</span>
          </div>
          <div class="info-item">
            <label>性别</label>
            <span>{{ genderLabel(pet.gender) }}</span>
          </div>
          <div class="info-item">
            <label>年龄</label>
            <span>{{ computeAge(pet.birthday) }}</span>
          </div>
          <div class="info-item">
            <label>生日</label>
            <span>{{ pet.birthday || '-' }}</span>
          </div>
          <div class="info-item full-width">
            <label>备注</label>
            <span>{{ pet.note || '-' }}</span>
          </div>
        </div>
        <div class="pet-footer">
          <div class="actions">
            <el-button size="small" @click="handleViewDetail(pet)">查看详情</el-button>
            <el-button size="small" type="primary" @click="handleEdit(pet)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(pet)">删除</el-button>
          </div>
        </div>
      </el-card>
    </div>

    <div class="pagination" v-if="total > pageSize">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="onPageChange"
      />
    </div>

    <PetForm
      v-model="dialogVisible"
      :edit-id="editId"
      @success="handleFormSuccess"
    />
  </div>
</template>

<style scoped>
.pet-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}
.pet-card {
  transition: all 0.2s ease;
}
.pet-card:hover {
  transform: translateY(-2px);
}
.pet-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.pet-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary, #5a8dee), var(--primary-hover, #4a7ad4));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: white;
}
.pet-basic h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: var(--text-primary, #303133);
}
.pet-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 24px;
  margin-bottom: 20px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-item.full-width {
  grid-column: 1 / -1;
}
.info-item label {
  font-size: 12px;
  color: var(--text-muted, #909399);
}
.info-item span {
  font-size: 14px;
  color: var(--text-primary, #303133);
}
.pet-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  border-top: 1px solid var(--border, #ebeef5);
  padding-top: 16px;
  gap: 8px;
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
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
