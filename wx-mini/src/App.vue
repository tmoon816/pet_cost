<script setup>
import { onLaunch, onShow } from '@dcloudio/uni-app'

onLaunch(() => {
  console.log('App Launch')
})

onShow(() => {
  console.log('App Show')
})
</script>

<style>
/* 全局设计 token */
page {
  --c-primary: #5B5BF2;
  --c-primary-strong: #4F46E5;
  --c-primary-soft: #EEF0FF;
  --c-violet: #8B5CF6;
  --c-accent: #FB923C;
  --c-accent-soft: #FFEDD5;
  --c-success: #10B981;
  --c-success-soft: #D1FAE5;
  --c-warn: #F59E0B;
  --c-warn-soft: #FEF3C7;
  --c-danger: #EF4444;

  --c-text-1: #0F172A;
  --c-text-2: #475569;
  --c-text-3: #94A3B8;
  --c-text-inv: #FFFFFF;

  --c-bg: #F6F7FB;
  --c-card: #FFFFFF;
  --c-line: #EEF1F6;
  --c-fill: #F1F3F9;

  --r-sm: 12rpx;
  --r-md: 20rpx;
  --r-lg: 28rpx;
  --r-pill: 999rpx;

  --sd-1: 0 2rpx 8rpx rgba(15, 23, 42, 0.04);
  --sd-2: 0 6rpx 20rpx rgba(15, 23, 42, 0.05);
  --sd-3: 0 12rpx 32rpx rgba(15, 23, 42, 0.08);
  --sd-primary: 0 10rpx 30rpx rgba(91, 91, 242, 0.32);
  --sd-warm: 0 10rpx 30rpx rgba(251, 146, 60, 0.28);

  --g-primary: linear-gradient(135deg, #5B5BF2 0%, #8B5CF6 100%);
  --g-primary-soft: linear-gradient(135deg, #EEF0FF 0%, #F3E8FF 100%);
  --g-warm: linear-gradient(135deg, #FB923C 0%, #F472B6 100%);
  --g-mint: linear-gradient(135deg, #10B981 0%, #34D399 100%);

  background-color: var(--c-bg);
  color: var(--c-text-1);
  font-size: 28rpx;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
}
</style>
