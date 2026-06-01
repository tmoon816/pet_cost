<template>
  <view class="page">
    <!-- Hero -->
    <view class="hero">
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
    <view class="cell-group">
      <view class="cell" @click="onLogout">
        <text class="cell-icon">🚪</text>
        <view class="cell-main">
          <text class="cell-label danger">退出登录</text>
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
    confirmColor: '#FFA62B',
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

/* Hero —— 奶油暖白 */
.hero {
  display: flex;
  align-items: center;
  background: #FFFAF2;
  border: 1rpx solid #FFE4BD;
  border-radius: 24rpx;
  padding: 36rpx 32rpx;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04);
}
.avatar {
  width: 116rpx;
  height: 116rpx;
  border-radius: 28rpx;
  background: #FFA62B;
  color: #FFFFFF;
  font-size: 50rpx;
  font-weight: 600;
  text-align: center;
  line-height: 116rpx;
  margin-right: 28rpx;
  flex-shrink: 0;
  letter-spacing: 2rpx;
  box-shadow: 0 6rpx 16rpx rgba(255, 166, 43, 0.22);
}
.info {
  flex: 1;
}
.name {
  font-size: 36rpx;
  font-weight: 600;
  color: #212529;
  letter-spacing: 1rpx;
}
.role {
  margin-top: 10rpx;
  font-size: 24rpx;
  color: #6C757D;
}

/* Cell groups */
.cell-group {
  margin-top: 24rpx;
  background: #FFFFFF;
  border: 1rpx solid #E9ECEF;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 6rpx rgba(33, 37, 41, 0.04), 0 1rpx 2rpx rgba(33, 37, 41, 0.03);
}
.cell {
  display: flex;
  align-items: center;
  padding: 26rpx 28rpx;
  border-bottom: 1rpx solid #F1F3F5;
  &:last-child {
    border-bottom: none;
  }
  &:active {
    background: #F8F9FA;
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
  color: #212529;
  &.danger {
    color: #E03131;
  }
}
.cell-value {
  margin-top: 4rpx;
  font-size: 22rpx;
  color: #ADB5BD;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cell-arrow {
  color: #DEE2E6;
  font-size: 32rpx;
}

.footer {
  margin-top: 60rpx;
  text-align: center;
  font-size: 22rpx;
  color: #DEE2E6;
  letter-spacing: 1rpx;
}
</style>
