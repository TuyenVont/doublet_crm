import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.api import get_linked_tasks


class TestDoubleTTask(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.unique = frappe.generate_hash(length=10)

    def tearDown(self):
        frappe.set_user("Administrator")

    def make_task(self, **values):
        data = {
            "doctype": "DoubleT Task",
            "title": f"Task {self.unique}",
            "status": "Backlog",
            "priority": "Low",
        }
        data.update(values)
        return frappe.get_doc(data).insert()

    def make_references(self):
        lead = frappe.get_doc({
            "doctype": "DoubleT Lead",
            "first_name": f"Task Lead {self.unique}",
        }).insert()
        contact = frappe.get_doc({
            "doctype": "DoubleT Contact",
            "first_name": f"Task Contact {self.unique}",
        }).insert()
        company = frappe.get_doc({
            "doctype": "DoubleT Company",
            "company_name": f"Task Company {self.unique}",
        }).insert()
        stage = frappe.get_doc({
            "doctype": "DoubleT Deal Stage",
            "stage_name": f"Task Stage {self.unique}",
            "stage_type": "OPEN",
            "sort_order": 999,
            "enabled": 1,
        }).insert()
        deal = frappe.get_doc({
            "doctype": "DoubleT Deal",
            "deal_title": f"Task Deal {self.unique}",
            "deal_type": "PERSONAL",
            "contact": contact.name,
            "stage": stage.name,
        }).insert()
        return {
            "DoubleT Lead": lead.name,
            "DoubleT Deal": deal.name,
            "DoubleT Contact": contact.name,
            "DoubleT Company": company.name,
        }

    def test_create_task(self):
        task = self.make_task(description="Created task")
        self.assertTrue(frappe.db.exists("DoubleT Task", task.name))
        self.assertEqual(task.title, f"Task {self.unique}")
        self.assertEqual(task.status, "Backlog")

    def test_read_task(self):
        task = self.make_task(description="Stored description")
        saved = frappe.get_doc("DoubleT Task", task.name)
        self.assertEqual(saved.description, "Stored description")
        self.assertEqual(saved.priority, "Low")

    def test_update_task(self):
        task = self.make_task()
        task.title = "Updated task"
        task.status = "In Progress"
        task.priority = "High"
        task.save()
        saved = frappe.get_doc("DoubleT Task", task.name)
        self.assertEqual((saved.title, saved.status, saved.priority),
                         ("Updated task", "In Progress", "High"))

    def test_delete_task(self):
        task = self.make_task()
        task.delete()
        self.assertFalse(frappe.db.exists("DoubleT Task", task.name))

    def test_title_is_required(self):
        with self.assertRaises(frappe.ValidationError):
            self.make_task(title="")

    def test_status_options(self):
        for status in ("Backlog", "Todo", "In Progress", "Done", "Canceled"):
            with self.subTest(status=status):
                task = self.make_task(status=status)
                self.assertEqual(frappe.get_doc("DoubleT Task", task.name).status, status)

    def test_priority_options(self):
        for priority in ("Low", "Medium", "High", "Urgent"):
            with self.subTest(priority=priority):
                task = self.make_task(priority=priority)
                self.assertEqual(frappe.get_doc("DoubleT Task", task.name).priority, priority)

    def test_invalid_status_and_priority_are_rejected(self):
        for field in ("status", "priority"):
            with self.subTest(field=field), self.assertRaises(frappe.ValidationError):
                self.make_task(**{field: "Unsupported"})

    def test_assignment_to_existing_user(self):
        task = self.make_task(assigned_to="Administrator")
        self.assertEqual(frappe.get_doc("DoubleT Task", task.name).assigned_to, "Administrator")

    def test_all_supported_reference_types(self):
        for doctype, docname in self.make_references().items():
            with self.subTest(doctype=doctype):
                task = self.make_task(reference_doctype=doctype, reference_docname=docname)
                saved = frappe.get_doc("DoubleT Task", task.name)
                self.assertEqual((saved.reference_doctype, saved.reference_docname),
                                 (doctype, docname))

    def test_invalid_reference_doctype_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            self.make_task(reference_doctype="User", reference_docname="Administrator")
        with self.assertRaises(frappe.ValidationError):
            get_linked_tasks("User", "Administrator")

    def test_missing_reference_document_is_rejected(self):
        missing = f"missing-{self.unique}"
        with self.assertRaises(frappe.ValidationError):
            self.make_task(reference_doctype="DoubleT Lead", reference_docname=missing)
        with self.assertRaises(frappe.DoesNotExistError):
            get_linked_tasks("DoubleT Lead", missing)

    def test_incomplete_reference_is_rejected(self):
        lead_name = self.make_references()["DoubleT Lead"]
        with self.assertRaises(frappe.ValidationError):
            self.make_task(reference_doctype="DoubleT Lead", reference_docname="")
        with self.assertRaises(frappe.ValidationError):
            self.make_task(reference_doctype="", reference_docname=lead_name)

    def test_get_linked_tasks_retrieves_task(self):
        lead_name = self.make_references()["DoubleT Lead"]
        task = self.make_task(reference_doctype="DoubleT Lead", reference_docname=lead_name)
        response = get_linked_tasks("DoubleT Lead", lead_name)
        self.assertIn(task.name, {row.name for row in response[3]})
        row = next(row for row in response[3] if row.name == task.name)
        self.assertEqual(row.title, task.title)
        self.assertEqual(row.status, task.status)

    def test_get_linked_tasks_preserves_activities_structure(self):
        lead_name = self.make_references()["DoubleT Lead"]
        self.make_task(reference_doctype="DoubleT Lead", reference_docname=lead_name)
        response = get_linked_tasks("DoubleT Lead", lead_name)
        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 5)
        self.assertEqual(response[:3], [[], [], []])
        self.assertIsInstance(response[3], list)
        self.assertEqual(response[4], [])

    def test_permissions_and_unauthorized_access(self):
        lead_name = self.make_references()["DoubleT Lead"]
        task = self.make_task(reference_doctype="DoubleT Lead", reference_docname=lead_name)
        self.assertTrue(frappe.has_permission("DoubleT Task", "read", task.name))
        self.assertTrue(frappe.has_permission("DoubleT Task", "write", task.name))
        self.assertTrue(frappe.has_permission("DoubleT Task", "delete", task.name))

        frappe.set_user("Guest")
        self.assertFalse(frappe.has_permission("DoubleT Task", "read", task.name))
        self.assertFalse(frappe.has_permission("DoubleT Task", "create"))
        with self.assertRaises(frappe.PermissionError):
            get_linked_tasks("DoubleT Lead", lead_name)
        with self.assertRaises(frappe.PermissionError):
            self.make_task(title="Forbidden task")

    def test_linked_tasks_are_isolated_by_record(self):
        first_lead = self.make_references()["DoubleT Lead"]
        second_lead = frappe.get_doc({
            "doctype": "DoubleT Lead",
            "first_name": f"Other Task Lead {self.unique}",
        }).insert()
        first = self.make_task(reference_doctype="DoubleT Lead", reference_docname=first_lead)
        second = self.make_task(reference_doctype="DoubleT Lead", reference_docname=second_lead.name)
        self.assertEqual({row.name for row in get_linked_tasks("DoubleT Lead", first_lead)[3]},
                         {first.name})
        self.assertEqual({row.name for row in get_linked_tasks("DoubleT Lead", second_lead.name)[3]},
                         {second.name})
