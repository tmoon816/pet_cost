<template>
  <view class="page">
    <!-- 渐变 hero -->
    <view class="hero">
      <view class="hero-blob"></view>
      <view class="avatar">{{ avatarText }}</view>
      <view class="info">
        <view class="name">{{ auth.username || '未登录' }}</view>
        <view class="role">店员 · 单管理员</view>
      </view>
    </view>

    <!-- 设置组 -->
    <view class="cell-group">
      <view class="cell">
        <text class="cell-icon">📡</text>
        <view class="cell-main">
          <text class="cell-label">服务地址</text>
          <text class="cell-value">{{ baseUrl }}</text>
        </view>
      </view>
      <view class="cell">
        <text class="cell-icon">📦</text>
        <view class="cell-main">
          <text class="cell-label">版本</text>
          <text class="cell-value">v0.1.0</text>
        </view>
      </view>
    </view>

    <!-- 退出登录 -->
    <view class="cell-group danger">
      <view class="cell" @click="onLogout">
        <text class="cell-icon">🚪</text>
        <view class="cell-main">
          <text class="cell-label danger-label">退出登录</text>
        </view>
        <text class="cell-arrow">›</text>
      </view>
    </view>

    <view class="footer">为店员高效办公而生 🐾</view>
  </view>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { BASE_URL } from '@/utils/config'

const auth = useAuthStore()
const baseUrl = computed(() => BASE_URL)
const avatarText = computed(() => (auth.username || '?').slice(0, 1).toUpperCase())

onMounted(() => {
  if (!auth.isLogin) {
    uni.reLaunch({ url: '/pages/login/login' })
  }
})

function onLogout() {
  uni.showModal({
    title: '退出登录',
    content: '确定要退出登录吗？',
    confirmColor: '#5B5BF2',
    success: (res) => {
      if (res.confirm) {
        auth.logout()
        uni.reLaunch({ url: '/pages/login/login' })
      }
    },
  })
}
</script>

<style lang="scss">
.page {
  padding: 24rpx 24rpx 60rpx;
}

/* Hero */
.hero {
  position: relative;
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #5B5BF2 0%, #8B5CF6 100%);
  border-radius: 32rpx;
  padding: 40rpx 32rpx;
  color: #fff;
  overflow: hidden;
  box-shadow: 0 14rpx 40rpx rgba(91, 91, 242, 0.3);
}
.hero-blob {
  position: absolute;
  width: 280rpx;
  height: 280rpx;
  background: #F472B6;
  border-radius: 50%;
  filter: blur(50rpx);
  opacity: 0.45;
  bottom: -100rpx;
  right: -80rpx;
  pointer-events: none;
}
.avatar {
  position: relative;
  width: 120rpx;
  height: 120rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(20rpx);
  font-size: 52rpx;
  font-weight: 600;
  text-align: center;
  line-height: 120rpx;
  margin-right: 28rpx;
  flex-shrink: 0;
  letter-spacing: 2rpx;
}
.info {
  position: relative;
  flex: 1;
}
.name {
  font-size: 38rpx;
  font-weight: 600;
  letter-spacing: 1rpx;
}
.role {
  margin-top: 10rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.78);
}

/* Cell groups */
.cell-group {
  margin-top: 24rpx;
  background: #fff;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 6rpx 20rpx rgba(15, 23, 42, 0.04);
}
.cell {
  display: flex;
  align-items: center;
  padding: 28rpx 28rpx;
  border-bottom: 1rpx solid #F1F3F9;
  &:last-child {
    border-bottom: none;
  }
  &:active {
    background: #FAFBFE;
  }
}
.cell-icon {
  font-size: 32rpx;
  margin-right: 20rpx;
}
.cell-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.cell-label {
  font-size: 28rpx;
  color: #0F172A;
}
.cell-value {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #94A3B8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cell-arrow {
  color: #CBD5E1;
  font-size: 32rpx;
}
.cell-group.danger .danger-label {
  color: #EF4444;
}

.footer {
  margin-top: 60rpx;
  text-align: center;
  font-size: 22rpx;
  color: #CBD5E1;
  letter-spacing: 1rpx;
}
</style>
