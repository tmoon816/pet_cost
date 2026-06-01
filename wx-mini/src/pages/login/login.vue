<template>
  <view class="login">
    <view class="bg-blob bg-blob-1"></view>
    <view class="bg-blob bg-blob-2"></view>

    <view class="brand">
      <view class="logo">PC</view>
      <view class="brand-name">宠物店管理</view>
      <view class="brand-tag">店员办公 · 移动端</view>
    </view>

    <view class="card">
      <view class="card-title">欢迎回来</view>
      <view class="card-sub">登录账号继续工作</view>

      <view class="field">
        <text class="field-label">账号</text>
        <input
          class="field-input"
          v-model="form.username"
          placeholder="请输入管理员账号"
          placeholder-class="ph"
        />
      </view>

      <view class="field">
        <text class="field-label">密码</text>
        <input
          class="field-input"
          v-model="form.password"
          type="password"
          password
          placeholder="请输入密码"
          placeholder-class="ph"
        />
      </view>

      <button class="btn-primary" :loading="loading" :disabled="loading" @click="onSubmit">
        登录
      </button>

      <view class="tip">默认账号密码与桌面后台一致</view>
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
    /* request 已弹 toast */
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss">
.login {
  min-height: 100vh;
  background: linear-gradient(160deg, #5B5BF2 0%, #8B5CF6 60%, #EC4899 100%);
  padding: 220rpx 40rpx 60rpx;
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
}
.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60rpx);
  opacity: 0.4;
}
.bg-blob-1 {
  width: 400rpx;
  height: 400rpx;
  background: #F472B6;
  top: -100rpx;
  right: -120rpx;
}
.bg-blob-2 {
  width: 360rpx;
  height: 360rpx;
  background: #38BDF8;
  bottom: 200rpx;
  left: -120rpx;
}
.brand {
  position: relative;
  text-align: center;
  margin-bottom: 60rpx;
}
.logo {
  width: 120rpx;
  height: 120rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(20rpx);
  color: #fff;
  font-size: 48rpx;
  font-weight: 700;
  text-align: center;
  line-height: 120rpx;
  margin: 0 auto;
  letter-spacing: 2rpx;
  box-shadow: 0 12rpx 32rpx rgba(0, 0, 0, 0.18);
}
.brand-name {
  margin-top: 24rpx;
  font-size: 40rpx;
  font-weight: 600;
  color: #fff;
  letter-spacing: 1rpx;
}
.brand-tag {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.75);
}
.card {
  position: relative;
  background: #fff;
  border-radius: 32rpx;
  padding: 56rpx 44rpx 48rpx;
  box-shadow: 0 20rpx 60rpx rgba(15, 23, 42, 0.18);
}
.card-title {
  font-size: 40rpx;
  font-weight: 600;
  color: #0F172A;
}
.card-sub {
  margin-top: 8rpx;
  color: #94A3B8;
  font-size: 26rpx;
}
.field {
  margin-top: 36rpx;
}
.field-label {
  font-size: 24rpx;
  color: #475569;
  letter-spacing: 1rpx;
}
.field-input {
  margin-top: 14rpx;
  height: 92rpx;
  background: #F1F3F9;
  border-radius: 16rpx;
  padding: 0 28rpx;
  font-size: 30rpx;
  color: #0F172A;
}
.ph {
  color: #94A3B8;
}
.btn-primary {
  margin-top: 56rpx;
  height: 96rpx;
  line-height: 96rpx;
  background: linear-gradient(135deg, #5B5BF2 0%, #8B5CF6 100%);
  color: #fff;
  border-radius: 20rpx;
  font-size: 32rpx;
  font-weight: 500;
  letter-spacing: 2rpx;
  box-shadow: 0 12rpx 28rpx rgba(91, 91, 242, 0.4);
  border: none;
  &::after {
    border: none;
  }
}
.tip {
  margin-top: 32rpx;
  text-align: center;
  color: #94A3B8;
  font-size: 22rpx;
}
</style>
