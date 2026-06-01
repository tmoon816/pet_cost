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
/* 全局设计 token —— 对齐 web 端「活力元气风」 */
page {
  /* 主色 */
  --c-primary: #FFA62B;
  --c-primary-hover: #F5940F;
  --c-primary-light: #FFBD5C;
  --c-primary-soft: #FFF4E5;
  --c-primary-border: #FFE4BD;

  /* 背景 / 卡片 / 边框 */
  --c-bg: #F8F9FA;
  --c-bg-2: #F1F3F5;
  --c-bg-warm: #FFFAF2;
  --c-card: #FFFFFF;
  --c-border: #E9ECEF;
  --c-border-strong: #DEE2E6;
  --c-divider: #F1F3F5;

  /* 文字层级 */
  --c-text-1: #212529;
  --c-text-2: #6C757D;
  --c-text-3: #ADB5BD;
  --c-text-inv: #FFFFFF;

  /* 状态色（饱和度统一回收，不刺眼） */
  --c-success: #5DA716;
  --c-success-soft: #F4F9E6;
  --c-warn: #AE886A;
  --c-warn-soft: #F7EFE8;
  --c-danger: #E03131;
  --c-danger-soft: #FFEEEE;
  --c-info: #1C7ED6;
  --c-info-soft: #E7F3FB;
  --c-purple: #7048E8;
  --c-purple-soft: #F1ECFF;

  /* 圆角 */
  --r-sm: 12rpx;
  --r-md: 20rpx;
  --r-lg: 24rpx;
  --r-pill: 999rpx;

  /* 阴影：Notion 轻盈 — 极弱 */
  --sd-1: 0 2rpx 6rpx rgba(33, 37, 41, 0.04);
  --sd-2: 0 4rpx 12rpx rgba(33, 37, 41, 0.06);
  --sd-card: 0 2rpx 6rpx rgba(33, 37, 41, 0.04), 0 1rpx 2rpx rgba(33, 37, 41, 0.03);
  --sd-primary: 0 6rpx 16rpx rgba(255, 166, 43, 0.22);

  background-color: var(--c-bg);
  color: var(--c-text-1);
  font-size: 28rpx;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
}
</style>
