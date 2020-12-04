import Vue from 'vue'
import VueRouter from 'vue-router'


Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    meta: {
        requireAuth: true
    },

    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "home" */ '../views/Home.vue')
  },
  {
    path: '/Wavelabeling',
    name: 'Wavelabeling',
    meta: {
        requireAuth: true
    },

    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "wavelabeling" */ '../views/Wavelabeling.vue')
  },
  {
    path: '/Ocrlabeling',
    name: 'Ocrlabeling',
    meta: {
        requireAuth: true
    },

    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "ocrlabeling" */ '../views/Ocrlabeling.vue')
  },
  {
    path: '/Contentlabeling',
    name: 'Contentlabeling',
    meta: {
        requireAuth: true
    },

    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "contentlabeling" */ '../views/Contentlabeling.vue')
  },
  {
    path: '/Ocr',
    name: 'Ocr',
    meta: {
        requireAuth: true
    },

    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "ocr" */ '../views/Ocr.vue')
  },
  {
    path: '/Target',
    name: 'Target',
    meta: {
        requireAuth: true
    },

    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "target" */ '../views/Target.vue')
  },
  {
    path: '/logout',
    name: 'Logout',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "logout" */ '../views/Logout.vue')
  },
  {
    path: '/login',
    name: 'Login',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "login" */ '../views/Login.vue')
  },
  {
    path: '/about',
    name: 'About',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ '../views/About.vue')
  },
]

const router = new VueRouter({
  mode: 'hash',
  routes
})

export default router
