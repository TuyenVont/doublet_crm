# Graph Report - frontend  (2026-11-25)

## Corpus Check
- 330 files · ~149,411 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 1 file(s) not represented in the graph (top: .css 1)

## Summary
- 3298 nodes · 5872 edges · 151 communities (145 shown, 6 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 285 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `809089aa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ViewControls.vue
- QuotationForm.vue
- FilesUploaderArea.vue
- Tasks.vue
- Activities.vue
- LayoutHeader.vue
- OrderForm.vue
- DealsView.vue
- FrappeDeal.vue
- FilesUploader.vue
- PriceListsView.vue
- DoubleTContactInfoPanel.vue
- FrappeLead.vue
- ContactDetailView.vue
- DoubleTContactInfoPanel.vue
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
- WhatsAppBox.vue
- PipelineAnalyticsReport.vue
- composables/settings.js
- Questionnaire.vue
- SalesPerformanceReport.vue
- CommunicationArea.vue
- SidePanelLayout.vue
- CallLogs.vue
- call
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
- MultiSelectEmailInput.vue
- vue
- DealModal.vue
- OrganizationModal.vue
- ZaloConversationThread.vue
- ActivityHeader.vue
- useDoubleTProducts
- PriceListModal.vue
- DeleteLinkedDocModal.vue
- SortBy.vue
- AppSidebar.vue
- LeadsListView.vue
- WhatsAppArea.vue
- CallLogDetailModal.vue
- SmartInsightsReport.vue
- reportDatePreset
- OrdersView.vue
- ContactModal.vue
- quotation.js
- call
- CommentBox.vue
- IconPicker.vue
- AssignToBody.vue
- getParams
- LeadCreateModal.vue
- router.js
- DataFields.vue
- Autocomplete.vue
- telephony.js
- formatDate
- ReportsPage.vue
- AttachmentItem.vue
- QuotationOrderReport.vue
- vue-router
- Contacts.vue
- AttachControl.vue
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
- money
- close
- RatingInput.vue
- Organizations.vue
- ZaloRecordChat.vue
- ActivityContactCenterReport.vue
- DurationInput.vue
- AttachmentArea.vue
- ContactsListView.vue
- GridRowFieldsModal.vue
- SLASection.vue
- doctypeModal.js
- @vueuse/core
- GroupBy.vue
- view.js
- CallLogsListView.vue
- FilesUploadHandler
- WhatsappTemplateSelectorModal.vue
- ZaloCustomerDetails.vue
- EditIcon.vue
- TextEditorControl.vue
- useDoubleTCompanies
- useDoubleTContacts
- @vueuse/core
- productCatalog.js
- Password.vue
- Resizer.vue
- MultiActionButton.vue
- components.d.ts
- CollapsibleSection.vue
- ref_node_assert
- ProductThumbnail.vue
- useActiveTabManager
- useDoubleTPriceLists

## God Nodes (most connected - your core abstractions)
1. `vue` - 185 edges
2. `frappe-ui` - 174 edges
3. `call` - 150 edges
4. `vue-router` - 59 edges
5. `message()` - 46 edges
6. `useDocument()` - 40 edges
7. `getMeta()` - 40 edges
8. `formatDate()` - 33 edges
9. `usersStore` - 27 edges
10. `isTranslatable()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `load()` --calls--> `call`  [INFERRED]
  src/components/Calls/RecordCallHistory.vue → src/components/Activities/CallArea.vue
- `load()` --calls--> `call`  [INFERRED]
  src/pages/Dashboard.vue → src/components/Activities/CallArea.vue
- `openEdit()` --calls--> `call`  [INFERRED]
  src/pages/PriceListsView.vue → src/components/Activities/CallArea.vue
- `loadStages()` --calls--> `call`  [INFERRED]
  src/components/Contact/DoubleTContactInfoPanel.vue → src/components/Activities/CallArea.vue
- `loadLead()` --calls--> `call`  [INFERRED]
  src/pages/LeadDetailView.vue → src/components/Activities/CallArea.vue

## Import Cycles
- 2-file cycle: `src/components/Modals/SidePanelModal.vue -> src/components/SidePanelLayout.vue -> src/components/Modals/SidePanelModal.vue`
- 3-file cycle: `src/pages/Tasks.vue -> src/stores/session.js -> src/router.js -> src/pages/Tasks.vue`
- 4-file cycle: `src/components/Modals/LeadCreateModal.vue -> src/stores/session.js -> src/router.js -> src/pages/LeadsView.vue -> src/components/Modals/LeadCreateModal.vue`

## Communities (151 total, 6 thin omitted)

### Community 0 - "ViewControls.vue"
Cohesion: 0.04
Nodes (38): { brand }, cancelChanges(), createView(), customizeQuickFilter, defaultParams, { $dialog }, export_all, export_type (+30 more)

### Community 1 - "QuotationForm.vue"
Cohesion: 0.03
Nodes (69): activeTab, addItem(), addSelectedProducts(), canCreateOrder, canDelete, canWrite, catalogAdding, catalogQuantities (+61 more)

### Community 2 - "FilesUploaderArea.vue"
Cohesion: 0.07
Nodes (29): addFiles(), allowMultiple, allowTakePhoto, allowWebLink, cameraImage, canvas, checkRestrictions(), disableFileBrowser (+21 more)

### Community 3 - "Tasks.vue"
Cohesion: 0.06
Nodes (44): canCreate, dateValue(), deleteTask(), displayDue(), dueFilter, editingName, editorOpen, emptyForm() (+36 more)

### Community 4 - "Activities.vue"
Cohesion: 0.05
Nodes (38): activities, activitiesResource, all_activities, canCreateNote, canCreateTask, { capture }, doc, { document: _document } (+30 more)

### Community 5 - "LayoutHeader.vue"
Cohesion: 0.07
Nodes (22): showHeader, computedDescription, computedTitle, props, widthClass, {
  companiesResource,
  searchQuery,
  selectedIndustry,
  industryOptions,
  columns,
  rows,
  totalCount,
  reload,
  loadMore,
}, industryDropdownOptions, router (+14 more)

### Community 6 - "OrderForm.vue"
Cohesion: 0.06
Nodes (41): availableContacts, canWrite, changeStatus(), companies, companyChanged(), companyLabel, conflict, contactLabel (+33 more)

### Community 7 - "DealsView.vue"
Cohesion: 0.06
Nodes (34): dragging, emit, localColumns, movePending, onDragEnd(), props, rebuildColumns(), router (+26 more)

### Community 8 - "FrappeDeal.vue"
Cohesion: 0.05
Nodes (39): activities, addContact(), beforeStatusChange(), { brand }, canDelete, _contact, contactOptions(), dealContacts (+31 more)

### Community 9 - "FilesUploader.vue"
Cohesion: 0.15
Nodes (13): attachFile(), attachFiles(), disableAttachButton, emit, files, filesUploaderArea, fileUploadStarted, isAllPrivate (+5 more)

### Community 10 - "PriceListsView.vue"
Cohesion: 0.12
Nodes (11): actionError, openEdit(), priceLists, { priceListsResource, setFilters, reload, loadMore }, resourceError, searchQuery, selectedPriceList, selectedStatus (+3 more)

### Community 11 - "DoubleTContactInfoPanel.vue"
Cohesion: 0.12
Nodes (17): apiError(), checkDuplicates(), dirty, duplicateFilters(), duplicates, emit, error, fields (+9 more)

### Community 12 - "FrappeLead.vue"
Cohesion: 0.05
Nodes (26): activeTabName, activities, beforeStatusChange(), { brand }, canDelete, {
  $dialog,
  $socket,
  makeCall,
}, doc, {
  doctypeMeta,
} (+18 more)

### Community 13 - "ContactDetailView.vue"
Cohesion: 0.07
Nodes (29): loadCreatePermissions(), activeTabName, activities, apiError(), assignees, canDelete, canWrite, companyLabel (+21 more)

### Community 14 - "DoubleTContactInfoPanel.vue"
Cohesion: 0.10
Nodes (17): dealAmount(), deals, dealStageClass(), dealStages, dealStageType(), getDoc(), InfoRow, labels (+9 more)

### Community 15 - "CallLogDetails.vue"
Cohesion: 0.06
Nodes (35): actionError, actionSuccess, assigneeDraft, assigneeError, assigneeOptions, assignees, assigneesLoaded, assigneesLoading (+27 more)

### Community 16 - "Grid.vue"
Cohesion: 0.07
Nodes (29): addRow(), allFields, allRowsSelected, deleteRows(), fieldChange(), fields, getDefaultValue(), getFieldObj() (+21 more)

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
Cohesion: 0.08
Nodes (28): addValue(), create(), emit, error, filters, { getFields }, getLinkField(), linkField (+20 more)

### Community 23 - "ProductsView.vue"
Cohesion: 0.07
Nodes (31): actionError, canEditSelectedProduct, categories, categoriesError, categoryAssignments, categoryLabel(), categoryNames(), categoryOptions (+23 more)

### Community 24 - "Deals.vue"
Cohesion: 0.09
Nodes (26): actions(), after(), { capture }, columns, deals, dealsListView, defaults, { getDealStatus } (+18 more)

### Community 25 - "frappe-index.js"
Cohesion: 0.07
Nodes (23): checkMandatory(), _eval(), evaluateDependsOnValue(), evaluateExpression(), findMissingMandatory(), convertToConditions(), copyToClipboard(), deepClone() (+15 more)

### Community 26 - "EmailEditor.vue"
Cohesion: 0.06
Nodes (25): applyEmailTemplate(), attachments, bcc, bccEmails, bccInput, { capture }, cc, ccEmails (+17 more)

### Community 27 - "ProductModal.vue"
Cohesion: 0.09
Nodes (28): addVariantAttribute(), availableTemplates, clearFieldErrors(), displayImage, emit, ensurePrimaryCategory(), error, fieldErrors (+20 more)

### Community 28 - "useDocument"
Cohesion: 0.12
Nodes (27): deleteFileRecord(), isFileUrl(), pendingDeletionsMap, useAttachments(), processPendingDeletions(), trackOldFile(), assigneesCache, controllersCache (+19 more)

### Community 29 - "DealDetailView.vue"
Cohesion: 0.06
Nodes (39): activeTabName, activities, assignees, changeStage(), confirmLostStage(), currentStage, currentStageLabel, currentStageType (+31 more)

### Community 30 - "frappe-ui"
Cohesion: 0.09
Nodes (19): frappe-ui, { setTheme }, items, editMode, inputRef, isNew, localOption, props (+11 more)

### Community 31 - "DoubleTLeadInfoPanel.vue"
Cohesion: 0.07
Nodes (30): cancelEdit(), companies, convertedLabels, detailsEditing, detailsError, detailsForm, detailsSaving, emit (+22 more)

### Community 32 - "QuotationEmails.vue"
Cohesion: 0.04
Nodes (36): emailBox, props, status, _content, doc, files, gmailReplyToContent, iframeRef (+28 more)

### Community 33 - "TaskModal.vue"
Cohesion: 0.06
Nodes (45): activities, afterDoctype(), { capture }, createCallLog(), deleteTask(), emit, onboarding, props (+37 more)

### Community 34 - "ProductDetailView.vue"
Cohesion: 0.07
Nodes (29): canWrite, categories, categoryLabel(), currentProductId, error, errorMessage(), handleSaved(), loading (+21 more)

### Community 35 - "WhatsAppBox.vue"
Cohesion: 0.13
Nodes (14): { capture }, content, doc, emoji, fileType, placeholder, props, reply (+6 more)

### Community 36 - "PipelineAnalyticsReport.vue"
Cohesion: 0.07
Nodes (28): appliedFilters, cell(), comparisonChange(), data, decimal(), displayDate(), errorMessage, filters (+20 more)

### Community 37 - "composables/settings.js"
Cohesion: 0.14
Nodes (13): groupedActions, groupedWithLabelActions, normalActions, props, isActive, props, route, router (+5 more)

### Community 38 - "Questionnaire.vue"
Cohesion: 0.09
Nodes (21): advance(), answered, answers, autoAdvance(), canProceed, completed, current, emit (+13 more)

### Community 39 - "SalesPerformanceReport.vue"
Cohesion: 0.08
Nodes (28): appliedFilters, cell(), closedDeals, comparisonChange(), data, dealMetricsAvailable, decimal(), displayDate() (+20 more)

### Community 40 - "CommunicationArea.vue"
Cohesion: 0.09
Nodes (23): attachments, { capture }, commentEmpty, deleteAttachedFiles(), doc, emailEmpty, emit, { getUser } (+15 more)

### Community 41 - "SidePanelLayout.vue"
Cohesion: 0.07
Nodes (27): attrs, descriptionClasses, displayValue, inputRef, isFocused, props, maskStyle, props (+19 more)

### Community 42 - "CallLogs.vue"
Cohesion: 0.09
Nodes (18): callLogStats, callTypes, filteredLogs, loadCallLogs(), loadCallLogStats(), pageCount, pageError, pageLoading (+10 more)

### Community 43 - "call"
Cohesion: 0.12
Nodes (27): call, loadEmails(), submitReply(), applySaved(), deleteSaved(), emit, error, exportCsv() (+19 more)

### Community 44 - "DoubleTDealDataPanel.vue"
Cohesion: 0.11
Nodes (22): apiError(), dirty, editableFields, emit, error, fillForm(), form, getDoc() (+14 more)

### Community 45 - "meta.js"
Cohesion: 0.17
Nodes (18): doctypesMeta, userSettings, noValueFieldTypes, standardFieldsMeta, cint(), flt(), formatCurrency(), formatNumber() (+10 more)

### Community 46 - "FieldLayoutEditor.vue"
Cohesion: 0.06
Nodes (35): vuedraggable@^4.1.0, vuedraggable, addChart(), axisChart, axisCharts, chartType, chartTypes, donutChart (+27 more)

### Community 47 - "AudioPlayer.vue"
Cohesion: 0.06
Nodes (19): audio, currentPlaybackSpeed, currentTime, currentVolumn, duration, isPaused, options, progress (+11 more)

### Community 48 - "index.js"
Cohesion: 0.11
Nodes (14): props, displayText, exact, props, relative, { showExactTimestamp }, tooltipText, useDoubleTDeals() (+6 more)

### Community 49 - "Field.vue"
Cohesion: 0.10
Nodes (19): emit, getButtonTheme(), getButtonVariant(), data, docname, doctype, field, formDocument (+11 more)

### Community 50 - "getMeta"
Cohesion: 0.13
Nodes (22): gridSettings, doctypeScripts, fileScriptCache, fileScriptModules, getScript(), evaluateFormClass(), setupFormController(), setupHelperMethods() (+14 more)

### Community 51 - "ContactCenterCalls.vue"
Cohesion: 0.09
Nodes (21): callType, canManage, counts, error, fetchSearch, filtered, handlingOptions, handlingStatus (+13 more)

### Community 52 - "ZaloInbox.vue"
Cohesion: 0.10
Nodes (23): canRead, closeConversation(), conversations, detailsOpen, listError, listPending, loadConversations(), moreConversations (+15 more)

### Community 53 - "GridFieldsEditorModal.vue"
Cohesion: 0.10
Nodes (19): fields, addField(), dirty, dropdownFields, error, fieldObj(), fields, { getFields, getGridViewSettings, saveUserSettings } (+11 more)

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
Cohesion: 0.10
Nodes (20): pinia, deleteNote(), { getUser }, notes, brand, { getUser }, brandName, dropdownItems (+12 more)

### Community 58 - "ListBulkActions.vue"
Cohesion: 0.12
Nodes (21): close(), assignValues(), bulkActions(), bulkAssignees, { capture }, clearAssignments(), convertToDeal(), customBulkActions (+13 more)

### Community 59 - "ColumnSettings.vue"
Cohesion: 0.12
Nodes (16): addColumn(), apply(), column, columns, columnsUpdated, edit, emit, { getFields } (+8 more)

### Community 60 - "DoubleTLeadDataPanel.vue"
Cohesion: 0.10
Nodes (21): companies, dirty, editableFields, emit, error, fillForm(), form, getApiError() (+13 more)

### Community 61 - "package.json"
Cohesion: 0.12
Nodes (18): devDependencies, autoprefixer@^10.4.14, postcss@^8.4.5, tailwindcss@^3.4.15, vite@^5.4.21, @vitejs/plugin-vue@^5.2.4, name, private (+10 more)

### Community 62 - "MobileNotification.vue"
Cohesion: 0.18
Nodes (7): toggle(), { mark_as_read, mark_doc_as_read }, { $socket }, notifications, notificationsStore, unreadNotificationsCount, visible

### Community 63 - "LeadModal.vue"
Cohesion: 0.11
Nodes (16): { capture }, createLead, { document: lead, triggerOnBeforeCreate }, error, { getLeadStatus, statusOptions }, { getUser, isManager }, isLeadCreating, leadStatuses (+8 more)

### Community 64 - "EditValueModal.vue"
Cohesion: 0.10
Nodes (18): { capture }, emit, field, fields, getSelectOptions(), getValueComponent(), loading, newValue (+10 more)

### Community 65 - "ProductCategoriesView.vue"
Cohesion: 0.11
Nodes (18): actionError, categories, categoriesResource, categoryFields, deleteCategory(), deletingName, editingCategory, fetchCategories() (+10 more)

### Community 66 - "dependencies"
Cohesion: 0.09
Nodes (24): dependencies, dompurify@^3.3.3, frappe-ui@1.0.0-beta.19, @headlessui/vue@X, leaflet@^1.9.4, leaflet-draw@1.0.4, leaflet.locatecontrol@0.89.0, lodash@^4.18.1 (+16 more)

### Community 67 - "MultiSelectEmailInput.vue"
Cohesion: 0.07
Nodes (23): addValue(), emails, error, filterOptions, info, options, props, query (+15 more)

### Community 68 - "vue"
Cohesion: 0.11
Nodes (13): vue, emit, filteredTemplates, { on, send }, props, search, searchInput, show (+5 more)

### Community 69 - "DealModal.vue"
Cohesion: 0.10
Nodes (18): { capture }, chooseExistingContact, chooseExistingOrganization, createDeal(), dealStatuses, { document: deal, triggerOnBeforeCreate }, error, { getDealStatus, statusOptions } (+10 more)

### Community 70 - "OrganizationModal.vue"
Cohesion: 0.12
Nodes (16): vue-router, { capture }, createOrganization(), { document: organization, triggerOnBeforeCreate }, error, handleOrganizationUpdate(), { isManager }, loading (+8 more)

### Community 71 - "ZaloConversationThread.vue"
Cohesion: 0.11
Nodes (18): canReply, contextKey, conversationName, draft, emit, history, isComposing, loadThread() (+10 more)

### Community 72 - "ActivityHeader.vue"
Cohesion: 0.14
Nodes (14): callActions, defaultActions, emailBox, getTabIndex(), { makeCall }, openNote(), openTask(), props (+6 more)

### Community 73 - "useDoubleTProducts"
Cohesion: 0.38
Nodes (6): useDoubleTProducts(), fetchProducts(), reloadCategoryAssignments(), reloadTemplates(), setFilters(), handleSaved()

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
Cohesion: 0.11
Nodes (9): collapsedPreference, compactRoutes, contactCenterLinks, forceCompactRail, isSidebarCollapsed, links, narrow, route (+1 more)

### Community 78 - "LeadsListView.vue"
Cohesion: 0.06
Nodes (27): emit, getRowRoute(), openDetail(), props, router, emit, isLikeFilterApplied, list (+19 more)

### Community 79 - "WhatsAppArea.vue"
Cohesion: 0.07
Nodes (25): confirmingDelete, deleteComment(), editContent, editing, emit, isOwner, menuOptions, props (+17 more)

### Community 80 - "CallLogDetailModal.vue"
Cohesion: 0.12
Nodes (16): close(), activeSection, body, callDirectionIcon, customerRoute, duration, linkMessages, panel (+8 more)

### Community 81 - "SmartInsightsReport.vue"
Cohesion: 0.13
Nodes (15): actionFilters, actionStatus, appliedFilters, createFollowUp(), creating, data, error, filters (+7 more)

### Community 82 - "reportDatePreset"
Cohesion: 0.14
Nodes (20): apply(), emit, presets, props, reset(), setPreset(), validationError, formatInputDate() (+12 more)

### Community 83 - "OrdersView.vue"
Cohesion: 0.12
Nodes (15): canCreate, customerLabels, dealLabels, error, hasMore, load(), loadCustomerLabels(), loadDealLabels() (+7 more)

### Community 84 - "ContactModal.vue"
Cohesion: 0.11
Nodes (19): { capture }, createContact(), { document: _contact, triggerOnBeforeCreate }, error, handleContactUpdate(), insertContact, { isManager }, props (+11 more)

### Community 85 - "quotation.js"
Cohesion: 0.19
Nodes (14): totals, availableContacts, matchingDeals, totals, appendCatalogSelections(), contactsForCustomer(), createQuotationItem(), customerFromDeal() (+6 more)

### Community 86 - "call"
Cohesion: 0.13
Nodes (15): canCreate, customerLabels, dealLabels, error, hasMore, load(), loadCustomerLabels(), loadDealLabels() (+7 more)

### Community 87 - "CommentBox.vue"
Cohesion: 0.12
Nodes (12): @tiptap/vue-3@^3.26.0, @tiptap/vue-3, attachments, { capture }, content, editor, emoji, modelValue (+4 more)

### Community 88 - "IconPicker.vue"
Cohesion: 0.12
Nodes (16): gemoji@^8.1.0, gemoji, emoji, emojiGroups, randomInt(), reaction, reactionEmojis, search (+8 more)

### Community 89 - "AssignToBody.vue"
Cohesion: 0.12
Nodes (11): assignees, addAssignees, assignees, assignToMe, {
  capture,
}, eligibleUserNames, error, oldAssignees (+3 more)

### Community 90 - "getParams"
Cohesion: 0.17
Nodes (15): applyFilter(), applyLikeFilter(), applyQuickFilter(), createOrUpdateStandardView(), currentView, fetchAndUpdateKanbanColumns(), getParams(), getViewType() (+7 more)

### Community 91 - "LeadCreateModal.vue"
Cohesion: 0.16
Nodes (15): createLead(), createLeadAnyway(), duplicateCheck, duplicateMatches, emit, error, getEmptyLead(), insertLead (+7 more)

### Community 92 - "router.js"
Cohesion: 0.14
Nodes (12): CallLogDetails(), CompanyDetailView(), ContactDetailView(), DealDetailView(), FrappeLead(), OrderForm(), PriceListsView(), ProductCategoriesView() (+4 more)

### Community 93 - "DataFields.vue"
Cohesion: 0.22
Nodes (8): { document }, emit, instance, { isManager }, props, saveChanges(), showDataFieldsModal, tabs

### Community 94 - "Autocomplete.vue"
Cohesion: 0.14
Nodes (13): attrs, emit, filterOptions(), groups, inputClasses, props, query, search (+5 more)

### Community 95 - "telephony.js"
Cohesion: 0.18
Nodes (7): callEnabled, defaultCallingMedium, integrations, useTelephony(), brand, DEFAULT_SETTINGS, settings

### Community 96 - "formatDate"
Cohesion: 0.34
Nodes (14): timestampCell(), rows, parseRows(), parseRows(), rows, getFormattedCurrency(), getFormattedFloat(), getFormattedPercent() (+6 more)

### Community 97 - "ReportsPage.vue"
Cohesion: 0.15
Nodes (15): activeReportComponent, liveReportKeys, props, report, reportComponents, ReportsPage(), getReportSection(), REPORT_SECTIONS (+7 more)

### Community 98 - "AttachmentItem.vue"
Cohesion: 0.14
Nodes (7): mime@^4.0.1, mime, content, isImage, isSpreadsheet, props, showDialog

### Community 99 - "QuotationOrderReport.vue"
Cohesion: 0.08
Nodes (28): appliedFilters, cell(), comparisonChange(), conversion, data, decimal(), errorMessage, filters (+20 more)

### Community 100 - "vue-router"
Cohesion: 0.12
Nodes (13): callbackRoute(), { $dialog }, { getUser }, openTask(), props, router, emit, isLikeFilterApplied (+5 more)

### Community 101 - "Contacts.vue"
Cohesion: 0.15
Nodes (11): columns, contacts, contactsListView, { getFormattedPercent, getFormattedFloat, getFormattedCurrency }, { getOrganization }, loadMore, showContactModal, triggerResize (+3 more)

### Community 102 - "AttachControl.vue"
Cohesion: 0.15
Nodes (14): attrs, clearAttachment(), containerClasses, emit, filename, iconClasses, isImage, onAfterUpload() (+6 more)

### Community 103 - "KanbanSettings.vue"
Cohesion: 0.15
Nodes (10): allFields, apply(), columnField, columnFields, emit, { getFields }, list, props (+2 more)

### Community 104 - "CallLogAISummary.vue"
Cohesion: 0.16
Nodes (13): canGenerate, generate(), initialLoading, load(), notice, props, recordingMessages, refresh() (+5 more)

### Community 105 - "CustomerJourneyReport.vue"
Cohesion: 0.08
Nodes (28): appliedFilters, cell(), comparisonChange(), data, decimal(), errorMessage, filters, hasResults (+20 more)

### Community 106 - "Link.vue"
Cohesion: 0.19
Nodes (11): attrs, autocomplete, clearValue(), emit, labelClasses, options, props, stripHtml() (+3 more)

### Community 107 - "DataFieldsModal.vue"
Cohesion: 0.18
Nodes (12): { capture }, dirty, _doctype, emit, getParams(), loading, preview, props (+4 more)

### Community 108 - "SidePanelModal.vue"
Cohesion: 0.18
Nodes (12): { capture }, dirty, _doctype, emit, getParams(), loading, preview, props (+4 more)

### Community 109 - "Dashboard.vue"
Cohesion: 0.15
Nodes (9): Bars, cards, data, error, load(), loading, Restricted, router (+1 more)

### Community 110 - "RecordCallHistory.vue"
Cohesion: 0.18
Nodes (10): error, hasMore, load(), loading, props, rows, callOutcomeTheme(), caseStatusTheme (+2 more)

### Community 111 - "KanbanView.vue"
Cohesion: 0.21
Nodes (10): actions(), addColumn(), columns, deletedColumns, emit, kanban, titleField, updateColumn() (+2 more)

### Community 112 - "AssignmentModal.vue"
Cohesion: 0.18
Nodes (9): assignees, { capture }, emit, error, oldAssignees, props, show, updateAssignees() (+1 more)

### Community 113 - "LeadDetailView.vue"
Cohesion: 0.17
Nodes (10): dateValue(), error, InfoField, lead, loading, loadLead(), route, router (+2 more)

### Community 114 - "money"
Cohesion: 0.15
Nodes (12): canCreate, denied, error, hasMore, load(), loading, props, router (+4 more)

### Community 115 - "close"
Cohesion: 0.22
Nodes (11): reset(), getTabOptions(), close(), deleteView(), duplicateView(), editView(), isDefaultView(), pinView() (+3 more)

### Community 116 - "RatingInput.vue"
Cohesion: 0.20
Nodes (7): emit, hoveredStarValue, nStars, onStarClick(), props, savedStarValue, tooltipText

### Community 117 - "Organizations.vue"
Cohesion: 0.18
Nodes (9): columns, { getFormattedPercent, getFormattedFloat, getFormattedCurrency }, loadMore, organizations, organizationsListView, showOrganizationModal, triggerResize, updatedPageCount (+1 more)

### Community 118 - "ZaloRecordChat.vue"
Cohesion: 0.18
Nodes (10): conversations, error, loadConversations(), loading, props, referenceKey, requestContext, restricted (+2 more)

### Community 119 - "ActivityContactCenterReport.vue"
Cohesion: 0.08
Nodes (21): appliedFilters, barHeight(), channelOptions, data, employeeFilterSupported, employees, errorMessage, filters (+13 more)

### Community 120 - "DurationInput.vue"
Cohesion: 0.17
Nodes (14): attrs, commit(), editValue, emit, errorMessage, handleBlur(), handleKeydown(), inputRef (+6 more)

### Community 121 - "AttachmentArea.vue"
Cohesion: 0.22
Nodes (5): deleteAttachment(), { $dialog }, emit, togglePrivate(), convertSize()

### Community 122 - "ContactsListView.vue"
Cohesion: 0.09
Nodes (25): displayValue, handleFocus(), emit, getLabel(), isLikeFilterApplied, list, listBulkActionsRef, pageLengthCount (+17 more)

### Community 123 - "GridRowFieldsModal.vue"
Cohesion: 0.18
Nodes (12): { capture }, dirty, _doctype, emit, getParams(), loading, preview, props (+4 more)

### Community 124 - "SLASection.vue"
Cohesion: 0.38
Nodes (6): { capture }, { communicationStatuses }, data, emit, slaSection, formatTime()

### Community 125 - "doctypeModal.js"
Cohesion: 0.24
Nodes (9): callbacks, defaults, doctype, name, show, showModal(), title, triggerCallback() (+1 more)

### Community 126 - "@vueuse/core"
Cohesion: 0.47
Nodes (5): debouncedFn, emit, filter, props, updateFilter()

### Community 127 - "GroupBy.vue"
Cohesion: 0.25
Nodes (7): emit, groupByOptions, groupByValue, list, options, props, setGroupBy()

### Community 128 - "view.js"
Cohesion: 0.25
Nodes (5): breadcrumbs, breadcrumbs, getView(), { getView: getViewDetails }, standardView()

### Community 129 - "CallLogsListView.vue"
Cohesion: 0.22
Nodes (7): emit, getLabel(), isLikeFilterApplied, list, listBulkActionsRef, pageLengthCount, { user }

### Community 130 - "FilesUploadHandler"
Cohesion: 0.25
Nodes (4): EventListenerOption, FilesUploadHandler, UploadOptions, Window

### Community 131 - "WhatsappTemplateSelectorModal.vue"
Cohesion: 0.22
Nodes (7): emit, filteredTemplates, props, search, searchInput, show, templates

### Community 132 - "ZaloCustomerDetails.vue"
Cohesion: 0.22
Nodes (8): conversationName, details, emit, error, load(), loading, props, recordLinks

### Community 133 - "EditIcon.vue"
Cohesion: 0.25
Nodes (5): { isManager }, props, show, showGridRowFieldsModal, tabs

### Community 134 - "TextEditorControl.vue"
Cohesion: 0.29
Nodes (6): editorClasses, emit, isDirty, latestContent, onBlur(), props

### Community 135 - "useDoubleTCompanies"
Cohesion: 0.46
Nodes (8): useDoubleTCompanies(), fetchCompanies(), fetchCount(), fetchIndustryOptions(), getFilters(), getSearchFilters(), loadMore(), reload()

### Community 136 - "useDoubleTContacts"
Cohesion: 0.43
Nodes (7): useDoubleTContacts(), fetchContacts(), fetchCount(), findMatchingCompanyIds(), loadCompanyNames(), loadMore(), reload()

### Community 138 - "productCatalog.js"
Cohesion: 0.29
Nodes (9): useSellableProducts(), hydrateProductDetails(), loadProductCategories(), loadProducts(), buildProductListRequest(), buildSellableProductListRequest(), groupVariantAttributes(), resolveProductImage() (+1 more)

### Community 139 - "Password.vue"
Cohesion: 0.29
Nodes (4): props, show, showEye, isMac

### Community 140 - "Resizer.vue"
Cohesion: 0.38
Nodes (6): distance(), props, resize(), sidebarResizing, sidebarWidth, startResize()

### Community 142 - "MultiActionButton.vue"
Cohesion: 0.40
Nodes (5): activeButton, parsedOptions, props, showDropdown, DropdownOption()

### Community 147 - "CollapsibleSection.vue"
Cohesion: 0.13
Nodes (10): hide, opened, props, hasTabs, overrides, processedTabs, props, resolvedDocname (+2 more)

### Community 151 - "ref_node_assert"
Cohesion: 0.12
Nodes (13): source, viewsSource, whatsappSource, backendSource, dealsComposableSource, dealsViewSource, pipelineSource, reportsPageSource (+5 more)

### Community 155 - "useActiveTabManager"
Cohesion: 0.60
Nodes (5): useActiveTabManager(), findTabIndex(), getActiveTab(), getActiveTabFromUrl(), getTabIndex()

### Community 157 - "useDoubleTPriceLists"
Cohesion: 0.60
Nodes (4): useDoubleTPriceLists(), fetchPriceLists(), queryFilters(), setFilters()

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `vue` connect `vue` to `ViewControls.vue`, `QuotationForm.vue`, `FilesUploaderArea.vue`, `Tasks.vue`, `Activities.vue`, `LayoutHeader.vue`, `OrderForm.vue`, `DealsView.vue`, `FrappeDeal.vue`, `FilesUploader.vue`, `PriceListsView.vue`, `DoubleTContactInfoPanel.vue`, `FrappeLead.vue`, `ContactDetailView.vue`, `DoubleTContactInfoPanel.vue`, `CallLogDetails.vue`, `Grid.vue`, `Filter.vue`, `SharedNotes.vue`, `DoubleTEntityDetail.vue`, `DoubleTDealInfoPanel.vue`, `Leads.vue`, `TableMultiselectInput.vue`, `ProductsView.vue`, `Deals.vue`, `frappe-index.js`, `EmailEditor.vue`, `ProductModal.vue`, `useDocument`, `DealDetailView.vue`, `frappe-ui`, `DoubleTLeadInfoPanel.vue`, `QuotationEmails.vue`, `TaskModal.vue`, `ProductDetailView.vue`, `WhatsAppBox.vue`, `PipelineAnalyticsReport.vue`, `composables/settings.js`, `Questionnaire.vue`, `SalesPerformanceReport.vue`, `CommunicationArea.vue`, `SidePanelLayout.vue`, `CallLogs.vue`, `call`, `DoubleTDealDataPanel.vue`, `meta.js`, `FieldLayoutEditor.vue`, `AudioPlayer.vue`, `index.js`, `Field.vue`, `getMeta`, `ContactCenterCalls.vue`, `ZaloInbox.vue`, `GridFieldsEditorModal.vue`, `ConvertToDealModal.vue`, `DoubleTConvertToDealModal.vue`, `GeolocationControl.vue`, `users.js`, `ListBulkActions.vue`, `ColumnSettings.vue`, `DoubleTLeadDataPanel.vue`, `package.json`, `MobileNotification.vue`, `LeadModal.vue`, `EditValueModal.vue`, `ProductCategoriesView.vue`, `dependencies`, `MultiSelectEmailInput.vue`, `DealModal.vue`, `OrganizationModal.vue`, `ZaloConversationThread.vue`, `ActivityHeader.vue`, `PriceListModal.vue`, `DeleteLinkedDocModal.vue`, `SortBy.vue`, `AppSidebar.vue`, `LeadsListView.vue`, `WhatsAppArea.vue`, `CallLogDetailModal.vue`, `SmartInsightsReport.vue`, `reportDatePreset`, `OrdersView.vue`, `ContactModal.vue`, `quotation.js`, `call`, `CommentBox.vue`, `IconPicker.vue`, `AssignToBody.vue`, `LeadCreateModal.vue`, `DataFields.vue`, `Autocomplete.vue`, `telephony.js`, `ReportsPage.vue`, `AttachmentItem.vue`, `QuotationOrderReport.vue`, `vue-router`, `Contacts.vue`, `AttachControl.vue`, `KanbanSettings.vue`, `CallLogAISummary.vue`, `CustomerJourneyReport.vue`, `Link.vue`, `DataFieldsModal.vue`, `SidePanelModal.vue`, `Dashboard.vue`, `RecordCallHistory.vue`, `KanbanView.vue`, `AssignmentModal.vue`, `LeadDetailView.vue`, `money`, `RatingInput.vue`, `Organizations.vue`, `ZaloRecordChat.vue`, `ActivityContactCenterReport.vue`, `DurationInput.vue`, `ContactsListView.vue`, `GridRowFieldsModal.vue`, `SLASection.vue`, `doctypeModal.js`, `@vueuse/core`, `GroupBy.vue`, `view.js`, `CallLogsListView.vue`, `WhatsappTemplateSelectorModal.vue`, `ZaloCustomerDetails.vue`, `EditIcon.vue`, `TextEditorControl.vue`, `@vueuse/core`, `productCatalog.js`, `Password.vue`, `Resizer.vue`, `MultiActionButton.vue`, `CollapsibleSection.vue`, `ProductThumbnail.vue`, `useDoubleTPriceLists`?**
  _High betweenness centrality (0.426) - this node is a cross-community bridge._
- **Are the 148 inferred relationships involving `call` (e.g. with `deleteTask()` and `updateTaskStatus()`) actually correct?**
  _`call` has 148 INFERRED edges - model-reasoned connections that need verification._
- **Should `ViewControls.vue` be split into smaller, more focused modules?**
  _Cohesion score 0.042232277526395176 - nodes in this community are weakly interconnected._
- **Why does `frappe-ui` connect `frappe-ui` to `ViewControls.vue`, `QuotationForm.vue`, `FilesUploaderArea.vue`, `Tasks.vue`, `Activities.vue`, `LayoutHeader.vue`, `OrderForm.vue`, `DealsView.vue`, `FrappeDeal.vue`, `FilesUploader.vue`, `PriceListsView.vue`, `DoubleTContactInfoPanel.vue`, `FrappeLead.vue`, `ContactDetailView.vue`, `DoubleTContactInfoPanel.vue`, `CallLogDetails.vue`, `Grid.vue`, `Filter.vue`, `SharedNotes.vue`, `DoubleTEntityDetail.vue`, `DoubleTDealInfoPanel.vue`, `Leads.vue`, `TableMultiselectInput.vue`, `ProductsView.vue`, `Deals.vue`, `frappe-index.js`, `EmailEditor.vue`, `ProductModal.vue`, `useDocument`, `DealDetailView.vue`, `DoubleTLeadInfoPanel.vue`, `QuotationEmails.vue`, `TaskModal.vue`, `ProductDetailView.vue`, `WhatsAppBox.vue`, `PipelineAnalyticsReport.vue`, `composables/settings.js`, `Questionnaire.vue`, `SalesPerformanceReport.vue`, `CommunicationArea.vue`, `SidePanelLayout.vue`, `CallLogs.vue`, `call`, `DoubleTDealDataPanel.vue`, `meta.js`, `FieldLayoutEditor.vue`, `AudioPlayer.vue`, `index.js`, `Field.vue`, `getMeta`, `ContactCenterCalls.vue`, `ZaloInbox.vue`, `GridFieldsEditorModal.vue`, `ConvertToDealModal.vue`, `DoubleTConvertToDealModal.vue`, `GeolocationControl.vue`, `users.js`, `ListBulkActions.vue`, `ColumnSettings.vue`, `DoubleTLeadDataPanel.vue`, `package.json`, `MobileNotification.vue`, `LeadModal.vue`, `EditValueModal.vue`, `ProductCategoriesView.vue`, `dependencies`, `MultiSelectEmailInput.vue`, `vue`, `DealModal.vue`, `OrganizationModal.vue`, `ZaloConversationThread.vue`, `ActivityHeader.vue`, `PriceListModal.vue`, `DeleteLinkedDocModal.vue`, `SortBy.vue`, `AppSidebar.vue`, `LeadsListView.vue`, `WhatsAppArea.vue`, `CallLogDetailModal.vue`, `SmartInsightsReport.vue`, `OrdersView.vue`, `ContactModal.vue`, `call`, `CommentBox.vue`, `IconPicker.vue`, `AssignToBody.vue`, `LeadCreateModal.vue`, `DataFields.vue`, `Autocomplete.vue`, `telephony.js`, `QuotationOrderReport.vue`, `vue-router`, `Contacts.vue`, `AttachControl.vue`, `KanbanSettings.vue`, `CallLogAISummary.vue`, `CustomerJourneyReport.vue`, `Link.vue`, `DataFieldsModal.vue`, `SidePanelModal.vue`, `Dashboard.vue`, `RecordCallHistory.vue`, `KanbanView.vue`, `AssignmentModal.vue`, `LeadDetailView.vue`, `money`, `RatingInput.vue`, `ZaloRecordChat.vue`, `ActivityContactCenterReport.vue`, `DurationInput.vue`, `AttachmentArea.vue`, `ContactsListView.vue`, `GridRowFieldsModal.vue`, `SLASection.vue`, `@vueuse/core`, `GroupBy.vue`, `CallLogsListView.vue`, `WhatsappTemplateSelectorModal.vue`, `ZaloCustomerDetails.vue`, `EditIcon.vue`, `TextEditorControl.vue`, `productCatalog.js`, `Password.vue`, `MultiActionButton.vue`, `CollapsibleSection.vue`, `useDoubleTPriceLists`?**
  _High betweenness centrality (0.327) - this node is a cross-community bridge._
- **Should `QuotationForm.vue` be split into smaller, more focused modules?**
  _Cohesion score 0.03322784810126582 - nodes in this community are weakly interconnected._
- **Why does `vue-router` connect `OrganizationModal.vue` to `ViewControls.vue`, `QuotationForm.vue`, `Tasks.vue`, `Activities.vue`, `LayoutHeader.vue`, `OrderForm.vue`, `DealsView.vue`, `FrappeDeal.vue`, `@vueuse/core`, `DoubleTContactInfoPanel.vue`, `FrappeLead.vue`, `ContactDetailView.vue`, `DoubleTContactInfoPanel.vue`, `CallLogDetails.vue`, `SharedNotes.vue`, `DoubleTEntityDetail.vue`, `DoubleTDealInfoPanel.vue`, `Leads.vue`, `ProductsView.vue`, `Deals.vue`, `DealDetailView.vue`, `DoubleTLeadInfoPanel.vue`, `QuotationEmails.vue`, `TaskModal.vue`, `ProductDetailView.vue`, `PipelineAnalyticsReport.vue`, `composables/settings.js`, `Questionnaire.vue`, `CallLogs.vue`, `AudioPlayer.vue`, `ZaloInbox.vue`, `ConvertToDealModal.vue`, `users.js`, `ListBulkActions.vue`, `package.json`, `LeadModal.vue`, `ProductCategoriesView.vue`, `dependencies`, `DealModal.vue`, `DeleteLinkedDocModal.vue`, `AppSidebar.vue`, `LeadsListView.vue`, `OrdersView.vue`, `ContactModal.vue`, `call`, `router.js`, `vue-router`, `Contacts.vue`, `Dashboard.vue`, `LeadDetailView.vue`, `money`, `ActivityContactCenterReport.vue`, `ContactsListView.vue`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Should `FilesUploaderArea.vue` be split into smaller, more focused modules?**
  _Cohesion score 0.06825396825396825 - nodes in this community are weakly interconnected._