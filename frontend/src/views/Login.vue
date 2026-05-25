<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref(null)
const submitting = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    await authStore.login(form.username.trim(), form.password)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    router.replace(typeof redirect === 'string' && redirect.startsWith('/') ? redirect : '/')
  } catch (err) {
    if (err?.status === 401) {
      ElMessage.error('用户名或密码错误')
    } else if (err?.status === 503) {
      ElMessage.error('管理员账号未配置，请联系部署方')
    }
    // 其他错误已被 http 拦截器自动 toast
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    router.replace('/')
  }
})
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">
          <span class="paw">🐾</span>
        </div>
        <h2 class="login-title">宠物店管家</h2>
        <p class="login-subtitle">请使用管理员账号登录</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @keyup.enter="onSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="admin"
            :prefix-icon="User"
            autocomplete="username"
            size="large"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            autocomplete="current-password"
            show-password
            size="large"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="login-submit"
          :loading="submitting"
          @click="onSubmit"
        >
          登 录
        </el-button>
      </el-form>

      <p class="login-footer">部署在公网时务必同时启用 Nginx 访问控制</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(circle at 20% 20%, color-mix(in srgb, var(--primary) 18%, transparent), transparent 55%),
    radial-gradient(circle at 80% 80%, color-mix(in srgb, var(--orange) 14%, transparent), transparent 55%),
    var(--bg);
}
.login-card {
  width: 100%;
  max-width: 380px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 32px 28px 24px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.08);
}
.login-header {
  text-align: center;
  margin-bottom: 24px;
}
.login-logo {
  width: 56px;
  height: 56px;
  margin: 0 auto 12px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--primary), var(--orange));
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px color-mix(in srgb, var(--primary) 30%, transparent);
}
.login-logo .paw {
  font-size: 30px;
}
.login-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.login-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
}
.login-submit {
  width: 100%;
  height: 44px;
  border-radius: 999px;
  font-weight: 600;
  letter-spacing: 4px;
  margin-top: 4px;
}
.login-footer {
  margin-top: 20px;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
}
</style>
