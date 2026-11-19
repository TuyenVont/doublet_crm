<template>
	<div class="flex h-full flex-col overflow-hidden bg-surface-white">
		<LayoutHeader>
			<template #left-header>
				<div class="flex min-w-0 items-center gap-2">
					<Button
						variant="ghost"
						icon="chevron-left"
						@click="router.push({ name: listRoute })"
					/>
					<div class="flex min-w-0 items-center gap-1 text-lg-medium text-ink-gray-9">
						<button
							type="button"
							class="shrink-0 text-ink-gray-6 hover:text-ink-gray-9"
							@click="router.push({ name: listRoute })"
						>
							{{ __(listRoute) }}
						</button>
						<span class="text-ink-gray-4" aria-hidden="true">/</span>
						<span class="max-w-[52vw] truncate sm:max-w-[420px]">
							{{ isNew ? __("New {0}", [kind]) : title }}
						</span>
					</div>
				</div>
			</template>

			<template #right-header>
				<Button
					v-if="!isNew"
					:tooltip="__('Refresh')"
					icon="refresh-cw"
					:loading="loading"
					@click="load"
				/>
			</template>
		</LayoutHeader>

		<div
			v-if="loading && !doc && !isNew"
			class="flex flex-1 items-center justify-center text-sm text-ink-gray-5"
		>
			{{ __("Loading {0}...", [kind]) }}
		</div>

		<div
			v-else-if="error && !doc && !isNew"
			class="flex flex-1 flex-col items-center justify-center gap-3 px-5 text-center"
		>
			<div class="text-lg font-medium text-ink-gray-9">
				{{ __("Unable to load {0}", [kind]) }}
			</div>
			<p class="text-sm text-red-600">{{ error }}</p>
			<Button :label="__('Retry')" @click="load" />
		</div>

		<div v-else-if="isNew" class="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
			<section
				class="mx-auto max-w-4xl rounded-lg border border-outline-gray-2 bg-surface-white p-4 sm:p-6"
			>
				<div class="mb-5">
					<h1 class="text-xl font-semibold text-ink-gray-9">
						{{ __("New {0}", [kind]) }}
					</h1>
					<p class="mt-1 text-sm text-ink-gray-5">
						{{ __("Enter the {0} information below.", [kind.toLowerCase()]) }}
					</p>
				</div>

				<div
					v-if="error"
					role="alert"
					class="mb-4 rounded border border-red-300 p-3 text-sm text-red-600"
				>
					{{ error }}
				</div>

				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					<EntityField
						v-for="field in fields"
						:key="field.key"
						:field="field"
						:form="form"
						:editing="true"
						@link-change="setLinkValue"
					/>
				</div>

				<div class="mt-6 flex justify-end gap-2 border-t border-outline-gray-2 pt-4">
					<Button variant="subtle" :label="__('Cancel')" @click="cancel" />
					<Button
						v-if="canWrite"
						variant="solid"
						:label="__('Create')"
						:loading="saving"
						@click="save"
					/>
				</div>
			</section>
		</div>

		<div v-else-if="doc" class="min-h-0 flex-1 overflow-y-auto p-3 sm:p-5">
			<div
				v-if="error"
				role="alert"
				class="mx-auto mb-4 max-w-[1440px] rounded border border-red-300 p-3 text-sm text-red-600"
			>
				{{ error }}
			</div>

			<div
				class="mx-auto grid w-full max-w-[1440px] grid-cols-1 items-start gap-4 lg:grid-cols-[minmax(280px,340px)_minmax(0,1fr)]"
			>
				<aside
					class="min-w-0 overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white"
				>
					<div
						class="flex flex-col items-center border-b border-outline-gray-2 px-5 py-6 text-center"
					>
						<div
							class="flex size-16 items-center justify-center rounded-full bg-surface-gray-2 text-2xl font-semibold text-ink-gray-7"
							aria-hidden="true"
						>
							{{ recordInitial }}
						</div>
						<h1
							class="mt-3 max-w-full break-words text-xl font-semibold text-ink-gray-9"
						>
							{{ title }}
						</h1>
						<p class="mt-1 text-xs text-ink-gray-5">{{ recordName }}</p>
					</div>

					<div class="p-5">
						<div class="mb-4 flex items-center justify-between gap-3">
							<h2 class="text-base font-semibold text-ink-gray-9">
								{{ __("{0} Information", [kind]) }}
							</h2>
							<span v-if="editing" class="text-xs text-ink-gray-5">{{
								__("Editing")
							}}</span>
						</div>

						<div class="space-y-4">
							<EntityField
								v-for="field in profileFields"
								:key="field.key"
								:field="field"
								:form="form"
								:doc="doc"
								:editing="editing"
								@link-change="setLinkValue"
							/>
						</div>

						<div
							class="mt-6 flex flex-wrap justify-end gap-2 border-t border-outline-gray-2 pt-4"
						>
							<template v-if="editing">
								<Button variant="subtle" :label="__('Cancel')" @click="cancel" />
								<Button
									variant="solid"
									:label="__('Save')"
									:loading="saving"
									@click="save"
								/>
							</template>
							<template v-else>
								<Button
									v-if="canDelete"
									variant="subtle"
									icon="trash-2"
									:label="__('Delete')"
									@click="remove"
								/>
								<Button
									v-if="canWrite"
									variant="solid"
									iconLeft="edit-3"
									:label="__('Edit')"
									@click="editing = true"
								/>
							</template>
						</div>
					</div>
				</aside>

				<section
					class="min-w-0 overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white"
				>
					<Tabs
						v-model="relatedTabIndex"
						:tabs="relatedTabs"
						class="flex min-h-[34rem] flex-col overflow-hidden [&_[role='tab']]:shrink-0 [&_[role='tab']]:px-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-6 [&_[role='tablist']]:overflow-x-auto [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-1 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:min-h-0 [&_[role='tabpanel']:not([hidden])]:flex-1"
					>
						<template #tab-panel="{ tab }">
							<template v-if="tab.name === activeRelatedTab">
								<div
									v-if="activeRelatedGroup"
									class="min-w-0 flex-1 overflow-y-auto p-4 sm:p-5"
								>
									<div class="mb-4 flex items-center justify-between gap-3">
										<h2 class="text-lg font-semibold text-ink-gray-9">
											{{ __(activeRelatedGroup.label) }}
										</h2>
										<span
											class="rounded-full bg-surface-gray-2 px-2.5 py-1 text-xs font-medium text-ink-gray-6"
										>
											{{ activeRelatedGroup.rows.length }}
										</span>
									</div>

									<div
										v-if="activeRelatedGroup.rows.length"
										class="overflow-x-auto rounded border border-outline-gray-2"
									>
										<table class="w-full min-w-[640px] text-sm">
											<thead
												class="bg-surface-gray-1 text-left text-ink-gray-6"
											>
												<tr>
													<th
														v-for="column in activeRelatedGroup.columns"
														:key="column.key"
														class="px-4 py-3 font-medium"
													>
														{{ __(column.label) }}
													</th>
												</tr>
											</thead>
											<tbody>
												<tr
													v-for="entry in activeRelatedGroup.rows"
													:key="entry.name"
													class="border-t border-outline-gray-2"
												>
													<td
														v-for="(
															column, columnIndex
														) in activeRelatedGroup.columns"
														:key="column.key"
														class="max-w-[280px] px-4 py-3 text-ink-gray-7"
													>
														<RouterLink
															v-if="columnIndex === 0"
															:to="
																relatedRoute(
																	activeRelatedGroup,
																	entry,
																)
															"
															class="block truncate font-medium text-ink-gray-9 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500"
														>
															{{ entry[column.key] || "—" }}
														</RouterLink>
														<span
															v-else
															class="block truncate"
															:title="entry[column.key] || ''"
														>
															{{ entry[column.key] || "—" }}
														</span>
													</td>
												</tr>
											</tbody>
										</table>
									</div>

									<div
										v-else
										class="flex min-h-64 items-center justify-center rounded border border-dashed border-outline-gray-2 px-5 text-center text-sm text-ink-gray-5"
									>
										{{
											__("No {0} found.", [
												activeRelatedGroup.label.toLowerCase(),
											])
										}}
									</div>
								</div>

								<Activities
									v-else-if="activeRelatedTab === 'Tasks'"
									:doctype="doctype"
									:docname="recordName"
									:tabs="taskTabs"
								/>
								<SharedNotes
									v-else-if="activeRelatedTab === 'Notes'"
									:reference-doctype="doctype"
									:reference-name="recordName"
								/>
								<ZaloRecordChat
									v-else-if="activeRelatedTab === 'Zalo OA'"
									:reference-doctype="doctype"
									:reference-name="recordName"
								/>
							</template>
						</template>
					</Tabs>
				</section>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, defineComponent, h, reactive, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { call, Button, Tabs } from "frappe-ui";

import LayoutHeader from "@/components/LayoutHeader.vue";
import Activities from "@/components/Activities/Activities.vue";
import SharedNotes from "@/components/Notes/SharedNotes.vue";
import ZaloRecordChat from "@/components/Zalo/ZaloRecordChat.vue";
import TaskIcon from "@/components/Icons/TaskIcon.vue";
import NoteIcon from "@/components/Icons/NoteIcon.vue";
import WhatsAppIcon from "@/components/Icons/WhatsAppIcon.vue";
import Link from "@/components/Controls/Link.vue";

const props = defineProps({ kind: { type: String, required: true } });
const router = useRouter();
const route = useRoute();

const isContact = computed(() => props.kind === "Contact");
const doctype = computed(() => `DoubleT ${props.kind}`);
const listRoute = computed(() => (isContact.value ? "Contacts" : "Companies"));
const titleField = computed(() => (isContact.value ? "first_name" : "company_name"));
const recordName = computed(() => route.params[isContact.value ? "contactId" : "companyId"]);
const isNew = computed(() => !recordName.value);

const contactFields = [
	{ key: "first_name", label: "First Name", required: true },
	{ key: "last_name", label: "Last Name" },
	{ key: "phone", label: "Phone" },
	{ key: "email", label: "Email", type: "email" },
	{ key: "birthday", label: "Birthday", type: "date" },
	{ key: "address", label: "Address", multiline: true },
	{ key: "source", label: "Source", link: "DoubleT Lead Source" },
	{ key: "contact_owner", label: "Contact Owner", link: "User" },
	{ key: "company", label: "Company", link: "DoubleT Company" },
	{ key: "price_list", label: "Price List", link: "DoubleT Price List" },
	{ key: "job_title", label: "Job Title" },
	{ key: "notes", label: "Notes", multiline: true },
];

const companyFields = [
	{ key: "company_name", label: "Company Name", required: true },
	{ key: "tax_id", label: "Tax ID" },
	{ key: "phone", label: "Phone" },
	{ key: "email", label: "Email", type: "email" },
	{ key: "website", label: "Website", type: "url" },
	{ key: "address", label: "Address", multiline: true },
	{ key: "industry", label: "Industry" },
	{ key: "size", label: "Size" },
	{ key: "company_owner", label: "Company Owner", link: "User" },
	{ key: "price_list", label: "Price List", link: "DoubleT Price List" },
];

const fields = computed(() => (isContact.value ? contactFields : companyFields));
const profileFields = computed(() =>
	fields.value.filter((field) => field.key !== titleField.value),
);

const form = reactive({});
const doc = ref(null);
const related = ref([]);
const loading = ref(false);
const saving = ref(false);
const editing = ref(false);
const error = ref("");
const canWrite = ref(false);
const canDelete = ref(false);

const title = computed(() => {
	if (!doc.value) return __(props.kind);
	if (isContact.value) {
		return (
			[doc.value.first_name, doc.value.last_name].filter(Boolean).join(" ") || doc.value.name
		);
	}
	return doc.value[titleField.value] || doc.value.name;
});
const recordInitial = computed(
	() => title.value?.trim()?.charAt(0)?.toUpperCase() || props.kind.charAt(0),
);

const taskTabs = [{ name: "Tasks", label: __("Tasks"), icon: TaskIcon }];
const activityTabs = [
	{ name: "Tasks", label: __("Tasks"), icon: TaskIcon },
	{ name: "Notes", label: __("Notes"), icon: NoteIcon },
	{ name: "Zalo OA", label: __("Zalo OA"), icon: WhatsAppIcon },
];
const relatedTabIndex = ref(0);
const relatedTabs = computed(() => [
	...related.value.map((group) => ({
		name: group.name,
		label: `${__(group.label)} (${group.rows.length})`,
	})),
	...activityTabs,
]);
const activeRelatedTab = computed(
	() => relatedTabs.value[relatedTabIndex.value]?.name || related.value[0]?.name || "Tasks",
);
const activeRelatedGroup = computed(
	() => related.value.find((group) => group.name === activeRelatedTab.value) || null,
);

function apiError(exception) {
	return exception?.messages?.join?.("; ") || exception?.message || __("Request failed");
}

function fillForm(data = {}) {
	for (const field of fields.value) {
		form[field.key] = data[field.key] || "";
	}
}

function setLinkValue(field, value) {
	form[field.key] = value || "";
}

function normalizedWebsite(value) {
	if (!value) return "";
	return /^https?:\/\//i.test(value) ? value : `https://${value}`;
}

const EntityField = defineComponent({
	name: "EntityField",
	props: {
		field: { type: Object, required: true },
		form: { type: Object, required: true },
		doc: { type: Object, default: null },
		editing: { type: Boolean, default: false },
	},
	emits: ["link-change"],
	setup(fieldProps, { emit }) {
		return () => {
			const field = fieldProps.field;
			const label = h("label", { class: "mb-1 block text-xs font-medium text-ink-gray-5" }, [
				__(field.label),
				field.required ? h("span", { class: "ml-0.5 text-red-500" }, "*") : null,
			]);

			if (fieldProps.editing) {
				let control;
				if (field.multiline) {
					control = h("textarea", {
						value: fieldProps.form[field.key],
						rows: 3,
						class: "w-full rounded border border-outline-gray-2 bg-surface-white p-2 text-sm",
						onInput: (event) => {
							fieldProps.form[field.key] = event.target.value;
						},
					});
				} else if (field.link) {
					control = h(Link, {
						value: fieldProps.form[field.key],
						doctype: field.link,
						placeholder: __("Select {0}", [field.label]),
						onChange: (value) => emit("link-change", field, value),
					});
				} else {
					control = h("input", {
						value: fieldProps.form[field.key],
						type: field.type || "text",
						class: "w-full rounded border border-outline-gray-2 bg-surface-white p-2 text-sm",
						onInput: (event) => {
							fieldProps.form[field.key] = event.target.value;
						},
					});
				}

				return h("div", { class: "min-w-0" }, [label, control]);
			}

			const value = fieldProps.doc?.[field.key];
			let content;
			if (value && field.type === "email") {
				content = h(
					"a",
					{ class: "break-all text-blue-600 hover:underline", href: `mailto:${value}` },
					value,
				);
			} else if (value && field.type === "url") {
				content = h(
					"a",
					{
						class: "break-all text-blue-600 hover:underline",
						href: normalizedWebsite(value),
						target: "_blank",
						rel: "noopener noreferrer",
					},
					value,
				);
			} else {
				content = h(
					"p",
					{
						class: field.multiline
							? "whitespace-pre-line break-words text-ink-gray-8"
							: "break-words text-ink-gray-8",
					},
					value || "—",
				);
			}

			return h("div", { class: "min-w-0" }, [label, content]);
		};
	},
});

async function getRelated(definition) {
	try {
		const result = await call("frappe.client.get_list", {
			doctype: definition.doctype,
			filters: definition.filters,
			fields: definition.fields,
			order_by: "modified desc",
			limit_page_length: 100,
		});
		return {
			...definition,
			rows: (result || []).map(definition.mapRow),
		};
	} catch (exception) {
		console.warn(`Failed to load ${definition.label}`, exception);
		return { ...definition, rows: [] };
	}
}

async function loadRelated() {
	const name = recordName.value;
	if (!name) return;

	const definitions = isContact.value
		? [
				{
					name: "Deals",
					label: "Deals",
					doctype: "DoubleT Deal",
					filters: { contact: name },
					fields: ["name", "deal_title", "stage", "expected_close_date"],
					route: "DealDetail",
					param: "dealId",
					columns: [
						{ key: "label", label: "Deal" },
						{ key: "stage", label: "Stage" },
						{ key: "expected_close_date", label: "Expected Close Date" },
					],
					mapRow: (row) => ({ ...row, label: row.deal_title || row.name }),
				},
				{
					name: "Converted Leads",
					label: "Converted Leads",
					doctype: "DoubleT Lead",
					filters: { converted_contact: name },
					fields: ["name", "first_name", "last_name", "status", "source"],
					route: "LeadDetail",
					param: "leadId",
					columns: [
						{ key: "label", label: "Lead" },
						{ key: "status", label: "Status" },
						{ key: "source", label: "Source" },
					],
					mapRow: (row) => ({
						...row,
						label:
							[row.first_name, row.last_name].filter(Boolean).join(" ") || row.name,
					}),
				},
			]
		: [
				{
					name: "Deals",
					label: "Deals",
					doctype: "DoubleT Deal",
					filters: { company: name },
					fields: ["name", "deal_title", "stage", "expected_close_date"],
					route: "DealDetail",
					param: "dealId",
					columns: [
						{ key: "label", label: "Deal" },
						{ key: "stage", label: "Stage" },
						{ key: "expected_close_date", label: "Expected Close Date" },
					],
					mapRow: (row) => ({ ...row, label: row.deal_title || row.name }),
				},
				{
					name: "Contacts",
					label: "Contacts",
					doctype: "DoubleT Contact",
					filters: { company: name },
					fields: ["name", "first_name", "last_name", "email", "phone"],
					route: "ContactDetail",
					param: "contactId",
					columns: [
						{ key: "label", label: "Contact" },
						{ key: "email", label: "Email" },
						{ key: "phone", label: "Phone" },
					],
					mapRow: (row) => ({
						...row,
						label:
							[row.first_name, row.last_name].filter(Boolean).join(" ") || row.name,
					}),
				},
				{
					name: "Converted Leads",
					label: "Converted Leads",
					doctype: "DoubleT Lead",
					filters: { converted_company: name },
					fields: ["name", "first_name", "last_name", "status", "source"],
					route: "LeadDetail",
					param: "leadId",
					columns: [
						{ key: "label", label: "Lead" },
						{ key: "status", label: "Status" },
						{ key: "source", label: "Source" },
					],
					mapRow: (row) => ({
						...row,
						label:
							[row.first_name, row.last_name].filter(Boolean).join(" ") || row.name,
					}),
				},
			];

	related.value = await Promise.all(definitions.map(getRelated));
	relatedTabIndex.value = 0;
}

function relatedRoute(group, entry) {
	return { name: group.route, params: { [group.param]: entry.name } };
}

async function load() {
	error.value = "";
	loading.value = true;
	editing.value = isNew.value;
	doc.value = null;
	related.value = [];
	canWrite.value = false;
	canDelete.value = false;

	try {
		if (isNew.value) {
			const permission = await call("frappe.client.has_permission", {
				doctype: doctype.value,
				docname: "",
				perm_type: "create",
			});
			canWrite.value = Boolean(permission?.has_permission);
		} else {
			const [document, permissions] = await Promise.all([
				call("frappe.client.get", { doctype: doctype.value, name: recordName.value }),
				call("frappe.client.get_doc_permissions", {
					doctype: doctype.value,
					docname: recordName.value,
				}),
			]);
			doc.value = document;
			canWrite.value = Boolean(permissions?.permissions?.write);
			canDelete.value = Boolean(permissions?.permissions?.delete);
			await loadRelated();
		}
		fillForm(doc.value || {});
	} catch (exception) {
		error.value = apiError(exception);
	} finally {
		loading.value = false;
	}
}

function cancel() {
	if (isNew.value) {
		router.push({ name: listRoute.value });
		return;
	}
	fillForm(doc.value || {});
	editing.value = false;
	error.value = "";
}

async function save() {
	error.value = "";
	const required = fields.value.find(
		(field) => field.required && !String(form[field.key] || "").trim(),
	);
	if (required) {
		error.value = __("{0} is required", [required.label]);
		return;
	}

	saving.value = true;
	try {
		const values = Object.fromEntries(
			fields.value.map((field) => [field.key, form[field.key] || null]),
		);
		if (isNew.value) {
			const result = await call("frappe.client.insert", {
				doc: { doctype: doctype.value, ...values },
			});
			await router.replace({
				name: isContact.value ? "ContactDetail" : "CompanyDetail",
				params: { [isContact.value ? "contactId" : "companyId"]: result.name },
			});
		} else {
			await call("frappe.client.set_value", {
				doctype: doctype.value,
				name: recordName.value,
				fieldname: values,
			});
		}
		editing.value = false;
		await load();
	} catch (exception) {
		error.value = apiError(exception);
	} finally {
		saving.value = false;
	}
}

async function remove() {
	if (!window.confirm(__("Delete this {0}? This cannot be undone.", [props.kind.toLowerCase()])))
		return;
	error.value = "";
	try {
		await call("frappe.client.delete", { doctype: doctype.value, name: recordName.value });
		await router.push({ name: listRoute.value });
	} catch (exception) {
		error.value = apiError(exception);
	}
}

watch([recordName, () => props.kind], load, { immediate: true });
</script>
