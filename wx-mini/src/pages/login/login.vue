<template>
  <view class="login">
    <view class="login-card">
      <view class="title">宠物店管理</view>
      <view class="subtitle">店员登录</view>

      <view class="field">
        <text class="label">账号</text>
        <input
          class="input"
          v-model="form.username"
          placeholder="请输入管理员账号"
          placeholder-class="ph"
        />
      </view>

      <view class="field">
        <text class="label">密码</text>
        <input
          class="input"
          v-model="form.password"
          type="password"
          password
          placeholder="请输入密码"
          placeholder-class="ph"
        />
      </view>

      <button class="btn" :loading="loading" :disabled="loading" @click="onSubmit">
        登录
      </button>

      <view class="tip">提示：默认账号密码与桌面后台一致</view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function onSubmit() {
  if (!form.username || !form.password) {
    uni.showToast({ title: '请输入账号和密码', icon: 'none' })
    return
  }
  loading.value = true
  try {
    await auth.login({ username: form.username, password: form.password })
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => uni.switchTab({ url: '/pages/index/index' }), 400)
  } catch (e) {
    // request 已弹 toast
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss">
.login {
  min-height: 100vh;
  background: linear-gradient(160deg, #5b7fff 0%, #8aa3ff 100%);
  padding: 200rpx 40rpx 60rpx;
  box-sizing: border-box;
}
.login-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 60rpx 48rpx;
  box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.08);
}
.title {
  font-size: 44rpx;
  font-weight: 600;
  color: #1f2329;
}
.subtitle {
  margin-top: 8rpx;
  color: #8a8f99;
  font-size: 26rpx;
}
.field {
  margin-top: 40rpx;
}
.label {
  font-size: 26rpx;
  color: #4a5160;
}
.input {
  margin-top: 12rpx;
  height: 84rpx;
  border: 1rpx solid #e5e7eb;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 30rpx;
}
.ph {
  color: #b0b4bd;
}
.btn {
  margin-top: 56rpx;
  height: 88rpx;
  line-height: 88rpx;
  background: #5b7fff;
  color: #fff;
  border-radius: 12rpx;
  font-size: 32rpx;
}
.tip {
  margin-top: 32rpx;
  text-align: center;
  color: #b0b4bd;
  font-size: 24rpx;
}
</style>
