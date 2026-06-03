<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as customersApi from '@/api/customers'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  customerId: { type: [Number, String], required: true },
  customerName: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'success'])

const submitting = ref(false)
const formRef = ref(null)
const form = reactive({
  amount: '',
  bonus_amount: '',
  channel: 'wechat',
})

const rules = {
  amount: [
    { required: true, message: '请输入充值金额', trigger: 'blur' },
    {
      validator: (_, value, cb) => {
        const n = Number(value)
        if (Number.isFinite(n) && n > 0) cb()
        else cb(new Error('充值金额需大于 0'))
      },
      trigger: 'blur',
    },
  ],
  channel: [{ required: true, message: '请选择收款渠道', trigger: 'change' }],
}

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const totalCredit = computed(() => {
  const a = Number(form.amount) || 0
  const b = Number(form.bonus_amount) || 0
  return a + b
})

watch(visible, (v) => {
  if (v) {
    form.amount = ''
    form.bonus_amount = ''
    form.channel = 'wechat'
  }
})

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await customersApi.rechargeCustomer(props.customerId, {
        amount: String(form.amount),
        bonus_amount: form.bonus_amount ? String(form.bonus_amount) : '0',
        channel: form.channel,
      })
      ElMessage.success(`充值成功，到账 ¥${totalCredit.value.toFixed(2)}`)
      visible.value = false
      emit('success')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <el-dialog v-model="visible" :title="`充值 · ${customerName}`" width="440px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item label="充值金额" prop="amount">
        <el-input v-model="form.amount" placeholder="实付本金，单位元">
          <template #prefix>¥</template>
        </el-input>
      </el-form-item>
      <el-form-item label="赠送金额">
        <el-input v-model="form.bonus_amount" placeholder="选填，如充500送50">
          <template #prefix>¥</template>
        </el-input>
      </el-form-item>
      <el-form-item label="收款渠道" prop="channel">
        <el-radio-group v-model="form.channel">
          <el-radio label="wechat">微信</el-radio>
          <el-radio label="alipay">支付宝</el-radio>
          <el-radio label="cash">现金</el-radio>
        </el-radio-group>
      </el-form-item>
      <div class="credit-hint">本次到账（本金 + 赠送）：<b>¥{{ totalCredit.toFixed(2) }}</b></div>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :icon="'Wallet'" :loading="submitting" @click="submit">确认充值</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.credit-hint {
  margin-left: 90px;
  font-size: 13px;
  color: var(--el-text-color-secondary, #909399);
}
.credit-hint b {
  color: var(--el-color-success, #67c23a);
  font-size: 16px;
}
</style>
