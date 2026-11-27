import hashlib
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, now_datetime, nowdate

from doublet_crm.pricing import readable_doc as pricing_readable_doc, resolve_product_price


EXPIRABLE_STATUSES = {"Draft", "Sent"}
MANAGER_APPROVAL_ROLES = {"Sales Manager", "System Manager"}
APPROVAL_AUDIT_FIELDS = (
	"approval_status",
	"approval_requested_by",
	"approval_requested_on",
	"approved_by",
	"approved_on",
	"rejection_reason",
	"approval_snapshot_hash",
)


def decimal_value(value, label):
	try:
		result = Decimal(str(value))
		if not result.is_finite():
			raise InvalidOperation
		return result
	except (InvalidOperation, TypeError, ValueError):
		frappe.throw(_("{0} must be a finite number.").format(label))


def usd(value):
	return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def readable_doc(doctype, name):
	return pricing_readable_doc(doctype, name)


def is_quotation_expired(status, valid_until, today=None):
	if status not in EXPIRABLE_STATUSES or not valid_until:
		return False
	reference_date = getdate(today) if today else getdate(nowdate())
	return getdate(valid_until) < reference_date


def _discount_approval_settings():
	settings = frappe.get_doc("DoubleT Pricing Settings")
	threshold_pct = Decimal(str(settings.get("discount_approval_threshold_percent") or 0))
	threshold_amt = Decimal(str(settings.get("discount_approval_threshold_amount") or 0))
	return {
		"enabled": bool(cint(settings.get("enable_discount_approval"))),
		"threshold_percent": max(Decimal(0), threshold_pct),
		"threshold_amount": max(Decimal(0), threshold_amt),
	}


def evaluate_discount_approval_required(items, subtotal, total_discount, settings):
	if not settings or not settings.get("enabled"):
		return False
	threshold_pct = Decimal(str(settings.get("threshold_percent") or 0))
	threshold_amt = Decimal(str(settings.get("threshold_amount") or 0))
	if threshold_pct <= 0 and threshold_amt <= 0:
		return False

	total_disc = Decimal(str(total_discount or 0))
	if threshold_amt > 0 and total_disc > threshold_amt:
		return True

	if threshold_pct > 0:
		sub = Decimal(str(subtotal or 0))
		if sub > 0 and (total_disc * Decimal(100) / sub) > threshold_pct:
			return True
		for row in items or []:
			qty = Decimal(str(row.get("quantity") if isinstance(row, dict) else row.quantity or 0))
			price = Decimal(str(row.get("unit_price") if isinstance(row, dict) else row.unit_price or 0))
			gross = usd(qty * price)
			dtype = (row.get("discount_type") if isinstance(row, dict) else row.discount_type) or "Percentage"
			if dtype == "Percentage":
				pct = Decimal(str((row.get("discount_percent") if isinstance(row, dict) else row.discount_percent) or 0))
				if pct > threshold_pct:
					return True
			elif gross > 0:
				amt = Decimal(str((row.get("discount_amount") if isinstance(row, dict) else row.discount_amount) or 0))
				if (amt * Decimal(100) / gross) > threshold_pct:
					return True

	return False


def compute_financial_snapshot_hash(doc):
	def norm(val):
		return str(Decimal(str(val or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

	payload = {
		"subtotal": norm(doc.subtotal),
		"total_discount": norm(doc.total_discount),
		"grand_total": norm(doc.grand_total),
		"items": [
			[
				row.product or "",
				str(Decimal(str(row.quantity or 0)).normalize()),
				norm(row.unit_price),
				row.discount_type or "Percentage",
				str(Decimal(str(row.discount_percent or 0)).normalize()),
				norm(row.discount_amount),
				norm(row.line_total),
			]
			for row in (doc.items or [])
		],
	}
	encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
	return hashlib.sha256(encoded).hexdigest()


class DoubleTQuotation(Document):
	def validate(self):
		previous = self.get_doc_before_save()
		self.validate_lifecycle(previous)
		self.validate_customer()
		if getdate(self.valid_until) < getdate(self.quotation_date):
			frappe.throw(_("Valid Until cannot be before Quotation Date."))
		if previous and previous.status != "Draft":
			self.preserve_historical_totals(previous)
			self.preserve_approval_fields(previous)
			return
		self.validate_items_and_calculate(previous)
		self.sync_discount_approval_state(previous)
		if previous and previous.status == "Draft" and self.status == "Sent":
			ensure_quotation_can_send(self)

	def preserve_historical_totals(self, previous):
		self.subtotal = previous.subtotal
		self.total_discount = previous.total_discount
		self.grand_total = previous.grand_total

	def preserve_approval_fields(self, previous):
		for field in APPROVAL_AUDIT_FIELDS:
			self.set(field, previous.get(field))

	def clear_approval_metadata(self):
		self.approval_requested_by = None
		self.approval_requested_on = None
		self.approved_by = None
		self.approved_on = None
		self.rejection_reason = ""
		self.approval_snapshot_hash = ""

	def sync_discount_approval_state(self, previous):
		current_hash = compute_financial_snapshot_hash(self)
		if self.flags.get("from_approval_action"):
			self.approval_snapshot_hash = current_hash
			return

		if previous:
			self.preserve_approval_fields(previous)
		else:
			self.approval_status = "Not Required"
			self.clear_approval_metadata()

		requires_approval = evaluate_discount_approval_required(
			self.items, self.subtotal, self.total_discount, _discount_approval_settings()
		)
		snapshot_changed = (not previous) or ((previous.get("approval_snapshot_hash") or "") != current_hash)

		if requires_approval:
			if (
				self.approval_status == "Approved"
				and not snapshot_changed
				and self.approved_by
				and self.approval_snapshot_hash == current_hash
			):
				return
			if self.approval_status in ("Pending", "Rejected") and not snapshot_changed:
				return
			self.approval_status = "Required"
			self.clear_approval_metadata()
			return

		if snapshot_changed or self.approval_status in ("Required", "Rejected", ""):
			self.approval_status = "Not Required"
			self.clear_approval_metadata()

	def validate_lifecycle(self, previous):
		allowed = {"Draft": {"Draft", "Sent"}, "Sent": {"Sent", "Accepted", "Rejected"},
			"Accepted": {"Accepted"}, "Rejected": {"Rejected"}}
		if not previous:
			if self.status != "Draft":
				frappe.throw(_("A new quotation must be Draft."))
			return
		if self.status not in allowed.get(previous.status, set()):
			frappe.throw(_("Invalid quotation status transition."))
		if previous.status != "Draft":
			fields = ("deal", "customer_type", "contact", "company", "price_list", "quotation_template", "quotation_date", "valid_until", "terms", "notes")
			if any(self.has_value_changed(field) for field in fields):
				frappe.throw(_("Quotation fields are locked after Draft."))
			old_items = [self.item_snapshot(row) for row in previous.items]
			new_items = [self.item_snapshot(row) for row in self.items]
			if old_items != new_items:
				frappe.throw(_("Quotation items are locked after Draft."))

	@staticmethod
	def item_snapshot(row):
		def number(value):
			return Decimal(str(value or 0)).normalize()

		return (
			row.name,
			row.product,
			row.product_name,
			row.sku,
			number(row.unit_price),
			number(row.quantity),
			row.discount_type or "Percentage",
			number(row.discount_percent),
			number(row.discount_amount),
			number(row.line_total),
		)

	def validate_customer(self):
		if self.customer_type not in ("PERSONAL", "COMPANY"):
			frappe.throw(_("Select PERSONAL or COMPANY."))
		if self.customer_type == "PERSONAL" and (not self.contact or self.company):
			frappe.throw(_("A PERSONAL quotation requires a Contact and no Company."))
		if self.customer_type == "COMPANY" and not self.company:
			frappe.throw(_("A COMPANY quotation requires a Company."))
		contact = readable_doc("DoubleT Contact", self.contact) if self.contact else None
		if self.company:
			readable_doc("DoubleT Company", self.company)
		if self.customer_type == "COMPANY" and contact and contact.company != self.company:
			frappe.throw(_("Contact must belong to the selected Company."))
		if self.deal:
			deal = readable_doc("DoubleT Deal", self.deal)
			customer_levels = {deal.meta.get_field(field).permlevel for field in ("contact", "company")}
			if frappe.session.user != "Administrator" and not customer_levels.issubset(set(deal.meta.get_permlevel_access("read"))):
				frappe.throw(_("You cannot read the Deal customer fields."), frappe.PermissionError)
			if (deal.deal_type, deal.contact or None, deal.company or None) != (self.customer_type, self.contact or None, self.company or None):
				frappe.throw(_("Quotation customer must match the Deal customer."))

	def validate_items_and_calculate(self, previous):
		if not self.items:
			frappe.throw(_("At least one item is required."))
		old_items = {row.name: row for row in previous.items} if previous else {}
		subtotal = Decimal(0)
		total_discount = Decimal(0)
		for row in self.items:
			old = old_items.get(row.name)
			if old and old.product != row.product:
				frappe.throw(_("Remove and add an item to change its Product."))
			product = readable_doc("DoubleT Product", row.product)
			if not old:
				resolution = resolve_product_price(
					product,
					self.customer_type,
					contact=self.contact,
					company=self.company,
					price_list=self.price_list,
				)
				row.product_name, row.sku = product.product_name, product.sku
				if row.unit_price is None or row.unit_price == "":
					row.unit_price = resolution["price"]
			else:
				row.product_name, row.sku = old.product_name, old.sku
			quantity = decimal_value(row.quantity, _("Quantity"))
			price = decimal_value(row.unit_price, _("Unit Price"))
			discount_type = row.discount_type or "Percentage"
			discount_percent = decimal_value(row.discount_percent or 0, _("Discount"))
			discount_amount = decimal_value(row.discount_amount or 0, _("Discount Amount"))
			if quantity <= 0 or price < 0 or not 0 <= discount_percent <= 100:
				frappe.throw(_("Quantity must be positive, price nonnegative and discount between 0 and 100."))
			gross = usd(quantity * price)
			if discount_type == "Percentage":
				line_discount = usd(gross * discount_percent / 100)
				row.discount_type = "Percentage"
				row.discount_amount = line_discount
			elif discount_type == "Amount":
				if discount_percent:
					frappe.throw(_("Amount discounts cannot also have a discount percentage."))
				if not 0 <= discount_amount <= gross:
					frappe.throw(_("Discount Amount must be between zero and the gross line total."))
				line_discount = usd(discount_amount)
				row.discount_type = "Amount"
				row.discount_percent = 0
				row.discount_amount = line_discount
			else:
				frappe.throw(_("Discount Type must be Percentage or Amount."))
			row.line_total = usd(gross - line_discount)
			subtotal += gross
			total_discount += line_discount
		self.subtotal = usd(subtotal)
		self.total_discount = usd(total_discount)
		self.grand_total = usd(subtotal - total_discount)

	def on_trash(self):
		if self.status != "Draft":
			frappe.throw(_("Only Draft quotations can be deleted."))


def ensure_quotation_can_send(quotation):
	requires_approval = evaluate_discount_approval_required(
		quotation.items,
		quotation.subtotal,
		quotation.total_discount,
		_discount_approval_settings(),
	)
	if not requires_approval:
		return

	current_hash = compute_financial_snapshot_hash(quotation)
	if (
		quotation.approval_status != "Approved"
		or not quotation.approved_by
		or quotation.approval_snapshot_hash != current_hash
	):
		frappe.throw(
			_("This quotation requires discount approval before it can be sent."),
			frappe.ValidationError,
		)


@frappe.whitelist()
def get_site_today():
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required."), frappe.PermissionError)
	return {"today": str(getdate(nowdate()))}


def _check_approval_doc(name, modified=None):
	if not isinstance(name, str) or not name.strip():
		frappe.throw(_("Quotation is required."), frappe.ValidationError)
	# Serialize approval actions with each other and with send/conversion paths.
	doc = frappe.get_doc("DoubleT Quotation", name.strip(), for_update=True)
	doc.check_permission("write")
	if modified is not None and str(doc.modified) != str(modified):
		frappe.throw(_("This quotation was changed by another user. Reload the latest version first."), frappe.TimestampMismatchError)
	if doc.status != "Draft":
		frappe.throw(_("Discount approval actions are only allowed on Draft quotations."), frappe.ValidationError)
	return doc


def _check_manager_approval_permission(doc):
	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(MANAGER_APPROVAL_ROLES):
		frappe.throw(_("Only a Sales Manager or System Manager can approve or reject discount requests."), frappe.PermissionError)
	requester = doc.approval_requested_by or doc.owner
	if frappe.session.user == requester:
		frappe.throw(_("You cannot approve or reject your own discount approval request."), frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def request_discount_approval(name: str, modified=None):
	doc = _check_approval_doc(name, modified)
	if not evaluate_discount_approval_required(
		doc.items, doc.subtotal, doc.total_discount, _discount_approval_settings()
	):
		frappe.throw(_("Discount is within the configured threshold; approval is not required."), frappe.ValidationError)
	if doc.approval_status == "Pending":
		frappe.throw(_("Discount approval has already been requested."), frappe.ValidationError)
	if doc.approval_status == "Approved" and doc.approval_snapshot_hash == compute_financial_snapshot_hash(doc):
		frappe.throw(_("Discount approval has already been granted for this quotation."), frappe.ValidationError)

	doc.approval_status = "Pending"
	doc.approval_requested_by = frappe.session.user
	doc.approval_requested_on = now_datetime()
	doc.approved_by = None
	doc.approved_on = None
	doc.rejection_reason = ""
	doc.flags.from_approval_action = True
	doc.save()
	return doc.as_dict()


@frappe.whitelist(methods=["POST"])
def approve_discount(name: str, modified=None):
	doc = _check_approval_doc(name, modified)
	_check_manager_approval_permission(doc)
	if doc.approval_status != "Pending":
		frappe.throw(_("Only Pending discount approval requests can be approved."), frappe.ValidationError)

	doc.approval_status = "Approved"
	doc.approved_by = frappe.session.user
	doc.approved_on = now_datetime()
	doc.rejection_reason = ""
	doc.flags.from_approval_action = True
	doc.save()
	return doc.as_dict()


@frappe.whitelist(methods=["POST"])
def reject_discount(name: str, reason: str, modified=None):
	doc = _check_approval_doc(name, modified)
	_check_manager_approval_permission(doc)
	if doc.approval_status != "Pending":
		frappe.throw(_("Only Pending discount approval requests can be rejected."), frappe.ValidationError)
	cleaned_reason = (reason or "").strip()
	if not cleaned_reason:
		frappe.throw(_("A rejection reason is required."), frappe.ValidationError)

	doc.approval_status = "Rejected"
	doc.approved_by = frappe.session.user
	doc.approved_on = now_datetime()
	doc.rejection_reason = cleaned_reason
	doc.flags.from_approval_action = True
	doc.save()
	return doc.as_dict()


@frappe.whitelist()
def get_discount_approval_settings():
	settings = frappe.get_doc("DoubleT Pricing Settings")
	settings.check_permission("read")
	roles = set(frappe.get_roles(frappe.session.user))
	can_manage = bool(roles.intersection(MANAGER_APPROVAL_ROLES))
	return {
		"enable_discount_approval": cint(settings.get("enable_discount_approval")),
		"discount_approval_threshold_percent": float(settings.get("discount_approval_threshold_percent") or 0),
		"discount_approval_threshold_amount": float(settings.get("discount_approval_threshold_amount") or 0),
		"can_manage": can_manage,
		"current_user": frappe.session.user,
	}


@frappe.whitelist(methods=["POST"])
def update_discount_approval_settings(
	enable_discount_approval: int | str = 0,
	discount_approval_threshold_percent: float | str = 0,
	discount_approval_threshold_amount: float | str = 0,
):
	settings = frappe.get_doc("DoubleT Pricing Settings")
	settings.check_permission("read")
	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(MANAGER_APPROVAL_ROLES):
		frappe.throw(_("Only a Sales Manager or System Manager can update discount approval settings."), frappe.PermissionError)

	pct = decimal_value(discount_approval_threshold_percent or 0, _("Discount Approval Threshold (%)"))
	amt = decimal_value(discount_approval_threshold_amount or 0, _("Discount Approval Threshold (USD)"))
	if pct < 0 or pct > 100:
		frappe.throw(_("Discount Approval Threshold (%) must be between 0 and 100."), frappe.ValidationError)
	if amt < 0:
		frappe.throw(_("Discount Approval Threshold (USD) must be non-negative."), frappe.ValidationError)

	settings.enable_discount_approval = 1 if cint(enable_discount_approval) else 0
	settings.discount_approval_threshold_percent = float(pct)
	settings.discount_approval_threshold_amount = float(usd(amt))
	settings.save(ignore_permissions=True)
	return get_discount_approval_settings()


def _related_search_names(term):
	pattern = f"%{term}%"
	companies = frappe.get_list("DoubleT Company", or_filters=[["name", "like", pattern], ["company_name", "like", pattern]], pluck="name", limit_page_length=100) if frappe.has_permission("DoubleT Company", "read") else []
	contacts = frappe.get_list("DoubleT Contact", or_filters=[["name", "like", pattern], ["first_name", "like", pattern], ["last_name", "like", pattern]], pluck="name", limit_page_length=100) if frappe.has_permission("DoubleT Contact", "read") else []
	deals = frappe.get_list("DoubleT Deal", or_filters=[["name", "like", pattern], ["deal_title", "like", pattern]], pluck="name", limit_page_length=100) if frappe.has_permission("DoubleT Deal", "read") else []
	or_filters = [["name", "like", pattern]]
	if companies:
		or_filters.append(["company", "in", companies])
	if contacts:
		or_filters.append(["contact", "in", contacts])
	if deals:
		or_filters.append(["deal", "in", deals])
	return frappe.get_list("DoubleT Quotation", or_filters=or_filters, pluck="name", limit_page_length=0)


@frappe.whitelist()
def list_quotations(search=None, status=None, expiry=None, approval_status=None, limit_start=0, limit_page_length=20):
	"""Permission-scoped list search across Quotation number, Customer and Deal labels."""
	frappe.has_permission("DoubleT Quotation", "read", throw=True)
	filters = []
	term = (search or "").strip()
	if term:
		names = _related_search_names(term)
		if not names:
			return []
		filters.append(["name", "in", names])
	if status:
		filters.append(["status", "=", status])
	if approval_status:
		filters.append(["approval_status", "=", approval_status])
	today = nowdate()
	if expiry == "expired":
		filters.extend([["status", "in", ["Draft", "Sent"]], ["valid_until", "<", today]])
	elif expiry == "not_expired":
		valid_names = frappe.get_list("DoubleT Quotation", or_filters=[["status", "in", ["Accepted", "Rejected"]], ["valid_until", ">=", today]], pluck="name", limit_page_length=0)
		if not valid_names:
			return []
		filters.append(["name", "in", valid_names])
	elif expiry:
		frappe.throw(_("Invalid quotation validity filter."), frappe.ValidationError)
	return frappe.get_list(
		"DoubleT Quotation", fields=["name", "contact", "company", "deal", "quotation_date", "valid_until", "status", "approval_status", "grand_total"],
		filters=filters, order_by="modified desc", limit_start=max(0, cint(limit_start)),
		limit_page_length=min(100, max(1, cint(limit_page_length) or 20)),
	)
