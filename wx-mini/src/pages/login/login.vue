<template>
  <view class="login">
    <view class="brand">
      <view class="logo">
        <text class="logo-emoji">🐾</text>
      </view>
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
        登 录
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
  background: #FFFAF2;
  padding: 180rpx 48rpx 60rpx;
  box-sizing: border-box;
}
.brand {
  text-align: center;
  margin-bottom: 60rpx;
}
.logo {
  width: 128rpx;
  height: 128rpx;
  border-radius: 32rpx;
  background: #FFA62B;
  text-align: center;
  line-height: 128rpx;
  margin: 0 auto;
  box-shadow: 0 8rpx 24rpx rgba(255, 166, 43, 0.32);
}
.logo-emoji {
  font-size: 64rpx;
  line-height: 128rpx;
}
.brand-name {
  margin-top: 28rpx;
  font-size: 42rpx;
  font-weight: 600;
  color: #212529;
  letter-spacing: 1rpx;
}
.brand-tag {
  margin-top: 10rpx;
  font-size: 24rpx;
  color: #ADB5BD;
}

.card {
  background: #FFFFFF;
  border-radius: 24rpx;
  border: 1rpx solid #E9ECEF;
  padding: 56rpx 44rpx 48rpx;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04), 0 1rpx 2rpx rgba(33, 37, 41, 0.03);
}
.card-title {
  font-size: 38rpx;
  font-weight: 600;
  color: #212529;
}
.card-sub {
  margin-top: 8rpx;
  color: #ADB5BD;
  font-size: 24rpx;
}
.field {
  margin-top: 36rpx;
}
.field-label {
  font-size: 24rpx;
  color: #6C757D;
  font-weight: 500;
}
.field-input {
  margin-top: 14rpx;
  height: 92rpx;
  background: #F8F9FA;
  border: 1rpx solid #E9ECEF;
  border-radius: 16rpx;
  padding: 0 28rpx;
  font-size: 30rpx;
  color: #212529;
  transition: all 0.2s;
  &:focus {
    border-color: #FFA62B;
    background: #FFFFFF;
  }
}
.ph {
  color: #ADB5BD;
}
.btn-primary {
  margin-top: 56rpx;
  height: 92rpx;
  line-height: 92rpx;
  background: #FFA62B;
  color: #FFFFFF;
  border-radius: 16rpx;
  font-size: 32rpx;
  font-weight: 500;
  letter-spacing: 8rpx;
  border: none;
  &::after {
    border: none;
  }
  &:active {
    background: #F5940F;
  }
}
.tip {
  margin-top: 32rpx;
  text-align: center;
  color: #ADB5BD;
  font-size: 22rpx;
}
</style>
