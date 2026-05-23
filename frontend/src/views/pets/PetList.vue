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

const SPECIES_MAP = {
  dog:     { label: '犬',   emoji: '🐶' },
  cat:     { label: '猫',   emoji: '🐱' },
  hamster: { label: '仓鼠', emoji: '🐹' },
  rabbit:  { label: '兔子', emoji: '🐰' },
  bird:    { label: '鹦鹉', emoji: '🦜' },
  other:   { label: '其他', emoji: '🐾' }
}
const GENDER_MAP = { male: '公', female: '母', unknown: '未知' }

const speciesLabel = (code) => SPECIES_MAP[code]?.label || code || '-'
const speciesEmoji = (code) => SPECIES_MAP[code]?.emoji || '🐾'
const genderLabel  = (code) => GENDER_MAP[code]

// 年龄计算：空生日返回 ''（让上层决定不显示），避免 NaN
const computeAge = (birthday) => {
  if (!birthday) return ''
  const ms = new Date() - new Date(birthday)
  if (isNaN(ms)) return ''
  const years = Math.floor(ms / (1000 * 60 * 60 * 24 * 365))
  return years >= 0 ? `${years} 岁` : ''
}

// 最近到店：返回 { date, label } 或 null。null = 没消费记录
const formatLastVisit = (lastVisitAt) => {
  if (!lastVisitAt) return null
  const todayMid = new Date()
  todayMid.setHours(0, 0, 0, 0)
  const visit = new Date(`${lastVisitAt}T00:00:00`)
  if (isNaN(visit.getTime())) return { date: lastVisitAt, label: '' }
  const diffDays = Math.floor((todayMid - visit) / (1000 * 60 * 60 * 24))
  let label
  if (diffDays <= 0) label = '今天'
  else if (diffDays === 1) label = '昨天'
  else label = `${diffDays} 天前`
  return { date: lastVisitAt, label }
}

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (customerFilter.value) params.customer_id = customerFilter.value
    const res = await listPets(params)
    list.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
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
    if (list.value.length === 1 && page.value > 1) page.value -= 1
    await fetchList()
  } catch (e) {
    /* 拦截器兜底 */
  }
}
const handleViewDetail = (row) => router.push(`/pets/${row.id}`)
const handleViewOwner = (row) => router.push(`/customers/${row.customer_id}`)
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
    <div class="page-header">
      <h2>客户宠物档案</h2>
      <div class="page-actions">
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
        <div class="empty-emoji">🐾</div>
        <p class="empty-title">暂无宠物档案</p>
        <p class="empty-desc">点击右上角「新增宠物」按钮添加第一只宠物</p>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          立即新增
        </el-button>
      </div>

      <el-card
        v-for="pet in list"
        :key="pet.id"
        shadow="hover"
        class="pet-card"
        @click="handleViewDetail(pet)"
      >
        <div class="card-top">
          <div class="avatar">{{ speciesEmoji(pet.species) }}</div>
          <div class="ident">
            <div class="name-row">
              <span class="name">{{ pet.name }}</span>
              <el-tag size="small" effect="plain" type="info">
                {{ speciesLabel(pet.species) }}<span v-if="pet.breed"> · {{ pet.breed }}</span>
              </el-tag>
            </div>
            <div class="meta-row">
              <span v-if="genderLabel(pet.gender)" class="meta">{{ genderLabel(pet.gender) }}</span>
              <span v-if="computeAge(pet.birthday)" class="meta">{{ computeAge(pet.birthday) }}</span>
              <span v-if="pet.birthday" class="meta dim">生日 {{ pet.birthday }}</span>
            </div>
          </div>
        </div>

        <div class="owner-row">
          <span class="owner-label">主人</span>
          <el-link
            v-if="pet.customer_name"
            type="primary"
            :underline="false"
            @click.stop="handleViewOwner(pet)"
          >
            {{ pet.customer_name }}
          </el-link>
          <span v-else class="dim">#{{ pet.customer_id }}</span>
        </div>

        <div v-if="pet.note" class="note-row">
          <span class="note-label">备注</span>
          <span class="note-text">{{ pet.note }}</span>
        </div>

        <div class="card-bottom">
          <div class="last-visit">
            <template v-if="formatLastVisit(pet.last_visit_at)">
              <span class="lv-dot" />
              <span class="lv-date">{{ formatLastVisit(pet.last_visit_at).date }}</span>
              <span class="lv-rel">{{ formatLastVisit(pet.last_visit_at).label }}</span>
            </template>
            <span v-else class="lv-empty">暂无到店记录</span>
          </div>
          <div class="actions" @click.stop>
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
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
  flex-wrap: wrap;
}
.page-header h2 {
  margin: 0;
  font-size: 24px;
}
.page-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.pet-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}
.pet-card {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  border-radius: 12px;
}
.pet-card:hover {
  transform: translateY(-2px);
}
.pet-card :deep(.el-card__body) {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-top {
  display: flex;
  align-items: center;
  gap: 12px;
}
.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary, #5a8dee), var(--primary-hover, #4a7ad4));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  flex-shrink: 0;
}
.ident {
  flex: 1;
  min-width: 0;
}
.name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}
.meta-row {
  margin-top: 4px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-secondary, #606266);
}
.meta.dim {
  color: var(--text-muted, #909399);
}

.owner-row,
.note-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
}
.owner-label,
.note-label {
  color: var(--text-muted, #909399);
  flex-shrink: 0;
}
.note-text {
  color: var(--text-secondary, #606266);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.dim {
  color: var(--text-muted, #909399);
}

.card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border, #ebeef5);
  gap: 8px;
  flex-wrap: wrap;
}
.last-visit {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary, #606266);
}
.lv-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success, #67c23a);
  display: inline-block;
}
.lv-date {
  font-weight: 500;
  color: var(--text-primary, #303133);
}
.lv-rel {
  color: var(--text-muted, #909399);
}
.lv-empty {
  color: var(--text-muted, #909399);
  font-size: 12px;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 20px;
  color: var(--text-muted, #909399);
}
.empty-emoji {
  font-size: 80px;
  margin-bottom: 20px;
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
