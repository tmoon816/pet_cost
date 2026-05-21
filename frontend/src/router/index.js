import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/customers' },
  {
    path: '/customers',
    name: 'customers',
    component: () => import('@/views/customers/CustomerList.vue'),
    meta: { title: '客户管理' },
  },
  {
    path: '/customers/:id',
    name: 'customer-detail',
    component: () => import('@/views/customers/CustomerDetail.vue'),
    meta: { title: '客户详情' },
    props: true,
  },
  {
    path: '/pets/:id',
    name: 'pet-detail',
    component: () => import('@/views/pets/PetDetail.vue'),
    meta: { title: '宠物详情' },
    props: true,
  },
  {
    path: '/costs',
    name: 'costs',
    component: () => import('@/views/costs/CostList.vue'),
    meta: { title: '花费记录' },
  },
  {
    path: '/stats',
    name: 'stats',
    component: () => import('@/views/Stats.vue'),
    meta: { title: '花费统计' },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '分类设置' },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }
  next()
})

export default router
