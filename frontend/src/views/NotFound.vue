<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="not-found-icon">🐾</div>
      <h2>404</h2>
      <p>页面不存在</p>
      <el-button type="primary" size="large" @click="router.push('/dashboard')">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 160px);
}
.not-found-content {
  text-align: center;
}
.not-found-icon {
  font-size: 80px;
  margin-bottom: 16px;
}
.not-found-content h2 {
  font-size: 48px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}
.not-found-content p {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0 0 24px 0;
}
</style>