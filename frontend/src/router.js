import { createRouter, createWebHistory } from 'vue-router'

import DealsView from '@/pages/DealsView.vue'
const FrappeDeal = () => import('@/pages/FrappeDeal.vue')
import LeadsView from '@/pages/LeadsView.vue'
const FrappeLead = () => import('@/pages/FrappeLead.vue')
import ContactsView from '@/pages/ContactsView.vue'
import CompaniesView from '@/pages/CompaniesView.vue'
import PlaceholderView from '@/pages/PlaceholderView.vue'

const routes = [
  {
    path: '/',
    redirect: '/deals',
  },
  {
    path: '/deals',
    name: 'Deals',
    component: DealsView,
  },
  {
    path: '/deals/:dealId',
    name: 'DealDetail',
    component: FrappeDeal,
    props: true,
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: PlaceholderView,
    props: {
      title: 'Dashboard',
      description: 'DoubleT CRM Analytics & Overview',
    },
  },
  {
    path: '/leads',
    name: 'Leads',
    component: LeadsView,
  },
  {
    path: '/leads/:leadId',
    name: 'LeadDetail',
    component: FrappeLead,
    props: true,
  },
  {
    path: '/contacts',
    name: 'Contacts',
    component: ContactsView,
  },
  {
    path: '/companies',
    name: 'Companies',
    component: CompaniesView,
  },
  {
    path: '/notes',
    name: 'Notes',
    component: PlaceholderView,
    props: {
      title: 'Notes',
      description: 'DoubleT CRM Notes Management',
    },
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: PlaceholderView,
    props: {
      title: 'Tasks',
      description: 'DoubleT CRM Tasks Management',
    },
  },
  {
    path: '/call-logs',
    name: 'Call Logs',
    component: PlaceholderView,
    props: {
      title: 'Call Logs',
      description: 'DoubleT CRM Call Logs Management',
    },
  },
]

const router = createRouter({
  history: createWebHistory('/doublet-crm'),
  routes,
})

export default router
