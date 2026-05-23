<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, UploadFilled } from '@element-plus/icons-vue'
import {
  commitImport,
  downloadImportTemplate,
  previewImport,
} from '@/api/customers'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'imported'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const file = ref(null)
const fileInput = ref(null)
const previewResult = ref(null)  // {ok:[], errors:[], total}
const previewLoading = ref(false)
const submitting = ref(false)

const canSubmit = computed(
  () => previewResult.value && previewResult.value.errors.length === 0 && previewResult.value.ok.length > 0
)

async function downloadTemplate() {
  try {
    const blob = await downloadImportTemplate()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '客户导入模板.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('模板下载失败')
  }
}

function pickFile() {
  fileInput.value?.click()
}

async function onFileChange(e) {
  const f = e.target.files?.[0]
  if (!f) return
  if (!f.name.toLowerCase().endsWith('.xlsx')) {
    ElMessage.error('请上传 .xlsx 文件')
    e.target.value = ''
    return
  }
  file.value = f
  e.target.value = ''
  await runPreview()
}

async function runPreview() {
  if (!file.value) return
  previewLoading.value = true
  try {
    previewResult.value = await previewImport(file.value)
  } catch {
    previewResult.value = null
  } finally {
    previewLoading.value = false
  }
}

async function confirmImport() {
  if (!file.value || !canSubmit.value) return
  submitting.value = true
  try {
    const res = await commitImport(file.value)
    if (res.errors && res.errors.length) {
      previewResult.value = res
      ElMessage.error('导入被拒绝：仍有错误未修正')
      return
    }
    ElMessage.success(`成功导入 ${res.inserted} 条客户`)
    emit('imported')
    closeDialog()
  } finally {
    submitting.value = false
  }
}

function clearFile() {
  file.value = null
  previewResult.value = null
}

function closeDialog() {
  visible.value = false
  setTimeout(clearFile, 300)
}
</script>

<template>
  <el-dialog
    v-model="visible"
    title="批量导入客户"
    width="640px"
    :close-on-click-modal="false"
    @closed="clearFile"
  >
    <div class="import-body">
      <el-alert type="info" :closable="false" show-icon>
        <template #default>
          先下载模板填好再上传。系统会先校验所有行，全部通过才会真正写入；只要有一行错误，整批不写。
        </template>
      </el-alert>

      <div class="step">
        <span class="step-no">1</span>
        <span class="step-text">下载模板填写客户信息</span>
        <el-button type="primary" plain size="small" @click="downloadTemplate">
          <el-icon><Download /></el-icon>
          下载模板
        </el-button>
      </div>

      <div class="step">
        <span class="step-no">2</span>
        <span class="step-text">上传填好的 xlsx 文件</span>
        <input
          ref="fileInput"
          type="file"
          accept=".xlsx"
          style="display: none"
          @change="onFileChange"
        />
        <el-button size="small" @click="pickFile">
          <el-icon><UploadFilled /></el-icon>
          {{ file ? '重新选择' : '选择文件' }}
        </el-button>
      </div>

      <div v-if="file" class="file-name">
        当前文件：<strong>{{ file.name }}</strong>
        <el-button link type="primary" size="small" @click="clearFile">移除</el-button>
      </div>

      <el-skeleton v-if="previewLoading" :rows="3" animated />

      <div v-else-if="previewResult" class="preview">
        <div class="summary">
          <el-tag type="success" size="large">可导入 {{ previewResult.ok.length }} 行</el-tag>
          <el-tag :type="previewResult.errors.length ? 'danger' : 'info'" size="large">
            错误 {{ previewResult.errors.length }} 行
          </el-tag>
          <el-tag type="info" size="large">共 {{ previewResult.total }} 行</el-tag>
        </div>

        <div v-if="previewResult.errors.length" class="errors">
          <div class="errors-title">需要修正的行：</div>
          <el-table :data="previewResult.errors" max-height="240" size="small" border>
            <el-table-column prop="row" label="行号" width="80" align="center" />
            <el-table-column prop="name" label="姓名" width="120" />
            <el-table-column prop="message" label="错误原因" />
          </el-table>
          <div class="errors-hint">请在 Excel 中修正后重新上传。</div>
        </div>

        <div v-else-if="canSubmit" class="ready">
          所有行校验通过，可以点「确认导入」写入数据库。
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="closeDialog">取消</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        :disabled="!canSubmit"
        @click="confirmImport"
      >
        确认导入{{ canSubmit ? `（${previewResult.ok.length} 行）` : '' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.import-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-soft, #f6f8fb);
  border-radius: 8px;
}
.step-no {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--primary, #5a8dee);
  color: white;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
}
.step-text {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary, #303133);
}
.file-name {
  font-size: 13px;
  color: var(--text-secondary, #606266);
  display: flex;
  align-items: center;
  gap: 8px;
}
.preview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.summary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.errors-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--danger, #f56c6c);
  margin-bottom: 8px;
}
.errors-hint {
  font-size: 12px;
  color: var(--text-muted, #909399);
  margin-top: 8px;
}
.ready {
  padding: 12px;
  background: #f0f9eb;
  color: #67c23a;
  border-radius: 6px;
  text-align: center;
  font-size: 14px;
}
</style>
