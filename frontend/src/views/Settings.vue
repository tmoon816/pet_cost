<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCategoryStore } from '@/stores/categoryStore'
import * as settingsApi from '@/api/settings'
import * as packagesApi from '@/api/rechargePackages'

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
  loadPackages()
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

// ===== 充值套餐配置 =====
const pkgList = ref([])
const pkgLoading = ref(false)
const pkgDialogVisible = ref(false)
const pkgEditing = ref(null)
const pkgSubmitting = ref(false)
const pkgFormRef = ref(null)

const pkgForm = reactive({
  name: '',
  subtitle: '',
  price: 500,
  bonus_amount: 0,
  gifts: [],
  highlights: [],
  badge: '',
  is_recommended: false,
  is_active: true,
  sort_order: 0,
})

// 标签输入临时态
const giftInput = ref('')
const highlightInput = ref('')

const pkgRules = {
  name: [{ required: true, message: '请输入套餐名', trigger: 'blur' }],
  price: [{ required: true, message: '请输入实付价', trigger: 'blur' }],
}

async function loadPackages() {
  pkgLoading.value = true
  try {
    const res = await packagesApi.listPackages()
    pkgList.value = (res || []).map((p) => ({
      ...p,
      price: Number(p.price),
      bonus_amount: Number(p.bonus_amount),
      gifts: p.gifts || [],
      highlights: p.highlights || [],
    }))
  } catch (e) {
    pkgList.value = []
  } finally {
    pkgLoading.value = false
  }
}

function openPkgCreate() {
  pkgEditing.value = null
  Object.assign(pkgForm, {
    name: '', subtitle: '', price: 500, bonus_amount: 0,
    gifts: [], highlights: [], badge: '', is_recommended: false,
    is_active: true, sort_order: (pkgList.value.length + 1) * 10,
  })
  giftInput.value = ''
  highlightInput.value = ''
  pkgDialogVisible.value = true
}

function openPkgEdit(row) {
  pkgEditing.value = row
  Object.assign(pkgForm, {
    name: row.name,
    subtitle: row.subtitle || '',
    price: Number(row.price),
    bonus_amount: Number(row.bonus_amount),
    gifts: [...(row.gifts || [])],
    highlights: [...(row.highlights || [])],
    badge: row.badge || '',
    is_recommended: !!row.is_recommended,
    is_active: !!row.is_active,
    sort_order: row.sort_order,
  })
  giftInput.value = ''
  highlightInput.value = ''
  pkgDialogVisible.value = true
}

function addGift() {
  const v = giftInput.value.trim()
  if (v && !pkgForm.gifts.includes(v)) pkgForm.gifts.push(v)
  giftInput.value = ''
}
function removeGift(i) { pkgForm.gifts.splice(i, 1) }
function addHighlight() {
  const v = highlightInput.value.trim()
  if (v && !pkgForm.highlights.includes(v)) pkgForm.highlights.push(v)
  highlightInput.value = ''
}
function removeHighlight(i) { pkgForm.highlights.splice(i, 1) }

async function submitPkg() {
  if (!pkgFormRef.value) return
  await pkgFormRef.value.validate(async (valid) => {
    if (!valid) return
    // 收尾：把还没回车的输入也并入
    addGift()
    addHighlight()
    pkgSubmitting.value = true
    const payload = {
      name: pkgForm.name.trim(),
      subtitle: pkgForm.subtitle.trim() || null,
      price: Number(pkgForm.price).toFixed(2),
      bonus_amount: Number(pkgForm.bonus_amount || 0).toFixed(2),
      gifts: pkgForm.gifts,
      highlights: pkgForm.highlights,
      badge: pkgForm.badge.trim() || null,
      is_recommended: pkgForm.is_recommended,
      is_active: pkgForm.is_active,
      sort_order: Number(pkgForm.sort_order) || 0,
    }
    try {
      if (pkgEditing.value) {
        await packagesApi.updatePackage(pkgEditing.value.id, payload)
        ElMessage.success('套餐已更新')
      } else {
        await packagesApi.createPackage(payload)
        ElMessage.success('套餐已新增')
      }
      pkgDialogVisible.value = false
      await loadPackages()
    } finally {
      pkgSubmitting.value = false
    }
  })
}

async function onPkgDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除套餐「${row.name}」？删除后该套餐将不再出现在充值页。`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    return
  }
  await packagesApi.deletePackage(row.id)
  ElMessage.success('已删除')
  await loadPackages()
}

async function togglePkgActive(row) {
  try {
    await packagesApi.updatePackage(row.id, { is_active: !row.is_active })
    row.is_active = !row.is_active
    ElMessage.success(row.is_active ? '已启用' : '已停用')
  } catch (e) {
    /* http 拦截器已提示 */
  }
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

    <!-- 充值套餐配置 -->
    <el-card class="card" v-loading="pkgLoading">
      <template #header>
        <div class="card-header">
          <span class="title">充值套餐配置</span>
          <el-button type="primary" :icon="'Plus'" @click="openPkgCreate">新增套餐</el-button>
        </div>
      </template>

      <el-table :data="pkgList" stripe>
        <el-table-column label="套餐" min-width="160">
          <template #default="{ row }">
            <div class="pkg-name-cell">
              <span class="pkg-name">{{ row.name }}</span>
              <el-tag v-if="row.badge" size="small" type="warning" effect="plain">{{ row.badge }}</el-tag>
              <el-tag v-if="row.is_recommended" size="small" type="primary" effect="plain">推荐</el-tag>
            </div>
            <div class="pkg-sub" v-if="row.subtitle">{{ row.subtitle }}</div>
          </template>
        </el-table-column>
        <el-table-column label="实付价" width="110">
          <template #default="{ row }">¥ {{ Number(row.price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="赠送" width="110">
          <template #default="{ row }">
            <span :class="{ 'text-muted': !(row.bonus_amount > 0) }">
              {{ row.bonus_amount > 0 ? `¥ ${Number(row.bonus_amount).toFixed(2)}` : '—' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="到账" width="110">
          <template #default="{ row }">
            <strong>¥ {{ (Number(row.price) + Number(row.bonus_amount)).toFixed(2) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="赠品 / 卖点" min-width="220">
          <template #default="{ row }">
            <div class="pkg-tags">
              <el-tag v-for="(g, i) in row.gifts" :key="`g${i}`" size="small" type="success" effect="plain">🎁 {{ g }}</el-tag>
              <el-tag v-for="(h, i) in row.highlights" :key="`h${i}`" size="small" effect="plain">⭐ {{ h }}</el-tag>
              <span v-if="!row.gifts.length && !row.highlights.length" class="text-muted">—</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch :model-value="row.is_active" @change="togglePkgActive(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openPkgEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="onPkgDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <p class="hint">
        充值页只展示「已启用」的套餐；标记「推荐」的套餐会在充值页高亮并默认选中（建议只标一个）。
        到账金额 = 实付价 + 赠送金额；赠品、卖点为纯展示文案，赠品会写入充值流水备注。
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

    <!-- 套餐 新增/编辑 对话框 -->
    <el-dialog
      v-model="pkgDialogVisible"
      :title="pkgEditing ? '编辑套餐' : '新增套餐'"
      width="560px"
      top="6vh"
    >
      <el-form ref="pkgFormRef" :model="pkgForm" :rules="pkgRules" label-width="92px">
        <el-form-item label="套餐名" prop="name">
          <el-input v-model="pkgForm.name" maxlength="50" placeholder="如：Pro 卡" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="pkgForm.subtitle" maxlength="100" placeholder="一句话卖点，如：常来洗护，超值之选" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="实付价" prop="price">
              <el-input-number
                v-model="pkgForm.price" :min="1" :max="9999999" :precision="2" :step="100"
                controls-position="right" style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="赠送金额">
              <el-input-number
                v-model="pkgForm.bonus_amount" :min="0" :max="9999999" :precision="2" :step="50"
                controls-position="right" style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <div class="pkg-credit-preview">
          实际到账 <strong>¥ {{ (Number(pkgForm.price || 0) + Number(pkgForm.bonus_amount || 0)).toFixed(2) }}</strong>
        </div>

        <el-form-item label="赠品清单">
          <div class="tag-editor">
            <div class="tag-list" v-if="pkgForm.gifts.length">
              <el-tag
                v-for="(g, i) in pkgForm.gifts" :key="i"
                type="success" effect="plain" closable @close="removeGift(i)"
              >🎁 {{ g }}</el-tag>
            </div>
            <el-input
              v-model="giftInput"
              placeholder="输入赠品后回车添加，如：进口猫砂 1 袋"
              @keyup.enter="addGift"
            >
              <template #append>
                <el-button @click="addGift">添加</el-button>
              </template>
            </el-input>
          </div>
        </el-form-item>

        <el-form-item label="卖点清单">
          <div class="tag-editor">
            <div class="tag-list" v-if="pkgForm.highlights.length">
              <el-tag
                v-for="(h, i) in pkgForm.highlights" :key="i"
                effect="plain" closable @close="removeHighlight(i)"
              >⭐ {{ h }}</el-tag>
            </div>
            <el-input
              v-model="highlightInput"
              placeholder="输入卖点后回车添加，如：洗护 9 折"
              @keyup.enter="addHighlight"
            >
              <template #append>
                <el-button @click="addHighlight">添加</el-button>
              </template>
            </el-input>
          </div>
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="角标">
              <el-input v-model="pkgForm.badge" maxlength="20" placeholder="如：最受欢迎（可空）" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="pkgForm.sort_order" :min="0" :max="9999" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="设置">
          <el-checkbox v-model="pkgForm.is_recommended">推荐档（充值页高亮 + 默认选中）</el-checkbox>
          <el-checkbox v-model="pkgForm.is_active">启用（在充值页展示）</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pkgDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="pkgSubmitting" @click="submitPkg">保存</el-button>
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

/* 套餐配置 */
.pkg-name-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.pkg-name {
  font-weight: 600;
  color: var(--text-primary);
}
.pkg-sub {
  margin-top: 2px;
  font-size: 12px;
  color: var(--text-muted);
}
.pkg-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.tag-editor {
  width: 100%;
}
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}
.pkg-credit-preview {
  margin: -6px 0 16px 92px;
  font-size: 13px;
  color: var(--text-secondary);
}
.pkg-credit-preview strong {
  color: var(--primary);
  font-size: 15px;
}


</style>
