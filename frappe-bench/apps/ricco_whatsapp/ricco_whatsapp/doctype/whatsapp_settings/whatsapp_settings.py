# Copyright (c) 2024, Ricco Technologies and contributors
# For license information, please see license.txt

"""
WhatsApp Settings DocType
=========================

Configuration DocType for WhatsApp Business API integration.
Stores all credentials and configuration settings.
"""

import frappe
from frappe.model.document import Document
from frappe import _
import hashlib
import hmac


class WhatsAppSettings(Document):
    """WhatsApp Settings DocType Controller"""

    def validate(self):
        """Validate the settings before saving"""
        self.validate_phone_number_format()
        self.validate_credentials()
        self.generate_webhook_url()

    def validate_phone_number_format(self):
        """Validate phone number ID format"""
        if self.phone_number_id:
            # Phone Number ID should be numeric
            if not self.phone_number_id.isdigit():
                frappe.throw(_("Phone Number ID should contain only digits"))

    def validate_credentials(self):
        """Validate API credentials"""
        if self.is_active:
            if not self.phone_number_id:
                frappe.throw(_("Phone Number ID is required for active configuration"))
            if not self.business_account_id:
                frappe.throw(_("Business Account ID is required for active configuration"))
            if not self.access_token:
                frappe.throw(_("Access Token is required for active configuration"))

    def generate_webhook_url(self):
        """Generate webhook URL for Meta configuration"""
        site_url = frappe.utils.get_url()
        self.webhook_url = f"{site_url}/api/method/ricco_whatsapp.webhooks.webhook_handler.handle_webhook"

    def on_update(self):
        """Actions to perform after settings are updated"""
        # Clear cache for settings
        frappe.cache().delete_value("whatsapp_settings")

    @staticmethod
    def get_settings():
        """Get WhatsApp Settings singleton"""
        settings = frappe.cache().get_value("whatsapp_settings")
        if settings is None:
            settings = frappe.get_single("WhatsApp Settings").as_dict()
            frappe.cache().set_value("whatsapp_settings", settings)
        return settings

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature using app secret
        
        Args:
            payload: Raw request body as bytes
            signature: X-Hub-Signature-256 header value
            
        Returns:
            bool: True if signature is valid
        """
        if not self.app_secret:
            return False

        expected_signature = "sha256=" + hmac.new(
            self.app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def get_api_headers(self) -> dict:
        """Get headers for WhatsApp API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_api_url(self, endpoint: str = "") -> str:
        """
        Get full API URL for an endpoint
        
        Args:
            endpoint: API endpoint (optional)
            
        Returns:
            str: Full API URL
        """
        base_url = self.api_base_url.rstrip("/")
        if endpoint:
            return f"{base_url}/{endpoint.lstrip('/')}"
        return base_url

    def test_connection(self) -> dict:
        """
        Test the API connection
        
        Returns:
            dict: Connection test result
        """
        from ricco_whatsapp.api.whatsapp_api import get_business_phone_numbers
        
        try:
            result = get_business_phone_numbers()
            return {
                "success": True,
                "message": _("Connection successful"),
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }


@frappe.whitelist()
def test_whatsapp_connection():
    """Whitelisted function to test WhatsApp connection"""
    settings = frappe.get_single("WhatsApp Settings")
    return settings.test_connection()


@frappe.whitelist()
def refresh_templates():
    """Whitelisted function to refresh templates from WhatsApp"""
    from ricco_whatsapp.api.whatsapp_api import get_message_templates
    return get_message_templates()
