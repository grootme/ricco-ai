# Copyright (c) 2024, Ricco Technologies and contributors
# For license information, please see license.txt

"""
WhatsApp Conversation DocType
=============================

Tracks ongoing conversations with customers via WhatsApp.
"""

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime


class WhatsAppConversation(Document):
    """WhatsApp Conversation DocType Controller"""

    def validate(self):
        """Validate the conversation before saving"""
        self.format_phone_number()
        self.link_customer()

    def format_phone_number(self):
        """Format phone number to international format"""
        if self.phone_number:
            # Remove all non-numeric characters except +
            number = ''.join(c for c in str(self.phone_number) if c.isdigit() or c == '+')
            
            # Add + prefix if not present
            if not number.startswith('+'):
                number = '+' + number
            
            self.phone_number = number

    def link_customer(self):
        """Try to link conversation to existing customer"""
        if not self.customer and self.phone_number:
            # Try to find customer by phone number
            customer = frappe.db.get_value(
                "Contact Phone",
                {"phone": ["like", f"%{self.phone_number[-9:]}%"]},
                "parent"
            )
            
            if customer:
                contact = frappe.db.get_value("Contact", customer, ["name", "links"])
                if contact:
                    # Get linked customer
                    links = frappe.get_all(
                        "Dynamic Link",
                        filters={
                            "parenttype": "Contact",
                            "parent": customer,
                            "link_doctype": "Customer"
                        },
                        fields=["link_name"]
                    )
                    if links:
                        self.customer = links[0].link_name

    def on_update(self):
        """Actions after conversation is updated"""
        # Clear conversation cache
        frappe.cache().delete_key(f"whatsapp_conversation_{self.phone_number}")

    def add_message(self, message_doc: 'WhatsAppMessage') -> None:
        """
        Add a message to this conversation
        
        Args:
            message_doc: WhatsApp Message document
        """
        self.last_message = message_doc.name
        self.last_message_time = message_doc.timestamp
        self.last_message_type = message_doc.message_type
        self.last_message_content = message_doc.content[:200] if message_doc.content else ""
        self.last_message_direction = message_doc.direction
        self.total_messages = (self.total_messages or 0) + 1
        
        if message_doc.direction == "Inbound":
            self.unread_count = (self.unread_count or 0) + 1
        
        if not self.first_message_time:
            self.first_message_time = message_doc.timestamp
        
        self.save(ignore_permissions=True)

    def mark_as_read(self) -> None:
        """Mark all messages in conversation as read"""
        self.unread_count = 0
        self.save(ignore_permissions=True)
        
        # Update all inbound messages
        frappe.db.sql("""
            UPDATE `tabWhatsApp Message`
            SET status = 'Read'
            WHERE from_number = %s AND status = 'Received'
        """, self.phone_number)

    def close_conversation(self) -> None:
        """Close the conversation"""
        self.status = "Closed"
        self.save()

    def reopen_conversation(self) -> None:
        """Reopen a closed conversation"""
        self.status = "Open"
        self.save()

    def assign_to(self, user: str) -> None:
        """
        Assign conversation to a user
        
        Args:
            user: User ID to assign to
        """
        self.assigned_to = user
        self.save()
        
        # Create notification for the user
        frappe.get_doc({
            "doctype": "Notification Log",
            "for_user": user,
            "type": "Assignment",
            "document_type": "WhatsApp Conversation",
            "document_name": self.name,
            "subject": f"WhatsApp conversation assigned: {self.phone_number}",
            "from_user": frappe.session.user
        }).insert(ignore_permissions=True)

    @staticmethod
    def get_or_create(phone_number: str, customer: str = None) -> 'WhatsAppConversation':
        """
        Get existing conversation or create new one
        
        Args:
            phone_number: Customer phone number
            customer: Optional customer link
            
        Returns:
            WhatsAppConversation: Conversation document
        """
        # Normalize phone number
        number = ''.join(c for c in str(phone_number) if c.isdigit() or c == '+')
        if not number.startswith('+'):
            number = '+' + number
        
        # Check for existing conversation
        existing = frappe.db.get_value("WhatsApp Conversation", {"phone_number": number})
        
        if existing:
            return frappe.get_doc("WhatsApp Conversation", existing)
        
        # Create new conversation
        conversation = frappe.get_doc({
            "doctype": "WhatsApp Conversation",
            "phone_number": number,
            "customer": customer,
            "status": "Open"
        })
        conversation.insert(ignore_permissions=True)
        
        return conversation

    def get_messages(self, limit: int = 50) -> list:
        """
        Get messages for this conversation
        
        Args:
            limit: Maximum number of messages
            
        Returns:
            list: List of message dictionaries
        """
        return frappe.get_all(
            "WhatsApp Message",
            filters={"phone_number": self.phone_number},
            or_filters=[
                ["from_number", "=", self.phone_number],
                ["to_number", "=", self.phone_number]
            ],
            fields=["*"],
            order_by="timestamp desc",
            limit=limit
        )


@frappe.whitelist()
def get_active_conversations(user: str = None):
    """Get active conversations, optionally filtered by assigned user"""
    filters = {"status": ["in", ["Open", "Pending"]]}
    
    if user:
        filters["assigned_to"] = user
    
    conversations = frappe.get_all(
        "WhatsApp Conversation",
        filters=filters,
        fields=["name", "phone_number", "customer", "contact_name", "status", 
                "last_message_time", "unread_count", "priority"],
        order_by="last_message_time desc"
    )
    
    return conversations


@frappe.whitelist()
def get_conversation_stats():
    """Get conversation statistics"""
    stats = {
        "total": frappe.db.count("WhatsApp Conversation"),
        "open": frappe.db.count("WhatsApp Conversation", {"status": "Open"}),
        "pending": frappe.db.count("WhatsApp Conversation", {"status": "Pending"}),
        "resolved": frappe.db.count("WhatsApp Conversation", {"status": "Resolved"}),
        "unread": frappe.db.sql("""
            SELECT SUM(unread_count) FROM `tabWhatsApp Conversation`
        """)[0][0] or 0
    }
    
    return stats


@frappe.whitelist()
def mark_conversation_read(conversation_name: str):
    """Mark all messages in conversation as read"""
    conversation = frappe.get_doc("WhatsApp Conversation", conversation_name)
    conversation.mark_as_read()
    return {"success": True}


@frappe.whitelist()
def send_quick_reply(conversation_name: str, message: str):
    """Send a quick reply to a conversation"""
    from ricco_whatsapp.api.whatsapp_api import send_message
    
    conversation = frappe.get_doc("WhatsApp Conversation", conversation_name)
    
    result = send_message(
        to_number=conversation.phone_number,
        message_type="Text",
        content=message
    )
    
    return result


@frappe.whitelist()
def assign_conversation(conversation_name: str, user: str):
    """Assign conversation to a user"""
    conversation = frappe.get_doc("WhatsApp Conversation", conversation_name)
    conversation.assign_to(user)
    return {"success": True}
