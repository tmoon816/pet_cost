<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Present, Select, Wallet, CreditCard } from '@element-plus/icons-vue'
import { listPackages, checkoutPackage } from '@/api/rechargePackages'
import * as customersApi from '@/api/customers'

const packages = ref([])
const loadingPackages = ref(false)
const selectedPackageId = ref(null)

const customerOptions = ref([])
const customerLoading = ref(false)
const selectedCustomerId = ref(null)
const channel = ref('wechat')
const note = ref('')
const submitting = ref(false)

const channelOptions = [
  { value: 'wechat', label: '微信', emoji: '💚' },
  { value: 'alipay', label: '支付宝', emoji: '💙' },
  { value: 'cash', label: '现金', emoji: '💵' },
]

const moneyFmt = new Intl.NumberFormat('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const intFmt = new Intl.NumberFormat('zh-CN')
function formatMoney(n) { return `¥${moneyFmt.format(Number(n) || 0)}` }

const selectedPackage = computed(() =>
  packages.value.find((p) => p.id === selectedPackageId.value) || null)

const selectedCustomer = computed(() =>
  customerOptions.value.find((c) => c.id === selectedCustomerId.value) || null)

const creditedAmount = computed(() => {
  if (!selectedPackage.value) return 0
  return Number(selectedPackage.value.price) + Number(selectedPackage.value.bonus_amount)
})

// 赠送比例，给卡片角上展示「多送 X%」
function bonusPct(pkg) {
  if (!pkg || !pkg.price) return 0
  return Math.round((Number(pkg.bonus_amount) / Number(pkg.price)) * 100)
}

const canSubmit = computed(() => selectedPackageId.value && selectedCustomerId.value && !submitting.value)

const fetchPackages = async () => {
  loadingPackages.value = true
  try {
    const res = await listPackages({ active_only: true })
    packages.value = (res || []).map((p) => ({
      ...p,
      price: Number(p.price),
      bonus_amount: Number(p.bonus_amount),
      gifts: p.gifts || [],
      highlights: p.highlights || [],
    }))
    const recommended = packages.value.find((p) => p.is_recommended)
    selectedPackageId.value = recommended?.id ?? packages.value[0]?.id ?? null
  } catch (e) {
    packages.value = []
  } finally {
    loadingPackages.value = false
  }
}

const loadCustomers = async (query) => {
  customerLoading.value = true
  try {
    const data = await customersApi.listCustomers({ q: query || undefined, page: 1, page_size: 50 })
    customerOptions.value = data.items || []
  } catch (e) {
    customerOptions.value = []
  } finally {
    customerLoading.value = false
  }
}

function selectPackage(id) {
  selectedPackageId.value = id
}

const submit = async () => {
  if (!selectedPackageId.value) {
    ElMessage.warning('请先选择一个套餐')
    return
  }
  if (!selectedCustomerId.value) {
    ElMessage.warning('请选择要充值的会员')
    return
  }
  const pkg = selectedPackage.value
  const cust = selectedCustomer.value
  const channelLabel = channelOptions.find((c) => c.value === channel.value)?.label || channel.value

  try {
    await ElMessageBox.confirm(
      `为「${cust.name}」办理「${pkg.name}」\n实付 ${formatMoney(pkg.price)}，到账 ${formatMoney(creditedAmount.value)}` +
      (pkg.bonus_amount > 0 ? `（含赠送 ${formatMoney(pkg.bonus_amount)}）` : '') +
      `\n收款方式：${channelLabel}`,
      '确认充值',
      { confirmButtonText: '确认充值', cancelButtonText: '再想想', type: 'warning' }
    )
  } catch {
    return
  }

  submitting.value = true
  try {
    const res = await checkoutPackage(pkg.id, {
      customer_id: cust.id,
      channel: channel.value,
      note: note.value || undefined,
    })
    ElMessage.success(`充值成功！${res.customer_name} 当前余额 ${formatMoney(res.balance)}`)
    selectedCustomerId.value = null
    note.value = ''
    customerOptions.value = []
  } catch (e) {
    const detail = e?.response?.data?.detail
    ElMessage.error(detail === 'package_inactive' ? '该套餐已停用' : '充值失败，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchPackages()
  loadCustomers()
})
</script>

<template>
  <div class="recharge-page">
    <!-- 页头 -->
    <header class="rc-header">
      <div class="rc-header-text">
        <h2>套餐充值</h2>
        <p>为会员选购储值套餐，充得越多送得越多 ✨</p>
      </div>
      <div class="rc-step-hint">
        <span class="rc-step"><i>1</i> 选套餐</span>
        <span class="rc-step-arrow">→</span>
        <span class="rc-step"><i>2</i> 选会员</span>
        <span class="rc-step-arrow">→</span>
        <span class="rc-step"><i>3</i> 确认充值</span>
      </div>
    </header>

    <!-- 套餐卡片区 -->
    <section class="tiers" v-loading="loadingPackages">
      <article
        v-for="pkg in packages"
        :key="pkg.id"
        class="tier"
        :class="{ selected: pkg.id === selectedPackageId, featured: pkg.is_recommended }"
        @click="selectPackage(pkg.id)"
      >
        <div class="tier-badge" v-if="pkg.badge">{{ pkg.badge }}</div>

        <div class="tier-top">
          <div class="tier-name">{{ pkg.name }}</div>
          <div class="tier-sub">{{ pkg.subtitle || '储值套餐' }}</div>
        </div>

        <div class="tier-price">
          <span class="tier-cur">¥</span>
          <span class="tier-num">{{ intFmt.format(pkg.price) }}</span>
        </div>

        <div class="tier-credit-row">
          <span class="tier-credit-label">实际到账</span>
          <span class="tier-credit-val">{{ formatMoney(pkg.price + pkg.bonus_amount) }}</span>
        </div>
        <div class="tier-bonus-tag" v-if="pkg.bonus_amount > 0">
          🎁 充 {{ intFmt.format(pkg.price) }} 送 {{ intFmt.format(pkg.bonus_amount) }}
          <span class="tier-bonus-pct" v-if="bonusPct(pkg) > 0">多 {{ bonusPct(pkg) }}%</span>
        </div>
        <div class="tier-bonus-tag muted" v-else>无赠送金额</div>

        <div class="tier-divider"></div>

        <ul class="tier-feats">
          <li v-for="(h, i) in pkg.highlights" :key="`h-${i}`">
            <el-icon class="fi ok"><Select /></el-icon><span>{{ h }}</span>
          </li>
          <li v-for="(g, i) in pkg.gifts" :key="`g-${i}`" class="gift">
            <el-icon class="fi gift"><Present /></el-icon><span>赠 {{ g }}</span>
          </li>
        </ul>

        <button class="tier-pick" :class="{ on: pkg.id === selectedPackageId }" type="button">
          <el-icon v-if="pkg.id === selectedPackageId"><Check /></el-icon>
          {{ pkg.id === selectedPackageId ? '已选择' : '选择该套餐' }}
        </button>
      </article>

      <div class="tiers-empty" v-if="!loadingPackages && packages.length === 0">
        <div class="empty-emoji">💳</div>
        <p class="empty-title">还没有可用套餐</p>
        <p class="empty-hint">请先在后台配置充值套餐</p>
      </div>
    </section>

    <!-- 结算区：左收银表单 + 右订单小票 -->
    <section class="checkout" v-if="packages.length > 0">
      <div class="checkout-form">
        <h3 class="block-title">充值信息</h3>

        <div class="field">
          <label>会员<i>*</i></label>
          <el-select
            v-model="selectedCustomerId"
            filterable remote clearable
            :remote-method="loadCustomers"
            :loading="customerLoading"
            placeholder="搜索姓名 / 手机号"
            size="large"
            style="width: 100%"
          >
            <el-option
              v-for="c in customerOptions"
              :key="c.id"
              :label="c.phone ? `${c.name}（${c.phone}）` : c.name"
              :value="c.id"
            />
          </el-select>
        </div>

        <div class="field">
          <label>收款方式</label>
          <div class="pay-methods">
            <button
              v-for="ch in channelOptions"
              :key="ch.value"
              type="button"
              class="pay-method"
              :class="{ on: channel === ch.value }"
              @click="channel = ch.value"
            >
              <span class="pay-emoji">{{ ch.emoji }}</span>{{ ch.label }}
            </button>
          </div>
        </div>

        <div class="field">
          <label>备注</label>
          <el-input v-model="note" placeholder="选填，如：双十一活动办卡" maxlength="100" size="large" />
        </div>
      </div>

      <!-- 订单小票 -->
      <aside class="receipt">
        <div class="receipt-head">
          <el-icon><Wallet /></el-icon><span>充值小票</span>
        </div>

        <div class="receipt-body" v-if="selectedPackage">
          <div class="r-row">
            <span>套餐</span>
            <strong>{{ selectedPackage.name }}</strong>
          </div>
          <div class="r-row">
            <span>会员</span>
            <strong>{{ selectedCustomer ? selectedCustomer.name : '未选择' }}</strong>
          </div>
          <div class="r-row">
            <span>实付本金</span>
            <strong>{{ formatMoney(selectedPackage.price) }}</strong>
          </div>
          <div class="r-row bonus" v-if="selectedPackage.bonus_amount > 0">
            <span>赠送金额</span>
            <strong>+ {{ formatMoney(selectedPackage.bonus_amount) }}</strong>
          </div>
          <div class="r-gifts" v-if="selectedPackage.gifts.length">
            <span>随附赠品</span>
            <div class="r-gift-tags">
              <span v-for="(g, i) in selectedPackage.gifts" :key="i" class="r-gift">🎁 {{ g }}</span>
            </div>
          </div>

          <div class="receipt-total">
            <span>实际到账</span>
            <span class="receipt-total-num">{{ formatMoney(creditedAmount) }}</span>
          </div>

          <el-button
            type="primary" size="large" class="pay-btn"
            :icon="CreditCard" :loading="submitting" :disabled="!canSubmit"
            @click="submit"
          >
            确认充值
          </el-button>
          <p class="pay-tip">充值后立即到账会员余额，可在客户详情查看流水</p>
        </div>

        <div class="receipt-empty" v-else>
          <div class="empty-emoji">🧾</div>
          <p>请选择一个套餐</p>
        </div>
      </aside>
    </section>
  </div>
</template>

<style scoped>
.recharge-page {
  max-width: 1180px;
  margin: 0 auto;
  padding-bottom: 24px;
}

/* ---- 页头 ---- */
.rc-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}
.rc-header-text h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}
.rc-header-text p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}
.rc-step-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--text-secondary);
}
.rc-step { display: inline-flex; align-items: center; gap: 6px; font-weight: 500; }
.rc-step i {
  width: 18px; height: 18px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--primary) 16%, transparent);
  color: var(--primary);
  font-style: normal;
  font-size: 11px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.rc-step-arrow { color: var(--text-muted); }

/* ---- 套餐卡片 ---- */
.tiers {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 22px;
  align-items: stretch;
  margin-bottom: 28px;
  min-height: 220px;
}
.tier {
  position: relative;
  background: var(--card);
  border: 1.5px solid var(--border);
  border-radius: 20px;
  padding: 28px 24px 22px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.tier:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.10);
  border-color: color-mix(in srgb, var(--primary) 50%, var(--border));
}
.tier.selected {
  border-color: var(--primary);
  box-shadow: 0 18px 44px color-mix(in srgb, var(--primary) 22%, transparent);
}
/* 推荐档：放大悬浮 + 渐变描边感 */
.tier.featured {
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--primary) 7%, var(--card)) 0%, var(--card) 60%);
  border-color: color-mix(in srgb, var(--primary) 45%, var(--border));
  box-shadow: 0 16px 38px color-mix(in srgb, var(--primary) 18%, transparent);
}
@media (min-width: 940px) {
  .tier.featured { transform: scale(1.045); }
  .tier.featured:hover { transform: scale(1.045) translateY(-6px); }
}

.tier-badge {
  position: absolute;
  top: -13px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, var(--primary), var(--orange));
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 5px 16px;
  border-radius: 999px;
  white-space: nowrap;
  box-shadow: 0 6px 14px color-mix(in srgb, var(--primary) 45%, transparent);
}

.tier-name {
  font-size: 22px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}
.tier-sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-secondary);
  min-height: 18px;
}

.tier-price {
  margin-top: 20px;
  display: flex;
  align-items: baseline;
  gap: 3px;
}
.tier-cur { font-size: 22px; font-weight: 700; color: var(--text-primary); }
.tier-num {
  font-size: 46px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
  letter-spacing: -1.5px;
}

.tier-credit-row {
  margin-top: 14px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
.tier-credit-label { font-size: 13px; color: var(--text-muted); }
.tier-credit-val { font-size: 16px; font-weight: 700; color: var(--text-primary); }

.tier-bonus-tag {
  margin-top: 10px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  align-self: flex-start;
  padding: 5px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--success) 14%, transparent);
  color: var(--success);
  font-size: 12.5px;
  font-weight: 600;
}
.tier-bonus-tag.muted {
  background: var(--bg-secondary);
  color: var(--text-muted);
}
.tier-bonus-pct {
  background: var(--success);
  color: #fff;
  border-radius: 999px;
  padding: 0 7px;
  font-size: 11px;
}

.tier-divider {
  height: 1px;
  background: var(--border);
  margin: 18px 0 16px;
}

.tier-feats {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 11px;
  flex: 1;
}
.tier-feats li {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  font-size: 13.5px;
  color: var(--text-secondary);
  line-height: 1.45;
}
.fi { font-size: 15px; margin-top: 1px; flex-shrink: 0; }
.fi.ok { color: var(--primary); }
.fi.gift { color: var(--orange); }
.tier-feats li.gift span { color: var(--text-primary); font-weight: 500; }

.tier-pick {
  margin-top: 22px;
  width: 100%;
  height: 44px;
  border: 1.5px solid var(--border);
  background: var(--card);
  color: var(--text-primary);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.18s ease;
}
.tier:hover .tier-pick { border-color: var(--primary); color: var(--primary); }
.tier-pick.on {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
  box-shadow: 0 8px 18px color-mix(in srgb, var(--primary) 35%, transparent);
}

.tiers-empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 48px;
}
.empty-emoji { font-size: 46px; }
.empty-title { margin: 10px 0 2px; font-weight: 600; color: var(--text-secondary); }
.empty-hint { margin: 0; font-size: 13px; color: var(--text-muted); }

/* ---- 结算区 ---- */
.checkout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 22px;
  align-items: start;
}
.checkout-form {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 24px 26px;
}
.block-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 18px;
}
.field { margin-bottom: 20px; }
.field:last-child { margin-bottom: 0; }
.field > label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.field > label i { color: var(--danger); font-style: normal; margin-left: 2px; }

.pay-methods { display: flex; gap: 12px; flex-wrap: wrap; }
.pay-method {
  flex: 1;
  min-width: 96px;
  height: 48px;
  border: 1.5px solid var(--border);
  background: var(--card);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.18s ease;
}
.pay-method:hover { border-color: var(--primary); color: var(--primary); }
.pay-method.on {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 8%, transparent);
  color: var(--primary);
}
.pay-emoji { font-size: 16px; }

/* 订单小票 */
.receipt {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  overflow: hidden;
  position: sticky;
  top: 16px;
}
.receipt-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  background: linear-gradient(135deg, color-mix(in srgb, var(--primary) 12%, var(--card)), var(--card));
  border-bottom: 1px dashed var(--border);
}
.receipt-head .el-icon { color: var(--primary); }
.receipt-body { padding: 18px 20px 22px; }
.r-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  font-size: 14px;
  color: var(--text-secondary);
  padding: 7px 0;
}
.r-row strong { color: var(--text-primary); font-weight: 600; }
.r-row.bonus strong { color: var(--success); }
.r-gifts { padding: 8px 0; font-size: 14px; color: var(--text-secondary); }
.r-gift-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.r-gift {
  font-size: 12px;
  background: color-mix(in srgb, var(--orange) 12%, transparent);
  color: var(--orange);
  padding: 3px 9px;
  border-radius: 8px;
  font-weight: 500;
}
.receipt-total {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  padding-top: 16px;
  border-top: 1px dashed var(--border);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.receipt-total-num {
  font-size: 26px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.5px;
}
.pay-btn {
  width: 100%;
  margin-top: 18px;
  height: 48px;
  font-size: 15px;
  font-weight: 700;
  border-radius: 12px;
}
.pay-tip {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  line-height: 1.5;
}
.receipt-empty {
  padding: 48px 20px;
  text-align: center;
  color: var(--text-muted);
}
.receipt-empty .empty-emoji { font-size: 40px; }
.receipt-empty p { margin: 10px 0 0; font-size: 14px; }

@media (max-width: 880px) {
  .checkout { grid-template-columns: 1fr; }
  .receipt { position: static; }
}
</style>
