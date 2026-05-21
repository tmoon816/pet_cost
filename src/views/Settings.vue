<script setup>
import { ref } from 'vue'
import { useCostStore } from '@/stores/costStore'
import { ElMessage, ElMessageBox, ElInput } from 'element-plus'

const store = useCostStore()

const newPetName = ref('')
const newTypeName = ref('')

// 添加宠物类型
const handleAddPet = async () => {
  if (!newPetName.value.trim()) {
    ElMessage.warning('请输入宠物名称')
    return
  }
  if (store.petList.includes(newPetName.value.trim())) {
    ElMessage.warning('该宠物类型已经存在')
    return
  }
  
  store.addPet(newPetName.value.trim())
  ElMessage.success('添加成功')
  newPetName.value = ''
}

// 删除宠物类型
const handleDeletePet = (petName) => {
  // 检查是否有花费记录使用该类型
  const hasUsed = store.costList.some(item => item.pet === petName)
  if (hasUsed) {
    ElMessage.error('该宠物类型已有花费记录，无法删除')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除宠物类型 "${petName}" 吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    store.deletePet(petName)
    ElMessage.success('删除成功')
  }).catch(() => {})
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
              <span>宠物类型管理</span>
              <div style="display: flex; align-items: center">
                <el-input
                  v-model="newPetName"
                  placeholder="输入新宠物类型"
                  style="width: 200px; margin-right: 10px"
                  @keyup.enter="handleAddPet"
                />
                <el-button type="primary" @click="handleAddPet">添加</el-button>
              </div>
            </div>
          </template>
          <div class="tag-list">
            <el-tag
              v-for="pet in store.petList"
              :key="pet"
              closable
              @close="handleDeletePet(pet)"
              style="margin-right: 10px; margin-bottom: 10px"
            >
              {{ pet }}
            </el-tag>
            <div v-if="store.petList.length === 0" style="color: #909399; text-align: center; padding: 20px">
              暂无宠物类型
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
              style="margin-right: 10px; margin-bottom: 10px"
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
        <p>版本：v1.0.0</p>
        <p>技术栈：Vue3 + Vite + Element Plus + Pinia + VueRouter4</p>
        <p>特性：纯前端实现，数据本地存储，无需后端服务，支持数据导入导出，图表统计分析</p>
        <p style="margin-top: 10px; color: #909399">数据存储在浏览器的localStorage中，清理浏览器数据会导致数据丢失，建议定期导出备份。</p>
      </div>
    </el-card>
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
  color: #303133;
}
.data-desc {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 16px;
}
</style>
