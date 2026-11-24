# Graph Report - frontend  (2026-11-24)

## Corpus Check
- 327 files · ~146,416 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 1 file(s) not represented in the graph (top: .css 1)

## Summary
- 3239 nodes · 5780 edges · 154 communities (149 shown, 5 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 277 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `015251fe`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ViewControls.vue
- QuotationForm.vue
- FilesUploaderArea.vue
- Tasks.vue
- Activities.vue
- ContactsView.vue
- OrderForm.vue
- DealsView.vue
- FrappeDeal.vue
- FilesUploader.vue
- PriceListsView.vue
- DoubleTContactInfoPanel.vue
- FrappeLead.vue
- ContactDetailView.vue
- CommentArea.vue
- CallLogDetails.vue
- Grid.vue
- Filter.vue
- SharedNotes.vue
- DoubleTEntityDetail.vue
- DoubleTDealInfoPanel.vue
- Leads.vue
- TableMultiselectInput.vue
- ProductsView.vue
- Deals.vue
- frappe-index.js
- EmailEditor.vue
- ProductModal.vue
- useDocument
- DealDetailView.vue
- frappe-ui
- DoubleTLeadInfoPanel.vue
- QuotationEmails.vue
- TaskModal.vue
- ProductDetailView.vue
- AllModals.vue
- PipelineAnalyticsReport.vue
- composables/settings.js
- Questionnaire.vue
- SalesPerformanceReport.vue
- CommunicationArea.vue
- SidePanelLayout.vue
- CallLogs.vue
- message
- DoubleTDealDataPanel.vue
- meta.js
- FieldLayoutEditor.vue
- AudioPlayer.vue
- index.js
- Field.vue
- getMeta
- ContactCenterCalls.vue
- ZaloInbox.vue
- GridFieldsEditorModal.vue
- ConvertToDealModal.vue
- DoubleTConvertToDealModal.vue
- GeolocationControl.vue
- users.js
- ListBulkActions.vue
- ColumnSettings.vue
- DoubleTLeadDataPanel.vue
- package.json
- MobileNotification.vue
- LeadModal.vue
- EditValueModal.vue
- ProductCategoriesView.vue
- dependencies
- Popover.vue
- EmailContent.vue
- DealModal.vue
- OrganizationModal.vue
- ZaloConversationThread.vue
- ActivityHeader.vue
- formatCurrency
- PriceListModal.vue
- DeleteLinkedDocModal.vue
- SortBy.vue
- AppSidebar.vue
- FrappeDealsListView.vue
- WhatsAppBox.vue
- CallLogDetailModal.vue
- MultiSelectEmailInput.vue
- reportDatePreset
- OrdersView.vue
- ContactModal.vue
- quotation.js
- QuotationsView.vue
- CommentBox.vue
- call
- AssignToBody.vue
- AddChartModal.vue
- LeadCreateModal.vue
- router.js
- FieldLayout.vue
- Autocomplete.vue
- telephony.js
- formatDate
- ReportsPage.vue
- AttachmentItem.vue
- QuotationOrderReport.vue
- vue-router
- Contacts.vue
- ListRows.vue
- KanbanSettings.vue
- CallLogAISummary.vue
- CustomerJourneyReport.vue
- Link.vue
- DataFieldsModal.vue
- SidePanelModal.vue
- Dashboard.vue
- RecordCallHistory.vue
- KanbanView.vue
- AssignmentModal.vue
- LeadDetailView.vue
- DoubleTDealKanban.vue
- close
- RatingInput.vue
- Organizations.vue
- ZaloRecordChat.vue
- ActivityContactCenterReport.vue
- DurationInput.vue
- TableMultiselectInput.vue
- OrganizationsListView.vue
- LayoutHeader.vue
- SLASection.vue
- TasksListView.vue
- @vueuse/core
- GroupBy.vue
- view.js
- CallLogsListView.vue
- main.js
- WhatsappTemplateSelectorModal.vue
- ZaloCustomerDetails.vue
- FormattedInput.vue
- TextEditorControl.vue
- useDoubleTCompanies
- useDoubleTContacts
- vue
- resolveProductImage
- Password.vue
- Resizer.vue
- itemPricing
- MultiActionButton.vue
- SidePanelLayoutEditor.vue
- saveStage
- LeadsListView.vue
- components.d.ts
- initMap
- pipelineAnalytics.test.mjs
- Icon.vue
- ProductThumbnail.vue

## God Nodes (most connected - your core abstractions)
1. `vue` - 183 edges
2. `frappe-ui` - 172 edges
3. `call` - 144 edges
4. `vue-router` - 59 edges
5. `useDocument()` - 40 edges
6. `getMeta()` - 40 edges
7. `message()` - 38 edges
8. `formatDate()` - 33 edges
9. `usersStore` - 27 edges
10. `isTranslatable()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `list()` --calls--> `call`  [INFERRED]
  src/pages/QuotationForm.vue → src/components/Activities/CallArea.vue
- `openEdit()` --calls--> `call`  [INFERRED]
  src/pages/PriceListsView.vue → src/components/Activities/CallArea.vue
- `load()` --calls--> `call`  [INFERRED]
  src/pages/Dashboard.vue → src/components/Activities/CallArea.vue
- `loadStages()` --calls--> `call`  [INFERRED]
  src/components/Contact/DoubleTContactInfoPanel.vue → src/components/Activities/CallArea.vue
- `load()` --calls--> `call`  [INFERRED]
  src/components/Calls/RecordCallHistory.vue → src/components/Activities/CallArea.vue

## Import Cycles
- 2-file cycle: `src/components/Modals/SidePanelModal.vue -> src/components/SidePanelLayout.vue -> src/components/Modals/SidePanelModal.vue`
- 3-file cycle: `src/pages/Tasks.vue -> src/stores/session.js -> src/router.js -> src/pages/Tasks.vue`
- 4-file cycle: `src/components/Modals/LeadCreateModal.vue -> src/stores/session.js -> src/router.js -> src/pages/LeadsView.vue -> src/components/Modals/LeadCreateModal.vue`

## Communities (154 total, 5 thin omitted)

### Community 0 - "ViewControls.vue"
Cohesion: 0.04
Nodes (50): applyFilter(), applyLikeFilter(), applyQuickFilter(), { brand }, cancelChanges(), createOrUpdateStandardView(), currentView, customizeQuickFilter (+42 more)

### Community 1 - "QuotationForm.vue"
Cohesion: 0.03
Nodes (56): activeTab, canCreateOrder, canDelete, canWrite, catalogAdding, catalogQuantities, catalogSelectedNames, catalogSelectedProducts (+48 more)

### Community 2 - "FilesUploaderArea.vue"
Cohesion: 0.05
Nodes (34): deleteAttachment(), { $dialog }, emit, togglePrivate(), addFiles(), allowMultiple, allowTakePhoto, allowWebLink (+26 more)

### Community 3 - "Tasks.vue"
Cohesion: 0.06
Nodes (44): canCreate, dateValue(), deleteTask(), displayDue(), dueFilter, editingName, editorOpen, emptyForm() (+36 more)

### Community 4 - "Activities.vue"
Cohesion: 0.05
Nodes (38): activities, activitiesResource, all_activities, canCreateNote, canCreateTask, { capture }, doc, { document: _document } (+30 more)

### Community 5 - "ContactsView.vue"
Cohesion: 0.13
Nodes (10): vue-router, {
  companiesResource,
  searchQuery,
  selectedIndustry,
  industryOptions,
  columns,
  rows,
  totalCount,
  reload,
  loadMore,
}, industryDropdownOptions, router, canCreate, {
  loading,

  searchQuery,
  selectedSource,
  sourceOptions,

  columns,
  rows,

  totalCount,

  reload,
  loadMore,
}, router, sourceDropdownOptions (+2 more)

### Community 6 - "OrderForm.vue"
Cohesion: 0.06
Nodes (42): availableContacts, canWrite, changeStatus(), companies, companyChanged(), companyLabel, conflict, contactLabel (+34 more)

### Community 7 - "DealsView.vue"
Cohesion: 0.09
Nodes (23): cancelPendingMove(), confirmLost(), confirmWon(), filteredRows, finishDealMove(), handleDealMove(), lostReason, moveError (+15 more)

### Community 8 - "FrappeDeal.vue"
Cohesion: 0.05
Nodes (39): activities, addContact(), beforeStatusChange(), { brand }, canDelete, _contact, contactOptions(), dealContacts (+31 more)

### Community 9 - "FilesUploader.vue"
Cohesion: 0.06
Nodes (31): attrs, clearAttachment(), containerClasses, emit, filename, iconClasses, isImage, onAfterUpload() (+23 more)

### Community 10 - "PriceListsView.vue"
Cohesion: 0.10
Nodes (16): useDoubleTPriceLists(), fetchPriceLists(), queryFilters(), setFilters(), actionError, openEdit(), priceLists, { priceListsResource, setFilters, reload, loadMore } (+8 more)

### Community 11 - "DoubleTContactInfoPanel.vue"
Cohesion: 0.06
Nodes (30): apiError(), checkDuplicates(), dirty, duplicateFilters(), duplicates, emit, error, fields (+22 more)

### Community 12 - "FrappeLead.vue"
Cohesion: 0.05
Nodes (28): assignees, activeTabName, activities, beforeStatusChange(), { brand }, canDelete, {
  $dialog,
  $socket,
  makeCall,
}, doc (+20 more)

### Community 13 - "ContactDetailView.vue"
Cohesion: 0.08
Nodes (27): activeTabName, activities, apiError(), assignees, canDelete, canWrite, companyLabel, contact (+19 more)

### Community 14 - "CommentArea.vue"
Cohesion: 0.19
Nodes (12): confirmingDelete, deleteComment(), editContent, editing, emit, isOwner, menuOptions, props (+4 more)

### Community 15 - "CallLogDetails.vue"
Cohesion: 0.06
Nodes (35): actionError, actionSuccess, assigneeDraft, assigneeError, assigneeOptions, assignees, assigneesLoaded, assigneesLoading (+27 more)

### Community 16 - "Grid.vue"
Cohesion: 0.07
Nodes (30): addRow(), allFields, allRowsSelected, deleteRows(), fieldChange(), fields, getDefaultValue(), getFieldObj() (+22 more)

### Community 17 - "Filter.vue"
Cohesion: 0.09
Nodes (32): apply(), availableFilters, clearfilter(), convertFilters(), emit, filterableFields, filters, getDefaultOperator() (+24 more)

### Community 18 - "SharedNotes.vue"
Cohesion: 0.08
Nodes (31): actionError, apiError(), applyManagementFilters(), canCreateNote, deleteNote(), deletingName, editingName, form (+23 more)

### Community 19 - "DoubleTEntityDetail.vue"
Cohesion: 0.06
Nodes (40): activeRelatedGroup, activeRelatedTab, activityTabs, apiError(), cancel(), canDelete, canWrite, companyFields (+32 more)

### Community 20 - "DoubleTDealInfoPanel.vue"
Cohesion: 0.08
Nodes (29): apiError(), cancelEdit(), detailsEditing, detailsError, detailsForm, detailsSaving, detailsStage, detailsStageType (+21 more)

### Community 21 - "Leads.vue"
Cohesion: 0.08
Nodes (26): actions(), after(), { capture }, columns, defaults, { getFormattedPercent, getFormattedFloat, getFormattedCurrency }, getGroupedByRows(), getKanbanRows() (+18 more)

### Community 22 - "TableMultiselectInput.vue"
Cohesion: 0.14
Nodes (13): error, linkRef, lostNotes, lostReason, onCreate(), props, show, createDocument() (+5 more)

### Community 23 - "ProductsView.vue"
Cohesion: 0.07
Nodes (31): reloadTemplates(), actionError, canEditSelectedProduct, categories, categoriesError, categoryAssignments, categoryLabel(), categoryNames() (+23 more)

### Community 24 - "Deals.vue"
Cohesion: 0.09
Nodes (26): actions(), after(), { capture }, columns, deals, dealsListView, defaults, { getDealStatus } (+18 more)

### Community 25 - "frappe-index.js"
Cohesion: 0.08
Nodes (20): ConfirmDelete(), convertToConditions(), cstr(), deepClone(), formatDate(), getBrowserTimezone(), getFormat(), getFormScript() (+12 more)

### Community 26 - "EmailEditor.vue"
Cohesion: 0.06
Nodes (25): applyEmailTemplate(), attachments, bcc, bccEmails, bccInput, { capture }, cc, ccEmails (+17 more)

### Community 27 - "ProductModal.vue"
Cohesion: 0.09
Nodes (27): addVariantAttribute(), availableTemplates, clearFieldErrors(), emit, ensurePrimaryCategory(), error, fieldErrors, form (+19 more)

### Community 28 - "useDocument"
Cohesion: 0.12
Nodes (27): deleteFileRecord(), isFileUrl(), pendingDeletionsMap, useAttachments(), processPendingDeletions(), trackOldFile(), assigneesCache, controllersCache (+19 more)

### Community 29 - "DealDetailView.vue"
Cohesion: 0.06
Nodes (28): activeTabName, activities, assignees, currentStage, currentStageLabel, currentStageType, deal, dealId (+20 more)

### Community 30 - "frappe-ui"
Cohesion: 0.14
Nodes (11): frappe-ui, items, editMode, inputRef, isNew, localOption, props, saveOption() (+3 more)

### Community 31 - "DoubleTLeadInfoPanel.vue"
Cohesion: 0.09
Nodes (26): cancelEdit(), companies, convertedLabels, detailsEditing, detailsError, detailsForm, detailsSaving, emit (+18 more)

### Community 32 - "QuotationEmails.vue"
Cohesion: 0.08
Nodes (23): apiCanWrite, canReply, canSendPdf, description, draft, emails, emit, emptyDescription (+15 more)

### Community 33 - "TaskModal.vue"
Cohesion: 0.09
Nodes (27): currentUser(), editingName, emit, emptyForm(), error, form, loadTask(), loadUsers() (+19 more)

### Community 34 - "ProductDetailView.vue"
Cohesion: 0.08
Nodes (25): canWrite, categories, categoryLabel(), currentProductId, error, errorMessage(), handleSaved(), loading (+17 more)

### Community 35 - "AllModals.vue"
Cohesion: 0.10
Nodes (26): activities, afterDoctype(), { capture }, createCallLog(), deleteTask(), emit, onboarding, props (+18 more)

### Community 36 - "PipelineAnalyticsReport.vue"
Cohesion: 0.09
Nodes (26): moneyMetric(), cell(), comparisonChange(), data, decimal(), displayDate(), errorMessage, filters (+18 more)

### Community 37 - "composables/settings.js"
Cohesion: 0.09
Nodes (19): emit, filteredTemplates, { on, send }, props, search, searchInput, show, templates (+11 more)

### Community 38 - "Questionnaire.vue"
Cohesion: 0.09
Nodes (21): advance(), answered, answers, autoAdvance(), canProceed, completed, current, emit (+13 more)

### Community 39 - "SalesPerformanceReport.vue"
Cohesion: 0.08
Nodes (26): cell(), closedDeals, comparisonChange(), data, dealMetricsAvailable, decimal(), displayDate(), displayDateTime() (+18 more)

### Community 40 - "CommunicationArea.vue"
Cohesion: 0.06
Nodes (35): attachments, { capture }, commentEmpty, deleteAttachedFiles(), doc, emailEmpty, emit, { getUser } (+27 more)

### Community 41 - "SidePanelLayout.vue"
Cohesion: 0.08
Nodes (26): maskStyle, props, scrollableDiv, side, doc, document, emit, fieldChange() (+18 more)

### Community 42 - "CallLogs.vue"
Cohesion: 0.09
Nodes (18): callLogStats, callTypes, filteredLogs, loadCallLogs(), loadCallLogStats(), pageCount, pageError, pageLoading (+10 more)

### Community 43 - "message"
Cohesion: 0.10
Nodes (24): canCreate, denied, error, hasMore, load(), loading, props, router (+16 more)

### Community 44 - "DoubleTDealDataPanel.vue"
Cohesion: 0.11
Nodes (22): apiError(), dirty, editableFields, emit, error, fillForm(), form, getDoc() (+14 more)

### Community 45 - "meta.js"
Cohesion: 0.17
Nodes (18): doctypesMeta, userSettings, noValueFieldTypes, standardFieldsMeta, cint(), flt(), formatCurrency(), formatNumber() (+10 more)

### Community 46 - "FieldLayoutEditor.vue"
Cohesion: 0.15
Nodes (14): addTab(), { $dialog }, { getFields }, getSectionOptions(), getTabOptions(), isDragging, onFieldDroppedToEmptyTab(), props (+6 more)

### Community 47 - "AudioPlayer.vue"
Cohesion: 0.06
Nodes (19): audio, currentPlaybackSpeed, currentTime, currentVolumn, duration, isPaused, options, progress (+11 more)

### Community 48 - "index.js"
Cohesion: 0.14
Nodes (15): displayText, exact, props, relative, { showExactTimestamp }, tooltipText, useDoubleTDeals(), fetchStages() (+7 more)

### Community 49 - "Field.vue"
Cohesion: 0.09
Nodes (20): emit, getButtonTheme(), getButtonVariant(), data, docname, doctype, field, formDocument (+12 more)

### Community 50 - "getMeta"
Cohesion: 0.15
Nodes (20): doctypeScripts, fileScriptCache, fileScriptModules, getScript(), evaluateFormClass(), setupFormController(), setupHelperMethods(), setupMultipleFormControllers() (+12 more)

### Community 51 - "ContactCenterCalls.vue"
Cohesion: 0.09
Nodes (21): callType, canManage, counts, error, fetchSearch, filtered, handlingOptions, handlingStatus (+13 more)

### Community 52 - "ZaloInbox.vue"
Cohesion: 0.10
Nodes (23): canRead, closeConversation(), conversations, detailsOpen, listError, listPending, loadConversations(), moreConversations (+15 more)

### Community 53 - "GridFieldsEditorModal.vue"
Cohesion: 0.10
Nodes (20): fields, addField(), dirty, dropdownFields, error, fieldObj(), fields, { getFields, getGridViewSettings, saveUserSettings } (+12 more)

### Community 54 - "ConvertToDealModal.vue"
Cohesion: 0.09
Nodes (20): { capture }, convertToDeal(), dealStatuses, dealTabs, { document: deal }, error, existingContact, existingContactChecked (+12 more)

### Community 55 - "DoubleTConvertToDealModal.vue"
Cohesion: 0.09
Nodes (21): amount, applyLeadCompanyDefault(), companies, companyMode, companyName, companyOptions, companySummary, convertLead() (+13 more)

### Community 56 - "GeolocationControl.vue"
Cohesion: 0.11
Nodes (16): addNonGroupLayers(), attrs, clearLocation(), containerClasses, coordinateSummary, { coords: geoCoords }, emit, fitMap() (+8 more)

### Community 57 - "users.js"
Cohesion: 0.18
Nodes (11): brand, brandName, dropdownItems, { getUser }, session, userFullName, usersStore, currentUserDisplayName() (+3 more)

### Community 58 - "ListBulkActions.vue"
Cohesion: 0.12
Nodes (21): close(), assignValues(), bulkActions(), bulkAssignees, { capture }, clearAssignments(), convertToDeal(), customBulkActions (+13 more)

### Community 59 - "ColumnSettings.vue"
Cohesion: 0.12
Nodes (17): addColumn(), apply(), column, columns, columnsUpdated, edit, emit, { getFields } (+9 more)

### Community 60 - "DoubleTLeadDataPanel.vue"
Cohesion: 0.10
Nodes (21): companies, dirty, editableFields, emit, error, fillForm(), form, getApiError() (+13 more)

### Community 61 - "package.json"
Cohesion: 0.12
Nodes (18): devDependencies, autoprefixer@^10.4.14, postcss@^8.4.5, tailwindcss@^3.4.15, vite@^5.4.21, @vitejs/plugin-vue@^5.2.4, name, private (+10 more)

### Community 62 - "MobileNotification.vue"
Cohesion: 0.12
Nodes (10): hide, opened, props, toggle(), { mark_as_read, mark_doc_as_read }, { $socket }, notifications, notificationsStore (+2 more)

### Community 63 - "LeadModal.vue"
Cohesion: 0.10
Nodes (16): { capture }, createLead, { document: lead, triggerOnBeforeCreate }, error, { getLeadStatus, statusOptions }, { getUser, isManager }, isLeadCreating, leadStatuses (+8 more)

### Community 64 - "EditValueModal.vue"
Cohesion: 0.10
Nodes (18): { capture }, emit, field, fields, getSelectOptions(), getValueComponent(), loading, newValue (+10 more)

### Community 65 - "ProductCategoriesView.vue"
Cohesion: 0.11
Nodes (19): actionError, categories, categoriesResource, categoryFields, deleteCategory(), deletingName, editingCategory, fetchCategories() (+11 more)

### Community 66 - "dependencies"
Cohesion: 0.11
Nodes (19): dependencies, dompurify@^3.3.3, frappe-ui@1.0.0-beta.19, gemoji@^8.1.0, lodash@^4.18.1, mime@^4.0.1, pinia@^2.0.33, @tiptap/extension-paragraph@^3.26.0 (+11 more)

### Community 67 - "Popover.vue"
Cohesion: 0.13
Nodes (10): @popperjs/core@^2.11.8, @popperjs/core, close(), mounted(), onMouseleave(), open(), setupPopper(), show() (+2 more)

### Community 68 - "EmailContent.vue"
Cohesion: 0.17
Nodes (12): _content, doc, files, gmailReplyToContent, iframeRef, outlookReplyToContent, parser, parseReplyToContent() (+4 more)

### Community 69 - "DealModal.vue"
Cohesion: 0.10
Nodes (19): { capture }, chooseExistingContact, chooseExistingOrganization, dealStatuses, { document: deal, triggerOnBeforeCreate }, error, { getDealStatus, statusOptions }, { getUser, isManager } (+11 more)

### Community 70 - "OrganizationModal.vue"
Cohesion: 0.12
Nodes (16): createDeal(), createNewLead(), { capture }, createOrganization(), { document: organization, triggerOnBeforeCreate }, error, handleOrganizationUpdate(), { isManager } (+8 more)

### Community 71 - "ZaloConversationThread.vue"
Cohesion: 0.11
Nodes (18): canReply, contextKey, conversationName, draft, emit, history, isComposing, loadThread() (+10 more)

### Community 72 - "ActivityHeader.vue"
Cohesion: 0.12
Nodes (16): loadCreatePermissions(), callActions, defaultActions, emailBox, getTabIndex(), { makeCall }, openNote(), openTask() (+8 more)

### Community 73 - "formatCurrency"
Cohesion: 0.16
Nodes (15): dealAmount(), displayAmount, useDoubleTProducts(), fetchProducts(), reloadCategoryAssignments(), setFilters(), displayAmount, openProduct() (+7 more)

### Community 74 - "PriceListModal.vue"
Cohesion: 0.15
Nodes (17): addItem(), clearErrors(), emit, error, fieldErrors, form, isChecked(), isEditMode (+9 more)

### Community 75 - "DeleteLinkedDocModal.vue"
Cohesion: 0.13
Nodes (13): confirmDeleteInfo, deleteDoc(), deleting, linkedDocs, linkedDocsResource, lookup, props, removeDocLinks() (+5 more)

### Community 76 - "SortBy.vue"
Cohesion: 0.15
Nodes (14): apply(), clearSort(), convertToString(), emit, list, options, props, removeSort() (+6 more)

### Community 77 - "AppSidebar.vue"
Cohesion: 0.12
Nodes (9): collapsedPreference, compactRoutes, contactCenterLinks, forceCompactRail, isSidebarCollapsed, links, narrow, route (+1 more)

### Community 78 - "FrappeDealsListView.vue"
Cohesion: 0.13
Nodes (10): emit, isLikeFilterApplied, list, pageLengthCount, emit, isLikeFilterApplied, list, pageLengthCount (+2 more)

### Community 79 - "WhatsAppBox.vue"
Cohesion: 0.05
Nodes (32): { capture }, emoji, formatWhatsAppMessage(), list, messageOptions(), reaction, reply, replyMode (+24 more)

### Community 80 - "CallLogDetailModal.vue"
Cohesion: 0.12
Nodes (16): close(), activeSection, body, callDirectionIcon, customerRoute, duration, linkMessages, panel (+8 more)

### Community 81 - "MultiSelectEmailInput.vue"
Cohesion: 0.11
Nodes (17): @headlessui/vue@X, @headlessui/vue, addValue(), emails, error, filterOptions, info, options (+9 more)

### Community 82 - "reportDatePreset"
Cohesion: 0.12
Nodes (22): emit, presets, props, setPreset(), validationError, formatInputDate(), isPermissionError(), previousReportPeriod() (+14 more)

### Community 83 - "OrdersView.vue"
Cohesion: 0.13
Nodes (12): canCreate, customerLabels, dealLabels, error, hasMore, loading, router, rows (+4 more)

### Community 84 - "ContactModal.vue"
Cohesion: 0.14
Nodes (15): { capture }, createContact(), { document: _contact, triggerOnBeforeCreate }, error, handleContactUpdate(), insertContact, { isManager }, props (+7 more)

### Community 85 - "quotation.js"
Cohesion: 0.19
Nodes (14): totals, availableContacts, matchingDeals, totals, appendCatalogSelections(), contactsForCustomer(), createQuotationItem(), customerFromDeal() (+6 more)

### Community 86 - "QuotationsView.vue"
Cohesion: 0.14
Nodes (12): canCreate, customerLabels, dealLabels, error, hasMore, loading, router, rows (+4 more)

### Community 87 - "CommentBox.vue"
Cohesion: 0.14
Nodes (10): attachments, { capture }, content, editor, emoji, modelValue, textEditor, textEditorMenuButtons (+2 more)

### Community 88 - "call"
Cohesion: 0.13
Nodes (19): call, loadCompanies(), loadConvertedLabels(), loadSources(), loadUsers(), loadRelatedRecords(), create(), duplicateMode (+11 more)

### Community 89 - "AssignToBody.vue"
Cohesion: 0.10
Nodes (14): deleteNote(), { getUser }, notes, addAssignees, assignees, assignToMe, {
  capture,
}, eligibleUserNames (+6 more)

### Community 90 - "AddChartModal.vue"
Cohesion: 0.13
Nodes (15): addChart(), axisChart, axisCharts, chartType, chartTypes, donutChart, donutCharts, filters (+7 more)

### Community 91 - "LeadCreateModal.vue"
Cohesion: 0.16
Nodes (15): createLead(), createLeadAnyway(), duplicateCheck, duplicateMatches, emit, error, getEmptyLead(), insertLead (+7 more)

### Community 92 - "router.js"
Cohesion: 0.16
Nodes (10): CallLogDetails(), CompanyDetailView(), ContactDetailView(), DealDetailView(), FrappeLead(), OrderForm(), ProductsView(), QuotationForm() (+2 more)

### Community 93 - "FieldLayout.vue"
Cohesion: 0.13
Nodes (11): { isManager }, props, show, showGridRowFieldsModal, tabs, hasTabs, overrides, processedTabs (+3 more)

### Community 94 - "Autocomplete.vue"
Cohesion: 0.14
Nodes (13): attrs, emit, filterOptions(), groups, inputClasses, props, query, search (+5 more)

### Community 95 - "telephony.js"
Cohesion: 0.15
Nodes (9): callEnabled, defaultCallingMedium, integrations, useTelephony(), useTimelinePreferences(), brand, DEFAULT_SETTINGS, getSettings() (+1 more)

### Community 96 - "formatDate"
Cohesion: 0.53
Nodes (10): timestampCell(), rows, parseRows(), parseRows(), rows, getFormattedCurrency(), getFormattedFloat(), getFormattedPercent() (+2 more)

### Community 97 - "ReportsPage.vue"
Cohesion: 0.20
Nodes (11): liveReportKeys, props, report, ReportsPage(), getReportSection(), REPORT_SECTIONS, REPORTS_HOME_ROUTE, reportsPageSource (+3 more)

### Community 98 - "AttachmentItem.vue"
Cohesion: 0.11
Nodes (8): emailBox, props, status, content, isImage, isSpreadsheet, props, showDialog

### Community 99 - "QuotationOrderReport.vue"
Cohesion: 0.09
Nodes (26): cell(), comparisonChange(), conversion, data, decimal(), errorMessage, filters, hasResults (+18 more)

### Community 100 - "vue-router"
Cohesion: 0.22
Nodes (7): callbackRoute(), { $dialog }, { getUser }, openTask(), props, router, taskStatusOptions()

### Community 101 - "Contacts.vue"
Cohesion: 0.15
Nodes (11): columns, contacts, contactsListView, { getFormattedPercent, getFormattedFloat, getFormattedCurrency }, { getOrganization }, loadMore, showContactModal, triggerResize (+3 more)

### Community 102 - "ListRows.vue"
Cohesion: 0.15
Nodes (10): emit, getRowRoute(), openDetail(), props, router, props, reactivieRows, scrollContainer (+2 more)

### Community 103 - "KanbanSettings.vue"
Cohesion: 0.15
Nodes (10): allFields, apply(), columnField, columnFields, emit, { getFields }, list, props (+2 more)

### Community 104 - "CallLogAISummary.vue"
Cohesion: 0.16
Nodes (13): canGenerate, generate(), initialLoading, load(), notice, props, recordingMessages, refresh() (+5 more)

### Community 105 - "CustomerJourneyReport.vue"
Cohesion: 0.09
Nodes (24): cell(), comparisonChange(), data, decimal(), errorMessage, filters, hasResults, initialRange (+16 more)

### Community 106 - "Link.vue"
Cohesion: 0.19
Nodes (11): attrs, autocomplete, clearValue(), emit, labelClasses, options, props, stripHtml() (+3 more)

### Community 107 - "DataFieldsModal.vue"
Cohesion: 0.10
Nodes (20): { document }, emit, instance, { isManager }, props, saveChanges(), showDataFieldsModal, tabs (+12 more)

### Community 108 - "SidePanelModal.vue"
Cohesion: 0.18
Nodes (12): { capture }, dirty, _doctype, emit, getParams(), loading, preview, props (+4 more)

### Community 109 - "Dashboard.vue"
Cohesion: 0.11
Nodes (13): computedDescription, computedTitle, props, widthClass, Bars, cards, data, error (+5 more)

### Community 110 - "RecordCallHistory.vue"
Cohesion: 0.18
Nodes (10): error, hasMore, load(), loading, props, rows, callOutcomeTheme(), caseStatusTheme (+2 more)

### Community 111 - "KanbanView.vue"
Cohesion: 0.19
Nodes (11): actions(), addColumn(), columns, deletedColumns, emit, kanban, titleField, updateColumn() (+3 more)

### Community 112 - "AssignmentModal.vue"
Cohesion: 0.18
Nodes (9): assignees, { capture }, emit, error, oldAssignees, props, show, updateAssignees() (+1 more)

### Community 113 - "LeadDetailView.vue"
Cohesion: 0.17
Nodes (10): dateValue(), error, InfoField, lead, loading, loadLead(), route, router (+2 more)

### Community 114 - "DoubleTDealKanban.vue"
Cohesion: 0.14
Nodes (11): dragging, emit, localColumns, movePending, onDragEnd(), props, rebuildColumns(), router (+3 more)

### Community 115 - "close"
Cohesion: 0.28
Nodes (9): close(), deleteView(), duplicateView(), editView(), isDefaultView(), pinView(), publicView(), setAsDefault() (+1 more)

### Community 116 - "RatingInput.vue"
Cohesion: 0.11
Nodes (14): emit, hoveredStarValue, nStars, onStarClick(), props, savedStarValue, tooltipText, emit (+6 more)

### Community 117 - "Organizations.vue"
Cohesion: 0.12
Nodes (13): groupedActions, groupedWithLabelActions, normalActions, props, columns, { getFormattedPercent, getFormattedFloat, getFormattedCurrency }, loadMore, organizations (+5 more)

### Community 118 - "ZaloRecordChat.vue"
Cohesion: 0.18
Nodes (10): conversations, error, loadConversations(), loading, props, referenceKey, requestContext, restricted (+2 more)

### Community 119 - "ActivityContactCenterReport.vue"
Cohesion: 0.09
Nodes (18): barHeight(), data, employeeFilterSupported, employees, errorMessage, filters, initialRange, legend (+10 more)

### Community 120 - "DurationInput.vue"
Cohesion: 0.17
Nodes (14): attrs, commit(), editValue, emit, errorMessage, handleBlur(), handleKeydown(), inputRef (+6 more)

### Community 121 - "TableMultiselectInput.vue"
Cohesion: 0.17
Nodes (15): addValue(), create(), emit, error, filters, { getFields }, getLinkField(), linkField (+7 more)

### Community 122 - "OrganizationsListView.vue"
Cohesion: 0.14
Nodes (18): displayValue, handleFocus(), getLabel(), getLabel(), getLabel(), getLabel(), emit, getLabel() (+10 more)

### Community 123 - "LayoutHeader.vue"
Cohesion: 0.13
Nodes (11): showHeader, availableSources, filteredRows, {
  leadsResource,
  columns,
  rows,
  totalCount,
  reload,
  loadMore,
}, searchQuery, selectedSource, selectedStatus, showCreateLead (+3 more)

### Community 124 - "SLASection.vue"
Cohesion: 0.31
Nodes (7): { capture }, { communicationStatuses }, data, emit, slaSection, statusesStore, formatTime()

### Community 125 - "TasksListView.vue"
Cohesion: 0.15
Nodes (7): props, emit, isLikeFilterApplied, list, listBulkActionsRef, pageLengthCount, { user }

### Community 126 - "@vueuse/core"
Cohesion: 0.19
Nodes (12): @vueuse/core@^15.0.0, @vueuse/core, debouncedFn, emit, filter, props, updateFilter(), useActiveTabManager() (+4 more)

### Community 127 - "GroupBy.vue"
Cohesion: 0.25
Nodes (7): emit, groupByOptions, groupByValue, list, options, props, setGroupBy()

### Community 128 - "view.js"
Cohesion: 0.25
Nodes (5): breadcrumbs, breadcrumbs, getView(), { getView: getViewDetails }, standardView()

### Community 129 - "CallLogsListView.vue"
Cohesion: 0.22
Nodes (7): emit, getLabel(), isLikeFilterApplied, list, listBulkActionsRef, pageLengthCount, { user }

### Community 130 - "main.js"
Cohesion: 0.16
Nodes (8): { setTheme }, app, globalComponents, pinia, router, format(), translate(), translationPlugin()

### Community 131 - "WhatsappTemplateSelectorModal.vue"
Cohesion: 0.22
Nodes (7): emit, filteredTemplates, props, search, searchInput, show, templates

### Community 132 - "ZaloCustomerDetails.vue"
Cohesion: 0.22
Nodes (8): conversationName, details, emit, error, load(), loading, props, recordLinks

### Community 133 - "FormattedInput.vue"
Cohesion: 0.25
Nodes (6): attrs, descriptionClasses, displayValue, inputRef, isFocused, props

### Community 134 - "TextEditorControl.vue"
Cohesion: 0.29
Nodes (6): editorClasses, emit, isDirty, latestContent, onBlur(), props

### Community 135 - "useDoubleTCompanies"
Cohesion: 0.46
Nodes (8): useDoubleTCompanies(), fetchCompanies(), fetchCount(), fetchIndustryOptions(), getFilters(), getSearchFilters(), loadMore(), reload()

### Community 136 - "useDoubleTContacts"
Cohesion: 0.43
Nodes (7): useDoubleTContacts(), fetchContacts(), fetchCount(), findMatchingCompanyIds(), loadCompanyNames(), loadMore(), reload()

### Community 137 - "vue"
Cohesion: 0.40
Nodes (5): pinia, vue, { logout }, sessionStore, viewsStore

### Community 138 - "resolveProductImage"
Cohesion: 0.31
Nodes (8): displayImage, useSellableProducts(), hydrateProductDetails(), loadProducts(), resolvedImage, productImage(), buildSellableProductListRequest(), resolveProductImage()

### Community 139 - "Password.vue"
Cohesion: 0.29
Nodes (4): props, show, showEye, isMac

### Community 140 - "Resizer.vue"
Cohesion: 0.38
Nodes (6): distance(), props, resize(), sidebarResizing, sidebarWidth, startResize()

### Community 141 - "itemPricing"
Cohesion: 0.27
Nodes (10): addItem(), addSelectedProducts(), itemPricing(), markManualPrice(), pricingContextChanged(), pricingPending, pricingSourceLabel(), repriceAutomaticItems() (+2 more)

### Community 142 - "MultiActionButton.vue"
Cohesion: 0.40
Nodes (5): activeButton, parsedOptions, props, showDropdown, DropdownOption()

### Community 143 - "SidePanelLayoutEditor.vue"
Cohesion: 0.22
Nodes (6): vuedraggable@^4.1.0, vuedraggable, { getFields }, props, restrictedFieldTypes, sections

### Community 144 - "saveStage"
Cohesion: 0.22
Nodes (11): changeStage(), confirmLostStage(), getApiError(), getStage(), loadDeal(), loadStages(), onDealSaved(), parseAssigneesFromJson() (+3 more)

### Community 145 - "LeadsListView.vue"
Cohesion: 0.22
Nodes (7): emit, isLikeFilterApplied, list, listBulkActionsRef, pageLengthCount, route, { user }

### Community 147 - "initMap"
Cohesion: 0.29
Nodes (7): leaflet@^1.9.4, leaflet-draw@1.0.4, leaflet.locatecontrol@0.89.0, leaflet, leaflet-draw, leaflet.locatecontrol, initMap()

### Community 151 - "pipelineAnalytics.test.mjs"
Cohesion: 0.33
Nodes (5): backendSource, dealsComposableSource, dealsViewSource, pipelineSource, reportsPageSource

### Community 152 - "Icon.vue"
Cohesion: 0.40
Nodes (4): createView(), getIcon(), viewsDropdownOptions, isEmoji()

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `vue` connect `vue` to `ViewControls.vue`, `QuotationForm.vue`, `FilesUploaderArea.vue`, `Tasks.vue`, `Activities.vue`, `ContactsView.vue`, `OrderForm.vue`, `DealsView.vue`, `FrappeDeal.vue`, `FilesUploader.vue`, `PriceListsView.vue`, `DoubleTContactInfoPanel.vue`, `FrappeLead.vue`, `ContactDetailView.vue`, `CommentArea.vue`, `CallLogDetails.vue`, `Grid.vue`, `Filter.vue`, `SharedNotes.vue`, `DoubleTEntityDetail.vue`, `DoubleTDealInfoPanel.vue`, `Leads.vue`, `TableMultiselectInput.vue`, `ProductsView.vue`, `Deals.vue`, `frappe-index.js`, `EmailEditor.vue`, `ProductModal.vue`, `useDocument`, `DealDetailView.vue`, `frappe-ui`, `DoubleTLeadInfoPanel.vue`, `QuotationEmails.vue`, `TaskModal.vue`, `ProductDetailView.vue`, `AllModals.vue`, `PipelineAnalyticsReport.vue`, `composables/settings.js`, `Questionnaire.vue`, `SalesPerformanceReport.vue`, `CommunicationArea.vue`, `SidePanelLayout.vue`, `CallLogs.vue`, `message`, `DoubleTDealDataPanel.vue`, `meta.js`, `FieldLayoutEditor.vue`, `AudioPlayer.vue`, `index.js`, `Field.vue`, `getMeta`, `ContactCenterCalls.vue`, `ZaloInbox.vue`, `GridFieldsEditorModal.vue`, `ConvertToDealModal.vue`, `DoubleTConvertToDealModal.vue`, `GeolocationControl.vue`, `users.js`, `ListBulkActions.vue`, `ColumnSettings.vue`, `DoubleTLeadDataPanel.vue`, `package.json`, `MobileNotification.vue`, `LeadModal.vue`, `EditValueModal.vue`, `ProductCategoriesView.vue`, `dependencies`, `EmailContent.vue`, `DealModal.vue`, `OrganizationModal.vue`, `ZaloConversationThread.vue`, `ActivityHeader.vue`, `formatCurrency`, `PriceListModal.vue`, `DeleteLinkedDocModal.vue`, `SortBy.vue`, `AppSidebar.vue`, `FrappeDealsListView.vue`, `WhatsAppBox.vue`, `CallLogDetailModal.vue`, `MultiSelectEmailInput.vue`, `reportDatePreset`, `OrdersView.vue`, `ContactModal.vue`, `quotation.js`, `QuotationsView.vue`, `CommentBox.vue`, `call`, `AssignToBody.vue`, `AddChartModal.vue`, `LeadCreateModal.vue`, `FieldLayout.vue`, `Autocomplete.vue`, `telephony.js`, `ReportsPage.vue`, `AttachmentItem.vue`, `QuotationOrderReport.vue`, `Contacts.vue`, `ListRows.vue`, `KanbanSettings.vue`, `CallLogAISummary.vue`, `CustomerJourneyReport.vue`, `Link.vue`, `DataFieldsModal.vue`, `SidePanelModal.vue`, `Dashboard.vue`, `RecordCallHistory.vue`, `KanbanView.vue`, `AssignmentModal.vue`, `LeadDetailView.vue`, `DoubleTDealKanban.vue`, `RatingInput.vue`, `Organizations.vue`, `ZaloRecordChat.vue`, `ActivityContactCenterReport.vue`, `DurationInput.vue`, `TableMultiselectInput.vue`, `OrganizationsListView.vue`, `LayoutHeader.vue`, `SLASection.vue`, `TasksListView.vue`, `@vueuse/core`, `GroupBy.vue`, `view.js`, `CallLogsListView.vue`, `main.js`, `WhatsappTemplateSelectorModal.vue`, `ZaloCustomerDetails.vue`, `FormattedInput.vue`, `TextEditorControl.vue`, `resolveProductImage`, `Password.vue`, `Resizer.vue`, `MultiActionButton.vue`, `SidePanelLayoutEditor.vue`, `LeadsListView.vue`, `ProductThumbnail.vue`?**
  _High betweenness centrality (0.382) - this node is a cross-community bridge._
- **Are the 142 inferred relationships involving `call` (e.g. with `deleteTask()` and `updateTaskStatus()`) actually correct?**
  _`call` has 142 INFERRED edges - model-reasoned connections that need verification._
- **Should `ViewControls.vue` be split into smaller, more focused modules?**
  _Cohesion score 0.042162698412698416 - nodes in this community are weakly interconnected._
- **Why does `frappe-ui` connect `frappe-ui` to `ViewControls.vue`, `QuotationForm.vue`, `FilesUploaderArea.vue`, `Tasks.vue`, `Activities.vue`, `ContactsView.vue`, `OrderForm.vue`, `DealsView.vue`, `FrappeDeal.vue`, `FilesUploader.vue`, `PriceListsView.vue`, `DoubleTContactInfoPanel.vue`, `FrappeLead.vue`, `ContactDetailView.vue`, `CommentArea.vue`, `CallLogDetails.vue`, `Grid.vue`, `Filter.vue`, `SharedNotes.vue`, `DoubleTEntityDetail.vue`, `DoubleTDealInfoPanel.vue`, `Leads.vue`, `TableMultiselectInput.vue`, `ProductsView.vue`, `Deals.vue`, `frappe-index.js`, `EmailEditor.vue`, `ProductModal.vue`, `useDocument`, `DealDetailView.vue`, `DoubleTLeadInfoPanel.vue`, `QuotationEmails.vue`, `TaskModal.vue`, `ProductDetailView.vue`, `AllModals.vue`, `PipelineAnalyticsReport.vue`, `composables/settings.js`, `Questionnaire.vue`, `SalesPerformanceReport.vue`, `CommunicationArea.vue`, `SidePanelLayout.vue`, `CallLogs.vue`, `message`, `DoubleTDealDataPanel.vue`, `meta.js`, `FieldLayoutEditor.vue`, `AudioPlayer.vue`, `index.js`, `Field.vue`, `getMeta`, `ContactCenterCalls.vue`, `ZaloInbox.vue`, `GridFieldsEditorModal.vue`, `ConvertToDealModal.vue`, `DoubleTConvertToDealModal.vue`, `GeolocationControl.vue`, `users.js`, `ListBulkActions.vue`, `ColumnSettings.vue`, `DoubleTLeadDataPanel.vue`, `package.json`, `MobileNotification.vue`, `LeadModal.vue`, `EditValueModal.vue`, `ProductCategoriesView.vue`, `dependencies`, `DealModal.vue`, `OrganizationModal.vue`, `ZaloConversationThread.vue`, `ActivityHeader.vue`, `formatCurrency`, `PriceListModal.vue`, `DeleteLinkedDocModal.vue`, `SortBy.vue`, `AppSidebar.vue`, `FrappeDealsListView.vue`, `WhatsAppBox.vue`, `CallLogDetailModal.vue`, `MultiSelectEmailInput.vue`, `OrdersView.vue`, `ContactModal.vue`, `QuotationsView.vue`, `CommentBox.vue`, `call`, `AssignToBody.vue`, `AddChartModal.vue`, `LeadCreateModal.vue`, `FieldLayout.vue`, `Autocomplete.vue`, `telephony.js`, `AttachmentItem.vue`, `QuotationOrderReport.vue`, `vue-router`, `Contacts.vue`, `ListRows.vue`, `KanbanSettings.vue`, `CallLogAISummary.vue`, `CustomerJourneyReport.vue`, `Link.vue`, `DataFieldsModal.vue`, `SidePanelModal.vue`, `Dashboard.vue`, `RecordCallHistory.vue`, `KanbanView.vue`, `AssignmentModal.vue`, `LeadDetailView.vue`, `DoubleTDealKanban.vue`, `RatingInput.vue`, `Organizations.vue`, `ZaloRecordChat.vue`, `ActivityContactCenterReport.vue`, `DurationInput.vue`, `OrganizationsListView.vue`, `LayoutHeader.vue`, `SLASection.vue`, `TasksListView.vue`, `@vueuse/core`, `GroupBy.vue`, `CallLogsListView.vue`, `main.js`, `WhatsappTemplateSelectorModal.vue`, `ZaloCustomerDetails.vue`, `FormattedInput.vue`, `TextEditorControl.vue`, `vue`, `resolveProductImage`, `Password.vue`, `MultiActionButton.vue`, `SidePanelLayoutEditor.vue`, `LeadsListView.vue`?**
  _High betweenness centrality (0.323) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `useDocument()` (e.g. with `getControllers()` and `setFieldHtml()`) actually correct?**
  _`useDocument()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Should `QuotationForm.vue` be split into smaller, more focused modules?**
  _Cohesion score 0.033016734509271825 - nodes in this community are weakly interconnected._
- **Why does `vue-router` connect `ContactsView.vue` to `ViewControls.vue`, `QuotationForm.vue`, `Tasks.vue`, `Activities.vue`, `OrderForm.vue`, `DealsView.vue`, `FrappeDeal.vue`, `vue`, `DoubleTContactInfoPanel.vue`, `FrappeLead.vue`, `ContactDetailView.vue`, `CallLogDetails.vue`, `LeadsListView.vue`, `SharedNotes.vue`, `DoubleTEntityDetail.vue`, `DoubleTDealInfoPanel.vue`, `Leads.vue`, `ProductsView.vue`, `Deals.vue`, `DealDetailView.vue`, `DoubleTLeadInfoPanel.vue`, `QuotationEmails.vue`, `ProductDetailView.vue`, `AllModals.vue`, `PipelineAnalyticsReport.vue`, `composables/settings.js`, `Questionnaire.vue`, `CallLogs.vue`, `message`, `AudioPlayer.vue`, `ZaloInbox.vue`, `ConvertToDealModal.vue`, `ListBulkActions.vue`, `package.json`, `LeadModal.vue`, `ProductCategoriesView.vue`, `dependencies`, `DealModal.vue`, `OrganizationModal.vue`, `DeleteLinkedDocModal.vue`, `AppSidebar.vue`, `OrdersView.vue`, `ContactModal.vue`, `QuotationsView.vue`, `router.js`, `vue-router`, `Contacts.vue`, `ListRows.vue`, `Dashboard.vue`, `LeadDetailView.vue`, `DoubleTDealKanban.vue`, `RatingInput.vue`, `ActivityContactCenterReport.vue`, `OrganizationsListView.vue`, `@vueuse/core`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._