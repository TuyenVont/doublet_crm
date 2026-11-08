
import { createRouter, createWebHistory } from 'vue-router'

import DealsView from '@/pages/DealsView.vue'
const DealDetailView = () => import('@/pages/DealDetailView.vue')
import LeadsView from '@/pages/LeadsView.vue'
const FrappeLead = () => import('@/pages/FrappeLead.vue')
import ContactsView from '@/pages/ContactsView.vue'
const ContactDetailView = () => import('@/pages/ContactDetailView.vue')
import CompaniesView from '@/pages/CompaniesView.vue'
const ProductsView = () => import('@/pages/ProductsView.vue')
const ProductCategoriesView = () => import('@/pages/ProductCategoriesView.vue')
const QuotationsView = () => import('@/pages/QuotationsView.vue')
const QuotationForm = () => import('@/pages/QuotationForm.vue')
const CompanyDetailView = () => import('@/pages/CompanyDetailView.vue')
import PlaceholderView from '@/pages/PlaceholderView.vue'
const TasksView = () => import('@/pages/Tasks.vue')
const NotesView = () => import('@/pages/Notes.vue')

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
    component: DealDetailView,
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
    path: '/contacts/new',
    name: 'ContactCreate',
    component: ContactDetailView,
  },
  {
    path: '/contacts/:contactId',
    name: 'ContactDetail',
    component: ContactDetailView,
  },
  {
    path: '/companies',
    name: 'Companies',
    component: CompaniesView,
  },
  {
    path: '/companies/new',
    name: 'CompanyCreate',
    component: CompanyDetailView,
  },
  {
    path: '/companies/:companyId',
    name: 'CompanyDetail',
    component: CompanyDetailView,
  },
  {
    path: '/products/categories',
    name: 'ProductCategories',
    component: ProductCategoriesView,
  },
  {
    path: '/products',
    name: 'Products',
    component: ProductsView,
  },
  { path: '/quotations', name: 'Quotations', component: QuotationsView },
  { path: '/quotations/new', name: 'QuotationCreate', component: QuotationForm },
  { path: '/quotations/:quotationId', name: 'QuotationDetail', component: QuotationForm, props: true },
  {
    path: '/notes',
    name: 'Notes',
    component: NotesView,
  },
{
  path: '/tasks',
  name: 'Tasks',
  component: TasksView,
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
