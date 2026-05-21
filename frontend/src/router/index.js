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
    meta: { title: '营业概览' }
  },
  {
    path: '/customers',
    name: 'customers',
    component: () => import('@/views/customers/CustomerList.vue'),
    meta: { title: '会员/客户档案' }
  },
  {
    path: '/customers/:id',
    name: 'customer-detail',
    component: () => import('@/views/customers/CustomerDetail.vue'),
    props: true,
    meta: { title: '客户详情' }
  },
  {
    path: '/bills',
    name: 'bills',
    component: () => import('@/views/bills/BillList.vue'),
    meta: { title: '服务订单' }
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
    props: true,
    meta: { title: '宠物详情' }
  },
  {
    path: '/categories',
    name: 'categories',
    component: () => import('@/views/categories/CategoryList.vue'),
    meta: { title: '服务项目' }
  },
  {
    path: '/budget',
    name: 'budget',
    component: () => import('@/views/budget/Budget.vue'),
    meta: { title: '经营预算' }
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

router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 宠物店管理系统`
  }
  next()
})

export default router
