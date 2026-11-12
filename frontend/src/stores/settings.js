import { reactive, ref } from 'vue'

const DEFAULT_SETTINGS = {
  brand_name: 'DoubleT CRM',
  brand_logo: null,
  favicon: '/assets/frappe/images/frappe-favicon.svg',
  crm_timeline_timestamp_format: 'Relative',
  crm_timeline_sort_order: 'Oldest First',
}

const bootSettings =
  typeof window !== 'undefined' ? window.doublet_crm_settings : null
const settings = ref({ ...DEFAULT_SETTINGS, ...(bootSettings || {}) })
const brand = reactive({})

// Keep the resource-like `.doc` shape used by existing consumers without
// fetching a Single DocType that does not belong to DoubleT CRM.
const _settings = reactive({ doc: settings.value })

export function getSettings() {
  function setupBrand() {
    brand.name = settings.value.brand_name || DEFAULT_SETTINGS.brand_name
    brand.logo = settings.value.brand_logo || null
    brand.favicon = settings.value.favicon || DEFAULT_SETTINGS.favicon

    if (typeof document !== 'undefined') {
      document.title = brand.name
      let favicon = document.querySelector('link[rel="icon"]')
      if (!favicon) {
        favicon = document.createElement('link')
        favicon.rel = 'icon'
        document.head.appendChild(favicon)
      }
      favicon.href = brand.favicon
    }
  }

  return {
    _settings,
    settings,
    brand,
    setupBrand,
  }
}

getSettings().setupBrand()
