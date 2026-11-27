<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header><Button variant="subtle" :label="__('Quotations')" @click="router.push({ name: 'Quotations' })" /><span class="ml-2 text-base font-semibold">{{ isNew ? __('New Quotation') : (doc?.name || __('Quotation')) }}</span></template>
      <template #right-header>
        <Button v-if="!isNew && doc && !editing && (existingOrder || (canCreateOrder && doc.status === 'Accepted'))" :label="existingOrder ? __('Open Order') : __('Create Order')" :loading="creatingOrder" :disabled="saving" @click="createOrder" />
        <Button v-if="!isNew && doc && !editing" :label="__('Export PDF')" :loading="exporting" @click="exportPdf" />
        <Button v-if="!isNew && doc?.deal" :label="__('Back to Deal')" @click="router.push({ name: 'DealDetail', params: { dealId: doc.deal }, hash: '#quotations' })" />
        <Button v-if="!isNew && doc && canWrite && doc.status === 'Draft' && !editing" :label="__('Edit')" @click="startEditing" />
        <Button v-if="editable" variant="solid" :label="isNew ? __('Create') : __('Save')" :loading="saving" :disabled="dealLoading || pricingPending" @click="save" />
        <Button v-if="!isNew && editing" :label="__('Cancel')" @click="loadDocument" />
        <Button v-if="doc && canDelete && doc.status === 'Draft' && !editing" :label="__('Delete')" :loading="saving" @click="remove" />
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5">
      <div v-if="loading" class="p-8 text-center">{{ __('Loading quotation...') }}</div>
      <template v-else>
        <ErrorMessage v-if="error" class="mb-4" :message="error" />
        <p v-if="emailQueue" class="mb-4 text-sm text-ink-gray-7" role="status">
          {{ __('Email queued for automatic delivery. Its status will update in the Emails tab.') }} {{ emailQueue }}
        </p>
        <Button v-if="conflict" class="mb-4" :label="__('Reload latest quotation')" @click="loadDocument" />
        <div v-if="doc" class="mx-auto w-full min-w-0 max-w-[1440px] space-y-5">
          <div v-if="!isNew" class="flex gap-1 border-b border-outline-gray-2" role="tablist" :aria-label="__('Quotation sections')">
            <Button
              :label="__('Details')"
              variant="ghost"
              :class="activeTab === 'details' ? 'border-b-2 border-ink-gray-8 rounded-b-none' : ''"
              role="tab"
              :aria-selected="activeTab === 'details'"
              @click="activeTab = 'details'"
            />
            <Button
              :label="__('Emails')"
              variant="ghost"
              :class="activeTab === 'emails' ? 'border-b-2 border-ink-gray-8 rounded-b-none' : ''"
              role="tab"
              :aria-selected="activeTab === 'emails'"
              @click="activeTab = 'emails'"
            />
          </div>
          <template v-if="isNew || activeTab === 'details'">
          <div class="flex flex-wrap items-center gap-3">
            <span class="font-semibold">{{ __('Status') }}: {{ doc.status || 'Draft' }}</span>
            <span v-if="isQuotationExpired(doc, siteToday)" class="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">{{ __('Expired') }}</span>
            <span
              v-if="doc.approval_status && doc.approval_status !== 'Not Required'"
              class="rounded-full px-2 py-0.5 text-xs font-medium"
              :class="approvalBadgeClass(doc.approval_status)"
            >
              {{ __('Approval') }}: {{ __(doc.approval_status) }}
            </span>
            <span v-if="doc.deal">{{ __('Deal') }}: <button v-if="dealLabel" class="font-medium hover:underline" @click="openDeal">{{ dealLabel }}</button><span v-else>—</span></span>
            <template v-if="!isNew && !editing && canWrite">
              <Button v-if="doc.status === 'Draft'" :label="__('Send by Email')" :disabled="saving || sendingEmail || approvalBlockingSend" :tooltip="approvalBlockingSend ? __('Discount approval is required before sending.') : ''" @click="openEmailDialog" />
              <Button v-if="doc.status === 'Draft'" :label="__('Mark as Sent')" :loading="saving" :disabled="approvalBlockingSend" :tooltip="approvalBlockingSend ? __('Discount approval is required before sending.') : ''" @click="changeStatus('Sent')" />
              <template v-if="doc.status === 'Sent'"><Button :label="__('Mark Accepted')" :loading="saving" @click="changeStatus('Accepted')" /><Button :label="__('Mark Rejected')" :loading="saving" @click="changeStatus('Rejected')" /></template>
            </template>
            <span v-if="doc.status === 'Sent'" class="text-xs text-ink-gray-5">{{ __('Delivery confirmed manually.') }}</span>
          </div>
          <div v-if="!isNew && doc.approval_status && doc.approval_status !== 'Not Required'" class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 text-sm">
            <div class="space-y-1">
              <p class="font-medium text-ink-gray-8">
                {{ __('Discount Approval') }}: {{ __(doc.approval_status) }}
              </p>
              <p v-if="doc.approval_requested_by" class="text-xs text-ink-gray-6">
                {{ __('Requested by {0}', [doc.approval_requested_by]) }}<span v-if="doc.approval_requested_on"> · {{ doc.approval_requested_on }}</span>
              </p>
              <p v-if="doc.approved_by && ['Approved', 'Rejected'].includes(doc.approval_status)" class="text-xs text-ink-gray-6">
                {{ doc.approval_status === 'Approved' ? __('Approved by {0}', [doc.approved_by]) : __('Rejected by {0}', [doc.approved_by]) }}<span v-if="doc.approved_on"> · {{ doc.approved_on }}</span>
              </p>
              <p v-if="doc.approval_status === 'Rejected' && doc.rejection_reason" class="text-xs text-red-700">
                {{ __('Reason') }}: {{ doc.rejection_reason }}
              </p>
              <p v-if="doc.approval_status === 'Pending' && isOwnApprovalRequest" class="text-xs text-amber-700">
                {{ __('You cannot approve or reject your own discount approval request.') }}
              </p>
            </div>
            <div v-if="!editing && doc.status === 'Draft'" class="flex flex-wrap gap-2">
              <Button
                v-if="canWrite && ['Required', 'Rejected'].includes(doc.approval_status)"
                variant="solid"
                :label="__('Request Approval')"
                :loading="approvalBusy"
                @click="requestApproval"
              />
              <template v-if="doc.approval_status === 'Pending' && canManageApproval && !isOwnApprovalRequest">
                <Button variant="solid" :label="__('Approve Discount')" :loading="approvalBusy" @click="approveDiscountRequest" />
                <Button variant="subtle" theme="red" :label="__('Reject Discount')" :loading="approvalBusy" @click="rejectDiscountRequest" />
              </template>
            </div>
          </div>
          <fieldset :disabled="!editable" class="space-y-4">
            <div class="grid gap-3 lg:grid-cols-2 xl:grid-cols-4">
              <section class="setup-step">
                <p class="setup-step-title"><span>1</span>{{ __('Customer Type') }} *</p>
                <label class="field">
                  <span class="sr-only">{{ __('Customer Type') }}</span>
                  <select v-model="doc.customer_type" :disabled="Boolean(doc.deal)" @change="customerChanged">
                    <option value="">{{ __('Select customer type') }}</option>
                    <option value="PERSONAL">Personal</option>
                    <option value="COMPANY">Company</option>
                  </select>
                </label>
                <p v-if="doc.deal" class="setup-guidance">{{ __('Unlink the Deal before changing Customer Type.') }}</p>
                <p v-else class="setup-guidance">{{ __('Choose Personal or Company to continue.') }}</p>
              </section>

              <section class="setup-step">
                <p class="setup-step-title"><span>2</span>{{ __('Contact / Company') }}</p>
                <p v-if="!doc.customer_type" class="setup-placeholder">{{ __('Select a customer type first.') }}</p>
                <template v-else-if="doc.customer_type === 'PERSONAL'">
                  <label class="field">{{ __('Contact') }} *
                    <select v-model="doc.contact" :disabled="Boolean(doc.deal)" @change="contactChanged">
                      <option value="">{{ __('Select Contact') }}</option>
                      <option v-if="doc.contact && !contacts.some(x => x.name === doc.contact)" :value="doc.contact">{{ doc.contact }} ({{ __('unavailable') }})</option>
                      <option v-for="contact in availableContacts" :key="contact.name" :value="contact.name">{{ contactLabel(contact) }}</option>
                    </select>
                  </label>
                </template>
                <template v-else>
                  <label class="field">{{ __('Company') }} *
                    <select v-model="doc.company" :disabled="Boolean(doc.deal)" @change="companyChanged">
                      <option value="">{{ __('Select Company') }}</option>
                      <option v-if="doc.company && !companies.some(x => x.name === doc.company)" :value="doc.company">{{ doc.company }} ({{ __('unavailable') }})</option>
                      <option v-for="company in companies" :key="company.name" :value="company.name">{{ company.company_name || company.name }}</option>
                    </select>
                  </label>
                  <label class="field">{{ __('Contact') }} <span class="font-normal text-ink-gray-5">({{ __('optional') }})</span>
                    <select v-model="doc.contact" :disabled="Boolean(doc.deal) || !doc.company" @change="contactChanged">
                      <option value="">{{ doc.company ? __('No Contact') : __('Select a Company first') }}</option>
                      <option v-if="doc.contact && !availableContacts.some(x => x.name === doc.contact)" :value="doc.contact">{{ doc.contact }} ({{ __('unavailable') }})</option>
                      <option v-for="contact in availableContacts" :key="contact.name" :value="contact.name">{{ contactLabel(contact) }}</option>
                    </select>
                  </label>
                  <p v-if="!doc.company" class="setup-guidance">{{ __('Select a Company before choosing its Contact.') }}</p>
                </template>
                <p v-if="customerNotice" class="text-xs text-amber-700" role="status">{{ customerNotice }}</p>
              </section>

              <section class="setup-step">
                <p class="setup-step-title"><span>3</span>{{ __('Deal') }} <span class="font-normal text-ink-gray-5">({{ __('optional') }})</span></p>
                <p v-if="!dealContextReady" class="setup-placeholder">{{ __('Select a customer first.') }}</p>
                <div v-else-if="doc.deal" class="space-y-2">
                  <p class="rounded-md bg-surface-gray-1 px-3 py-2 text-sm font-medium text-ink-gray-8">{{ dealLabel || doc.deal }}</p>
                  <Button variant="subtle" :label="__('Unlink Deal')" :disabled="dealLoading" @click="unlinkDeal" />
                  <p class="setup-guidance">{{ __('Unlink the Deal to change Customer Type, Contact, or Company.') }}</p>
                </div>
                <label v-else class="field">
                  <span class="sr-only">{{ __('Deal') }}</span>
                  <select :value="doc.deal" :disabled="dealLoading" @change="selectDeal($event.target.value)">
                    <option value="">{{ __('No Deal (standalone quotation)') }}</option>
                    <option v-for="deal in matchingDeals" :key="deal.name" :value="deal.name">{{ deal.deal_title || deal.name }}</option>
                    <option v-if="!matchingDeals.length" disabled>{{ __('No matching deals') }}</option>
                  </select>
                  <span class="setup-guidance">{{ matchingDeals.length ? __('Only Deals matching this customer are shown.') : __('No matching Deal is required to create this quotation.') }}</span>
                </label>
                <span v-if="dealError" class="text-xs text-red-600">{{ dealError }}</span>
                <span v-else-if="dealNotice" class="text-xs text-amber-700" role="status">{{ dealNotice }}</span>
              </section>

              <section class="setup-step">
                <p class="setup-step-title"><span>4</span>{{ __('Price List') }}</p>
                <p v-if="!dealContextReady" class="setup-placeholder">{{ __('Select a customer first.') }}</p>
                <label v-else class="field">
                  <span class="sr-only">{{ __('Price List') }}</span>
                  <select v-model="doc.price_list" @change="pricingContextChanged">
                    <option value="">{{ __('Automatic') }}</option>
                    <option v-if="doc.price_list && !priceLists.some(x => x.name === doc.price_list)" :value="doc.price_list">{{ doc.price_list }} ({{ __('unavailable') }})</option>
                    <option v-for="priceList in priceLists" :key="priceList.name" :value="priceList.name">{{ priceList.price_list_name || priceList.name }}</option>
                  </select>
                  <span class="setup-guidance">{{ pricingExplanation }}</span>
                  <span class="setup-guidance">{{ __('Saved or manually entered unit prices are never changed automatically.') }}</span>
                </label>
              </section>
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
              <label class="field">{{ __('Quotation Date') }} *<TextInput v-model="doc.quotation_date" type="date" /></label>
              <label class="field">{{ __('Valid Until') }} *<TextInput v-model="doc.valid_until" type="date" /></label>
              <label class="field sm:col-span-2">{{ __('Terms & Conditions') }}<textarea v-model="doc.terms" rows="2" /></label>
              <label class="field sm:col-span-2">{{ __('Notes') }}<textarea v-model="doc.notes" rows="2" /></label>
            </div>
          </fieldset>
          <div v-if="editable && quotationTemplates.length" class="flex flex-wrap items-end gap-2 rounded border border-outline-gray-2 bg-surface-gray-1 p-3">
            <label class="min-w-64 flex-1 text-sm text-ink-gray-7">{{ __('Load from Quotation Template') }}
              <select v-model="selectedTemplate" class="mt-1" :disabled="applyingTemplate">
                <option value="">{{ __('Select a template...') }}</option>
                <option v-for="tpl in quotationTemplates" :key="tpl.name" :value="tpl.name">
                  {{ tpl.template_name || tpl.name }}{{ tpl.product_category ? ` (${tpl.product_category})` : '' }}
                </option>
              </select>
            </label>
            <Button :label="__('Apply Template')" :loading="applyingTemplate" :disabled="!selectedTemplate" @click="applySelectedTemplate" />
          </div>
          <div v-if="optionsError" class="text-sm text-red-600">{{ optionsError }}</div>
          <div v-if="editable" class="flex flex-wrap items-end gap-2 rounded border p-3">
            <label class="min-w-64 flex-1 text-sm text-ink-gray-7">{{ __('Search sellable products') }}
              <TextInput v-model="productSearch" type="search" :placeholder="__('Search name or SKU...')" />
            </label>
            <Button v-if="productHasNextPage" variant="subtle" :label="__('Load more products')" :loading="productsLoading" @click="loadProducts({ append: true })" />
            <span v-else-if="productsLoading" class="text-sm text-ink-gray-5">{{ __('Loading products...') }}</span>
            <span class="text-xs text-ink-gray-5">{{ __('Only active Standard Products and Variants are available.') }}</span>
          </div>
          <div v-if="productPickerError" class="mt-2 text-sm text-red-600">{{ productPickerError }}</div>
          <div class="max-w-full min-w-0 overflow-x-auto rounded-lg border border-outline-gray-2">
            <table class="w-full min-w-[1120px] table-fixed text-left text-sm"><thead class="bg-surface-gray-1 text-ink-gray-6"><tr><th class="w-[29%] p-3">{{ __('Product') }}</th><th class="w-[16%] p-3">{{ __('Unit Price (USD)') }}</th><th class="w-[10%] p-3">{{ __('Quantity') }}</th><th class="w-[13%] p-3">{{ __('Discount Type') }}</th><th class="w-[14%] p-3">{{ __('Discount') }}</th><th class="w-[12%] p-3 text-right">{{ __('Line Total (USD)') }}</th><th class="w-[6%] p-3" /></tr></thead>
              <tbody><tr v-for="(item, index) in doc.items" :key="item.name || index" class="border-t border-outline-gray-2 align-top">
                <td class="p-3"><select v-if="editable && !item.name" v-model="item.product" @change="selectProduct(item)"><option value="">{{ __('Select product') }}</option><option v-for="product in productOptionsForItem(products, item)" :key="product.name" :value="product.name">{{ productPickerLabel(product) }}</option></select><div v-else class="font-medium text-ink-gray-8">{{ item.product_name || item.product || '—' }}</div><div v-if="item.sku" class="mt-1 text-xs text-ink-gray-5">{{ __('SKU') }}: {{ item.sku }}</div></td>
                <td class="p-3"><TextInput v-if="editable" v-model="item.unit_price" type="number" min="0" step="0.01" @update:modelValue="markManualPrice(item)" /><span v-else>{{ money(item.unit_price) }}</span><div v-if="itemPricing(item).loading" class="mt-1 text-xs text-ink-gray-5">{{ __('Loading price...') }}</div><div v-else-if="itemPricing(item).error" class="mt-1 text-xs text-red-600">{{ itemPricing(item).error }}</div><div v-else-if="itemPricing(item).source" class="mt-1 text-xs text-ink-gray-5">{{ pricingSourceLabel(item) }}</div></td>
                <td class="p-3"><TextInput v-if="editable" v-model="item.quantity" type="number" min="0" step="any" /><span v-else>{{ item.quantity }}</span></td>
                <td class="p-3"><select v-if="editable" v-model="item.discount_type" @change="discountTypeChanged(item)"><option value="Percentage">{{ __('Percentage') }}</option><option value="Amount">{{ __('Amount') }}</option></select><span v-else>{{ item.discount_type === 'Amount' ? __('Amount') : __('Percentage') }}</span></td>
                <td class="p-3"><TextInput v-if="editable && item.discount_type === 'Amount'" v-model="item.discount_amount" type="number" min="0" step="0.01" /><TextInput v-else-if="editable" v-model="item.discount_percent" type="number" min="0" max="100" step="any" /><span v-else>{{ item.discount_type === 'Amount' ? money(item.discount_amount) : `${item.discount_percent || 0}%` }}</span></td>
                <td class="p-3 text-right font-medium text-ink-gray-8">{{ money(editable ? lineAmounts(item).total : item.line_total) }}</td>
                <td class="p-3 text-right"><Button v-if="editable" icon="trash-2" variant="ghost" :tooltip="__('Remove')" @click="doc.items.splice(index, 1)" /></td>
              </tr></tbody>
            </table>
          </div>
          <div v-if="editable" class="flex flex-wrap gap-2">
            <Button :label="__('Add item')" iconLeft="plus" @click="addItem" />
            <Button
              :label="__('Browse Catalog')"
              iconLeft="layout-grid"
              :disabled="!dealContextReady"
              :tooltip="dealContextReady ? __('Select several products at once') : __('Select a customer first')"
              @click="openCatalog"
            />
          </div>
          <div class="ml-auto max-w-xs space-y-2 text-right text-sm"><p>{{ __('Subtotal') }}: {{ money(editable ? totals.gross : doc.subtotal) }}</p><p>{{ __('Total discount') }}: {{ money(editable ? totals.discount : doc.total_discount) }}</p><p class="font-semibold">{{ __('Grand total') }}: {{ money(editable ? totals.total : doc.grand_total) }}</p><p v-if="editable" class="text-xs text-ink-gray-5">{{ __('Preview; final amounts are calculated by the server.') }}</p></div>
          </template>
          <QuotationEmails
            v-else
            :quotation="doc.name"
            :status="doc.status"
            :can-write="canWrite"
            :refresh-key="emailRefreshKey"
            @send-pdf="openEmailDialog"
          />
        </div>
      </template>
    </div>
    <Dialog v-model:open="showCatalogDialog" :title="__('Browse Catalog')" size="3xl" :dismissible="!catalogAdding" :showCloseButton="!catalogAdding">
      <div class="flex max-h-[80vh] min-h-0 flex-col">
        <div class="flex shrink-0 flex-wrap items-end gap-2 border-b border-outline-gray-2 pb-3">
          <label class="min-w-64 flex-1 text-sm text-ink-gray-7">{{ __('Search products') }}
            <TextInput v-model="productSearch" type="search" :placeholder="__('Search name or SKU...')" :disabled="catalogAdding" />
          </label>
          <label class="w-full text-sm text-ink-gray-7 sm:w-56">{{ __('Category') }}
            <select v-model="productCategory" :disabled="catalogAdding || productCategoriesLoading">
              <option value="">{{ __('All Categories') }}</option>
              <option v-for="category in productCategories" :key="category.name" :value="category.name">{{ category.category_name || category.name }}</option>
            </select>
          </label>
          <span class="text-xs text-ink-gray-5">{{ __('Active Standard Products and Variants only.') }}</span>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto py-3">
          <p v-if="productCategoriesError" class="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{{ productCategoriesError }}</p>
          <p v-if="productPickerError" class="rounded-md bg-red-50 p-3 text-sm text-red-700">{{ productPickerError }}</p>
          <p v-else-if="productsLoading && !products.length" class="p-8 text-center text-sm text-ink-gray-5">{{ __('Loading products...') }}</p>
          <p v-else-if="!products.length" class="p-8 text-center text-sm text-ink-gray-5">{{ __('No matching products.') }}</p>
          <div v-else class="grid gap-3 sm:grid-cols-2">
            <label
              v-for="product in products"
              :key="product.name"
              class="flex cursor-pointer gap-3 rounded-lg border border-outline-gray-2 p-3 hover:bg-surface-gray-1"
            >
              <input
                type="checkbox"
                class="mt-1 h-4 w-4 shrink-0"
                :checked="catalogProductSelected(product.name)"
                :disabled="catalogAdding"
                @change="toggleCatalogProduct(product.name, $event.target.checked)"
              />
              <ProductThumbnail class="h-16 w-16" :src="product.resolved_image" :alt="product.product_name || product.name" />
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium text-ink-gray-8">{{ product.product_name || product.name }}</span>
                <span class="mt-1 block text-xs text-ink-gray-5">{{ product.sku || __('No SKU') }} · {{ __(product.product_kind) }}</span>
                <span v-if="product.variant_attributes?.length" class="mt-1 block text-xs text-ink-gray-5">{{ product.variant_attributes.join(', ') }}</span>
                <span class="mt-2 flex items-center gap-2 text-xs text-ink-gray-6">
                  {{ __('Quantity') }}
                  <TextInput
                    v-model="catalogQuantities[product.name]"
                    class="w-20"
                    type="number"
                    min="1"
                    step="1"
                    :disabled="catalogAdding || !catalogProductSelected(product.name)"
                    @click.stop
                  />
                </span>
              </span>
            </label>
          </div>
          <div v-if="productHasNextPage && products.length" class="mt-3 text-center">
            <Button variant="subtle" :label="__('Load more products')" :loading="productsLoading" :disabled="catalogAdding" @click="loadProducts({ append: true })" />
          </div>
        </div>
        <div class="flex shrink-0 flex-wrap items-center justify-between gap-2 border-t border-outline-gray-2 bg-surface-white pt-3">
          <span class="text-sm text-ink-gray-6">{{ __('{0} selected', [catalogSelectedNames.length]) }}</span>
          <div class="flex gap-2">
            <Button :label="__('Cancel')" :disabled="catalogAdding" @click="showCatalogDialog = false" />
            <Button variant="solid" :label="__('Add selected')" :loading="catalogAdding" :disabled="!catalogSelectedNames.length" @click="addSelectedProducts" />
          </div>
        </div>
      </div>
    </Dialog>
    <Dialog v-model:open="showEmailDialog" :title="__('Send Quotation by Email')" size="3xl" :dismissible="!sendingEmail" :showCloseButton="!sendingEmail">
      <form class="flex max-h-[80vh] min-h-0 flex-col" @submit.prevent="sendEmail">
        <div class="min-h-0 flex-1 space-y-4 overflow-y-auto px-1 pb-4">
          <label class="field">{{ __('To') }}
            <TextInput v-model="email.recipient" type="email" required :disabled="sendingEmail" @update:modelValue="recipientEdited" />
          </label>
          <p v-if="emailContextLoading" class="text-xs text-ink-gray-5">{{ __('Finding customer email…') }}</p>
          <p v-else-if="recipientSource" class="break-words text-xs text-ink-gray-6">
            {{ recipientSource }}
          </p>
          <p v-else-if="!email.recipient" class="text-xs text-ink-gray-5">
            {{ __('No readable customer email was found. Select a Company Contact below or enter an address manually.') }}
          </p>

          <div v-if="emailContext.company" class="space-y-2 rounded-md border border-outline-gray-2 p-3">
            <p class="text-sm font-medium">{{ __('Choose a Contact from {0}', [emailContext.company.label]) }}</p>
            <TextInput
              v-model="emailContactSearch"
              type="search"
              :placeholder="__('Search Contact name or email…')"
              :disabled="sendingEmail"
            />
            <select v-model="selectedEmailContact" :disabled="sendingEmail || emailContextLoading" @change="applyCompanyContact">
              <option value="">{{ emailContext.companyContacts.length ? __('Select a Contact') : __('No Contact with email found') }}</option>
              <option v-for="contact in emailContext.companyContacts" :key="contact.name" :value="contact.name">
                {{ contact.label }} &lt;{{ contact.email }}&gt;
              </option>
            </select>
          </div>

          <label class="field">{{ __('Subject') }}
            <TextInput v-model="email.subject" maxlength="140" required :disabled="sendingEmail" />
          </label>
          <label class="field">{{ __('Message') }}
            <textarea v-model="email.body" rows="7" maxlength="10000" required :disabled="sendingEmail" />
          </label>
          <p class="break-all text-sm text-ink-gray-6">{{ __('Attachment') }}: {{ doc?.name }}.pdf</p>
          <p v-if="emailContext.isExpired" class="rounded-md bg-yellow-50 p-3 text-sm text-yellow-800" role="alert">
            {{ __('This quotation expired on {0}. Sending the PDF requires confirmation.', [emailContext.validUntil]) }}
          </p>
          <ErrorMessage v-if="emailError" :message="emailError" />
        </div>
        <div class="flex shrink-0 flex-wrap justify-end gap-2 border-t border-outline-gray-2 bg-surface-white pt-3">
          <Button type="button" :label="__('Cancel')" :disabled="sendingEmail" @click="showEmailDialog = false" />
          <Button type="submit" variant="solid" :label="__('Send Email')" :loading="sendingEmail" :disabled="emailContextLoading" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Dialog, TextInput, call } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ProductThumbnail from '@/components/ProductThumbnail.vue'
import QuotationEmails from '@/components/QuotationEmails.vue'
import { appendCatalogSelections, approvalBadgeClass, buildQuotationItemsFromTemplate, contactsForCustomer, createQuotationItem, customerFromDeal, dealsForCustomer, isApprovalBlockingSend, isQuotationExpired, lineAmounts, message, money, productOptionsForItem, shouldRepriceItem } from '@/utils/quotation'
import { useSellableProducts } from '@/composables/useSellableProducts'

const route = useRoute(), router = useRouter()
const isNew = computed(() => route.name === 'QuotationCreate')
const doc = ref(null), loading = ref(true), saving = ref(false), editing = ref(false)
const exporting = ref(false)
const activeTab = ref('details'), emailRefreshKey = ref(0)
const creatingOrder = ref(false), canCreateOrder = ref(false), existingOrder = ref('')
const showEmailDialog = ref(false), sendingEmail = ref(false), emailError = ref(''), emailQueue = ref('')
const showCatalogDialog = ref(false), catalogAdding = ref(false)
const catalogSelectedProducts = reactive({})
const catalogQuantities = reactive({})
const catalogSelectedNames = computed(() => Object.keys(catalogSelectedProducts))
const email = reactive({ recipient: '', subject: '', body: '' })
const emailContextLoading = ref(false), emailContactSearch = ref(''), selectedEmailContact = ref(''), recipientSource = ref('')
const emailContext = reactive({ suggested: null, company: null, companyContacts: [], validUntil: '', isExpired: false })
const canWrite = ref(false), canDelete = ref(false), error = ref(''), dealError = ref(''), optionsError = ref(''), conflict = ref(false)
const customerNotice = ref(''), dealNotice = ref('')
const contacts = ref([]), companies = ref([]), deals = ref([]), priceLists = ref([]), quotationTemplates = ref([])
const selectedTemplate = ref(''), applyingTemplate = ref(false)
const siteToday = ref('')
const canManageApproval = ref(false), currentUser = ref(''), approvalBusy = ref(false)
const approvalBlockingSend = computed(() => isApprovalBlockingSend(doc.value))
const isOwnApprovalRequest = computed(() => Boolean(currentUser.value && (doc.value?.approval_requested_by || doc.value?.owner) === currentUser.value))
const {
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
} = useSellableProducts()
const dealLoading = ref(false)
const dealLabel = ref('')
let dealRequestId = 0
let emailContactSearchTimer = null
let emailContextRequest = 0
const pricingStates = new WeakMap()
const editable = computed(() => (isNew.value && canWrite.value) || (!isNew.value && editing.value && canWrite.value && doc.value?.status === 'Draft'))
const availableContacts = computed(() => contactsForCustomer(contacts.value, doc.value))
const dealContextReady = computed(() => doc.value?.customer_type === 'PERSONAL' ? Boolean(doc.value.contact) : doc.value?.customer_type === 'COMPANY' ? Boolean(doc.value.company) : false)
const pricingExplanation = computed(() => {
  if (doc.value?.price_list) return __('New automatically priced lines use the selected Price List, then the Product default when no matching row exists.')
  if (doc.value?.customer_type === 'COMPANY') return __('Automatic checks the Company Price List, optional Contact Price List, system default, then Product default.')
  return __('Automatic checks the Contact Price List, system default, then Product default.')
})
const matchingDeals = computed(() => {
  if (!doc.value || !dealContextReady.value) return []
  return dealsForCustomer(deals.value, doc.value)
})
const totals = computed(() => (doc.value?.items || []).reduce((sum, item) => { const a = lineAmounts(item); sum.gross += a.gross; sum.discount += a.discount; sum.total += a.total; return sum }, { gross: 0, discount: 0, total: 0 }))
const pricingPending = computed(() => (doc.value?.items || []).some(item => itemPricing(item).loading))
const list = (doctype, fields, filters = {}) => call('frappe.client.get_list', { doctype, fields, filters, limit_page_length: 500 })
async function loadOptions() {
  optionsError.value = ''
  const results = await Promise.allSettled([
    list('DoubleT Contact', ['name', 'first_name', 'last_name', 'company']),
    list('DoubleT Company', ['name', 'company_name']),
    list('DoubleT Deal', ['name', 'deal_title', 'deal_type', 'contact', 'company']),
    list('DoubleT Price List', ['name', 'price_list_name'], { is_active: 1 }),
    list('DoubleT Quotation Template', ['name', 'template_name', 'product_category'], { is_active: 1 }),
  ])
  ;[contacts, companies, deals, priceLists, quotationTemplates].forEach((target, i) => { if (results[i].status === 'fulfilled') target.value = results[i].value || [] })
  if (results.slice(0, 4).some(r => r.status === 'rejected')) optionsError.value = __('Some linked records could not be loaded. Check your access and retry.')
}

watch(emailContactSearch, () => {
  clearTimeout(emailContactSearchTimer)
  if (!showEmailDialog.value || !emailContext.company || emailContextLoading.value) return
  emailContactSearchTimer = setTimeout(() => loadEmailContext(emailContactSearch.value, false), 250)
})

async function loadDocument() {
  loading.value = true; error.value = ''; dealError.value = ''; customerNotice.value = ''; dealNotice.value = ''; conflict.value = false
  existingOrder.value = ''
  try {
    if (isNew.value) {
      const permission = await call('frappe.client.has_permission', { doctype: 'DoubleT Quotation', docname: '', perm_type: 'create' })
      canWrite.value = Boolean(permission?.has_permission)
      if (!canWrite.value) throw new Error(__('You do not have permission to create quotations.'))
      doc.value = { doctype: 'DoubleT Quotation', status: 'Draft', approval_status: 'Not Required', customer_type: '', contact: '', company: '', deal: '', price_list: '', quotation_template: '', quotation_date: '', valid_until: '', terms: '', notes: '', items: [] }
    } else {
      const [data, permissions] = await Promise.all([
        call('frappe.client.get', { doctype: 'DoubleT Quotation', name: route.params.quotationId }),
        call('frappe.client.get_doc_permissions', { doctype: 'DoubleT Quotation', docname: route.params.quotationId }),
      ])
      doc.value = data; canWrite.value = Boolean(permissions?.permissions?.write); canDelete.value = Boolean(permissions?.permissions?.delete)
      try {
        const linkedOrders = await list('DoubleT Order', ['name'], { quotation: data.name })
        existingOrder.value = linkedOrders?.[0]?.name || ''
      } catch { /* A restricted Order is not exposed from the Quotation. */ }
      await loadDealLabel(data.deal)
    }
    editing.value = false
  } catch (e) { error.value = message(e); doc.value = null } finally { loading.value = false }
}
function customerChanged() {
  const clearedCustomer = Boolean(doc.value.contact || doc.value.company)
  doc.value.contact = ''
  doc.value.company = ''
  customerNotice.value = clearedCustomer ? __('Customer Type changed. The previous Contact and Company selections were cleared.') : ''
  customerContextChanged(__('The linked Deal was removed because Customer Type changed.'))
}
function companyChanged() {
  const contact = contacts.value.find(row => row.name === doc.value.contact)
  if (doc.value.contact && (!doc.value.company || !contact || contact.company !== doc.value.company)) {
    doc.value.contact = ''
    customerNotice.value = __('The previous Contact was cleared because it does not belong to the selected Company.')
  } else customerNotice.value = ''
  customerContextChanged(__('The linked Deal was removed because it does not match the selected Company.'))
}
function contactChanged() {
  customerNotice.value = ''
  customerContextChanged(__('The linked Deal was removed because it does not match the selected Contact.'))
}
function clearDeal(notice = '') {
  dealRequestId += 1
  doc.value.deal = ''
  dealLoading.value = false
  dealLabel.value = ''
  dealError.value = ''
  dealNotice.value = notice
}
function customerContextChanged(notice = __('The linked Deal was removed because it no longer matches the customer.')) {
  if (doc.value.deal && !matchingDeals.value.some(deal => deal.name === doc.value.deal)) {
    clearDeal(notice)
  }
  pricingContextChanged()
}
function contactLabel(contact) { return [contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.name }
function unlinkDeal() {
  const label = dealLabel.value || doc.value?.deal
  if (!label) return
  clearDeal(__('Deal {0} was unlinked. You can now change the customer.', [label]))
}
function dealName(value) { return typeof value === 'string' ? value.trim() : '' }
async function loadDealLabel(value) {
  const name = dealName(value)
  dealLabel.value = ''
  if (!name) return
  try {
    const data = await list('DoubleT Deal', ['name', 'deal_title'], { name })
    const deal = data?.[0]
    if (deal?.name === name) dealLabel.value = deal.deal_title || __('Unnamed Deal')
  } catch { /* An unread Deal stays neutral in the UI. */ }
}
function openDeal() { if (doc.value?.deal && dealLabel.value) router.push({ name: 'DealDetail', params: { dealId: doc.value.deal } }) }
function startEditing() { activeTab.value = 'details'; editing.value = true }
function isPermissionError(e) { return e?.httpStatusCode === 403 || e?.status === 403 || e?.exc_type === 'PermissionError' || /\b(permission|not permitted|not allowed)\b/i.test(message(e)) }
async function selectDeal(value = doc.value?.deal) {
  const requestId = ++dealRequestId
  const name = dealName(value)
  if (!name) {
    clearDeal()
    return
  }

  doc.value.deal = name
  dealLoading.value = true
  dealError.value = ''
  dealNotice.value = ''
  try {
    const deal = await call('frappe.client.get', { doctype: 'DoubleT Deal', name })
    if (requestId !== dealRequestId) return
    if (!deal?.name) throw new Error(__('The selected Deal could not be found.'))
    if (!['PERSONAL', 'COMPANY'].includes(deal.deal_type) || (deal.deal_type === 'COMPANY' && !deal.company) || (deal.deal_type === 'PERSONAL' && !deal.contact)) {
      throw new Error(__('The Deal customer information is incomplete or unavailable. Check the Deal customer or ask an administrator to check your access.'))
    }
    Object.assign(doc.value, customerFromDeal(deal))
    customerNotice.value = ''
    await loadDealLabel(name)
    dealError.value = ''
    await repriceAutomaticItems()
  } catch (e) {
    if (requestId !== dealRequestId) return
    dealError.value = isPermissionError(e)
      ? __('You do not have permission to read the selected Deal.')
      : message(e)
    dealLabel.value = ''
  } finally { if (requestId === dealRequestId) dealLoading.value = false }
}

function itemPricing(item) {
  if (!pricingStates.has(item)) {
    pricingStates.set(item, reactive({
      loading: false,
      error: '',
      manual: Boolean(item.name),
      auto: false,
      source: '',
      priceList: '',
      requestId: 0,
    }))
  }
  return pricingStates.get(item)
}

function addItem() {
  const item = createQuotationItem()
  doc.value.items.push(item)
  itemPricing(item)
}

function catalogProductSelected(name) {
  return Boolean(catalogSelectedProducts[name])
}

function toggleCatalogProduct(name, selected) {
  if (selected) {
    const product = products.value.find(row => row.name === name)
    if (product) catalogSelectedProducts[name] = product
    if (!catalogQuantities[name]) catalogQuantities[name] = 1
    return
  }
  delete catalogSelectedProducts[name]
}

function openCatalog() {
  if (!editable.value || !dealContextReady.value) return
  Object.keys(catalogSelectedProducts).forEach(name => delete catalogSelectedProducts[name])
  Object.keys(catalogQuantities).forEach(name => delete catalogQuantities[name])
  showCatalogDialog.value = true
}

async function addSelectedProducts() {
  if (catalogAdding.value || !editable.value || !dealContextReady.value) return
  const selections = catalogSelectedNames.value
    .map(name => ({ product: catalogSelectedProducts[name], quantity: catalogQuantities[name] }))
  if (!selections.length) return

  catalogAdding.value = true
  try {
    await appendCatalogSelections(doc.value.items, selections, async item => {
      itemPricing(item)
      await resolveItemPrice(item)
    })
    showCatalogDialog.value = false
  } finally {
    catalogAdding.value = false
  }
}

function discountTypeChanged(item) {
  if (item.discount_type === 'Amount') item.discount_percent = 0
  else item.discount_amount = 0
}

function markManualPrice(item) {
  const state = itemPricing(item)
  state.requestId += 1
  state.loading = false
  state.error = ''
  state.manual = true
  state.auto = false
  state.source = ''
  state.priceList = ''
}

async function selectProduct(item) {
  const product = products.value.find(product => product.name === item.product)
  const state = itemPricing(item)
  state.requestId += 1
  state.error = ''
  state.manual = false
  state.auto = false
  state.loading = false
  state.source = ''
  state.priceList = ''
  item.unit_price = ''
  if (!product) {
    Object.assign(item, { product_name: '', sku: '' })
    return
  }
  Object.assign(item, { product_name: product.product_name, sku: product.sku })
  await resolveItemPrice(item)
}

async function resolveItemPrice(item) {
  if (!item.product || item.name) return
  const state = itemPricing(item)
  if (state.manual) return
  const requestId = ++state.requestId
  const selectedProduct = item.product
  state.loading = true
  state.error = ''
  state.source = ''
  state.priceList = ''
  item.unit_price = ''
  try {
    const result = await call('doublet_crm.pricing.get_product_price', {
      product: selectedProduct,
      customer_type: doc.value.customer_type,
      contact: doc.value.contact || null,
      company: doc.value.company || null,
      price_list: doc.value.price_list || null,
    })
    if (requestId !== state.requestId || item.product !== selectedProduct || state.manual) return
    if (result?.price === undefined || result?.price === null || result?.price === '') {
      throw new Error(__('The pricing service did not return a price.'))
    }
    item.unit_price = result.price
    state.auto = true
    state.source = result.source || ''
    state.priceList = result.price_list || ''
  } catch (exception) {
    if (requestId !== state.requestId || item.product !== selectedProduct || state.manual) return
    item.unit_price = ''
    state.auto = false
    state.error = message(exception) || __('Unable to load the product price.')
  } finally {
    if (requestId === state.requestId) state.loading = false
  }
}

async function repriceAutomaticItems() {
  const items = (doc.value?.items || []).filter(item => {
    return shouldRepriceItem(item, itemPricing(item))
  })
  await Promise.allSettled(items.map(resolveItemPrice))
}

function pricingContextChanged() {
  if (!dealContextReady.value) return
  void repriceAutomaticItems()
}

function pricingSourceLabel(item) {
  const state = itemPricing(item)
  if (state.source === 'price_list' && state.priceList) {
    const priceList = priceLists.value.find(row => row.name === state.priceList)
    return `${__('Price List')}: ${priceList?.price_list_name || state.priceList}`
  }
  if (state.source === 'product' && state.priceList) {
    const priceList = priceLists.value.find(row => row.name === state.priceList)
    return __('Product default price (no matching row in {0})', [priceList?.price_list_name || state.priceList])
  }
  return state.source === 'product' ? __('Product default price') : ''
}
function validate() {
  const d = doc.value
  if (dealError.value) return dealError.value
  if (!['PERSONAL', 'COMPANY'].includes(d.customer_type) || (d.customer_type === 'PERSONAL' && (!d.contact || d.company)) || (d.customer_type === 'COMPANY' && !d.company)) return __('Select a valid customer.')
  if (d.customer_type === 'COMPANY' && d.contact && contacts.value.some(c => c.name === d.contact && c.company !== d.company)) return __('Contact must belong to the selected Company.')
  if (!d.quotation_date || !d.valid_until || d.valid_until < d.quotation_date) return __('Enter valid quotation and expiry dates.')
  if (!d.items.length) return __('Add at least one item.')
  const decimal = value => /^\d+(\.\d+)?$/.test(String(value ?? '')) && Number.isFinite(Number(value))
  if (d.items.some((i) => {
    if (!i.product || !decimal(i.quantity) || Number(i.quantity) <= 0 || !decimal(i.unit_price)) return true
    if ((i.discount_type || 'Percentage') === 'Amount') {
      return !decimal(i.discount_amount ?? 0) || Number(i.discount_amount) > lineAmounts({ ...i, discount_amount: 0 }).gross
    }
    return !decimal(i.discount_percent ?? 0) || Number(i.discount_percent) > 100
  })) return __('Check product, quantity, price and discount for each item.')
  return ''
}
function setError(e) {
  const text = message(e)
  if (e?.exc_type === 'TimestampMismatchError' || /modified after/i.test(text)) { conflict.value = true; error.value = __('This quotation was changed by another user. Reload the latest version before saving.') }
  else error.value = text
}
async function createOrder() {
  if (creatingOrder.value || saving.value || editing.value || !doc.value?.name) return
  if (existingOrder.value) {
    await router.push({ name: 'OrderDetail', params: { orderId: existingOrder.value } })
    return
  }
  creatingOrder.value = true
  error.value = ''
  try {
    const orderId = await call('doublet_crm.doublet_crm.doctype.doublet_order.doublet_order.create_order_from_quotation', { quotation: doc.value.name })
    await router.push({ name: 'OrderDetail', params: { orderId } })
  } catch (e) { setError(e) } finally { creatingOrder.value = false }
}
async function exportPdf() {
  if (exporting.value || !doc.value?.name) return
  exporting.value = true; error.value = ''
  try {
    const query = new URLSearchParams({ name: doc.value.name })
    const response = await fetch(`/api/method/doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_pdf.download_quotation_pdf?${query}`, { credentials: 'same-origin', headers: { Accept: 'application/pdf' } })
    if (!response.ok) throw new Error(response.status === 403 ? __('You do not have permission to export this quotation.') : __('Unable to export this quotation. Please try again.'))
    if (!response.headers.get('content-type')?.includes('application/pdf')) throw new Error(__('Unable to export this quotation. Please sign in and try again.'))
    const url = URL.createObjectURL(await response.blob())
    const link = document.createElement('a'); link.href = url; link.download = `${doc.value.name.replace(/[\\/]/g, '-')}.pdf`; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (e) { error.value = message(e) } finally { exporting.value = false }
}
function resetEmailContext() {
  emailContextRequest += 1
  email.recipient = ''
  recipientSource.value = ''
  emailContactSearch.value = ''
  selectedEmailContact.value = ''
  Object.assign(emailContext, { suggested: null, company: null, companyContacts: [], validUntil: '', isExpired: false })
}

async function loadEmailContext(search = '', applySuggestion = false) {
  const request = ++emailContextRequest
  const quotation = doc.value?.name
  if (!quotation) return
  emailContextLoading.value = true
  try {
    const result = await call(
      'doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email.get_quotation_email_context',
      { name: quotation, search },
    )
    if (request !== emailContextRequest || quotation !== doc.value?.name) return
    Object.assign(emailContext, {
      suggested: result.suggested || null,
      company: result.company || null,
      companyContacts: result.company_contacts || [],
      validUntil: result.valid_until || doc.value.valid_until || '',
      isExpired: Boolean(result.is_expired),
    })
    if (applySuggestion && result.suggested) {
      email.recipient = result.suggested.email
      recipientSource.value = `${result.suggested.label} · ${__(result.suggested.source)}`
    }
  } catch (exception) {
    if (request === emailContextRequest) emailError.value = message(exception)
  } finally {
    if (request === emailContextRequest) emailContextLoading.value = false
  }
}

function recipientEdited() {
  recipientSource.value = ''
  selectedEmailContact.value = ''
}

function applyCompanyContact() {
  const contact = emailContext.companyContacts.find((row) => row.name === selectedEmailContact.value)
  if (!contact) return
  email.recipient = contact.email
  recipientSource.value = `${contact.label} · ${__(contact.source)}`
}

async function openEmailDialog() {
  resetEmailContext()
  email.subject = __('Quotation {0}', [doc.value.name])
  email.body = __('Please find our quotation attached.')
  emailError.value = ''
  showEmailDialog.value = true
  await loadEmailContext('', true)
}

async function sendEmail() {
  if (sendingEmail.value || doc.value?.status !== 'Draft') return
  let confirmExpired = 0
  if (emailContext.isExpired) {
    const confirmed = window.confirm(
      __('This quotation expired on {0}. Send the PDF anyway?', [emailContext.validUntil]),
    )
    if (!confirmed) return
    confirmExpired = 1
  }
  sendingEmail.value = true
  emailError.value = ''
  try {
    const result = await call('doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_pdf.send_quotation_email', {
      name: doc.value.name,
      modified: doc.value.modified,
      recipient: email.recipient,
      subject: email.subject,
      body: email.body,
      confirm_expired: confirmExpired,
    })
    emailQueue.value = result.email_queue
    showEmailDialog.value = false
    activeTab.value = 'emails'
    emailRefreshKey.value += 1
  } catch (e) {
    emailError.value = message(e)
  } finally {
    sendingEmail.value = false
  }
}

async function applySelectedTemplate() {
  if (applyingTemplate.value || !editable.value || !selectedTemplate.value) return
  if (doc.value.items?.length) {
    const confirmed = window.confirm(__('This quotation already has items. Replace current items and terms with the selected template?'))
    if (!confirmed) return
  }
  applyingTemplate.value = true
  error.value = ''
  try {
    const payload = await call('doublet_crm.doublet_crm.doctype.doublet_quotation_template.doublet_quotation_template.get_quotation_template_payload', {
      template: selectedTemplate.value,
      customer_type: doc.value.customer_type || null,
      contact: doc.value.contact || null,
      company: doc.value.company || null,
      price_list: doc.value.price_list || null,
    })
    const rows = buildQuotationItemsFromTemplate(payload)
    doc.value.items = rows
    doc.value.quotation_template = payload.template || selectedTemplate.value
    if (payload.terms) doc.value.terms = payload.terms
    rows.forEach((row, index) => {
      const sourceItem = payload.items?.[index]
      const state = itemPricing(row)
      state.manual = false
      state.auto = true
      state.source = sourceItem?.price_source || ''
      state.priceList = sourceItem?.price_list || ''
    })
  } catch (e) {
    error.value = message(e)
  } finally {
    applyingTemplate.value = false
  }
}

async function requestApproval() {
  if (approvalBusy.value || !doc.value?.name) return
  approvalBusy.value = true
  error.value = ''
  try {
    await call('doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation.request_discount_approval', {
      name: doc.value.name,
      modified: doc.value.modified,
    })
    await loadDocument()
  } catch (e) { setError(e) } finally { approvalBusy.value = false }
}

async function approveDiscountRequest() {
  if (approvalBusy.value || !doc.value?.name) return
  approvalBusy.value = true
  error.value = ''
  try {
    await call('doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation.approve_discount', {
      name: doc.value.name,
      modified: doc.value.modified,
    })
    await loadDocument()
  } catch (e) { setError(e) } finally { approvalBusy.value = false }
}

async function rejectDiscountRequest() {
  if (approvalBusy.value || !doc.value?.name) return
  const reason = window.prompt(__('Enter rejection reason:'))
  if (!reason || !reason.trim()) return
  approvalBusy.value = true
  error.value = ''
  try {
    await call('doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation.reject_discount', {
      name: doc.value.name,
      reason: reason.trim(),
      modified: doc.value.modified,
    })
    await loadDocument()
  } catch (e) { setError(e) } finally { approvalBusy.value = false }
}

async function save() {
  if (saving.value || dealLoading.value || pricingPending.value || !editable.value) return
  error.value = validate(); if (error.value) return
  saving.value = true
  try {
    const saved = await call(isNew.value ? 'frappe.client.insert' : 'frappe.client.save', { doc: doc.value })
    if (isNew.value) await router.replace({ name: 'QuotationDetail', params: { quotationId: saved.name } })
    await loadDocument()
  } catch (e) { setError(e) } finally { saving.value = false }
}
async function changeStatus(status) {
  if (saving.value || !canWrite.value || editing.value) return
  if (status === 'Sent' && !window.confirm(__('Confirm that the quotation PDF has already been sent through the agreed channel. This action only records the delivery; it does not send anything.'))) return
  saving.value = true
  try { await call('frappe.client.save', { doc: { ...doc.value, status } }); await loadDocument() } catch (e) { setError(e) } finally { saving.value = false }
}
async function remove() {
  if (saving.value || !canDelete.value || doc.value.status !== 'Draft' || !window.confirm(__('Delete this draft quotation?'))) return
  saving.value = true
  try { await call('frappe.client.delete', { doctype: 'DoubleT Quotation', name: doc.value.name }); await router.push({ name: 'Quotations' }) } catch (e) { setError(e) } finally { saving.value = false }
}
onMounted(async () => {
  call('frappe.client.has_permission', { doctype: 'DoubleT Order', docname: '', perm_type: 'create' })
    .then(result => { canCreateOrder.value = Boolean(result?.has_permission) })
    .catch(() => { canCreateOrder.value = false })
  call('doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation.get_site_today')
    .then(result => { if (result?.today) siteToday.value = result.today })
    .catch(() => {})
  call('doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation.get_discount_approval_settings')
    .then(result => {
      canManageApproval.value = Boolean(result?.can_manage)
      currentUser.value = result?.current_user || ''
    })
    .catch(() => { canManageApproval.value = false })
  loadOptions()
  loadProductCategories()
  loadProducts()
  await loadDocument()
  const queryDeal = Array.isArray(route.query.deal) ? '' : dealName(route.query.deal)
  if (isNew.value && queryDeal && doc.value) await selectDeal(queryDeal)
})
watch(() => route.params.quotationId, async (current, previous) => {
  if (!previous || current === previous) return
  resetEmailContext()
  showEmailDialog.value = false
  activeTab.value = 'details'
  await loadDocument()
})
onBeforeUnmount(() => {
  clearTimeout(emailContactSearchTimer)
})
</script>

<style scoped>
.field { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.875rem; }
.setup-step { min-width: 0; border: 1px solid var(--outline-gray-2, #e5e7eb); border-radius: 0.5rem; padding: 0.75rem; }
.setup-step-title { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.65rem; font-size: 0.875rem; font-weight: 600; color: var(--ink-gray-8, #1f2937); }
.setup-step-title > span:first-child { display: inline-grid; width: 1.25rem; height: 1.25rem; place-items: center; border-radius: 9999px; background: var(--surface-gray-2, #f3f4f6); font-size: 0.75rem; }
.setup-placeholder { display: grid; min-height: 4.5rem; place-items: center; border: 1px dashed var(--outline-gray-2, #d1d5db); border-radius: 0.375rem; padding: 0.75rem; text-align: center; font-size: 0.75rem; color: var(--ink-gray-5, #6b7280); }
.setup-guidance { font-size: 0.75rem; line-height: 1.25rem; color: var(--ink-gray-5, #6b7280); }
select, textarea { width: 100%; border: 1px solid #d1d5db; border-radius: 0.25rem; padding: 0.4rem; background: white; }
fieldset:disabled { opacity: 0.8; }
</style>
