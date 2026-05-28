# Copyright (c) 2024, Ricco Technologies and contributors
# For license information, please see license.txt

"""
WhatsApp Message DocType
========================

Tracks all incoming and outgoing WhatsApp messages with full metadata.
"""

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime
import json


class WhatsAppMessage(Document):
    """WhatsApp Message DocType Controller"""

    def validate(self):
        """Validate the message before saving"""
        self.validate_phone_numbers()
        self.validate_content()
        self.set_defaults()

    def validate_phone_numbers(self):
        """Validate phone number format"""
        if self.from_number:
            self.from_number = self.format_phone_number(self.from_number)
        if self.to_number:
            self.to_number = self.format_phone_number(self.to_number)

    def format_phone_number(self, number: str) -> str:
        """
        Format phone number to international format
        
        Args:
            number: Phone number string
            
        Returns:
            str: Formatted phone number
        """
        # Remove all non-numeric characters except +
        number = ''.join(c for c in str(number) if c.isdigit() or c == '+')
        
        # Add + prefix if not present
        if not number.startswith('+'):
            number = '+' + number
            
        return number

    def validate_content(self):
        """Validate message content based on type"""
        if self.message_type == "Text":
            if not self.content:
                frappe.throw(_("Message content is required for text messages"))
        
        elif self.message_type == "Template":
            if not self.template_name:
                frappe.throw(_("Template name is required for template messages"))
        
        elif self.message_type in ["Image", "Video", "Audio", "Document"]:
            if not self.media_url:
                frappe.throw(_("Media URL is required for media messages"))

    def set_defaults(self):
        """Set default values"""
        if not self.timestamp:
            self.timestamp = frappe.utils.now()
        
        if self.direction == "Outbound" and not self.status:
            self.status = "Queued"
        
        if self.direction == "Inbound" and not self.status:
            self.status = "Received"

    def on_update(self):
        """Actions after message is updated"""
        # Update conversation
        self.update_conversation()
        
        # Clear message cache
        self.clear_cache()

    def update_conversation(self):
        """Update the related conversation"""
        phone_number = self.from_number if self.direction == "Inbound" else self.to_number
        
        # Find or create conversation
        conversation_name = frappe.db.get_value(
            "WhatsApp Conversation",
            {"phone_number": phone_number}
        )
        
        if conversation_name:
            conversation = frappe.get_doc("WhatsApp Conversation", conversation_name)
            conversation.last_message = self.name
            conversation.last_message_time = self.timestamp
            conversation.last_message_type = self.message_type
            conversation.last_message_content = self.content[:200] if self.content else ""
            
            if self.direction == "Inbound":
                conversation.unread_count = (conversation.unread_count or 0) + 1
            
            conversation.save(ignore_permissions=True)

    def clear_cache(self):
        """Clear related caches"""
        frappe.cache().delete_key(f"whatsapp_messages_{self.customer}")
        frappe.cache().delete_key(f"whatsapp_conversation_{self.to_number}")

    def mark_as_read(self):
        """Mark message as read"""
        if self.status not in ["Read", "Failed"]:
            self.status = "Read"
            self.save(ignore_permissions=True)
            
            # Update WhatsApp
            if self.whatsapp_message_id:
                from ricco_whatsapp.api.whatsapp_api import mark_as_read
                mark_as_read(self.whatsapp_message_id)

    def retry_send(self):
        """Retry sending a failed message"""
        if self.status != "Failed":
            frappe.throw(_("Only failed messages can be retried"))
        
        if self.retry_count >= 3:
            frappe.throw(_("Maximum retry attempts reached"))
        
        self.status = "Queued"
        self.retry_count = (self.retry_count or 0) + 1
        self.error_code = None
        self.error_message = None
        self.save()

        # Queue the message for sending
        from ricco_whatsapp.api.whatsapp_api import send_message
        frappe.enqueue(
            send_message,
            to_number=self.to_number,
            message_type=self.message_type,
            content=self.content,
            message_doc=self.name
        )


def get_conversation_messages(phone_number: str, limit: int = 50) -> list:
    """
    Get all messages for a phone number
    
    Args:
        phone_number: Phone number to get messages for
        limit: Maximum number of messages to return
        
    Returns:
        list: List of message dictionaries
    """
    messages = frappe.get_all(
        "WhatsApp Message",
        filters={
            "to_number": phone_number,
            "from_number": phone_number
        },
        or_filters=[
            ["to_number", "=", phone_number],
            ["from_number", "=", phone_number]
        ],
        fields=["*"],
        order_by="timestamp desc",
        limit=limit
    )
    
    return messages


@frappe.whitelist()
def get_message_history(customer: str = None, phone_number: str = None, limit: int = 50):
    """Get message history for a customer or phone number"""
    filters = {}
    
    if customer:
        filters["customer"] = customer
    elif phone_number:
        filters = {
            "to_number": phone_number,
            "from_number": phone_number
        }
    
    messages = frappe.get_all(
        "WhatsApp Message",
        or_filters=[
            ["to_number", "=", phone_number] if phone_number else None,
            ["from_number", "=", phone_number] if phone_number else None
        ],
        filters=filters if customer else None,
        fields=["name", "direction", "message_type", "content", "status", "timestamp", "from_number", "to_number"],
        order_by="timestamp desc",
        limit=limit
    )
    
    return messages
