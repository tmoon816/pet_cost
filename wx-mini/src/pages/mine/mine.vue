<template>
  <view class="page">
    <view class="user-card">
      <view class="avatar">{{ avatarText }}</view>
      <view class="info">
        <view class="name">{{ auth.username || '未登录' }}</view>
        <view class="role">店员</view>
      </view>
    </view>

    <view class="cell-group">
      <view class="cell" @click="onLogout">
        <text class="cell-label">退出登录</text>
        <text class="cell-arrow">›</text>
      </view>
    </view>

    <view class="version">v0.0.1</view>
  </view>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

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
  padding: 32rpx;
}
.user-card {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}
.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: #5b7fff;
  color: #fff;
  font-size: 40rpx;
  font-weight: 600;
  text-align: center;
  line-height: 96rpx;
  margin-right: 24rpx;
}
.info {
  flex: 1;
}
.name {
  font-size: 32rpx;
  font-weight: 600;
  color: #1f2329;
}
.role {
  margin-top: 8rpx;
  color: #8a8f99;
  font-size: 24rpx;
}
.cell-group {
  margin-top: 32rpx;
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
}
.cell {
  display: flex;
  align-items: center;
  height: 96rpx;
  padding: 0 32rpx;
  border-bottom: 1rpx solid #f0f1f5;
  &:last-child {
    border-bottom: none;
  }
}
.cell-label {
  flex: 1;
  font-size: 28rpx;
  color: #1f2329;
}
.cell-arrow {
  color: #b0b4bd;
  font-size: 32rpx;
}
.version {
  margin-top: 60rpx;
  text-align: center;
  color: #b0b4bd;
  font-size: 24rpx;
}
</style>
