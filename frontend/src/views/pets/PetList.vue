<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, View } from '@element-plus/icons-vue'
import { listPets, deletePet } from '@/api/pets'
import PetForm from '@/components/PetForm.vue'

const router = useRouter()
const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editId = ref(null)

const fetchList = async () => {
  loading.value = true
  try {
    const res = await listPets()
    // 根据物种设置默认头像
    const avatarMap = {
      '狗': '🐶',
      '猫': '🐱',
      '仓鼠': '🐹',
      '兔子': '🐰',
      '鹦鹉': '🦜'
    }
    list.value = res.map(item => ({
      ...item,
      avatar: avatarMap[item.species] || '🐾',
      thisMonthCost: Number(item.thisMonthCost || 0)
    }))
  } catch (e) {
    ElMessage.error('获取宠物列表失败')
    console.error(e)
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

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除宠物「${row.name}」吗？删除后会级联删除其名下的所有花费记录，无法恢复！`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deletePet(row.id)
      ElMessage.success('删除成功')
      fetchList()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const handleViewDetail = (row) => {
  router.push(`/pets/${row.id}`)
}

const handleFormSuccess = () => {
  dialogVisible.value = false
  fetchList()
}

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="pet-list-page">
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h2 style="margin: 0; font-size: 24px;">宠物档案</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增宠物
      </el-button>
    </div>

    <div class="pet-grid" v-loading="loading">
      <div v-if="list.length === 0 && !loading" class="empty-state">
        <div style="font-size: 80px; margin-bottom: 20px;">🐾</div>
        <p class="empty-title">暂无宠物档案</p>
        <p class="empty-desc">点击右上角「新增宠物」按钮添加第一只爱宠吧~</p>
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
          <div class="pet-avatar">{{ pet.avatar }}</div>
          <div class="pet-basic">
            <h3>{{ pet.name }}</h3>
            <div class="pet-tag">
              <el-tag size="small" type="info">{{ pet.species }} · {{ pet.breed }}</el-tag>
            </div>
          </div>
        </div>
        <div class="pet-info-grid">
          <div class="info-item">
            <label>性别</label>
            <span>{{ pet.gender }}</span>
          </div>
          <div class="info-item">
            <label>年龄</label>
            <span>{{ Math.floor((new Date() - new Date(pet.birthday)) / (1000 * 60 * 60 * 24 * 365)) }}岁</span>
          </div>
          <div class="info-item">
            <label>体重</label>
            <span>{{ pet.weight }}</span>
          </div>
          <div class="info-item">
            <label>生日</label>
            <span>{{ pet.birthday }}</span>
          </div>
          <div class="info-item full-width">
            <label>健康记录</label>
            <span>{{ pet.healthRecord }}</span>
          </div>
        </div>
        <div class="pet-footer">
          <div class="month-cost">
            <span class="label">本月花费</span>
            <span class="amount text-danger">¥ {{ pet.thisMonthCost.toFixed(2) }}</span>
          </div>
          <div class="actions">
            <el-button size="small" @click="handleViewDetail(pet)">查看详情</el-button>
            <el-button size="small" @click="handleEdit(pet)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(pet)">删除</el-button>
          </div>
        </div>
      </el-card>
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
  background: linear-gradient(135deg, var(--primary), var(--primary-hover));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: white;
}
.pet-basic h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: var(--text-primary);
}
.pet-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.info-item.full-width {
  grid-column: 1 / -1;
}
.info-item label {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
  margin-bottom: 4px;
}
.info-item span {
  font-size: 14px;
  color: var(--text-secondary);
}
.pet-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.month-cost {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.month-cost .label {
  font-size: 12px;
  color: var(--text-muted);
}
.month-cost .amount {
  font-size: 18px;
  font-weight: 700;
}
.actions {
  display: flex;
  gap: 8px;
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
  .pet-grid {
    grid-template-columns: 1fr;
  }
  .pet-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  .actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
