import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe

from doublet_crm import reminders
from doublet_crm.doublet_crm.doctype.doublet_appointment import doublet_appointment
from doublet_crm.doublet_crm.doctype.doublet_task import doublet_task


class Record(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)


def reject(message, exc=None, **kwargs):
    raise (exc or frappe.ValidationError)(message)


class AppointmentHarness(doublet_appointment.DoubleTAppointment):
    def __init__(self, values=None, previous=None):
        self.__dict__.update(
            title="Customer review",
            starts_on="2026-11-27 10:00:00",
            ends_on="2026-11-27 11:00:00",
            assigned_to="sales@example.invalid",
            status="Scheduled",
            reminder_at="2026-11-27 09:30:00",
            reminder_sent_at=None,
            reference_doctype=None,
            reference_docname=None,
            previous=previous,
        )
        self.__dict__.update(values or {})

    def get_doc_before_save(self):
        return self.previous

    def has_value_changed(self, field):
        return self.get(field) != self.previous.get(field)


class TestAppointmentValidation(unittest.TestCase):
    def setUp(self):
        for target in (
            patch.object(frappe, "throw", side_effect=reject),
            patch.object(frappe, "db", Record(get_value=Mock(return_value=1))),
        ):
            target.start()
            self.addCleanup(target.stop)

    def test_valid_times_and_reminder(self):
        AppointmentHarness().validate()

    def test_end_before_start_and_late_reminder_are_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            AppointmentHarness({"ends_on": "2026-11-27 09:59:00"}).validate()
        with self.assertRaises(frappe.ValidationError):
            AppointmentHarness({"reminder_at": "2026-11-27 10:01:00"}).validate()

    def test_schedule_change_resets_sent_marker(self):
        old = AppointmentHarness({"reminder_sent_at": "2026-11-27 09:30:00"})
        changed = AppointmentHarness({"starts_on": "2026-11-27 12:00:00", "ends_on": "2026-11-27 13:00:00", "reminder_at": "2026-11-27 11:30:00", "reminder_sent_at": old.reminder_sent_at}, old)
        changed.validate()
        self.assertIsNone(changed.reminder_sent_at)

    def test_relative_reminder_moves_with_appointment(self):
        appointment = AppointmentHarness({"starts_on": "2026-11-27 12:00:00", "ends_on": "2026-11-27 12:30:00", "reminder_type": "30 Minutes Before", "reminder_at": None})
        appointment.validate()
        self.assertEqual(str(appointment.reminder_at), "2026-11-27 11:30:00")


class TestTaskReminderValidation(unittest.TestCase):
    def test_reminder_must_not_follow_due_date(self):
        task = Record(reminder_at="2026-11-27 11:00:00", due_date="2026-11-27 10:00:00", previous=None)
        task.get_doc_before_save = lambda: None
        with patch.object(frappe, "throw", side_effect=reject), self.assertRaises(frappe.ValidationError):
            doublet_task.DoubleTTask.validate_reminder(task)

    def test_relative_reminder_uses_due_date(self):
        task = Record(reminder_type="1 Hour Before", reminder_at=None, reminder_sent_at=None, due_date="2026-11-27 10:00:00", previous=None)
        task.get_doc_before_save = lambda: None
        doublet_task.DoubleTTask.validate_reminder(task)
        self.assertEqual(str(task.reminder_at), "2026-11-27 09:00:00")


class FakeReminderDoc(Record):
    def db_set(self, field, value, update_modified=False):
        setattr(self, field, value)


class TestReminderScheduling(unittest.TestCase):
    def test_scheduler_is_idempotent_and_targets_assignee(self):
        activity = FakeReminderDoc(
            doctype="DoubleT Appointment",
            name="APT-00001",
            title="Demo",
            reminder_at="2026-11-27 09:00:00",
            reminder_sent_at=None,
            status="Scheduled",
            assigned_to="sales@example.invalid",
        )
        notifications = []

        class Notification(Record):
            def insert(self, ignore_permissions=False):
                notifications.append(self)
                return self

        def get_doc(*args, **kwargs):
            if args and isinstance(args[0], dict):
                return Notification(**args[0])
            return activity

        with patch.object(frappe, "get_all", return_value=[activity.name]), \
             patch.object(frappe, "get_doc", side_effect=get_doc), \
             patch.object(frappe, "has_permission", return_value=True), \
             patch.object(frappe, "db", Record(get_value=Mock(return_value=1))):
            first = reminders.send_due_reminders("2026-11-27 09:05:00")
            second = reminders.send_due_reminders("2026-11-27 09:05:00")

        self.assertEqual(first, [("DoubleT Appointment", activity.name, activity.assigned_to)])
        self.assertEqual(second, [])
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].for_user, activity.assigned_to)

    def test_invalid_first_batch_does_not_starve_later_valid_reminder(self):
        invalid_names = [f"APT-{index:05d}" for index in range(reminders.BATCH_SIZE)]
        valid_name = "APT-99999"
        docs = {
            name: FakeReminderDoc(doctype="DoubleT Appointment", name=name, title=name, reminder_at="2026-11-27 09:00:00", reminder_sent_at=None, status="Scheduled", assigned_to="disabled@example.invalid")
            for name in invalid_names
        }
        docs[valid_name] = FakeReminderDoc(doctype="DoubleT Appointment", name=valid_name, title="Valid", reminder_at="2026-11-27 09:00:00", reminder_sent_at=None, status="Scheduled", assigned_to="sales@example.invalid")
        notifications = []

        class Notification(Record):
            def insert(self, ignore_permissions=False):
                notifications.append(self)
                return self

        def get_all(doctype, **kwargs):
            if doctype == "DoubleT Task":
                return []
            return invalid_names if not any(row[0] == "name" for row in kwargs["filters"]) else [valid_name]

        def get_doc(*args, **kwargs):
            if args and isinstance(args[0], dict):
                return Notification(**args[0])
            return docs[args[1]]

        with patch.object(frappe, "get_all", side_effect=get_all), \
             patch.object(frappe, "get_doc", side_effect=get_doc), \
             patch.object(frappe, "has_permission", return_value=True), \
             patch.object(frappe, "db", Record(get_value=Mock(side_effect=lambda _doctype, user, _field: user == "sales@example.invalid"))):
            sent = reminders.send_due_reminders("2026-11-27 09:05:00")

        self.assertEqual(sent, [("DoubleT Appointment", valid_name, "sales@example.invalid")])
        self.assertEqual(len(notifications), 1)


if __name__ == "__main__":
    unittest.main()
