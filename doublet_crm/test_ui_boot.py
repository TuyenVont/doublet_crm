from unittest import TestCase
from unittest.mock import patch

from doublet_crm.www.doublet_crm import get_whatsapp_feature_state


class TestWhatsAppFeatureState(TestCase):
    @patch("doublet_crm.www.doublet_crm.frappe.db.exists", return_value=False)
    def test_missing_integration_is_disabled(self, exists):
        self.assertEqual(
            get_whatsapp_feature_state(),
            {"whatsapp_installed": False, "whatsapp_enabled": False},
        )
        exists.assert_called_once_with("DocType", "WhatsApp Settings")

    @patch("doublet_crm.www.doublet_crm.frappe.get_cached_value")
    @patch("doublet_crm.www.doublet_crm.frappe.db.exists", return_value=True)
    def test_active_default_account_is_enabled(self, _exists, get_cached_value):
        get_cached_value.side_effect = ["WHATSAPP-ACCOUNT", "Active"]

        self.assertEqual(
            get_whatsapp_feature_state(),
            {"whatsapp_installed": True, "whatsapp_enabled": True},
        )

    @patch("doublet_crm.www.doublet_crm.frappe.get_cached_value", return_value=None)
    @patch("doublet_crm.www.doublet_crm.frappe.db.exists", return_value=True)
    def test_installed_without_default_account_is_disabled(self, _exists, _get_cached_value):
        self.assertEqual(
            get_whatsapp_feature_state(),
            {"whatsapp_installed": True, "whatsapp_enabled": False},
        )
