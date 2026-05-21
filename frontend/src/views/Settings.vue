<script setup>
import { ref, reactive } from 'vue'
import { useCostStore } from '@/stores/costStore'
import { ElMessage, ElMessageBox, ElInput } from 'element-plus'

const store = useCostStore()

const newTypeName = ref('')
const petDialogVisible = ref(false)
const isPetEdit = ref(false)
const currentPetId = ref(null)
const petForm = reactive({
  name: '',
  owner: '',
  remark: ''
})

// 打开新增宠物对话框
const handleAddPet = () => {
  isPetEdit.value = false
  currentPetId.value = null
  petForm.name = ''
  petForm.owner = ''
  petForm.remark = ''
  petDialogVisible.value = true
}

// 打开编辑宠物对话框
const handleEditPet = (pet) => {
  isPetEdit.value = true
  currentPetId.value = pet.id
  petForm.name = pet.name
  petForm.owner = pet.owner
  petForm.remark = pet.remark
  petDialogVisible.value = true
}

// 提交宠物表单
const handleSubmitPet = () => {
  if (!petForm.name.trim()) {
    ElMessage.warning('请输入宠物名称')
    return
  }
  
  // 检查名字是否重复
  const exists = store.petList.some(p => 
    p.name === petForm.name.trim() && p.id !== currentPetId.value
  )
  if (exists) {
    ElMessage.warning('该宠物名称已经存在')
    return
  }

  if (isPetEdit.value) {
    store.updatePet(currentPetId.value, petForm)
    ElMessage.success('宠物信息更新成功')
  } else {
    store.addPet(petForm)
    ElMessage.success('宠物添加成功')
  }
  
  petDialogVisible.value = false
}

// 删除宠物
const handleDeletePet = (pet) => {
  try {
    ElMessageBox.confirm(
      `确定要删除宠物 "${pet.name}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      store.deletePet(pet.id)
      ElMessage.success('删除成功')
    }).catch(() => {})
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 添加花费类型
const handleAddType = () => {
  if (!newTypeName.value.trim()) {
    ElMessage.warning('请输入花费类型名称')
    return
  }
  if (store.costTypeList.includes(newTypeName.value.trim())) {
    ElMessage.warning('该花费类型已经存在')
    return
  }
  
  store.addCostType(newTypeName.value.trim())
  ElMessage.success('添加成功')
  newTypeName.value = ''
}

// 删除花费类型
const handleDeleteType = (typeName) => {
  // 检查是否有花费记录使用该类型
  const hasUsed = store.costList.some(item => item.type === typeName)
  if (hasUsed) {
    ElMessage.error('该花费类型已有花费记录，无法删除')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除花费类型 "${typeName}" 吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    store.deleteCostType(typeName)
    ElMessage.success('删除成功')
  }).catch(() => {})
}

// 导出数据
const handleExport = () => {
  const data = {
    exportTime: new Date().toISOString(),
    costList: store.costList,
    petList: store.petList,
    costTypeList: store.costTypeList
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `pet_cost_${new Date().toISOString().substring(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('数据导出成功')
}

// 导入数据
const handleImport = (e) => {
  const file = e.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = (event) => {
    try {
      const data = JSON.parse(event.target.result)
      if (data.costList && Array.isArray(data.costList)) {
        ElMessageBox.confirm(
          '导入会覆盖现有所有数据，确定要继续吗？',
          '警告',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        ).then(() => {
          store.costList = data.costList
          if (data.petList && Array.isArray(data.petList)) {
            store.petList = data.petList
          }
          if (data.costTypeList && Array.isArray(data.costTypeList)) {
            store.costTypeList = data.costTypeList
          }
          store.saveData()
          store.savePetData()
          ElMessage.success('数据导入成功')
        }).catch(() => {})
      } else {
        ElMessage.error('导入的文件格式不正确')
      }
    } catch (error) {
      ElMessage.error('导入的文件不是有效的JSON文件')
    }
  }
  reader.readAsText(file)
  e.target.value = '' // 清空input，允许重复选择同一个文件
}

// 清空所有数据
const handleClearAll = () => {
  ElMessageBox.confirm(
    '确定要清空所有花费数据吗？此操作不可恢复！',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    store.costList = []
    store.saveData()
    ElMessage.success('数据已清空')
  }).catch(() => {})
}
</script>

<template>
  <div class="settings-page">
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="setting-card">
          <template #header>
            <div class="card-header">
              <span>宠物信息管理</span>
              <el-button type="primary" @click="handleAddPet">
                <el-icon><Plus /></el-icon>
                新增宠物
              </el-button>
            </div>
          </template>

          <!-- 宠物列表 -->
          <div class="pet-list">
            <div v-for="pet in store.petList" :key="pet.id" class="pet-item">
              <div class="pet-info">
                <div class="pet-name">{{ pet.name }}</div>
                <div class="pet-detail" v-if="pet.owner">主人：{{ pet.owner }}</div>
                <div class="pet-detail" v-if="pet.remark">{{ pet.remark }}</div>
              </div>
              <div class="pet-actions">
                <el-button size="small" type="primary" @click="handleEditPet(pet)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDeletePet(pet)">删除</el-button>
              </div>
            </div>
            <div v-if="store.petList.length === 0" class="empty-pet">
              暂无宠物信息，点击右上角"新增宠物"添加吧~
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="setting-card">
          <template #header>
            <div class="card-header">
              <span>花费类型管理</span>
              <div style="display: flex; align-items: center">
                <el-input
                  v-model="newTypeName"
                  placeholder="输入新花费类型"
                  style="width: 200px; margin-right: 10px"
                  @keyup.enter="handleAddType"
                />
                <el-button type="primary" @click="handleAddType">添加</el-button>
              </div>
            </div>
          </template>
          <div class="tag-list">
            <el-tag
              v-for="type in store.costTypeList"
              :key="type"
              closable
              @close="handleDeleteType(type)"
            >
              {{ type }}
            </el-tag>
            <div v-if="store.costTypeList.length === 0" style="color: #909399; text-align: center; padding: 20px">
              暂无花费类型
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" class="setting-card" style="margin-top: 20px">
      <template #header>
        <span>数据管理</span>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="8">
          <el-card shadow="hover" class="data-card">
            <div class="data-item">
              <el-icon size="40" style="color: #67c23a; margin-bottom: 15px"><Download /></el-icon>
              <div class="data-title">导出数据</div>
              <div class="data-desc">将所有花费数据导出为JSON文件备份</div>
              <el-button type="success" style="margin-top: 15px" @click="handleExport">
                立即导出
              </el-button>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-card shadow="hover" class="data-card">
            <div class="data-item">
              <el-icon size="40" style="color: #e6a23c; margin-bottom: 15px"><Upload /></el-icon>
              <div class="data-title">导入数据</div>
              <div class="data-desc">从备份的JSON文件恢复数据，会覆盖现有数据</div>
              <label for="import-file">
                <el-button type="warning" style="margin-top: 15px">
                  选择文件导入
                </el-button>
                <input id="import-file" type="file" accept=".json" style="display: none" @change="handleImport">
              </label>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-card shadow="hover" class="data-card">
            <div class="data-item">
              <el-icon size="40" style="color: #f56c6c; margin-bottom: 15px"><Delete /></el-icon>
              <div class="data-title">清空数据</div>
              <div class="data-desc">清空所有花费记录，此操作不可恢复，请谨慎操作</div>
              <el-button type="danger" style="margin-top: 15px" @click="handleClearAll">
                清空所有数据
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="hover" class="setting-card" style="margin-top: 20px">
      <template #header>
        <span>关于</span>
      </template>
      <div style="padding: 20px">
        <h3>🐾 宠物花费管理系统</h3>
        <p>版本：v1.1.0</p>
        <p>技术栈：Vue3 + Vite + Element Plus + Pinia + VueRouter4</p>
        <p>特性：纯前端实现，数据本地存储，无需后端服务，支持数据导入导出，图表统计分析</p>
        <p style="margin-top: 10px; color: #909399">数据存储在浏览器的localStorage中，清理浏览器数据会导致数据丢失，建议定期导出备份。</p>
      </div>
    </el-card>

    <!-- 宠物信息编辑弹窗 -->
    <el-dialog
      v-model="petDialogVisible"
      :title="isPetEdit ? '编辑宠物信息' : '新增宠物'"
      width="500px"
      :before-close="() => petDialogVisible = false"
    >
      <el-form label-width="80px">
        <el-form-item label="宠物名称" required>
          <el-input v-model="petForm.name" placeholder="请输入宠物名称" />
        </el-form-item>
        <el-form-item label="主人姓名">
          <el-input v-model="petForm.owner" placeholder="请输入主人姓名（可选）" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="petForm.remark" type="textarea" :rows="3" placeholder="请输入备注信息（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="petDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmitPet">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}
.tag-list {
  padding: 24px 0;
}
.el-tag {
  border-radius: 20px !important;
  padding: 0 16px !important;
  height: 36px !important;
  line-height: 34px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: white !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  margin-right: 10px;
  margin-bottom: 10px;
}
.el-tag:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
}
.setting-card {
  margin-bottom: 24px;
}
.data-card {
  height: 100%;
  transition: all 0.3s ease;
}
.data-card:hover {
  transform: translateY(-4px) !important;
}
.data-item {
  text-align: center;
  padding: 30px 20px;
}
.data-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #303333;
}
.data-desc {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 16px;
}

/* 宠物列表样式 */
.pet-list {
  padding: 10px 0;
}
.pet-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  margin-bottom: 12px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s ease;
}
.pet-item:hover {
  background: rgba(102, 126, 234, 0.08);
  transform: translateX(4px);
}
.pet-info {
  flex: 1;
}
.pet-name {
  font-size: 17px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}
.pet-detail {
  font-size: 13px;
  color: #606266;
  margin-top: 2px;
}
.pet-actions {
  display: flex;
  gap: 8px;
}
.empty-pet {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .data-card {
    margin-bottom: 20px;
  }
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  .card-header > div:last-child {
    width: 100%;
  }
  .card-header .el-input {
    width: 100%;
    margin-bottom: 10px;
  }
  .card-header .el-button {
    width: 100%;
  }
  .pet-item {
    flex-direction: column;
    align-items: flex-start;
  }
  .pet-actions {
    margin-top: 12px;
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
