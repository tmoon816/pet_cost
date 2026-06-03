<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCategoryStore } from '@/stores/categoryStore'
import * as settingsApi from '@/api/settings'

const categoryStore = useCategoryStore()

// ===== 客户分层阈值 + 折扣率配置 =====
const tierForm = reactive({
  vip_amount: 500,
  svip_amount: 2000,
  supreme_amount: 5000,
  vip_discount: 98,
  svip_discount: 95,
  supreme_discount: 90,
})
const tierLoading = ref(false)
const tierSaving = ref(false)

async function loadTierConfig() {
  tierLoading.value = true
  try {
    const cfg = await settingsApi.getTierConfig()
    tierForm.vip_amount = Number(cfg.vip_amount)
    tierForm.svip_amount = Number(cfg.svip_amount)
    tierForm.supreme_amount = Number(cfg.supreme_amount)
    tierForm.vip_discount = Number(cfg.vip_discount)
    tierForm.svip_discount = Number(cfg.svip_discount)
    tierForm.supreme_discount = Number(cfg.supreme_discount)
  } finally {
    tierLoading.value = false
  }
}

async function saveTierConfig() {
  // 前端先做顺序校验，给即时反馈
  if (!(tierForm.vip_amount > 0 && tierForm.vip_amount < tierForm.svip_amount && tierForm.svip_amount < tierForm.supreme_amount)) {
    ElMessage.error('金额阶梯必须满足：0 < VIP < SVIP < 至尊VIP')
    return
  }
  tierSaving.value = true
  try {
    await settingsApi.updateTierConfig({
      vip_amount: String(tierForm.vip_amount),
      svip_amount: String(tierForm.svip_amount),
      supreme_amount: String(tierForm.supreme_amount),
      vip_discount: tierForm.vip_discount,
      svip_discount: tierForm.svip_discount,
      supreme_discount: tierForm.supreme_discount,
    })
    ElMessage.success('分层配置已保存')
  } catch (err) {
    if (err?.status === 400) {
      ElMessage.error('配置不合法：请检查金额阶梯顺序与折扣范围')
    }
  } finally {
    tierSaving.value = false
  }
}

const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive({ code: '', label: '', sort_order: 0, default_amount: null })
const formRef = ref(null)
const submitting = ref(false)

const rules = {
  code: [
    { required: true, message: '请输入 code', trigger: 'blur' },
    { pattern: /^[a-z0-9_-]{1,30}$/i, message: '只能用字母/数字/下划线/中划线，最长 30', trigger: 'blur' },
  ],
  label: [{ required: true, message: '请输入显示名', trigger: 'blur' }],
}

onMounted(() => {
  categoryStore.fetch(true)
  loadTierConfig()
})

function openCreate() {
  editing.value = null
  Object.assign(form, { code: '', label: '', sort_order: 0, default_amount: null })
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  Object.assign(form, {
    code: row.code,
    label: row.label,
    sort_order: row.sort_order,
    default_amount: row.default_amount != null ? Number(row.default_amount) : null,
  })
  dialogVisible.value = true
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    // el-input-number 清空时 v-model 会写 undefined，这里统一兜底为 null
    // 任何非有限数（NaN / 字符串 NaN / 非法输入）也按 null 处理，避免后端 422
    const raw = form.default_amount
    let defaultAmountPayload = null
    if (raw !== null && raw !== undefined && raw !== '') {
      const n = Number(raw)
      if (Number.isFinite(n) && n >= 0) {
        defaultAmountPayload = n.toFixed(2)
      }
    }
    try {
      if (editing.value) {
        await categoryStore.update(editing.value.code, {
          label: form.label.trim(),
          sort_order: Number(form.sort_order) || 0,
          default_amount: defaultAmountPayload,
        })
        ElMessage.success('已更新')
      } else {
        await categoryStore.create({
          code: form.code.trim(),
          label: form.label.trim(),
          sort_order: Number(form.sort_order) || 0,
          default_amount: defaultAmountPayload,
        })
        ElMessage.success('已新增')
      }
      dialogVisible.value = false
    } catch (err) {
      if (err?.status === 409 && err.detail?.detail === 'category_code_exists') {
        ElMessage.error(`code "${err.detail.code}" 已存在`)
      }
      // 其他错误 http 拦截器已弹 ElMessage，这里不再二次提示
    } finally {
      submitting.value = false
    }
  })
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除分类「${row.label}」？被花费记录引用时无法删除。`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await categoryStore.remove(row.code)
    ElMessage.success('已删除')
  } catch (err) {
    if (err?.status === 409 && err.detail?.detail === 'category_in_use') {
      ElMessage.error(`分类「${row.label}」已被花费记录引用，无法删除`)
    }
  }
}

function formatDefaultAmount(v) {
  if (v == null || v === '') return '—'
  return `¥ ${Number(v).toFixed(2)}`
}
</script>

<template>
  <div class="settings-page">
    <el-card class="card" v-loading="tierLoading">
      <template #header>
        <div class="card-header">
          <span class="title">会员分层 & 折扣配置</span>
          <el-button type="primary" :loading="tierSaving" @click="saveTierConfig">保存配置</el-button>
        </div>
      </template>

      <el-table :data="[
        { key: 'vip', name: 'VIP', tagType: 'success' },
        { key: 'svip', name: 'SVIP', tagType: 'warning' },
        { key: 'supreme', name: '至尊VIP', tagType: 'danger' },
      ]" stripe>
        <el-table-column label="等级" width="140">
          <template #default="{ row }">
            <el-tag :type="row.tagType" effect="dark" size="small">{{ row.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="达标金额（累计贡献 ≥）" min-width="220">
          <template #default="{ row }">
            <el-input-number
              v-model="tierForm[`${row.key}_amount`]"
              :min="1"
              :max="99999999"
              :step="100"
              :precision="0"
              controls-position="right"
              style="width: 180px;"
            />
            <span class="unit">元</span>
          </template>
        </el-table-column>
        <el-table-column label="消费折扣率" min-width="220">
          <template #default="{ row }">
            <el-input-number
              v-model="tierForm[`${row.key}_discount`]"
              :min="50"
              :max="100"
              :step="1"
              :precision="0"
              controls-position="right"
              style="width: 140px;"
            />
            <span class="unit">% （{{ tierForm[`${row.key}_discount`] }}折后价 = 原价 × {{ tierForm[`${row.key}_discount`] }}%）</span>
          </template>
        </el-table-column>
      </el-table>

      <p class="hint">
        贡献金额口径 = 累计充值本金（不含赠送）+ 现金消费额（储值消费不重复计）。
        金额阶梯须满足 0 &lt; VIP &lt; SVIP &lt; 至尊VIP。
        折扣率为「付款百分比」：98 表示 98 折（付 98%），90 表示 9 折。开单选「储值扣款」时按此折扣自动算实付。
      </p>
    </el-card>

    <el-card class="card">
      <template #header>
        <div class="card-header">
          <span class="title">服务项目字典</span>
          <el-button type="primary" :icon="'Plus'" @click="openCreate">新增分类</el-button>
        </div>
      </template>

      <el-table v-loading="categoryStore.loading" :data="categoryStore.list" stripe>
        <el-table-column prop="code" label="Code" width="160" />
        <el-table-column prop="label" label="显示名" min-width="160" />
        <el-table-column label="默认价" width="140">
          <template #default="{ row }">
            <span :class="{ 'text-muted': row.default_amount == null }">
              {{ formatDefaultAmount(row.default_amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="100" />
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <p class="hint">
        提示：sort_order 越小越靠前；code 不可修改，删除时若已有花费记录引用会被拒绝。
        默认价填了后，录单选完此分类会自动填入金额（仍可手改）。
      </p>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑分类' : '新增分类'"
      width="440px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <el-form-item label="Code" prop="code">
          <el-input v-model="form.code" :disabled="!!editing" maxlength="30" />
        </el-form-item>
        <el-form-item label="显示名" prop="label">
          <el-input v-model="form.label" maxlength="30" />
        </el-form-item>
        <el-form-item label="默认价">
          <el-input-number
            v-model="form.default_amount"
            :min="0"
            :max="99999999"
            :precision="2"
            :step="10"
            controls-position="right"
            placeholder="留空表示无默认价"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
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
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card {
  border-radius: 12px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-header .title {
  font-size: 16px;
  font-weight: 600;
}
.hint {
  margin-top: 12px;
  color: #909399;
  font-size: 13px;
  line-height: 1.6;
}
.text-muted {
  color: #c0c4cc;
}
.unit {
  margin-left: 8px;
  color: #909399;
  font-size: 13px;
}
</style>
