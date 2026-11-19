import { onBeforeUnmount, ref, watch } from 'vue'
import { call } from 'frappe-ui'
import { message } from '@/utils/quotation'
import { buildSellableProductListRequest, resolveProductImage } from '@/utils/productCatalog'

// Shared sellable Product search used by Quotation and Order. Prices are resolved
// separately so loading this picker never overwrites saved transaction prices.
export function useSellableProducts() {
  const products = ref([]), productSearch = ref(''), productCategory = ref('')
  const productsLoading = ref(false), productHasNextPage = ref(true), productPickerError = ref('')
  const productCategories = ref([]), productCategoriesLoading = ref(false), productCategoriesError = ref('')
  let productRequestId = 0
  let productCategoryRequestId = 0
  let productSearchTimer = null
  const productPageLength = 20

  watch(productSearch, () => {
    clearTimeout(productSearchTimer)
    productSearchTimer = setTimeout(() => loadProducts(), 250)
  })
  watch(productCategory, () => {
    clearTimeout(productSearchTimer)
    void loadProducts()
  })

  async function loadProducts({ append = false } = {}) {
    if (productsLoading.value && append) return
    if (append && !productHasNextPage.value) return

    const requestId = ++productRequestId
    const start = append ? products.value.length : 0
    if (!append) {
      products.value = []
      productHasNextPage.value = true
    }
    productsLoading.value = true
    productPickerError.value = ''
    const search = productSearch.value.trim()
    try {
      const data = await call('frappe.client.get_list', buildSellableProductListRequest({
        fields: ['name', 'product_name', 'sku', 'product_kind', 'variant_of', 'image'],
        search,
        category: productCategory.value,
        start,
        pageLength: productPageLength,
      }))
      if (requestId !== productRequestId) return

      const page = Array.isArray(data) ? data : []
      const detailedPage = await hydrateProductDetails(page, requestId)
      if (requestId !== productRequestId) return
      const byName = new Map((append ? products.value : []).map((product) => [product.name, product]))
      detailedPage.forEach((product) => byName.set(product.name, product))
      products.value = [...byName.values()]
      productHasNextPage.value = page.length === productPageLength
    } catch (exception) {
      if (requestId === productRequestId) productPickerError.value = message(exception)
    } finally {
      if (requestId === productRequestId) productsLoading.value = false
    }
  }

  async function loadProductCategories() {
    const requestId = ++productCategoryRequestId
    productCategoriesLoading.value = true
    productCategoriesError.value = ''
    try {
      const data = await call('frappe.client.get_list', {
        doctype: 'DoubleT Product Category',
        fields: ['name', 'category_name'],
        order_by: 'category_name asc',
        limit_page_length: 500,
      })
      if (requestId === productCategoryRequestId) {
        productCategories.value = Array.isArray(data) ? data : []
      }
    } catch (exception) {
      if (requestId === productCategoryRequestId) productCategoriesError.value = message(exception)
    } finally {
      if (requestId === productCategoryRequestId) productCategoriesLoading.value = false
    }
  }

  async function hydrateProductDetails(page, requestId) {
    const variantParents = [...new Set(page.map((product) => product.variant_of).filter(Boolean))]
    const variantNames = page.filter((product) => product.product_kind === 'Variant').map((product) => product.name)
    if (!variantParents.length && !variantNames.length) {
      return page.map(product => ({
        ...product,
        resolved_image: resolveProductImage(product).url,
        variant_attributes: [],
      }))
    }

    const [parentsResult, attributesResult] = await Promise.allSettled([
      variantParents.length
        ? call('frappe.client.get_list', {
            doctype: 'DoubleT Product',
            fields: ['name', 'product_name', 'sku', 'image'],
            filters: [['name', 'in', variantParents]],
            limit_page_length: variantParents.length,
          })
        : Promise.resolve([]),
      variantNames.length
        ? call('frappe.client.get_list', {
            doctype: 'DoubleT Product Variant Attribute',
            parent: 'DoubleT Product',
            fields: ['parent', 'attribute_name', 'attribute_value'],
            filters: [
              ['parent', 'in', variantNames],
              ['parenttype', '=', 'DoubleT Product'],
              ['parentfield', '=', 'variant_attributes'],
            ],
            limit_page_length: 5000,
          })
        : Promise.resolve([]),
    ])
    if (requestId !== productRequestId) return []

    const parents = parentsResult.status === 'fulfilled' ? parentsResult.value : []
    const attributes = attributesResult.status === 'fulfilled' ? attributesResult.value : []

    const parentByName = new Map((parents || []).map((parent) => [parent.name, parent]))
    const attributesByProduct = {}
    for (const attribute of attributes || []) {
      if (!attribute.parent || !attribute.attribute_name) continue
      const values = attributesByProduct[attribute.parent] || (attributesByProduct[attribute.parent] = [])
      values.push(`${attribute.attribute_name}: ${attribute.attribute_value}`)
    }
    return page.map((product) => {
      const variantParent = parentByName.get(product.variant_of)
      return {
        ...product,
        resolved_image: resolveProductImage(product, variantParent ? [variantParent] : []).url,
        variant_parent: variantParent,
        variant_attributes: attributesByProduct[product.name] || [],
      }
    })
  }
  function productPickerLabel(product) {
    const details = [product.sku].filter(Boolean)
    if (product.product_kind === 'Variant') {
      if (product.variant_parent) details.push(`${__('Variant of')} ${product.variant_parent.product_name || product.variant_parent.name}`)
      if (product.variant_attributes?.length) details.push(product.variant_attributes.join(', '))
    }
    return `${product.product_name || product.name} — ${details.join(' · ')}`
  }

  onBeforeUnmount(() => {
    clearTimeout(productSearchTimer)
    productRequestId += 1
    productCategoryRequestId += 1
  })
  return {
    products,
    productSearch,
    productCategory,
    productCategories,
    productCategoriesLoading,
    productCategoriesError,
    productsLoading,
    productHasNextPage,
    productPickerError,
    loadProducts,
    loadProductCategories,
    productPickerLabel,
  }
}
