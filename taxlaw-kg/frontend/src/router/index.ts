import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('../pages/Layout.vue'),
      children: [
        {
          path: '',
          redirect: '/dashboard'
        },
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('../pages/Dashboard.vue')
        },
        {
          path: 'documents',
          name: 'Documents',
          component: () => import('../pages/Documents.vue')
        },
        {
          path: 'schema',
          name: 'Schema',
          component: () => import('../pages/Schema.vue')
        },
        {
          path: 'graph',
          name: 'Graph',
          component: () => import('../pages/Graph.vue')
        },
        {
          path: 'query',
          name: 'Query',
          component: () => import('../pages/Query.vue')
        }
      ]
    }
  ]
})

export default router
