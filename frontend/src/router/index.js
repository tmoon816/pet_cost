import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '数据大盘' }
  },
  {
    path: '/bills',
    name: 'bills',
    component: () => import('@/views/bills/BillList.vue'),
    meta: { title: '收支账单' }
  },
  {
    path: '/pets',
    name: 'pets',
    component: () => import('@/views/pets/PetList.vue'),
    meta: { title: '宠物档案' }
  },
  {
    path: '/pets/:id',
    name: 'pet-detail',
    component: () => import('@/views/pets/PetDetail.vue'),
    meta: { title: '宠物详情' }
  },
  {
    path: '/categories',
    name: 'categories',
    component: () => import('@/views/categories/CategoryList.vue'),
    meta: { title: '消费分类' }
  },
  {
    path: '/budget',
    name: 'budget',
    component: () => import('@/views/budget/Budget.vue'),
    meta: { title: '月度预算' }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 路由守卫修改页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 宠物花费管理系统`
  }
  next()
})

export default router
