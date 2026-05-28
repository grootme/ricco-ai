# Copyright (c) 2024, Ricco Technologies and contributors
# For license information, please see license.txt

"""
WhatsApp Business API Integration
=================================

Main API module for WhatsApp Business API integration.
Provides functions for sending messages, managing templates, and handling
integration with ERPNext.
"""

import frappe
from frappe import _
import requests
import json
from datetime import datetime
from typing import Optional, Dict, List, Any, Union


# ============================================================
# Core API Functions
# ============================================================

def get_settings() -> dict:
    """
    Get WhatsApp settings
    
    Returns:
        dict: WhatsApp Settings document
    """
    from ricco_whatsapp.doctype.whatsapp_settings.whatsapp_settings import WhatsAppSettings
    return WhatsAppSettings.get_settings()


def get_api_headers() -> dict:
    """Get headers for WhatsApp API requests"""
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.get('access_token')}",
        "Content-Type": "application/json"
    }


def get_api_url(endpoint: str = "") -> str:
    """
    Get full API URL for an endpoint
    
    Args:
        endpoint: API endpoint (e.g., 'messages', 'phone_numbers')
        
    Returns:
        str: Full API URL
    """
    settings = get_settings()
    base_url = settings.get("api_base_url", "https://graph.facebook.com/v18.0").rstrip("/")
    
    if endpoint:
        return f"{base_url}/{endpoint.lstrip('/')}"
    return base_url


def make_api_request(
    method: str,
    endpoint: str,
    payload: dict = None,
    params: dict = None
) -> dict:
    """
    Make a request to WhatsApp API
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        payload: Request body
        params: Query parameters
        
    Returns:
        dict: API response
        
    Raises:
        Exception: If API request fails
    """
    url = get_api_url(endpoint)
    headers = get_api_headers()
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=payload,
            params=params,
            timeout=30
        )
        
        response_data = response.json()
        
        if response.status_code >= 400:
            error = response_data.get("error", {})
            error_msg = error.get("message", str(response_data))
            error_code = error.get("code", response.status_code)
            
            frappe.log_error(
                title=f"WhatsApp API Error ({error_code})",
                message=f"URL: {url}\nPayload: {json.dumps(payload, indent=2)}\nError: {error_msg}",
                reference_doctype="WhatsApp Settings"
            )
            
            raise Exception(f"WhatsApp API Error: {error_msg}")
        
        return response_data
    
    except requests.exceptions.Timeout:
        frappe.log_error(
            title="WhatsApp API Timeout",
            message=f"Request timed out for: {url}",
            reference_doctype="WhatsApp Settings"
        )
        raise Exception("WhatsApp API request timed out")
    
    except requests.exceptions.RequestException as e:
        frappe.log_error(
            title="WhatsApp API Request Error",
            message=str(e),
            reference_doctype="WhatsApp Settings"
        )
        raise Exception(f"WhatsApp API request failed: {str(e)}")


# ============================================================
# Message Sending Functions
# ============================================================

@frappe.whitelist()
def send_message(
    to_number: str,
    message_type: str = "text",
    content: str = None,
    media_url: str = None,
    message_doc: str = None,
    **kwargs
) -> dict:
    """
    Send a message via WhatsApp Business API
    
    Args:
        to_number: Recipient phone number (with country code)
        message_type: Type of message (text, image, video, audio, document, location, contacts)
        content: Message body text
        media_url: URL for media messages
        message_doc: Optional WhatsApp Message document name to update
        **kwargs: Additional parameters
        
    Returns:
        dict: Response with message ID and status
    """
    settings = get_settings()
    
    # Check if WhatsApp is active
    if not settings.get("is_active"):
        frappe.throw(_("WhatsApp integration is not active"))
    
    # Format phone number
    to_number = format_phone_number(to_number)
    
    # Check test mode
    if settings.get("test_mode"):
        test_recipient = settings.get("test_recipient")
        if test_recipient:
            to_number = format_phone_number(test_recipient)
    
    # Build message payload
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number.lstrip("+")
    }
    
    # Add message content based on type
    if message_type.lower() == "text":
        payload["type"] = "text"
        payload["text"] = {
            "preview_url": kwargs.get("preview_url", False),
            "body": content
        }
    
    elif message_type.lower() == "image":
        payload["type"] = "image"
        payload["image"] = {
            "link": media_url,
            "caption": content
        }
    
    elif message_type.lower() == "video":
        payload["type"] = "video"
        payload["video"] = {
            "link": media_url,
            "caption": content
        }
    
    elif message_type.lower() == "audio":
        payload["type"] = "audio"
        payload["audio"] = {
            "link": media_url
        }
    
    elif message_type.lower() == "document":
        payload["type"] = "document"
        payload["document"] = {
            "link": media_url,
            "caption": content,
            "filename": kwargs.get("filename", "document.pdf")
        }
    
    elif message_type.lower() == "location":
        payload["type"] = "location"
        payload["location"] = {
            "latitude": kwargs.get("latitude"),
            "longitude": kwargs.get("longitude"),
            "name": kwargs.get("name"),
            "address": kwargs.get("address")
        }
    
    elif message_type.lower() == "contacts":
        payload["type"] = "contacts"
        payload["contacts"] = kwargs.get("contacts", [])
    
    else:
        frappe.throw(_("Invalid message type: {0}").format(message_type))
    
    # Get phone number ID
    phone_number_id = settings.get("phone_number_id")
    
    # Send message
    try:
        response = make_api_request(
            method="POST",
            endpoint=f"{phone_number_id}/messages",
            payload=payload
        )
        
        # Extract message ID
        messages = response.get("messages", [])
        message_id = messages[0].get("id") if messages else None
        
        # Update or create message document
        if message_doc:
            doc = frappe.get_doc("WhatsApp Message", message_doc)
            doc.whatsapp_message_id = message_id
            doc.status = "Sent"
            doc.save(ignore_permissions=True)
        else:
            # Create new message document
            doc = frappe.get_doc({
                "doctype": "WhatsApp Message",
                "message_type": message_type.capitalize(),
                "direction": "Outbound",
                "from_number": f"+{phone_number_id}",
                "to_number": to_number,
                "content": content,
                "status": "Sent",
                "whatsapp_message_id": message_id,
                "customer": kwargs.get("customer"),
                "sales_order": kwargs.get("sales_order"),
                "sales_invoice": kwargs.get("sales_invoice"),
                "delivery_note": kwargs.get("delivery_note")
            })
            doc.insert(ignore_permissions=True)
            message_doc = doc.name
        
        # Update conversation
        update_conversation(to_number, doc)
        
        return {
            "success": True,
            "message_id": message_id,
            "docname": message_doc
        }
    
    except Exception as e:
        # Update message document with error
        if message_doc:
            doc = frappe.get_doc("WhatsApp Message", message_doc)
            doc.status = "Failed"
            doc.error_message = str(e)
            doc.save(ignore_permissions=True)
        
        raise


@frappe.whitelist()
def send_template(
    to_number: str,
    template_name: str,
    language: str = "en",
    parameters: list = None,
    components: dict = None,
    **kwargs
) -> dict:
    """
    Send a template message via WhatsApp Business API
    
    Args:
        to_number: Recipient phone number (with country code)
        template_name: Name of the approved template
        language: Language code (e.g., 'en', 'en_US')
        parameters: List of parameter values for template
        components: Custom component structure
        **kwargs: Additional parameters (customer, sales_order, etc.)
        
    Returns:
        dict: Response with message ID and status
    """
    settings = get_settings()
    
    # Check if WhatsApp is active
    if not settings.get("is_active"):
        frappe.throw(_("WhatsApp integration is not active"))
    
    # Format phone number
    to_number = format_phone_number(to_number)
    
    # Check test mode
    if settings.get("test_mode"):
        test_recipient = settings.get("test_recipient")
        if test_recipient:
            to_number = format_phone_number(test_recipient)
    
    # Get template document
    template = frappe.db.get_value(
        "WhatsApp Template",
        {"name_column": template_name, "language": language, "status": "Approved"},
        "name"
    )
    
    if not template:
        # Try without language filter
        template = frappe.db.get_value(
            "WhatsApp Template",
            {"name_column": template_name, "status": "Approved"},
            "name"
        )
    
    # Build payload
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number.lstrip("+"),
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language
            }
        }
    }
    
    # Add components/parameters
    if components:
        payload["template"]["components"] = components
    elif parameters:
        # Build components from parameters
        template_components = []
        
        # Body parameters
        if parameters:
            body_params = []
            for param in parameters:
                body_params.append({
                    "type": "text",
                    "text": str(param)
                })
            
            template_components.append({
                "type": "body",
                "parameters": body_params
            })
        
        if template_components:
            payload["template"]["components"] = template_components
    
    # Get phone number ID
    phone_number_id = settings.get("phone_number_id")
    
    # Send message
    try:
        response = make_api_request(
            method="POST",
            endpoint=f"{phone_number_id}/messages",
            payload=payload
        )
        
        # Extract message ID
        messages = response.get("messages", [])
        message_id = messages[0].get("id") if messages else None
        
        # Create message document
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "message_type": "Template",
            "direction": "Outbound",
            "from_number": f"+{phone_number_id}",
            "to_number": to_number,
            "template_name": template,
            "template_language": language,
            "template_parameters": json.dumps(parameters) if parameters else None,
            "status": "Sent",
            "whatsapp_message_id": message_id,
            "customer": kwargs.get("customer"),
            "sales_order": kwargs.get("sales_order"),
            "sales_invoice": kwargs.get("sales_invoice"),
            "delivery_note": kwargs.get("delivery_note")
        })
        doc.insert(ignore_permissions=True)
        
        # Update template usage
        if template:
            frappe.db.set_value("WhatsApp Template", template, {
                "total_sent": frappe.db.get_value("WhatsApp Template", template, "total_sent") + 1,
                "last_used": frappe.utils.now()
            })
        
        # Update conversation
        update_conversation(to_number, doc)
        
        return {
            "success": True,
            "message_id": message_id,
            "docname": doc.name
        }
    
    except Exception as e:
        raise


@frappe.whitelist()
def mark_as_read(message_id: str) -> dict:
    """
    Mark a message as read in WhatsApp
    
    Args:
        message_id: WhatsApp message ID
        
    Returns:
        dict: API response
    """
    settings = get_settings()
    phone_number_id = settings.get("phone_number_id")
    
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    
    response = make_api_request(
        method="POST",
        endpoint=f"{phone_number_id}/messages",
        payload=payload
    )
    
    return response


# ============================================================
# Template Management Functions
# ============================================================

@frappe.whitelist()
def get_message_templates() -> dict:
    """
    Fetch all message templates from WhatsApp Business API
    
    Returns:
        dict: List of templates with their details
    """
    settings = get_settings()
    business_account_id = settings.get("business_account_id")
    
    response = make_api_request(
        method="GET",
        endpoint=f"{business_account_id}/message_templates"
    )
    
    return response


@frappe.whitelist()
def sync_templates() -> dict:
    """
    Sync templates from WhatsApp to local database
    
    Returns:
        dict: Sync result with count
    """
    response = get_message_templates()
    templates = response.get("data", [])
    
    synced_count = 0
    
    for template_data in templates:
        template_name = template_data.get("name")
        
        # Check if template exists
        existing = frappe.db.get_value(
            "WhatsApp Template",
            {"name_column": template_name, "language": template_data.get("language")},
            "name"
        )
        
        template_doc = {
            "doctype": "WhatsApp Template",
            "template_id": template_data.get("id"),
            "name_column": template_name,
            "language": template_data.get("language", "en"),
            "category": template_data.get("category", "UTILITY"),
            "status": template_data.get("status", "Pending").upper(),
            "approval_status": template_data.get("status", "Pending").upper(),
            "quality_score": template_data.get("quality_score", "Unknown"),
            "components": json.dumps(template_data.get("components", []))
        }
        
        if existing:
            doc = frappe.get_doc("WhatsApp Template", existing)
            doc.update(template_doc)
            doc.save(ignore_permissions=True)
        else:
            doc = frappe.get_doc(template_doc)
            doc.insert(ignore_permissions=True)
        
        synced_count += 1
    
    return {
        "success": True,
        "synced_count": synced_count,
        "total_templates": len(templates)
    }


@frappe.whitelist()
def update_template_status() -> dict:
    """
    Update status of all templates from WhatsApp
    
    Returns:
        dict: Update result
    """
    return sync_templates()


# ============================================================
# Phone Number Functions
# ============================================================

@frappe.whitelist()
def get_business_phone_numbers() -> dict:
    """
    Get all phone numbers for the WhatsApp Business Account
    
    Returns:
        dict: List of phone numbers with details
    """
    settings = get_settings()
    business_account_id = settings.get("business_account_id")
    
    response = make_api_request(
        method="GET",
        endpoint=f"{business_account_id}/phone_numbers"
    )
    
    return response


# ============================================================
# Helper Functions
# ============================================================

def format_phone_number(number: str) -> str:
    """
    Format phone number to international format
    
    Args:
        number: Phone number string
        
    Returns:
        str: Formatted phone number with + prefix
    """
    # Remove all non-numeric characters except +
    number = ''.join(c for c in str(number) if c.isdigit() or c == '+')
    
    # Add + prefix if not present
    if not number.startswith('+'):
        number = '+' + number
    
    return number


def update_conversation(phone_number: str, message_doc: 'WhatsAppMessage') -> None:
    """
    Update conversation with new message
    
    Args:
        phone_number: Customer phone number
        message_doc: WhatsApp Message document
    """
    from ricco_whatsapp.doctype.whatsapp_conversation.whatsapp_conversation import WhatsAppConversation
    
    conversation = WhatsAppConversation.get_or_create(phone_number)
    conversation.add_message(message_doc)


# ============================================================
# Scheduler Functions
# ============================================================

def process_message_queue():
    """Process queued messages for sending"""
    queued_messages = frappe.get_all(
        "WhatsApp Message",
        filters={"status": "Queued", "direction": "Outbound"},
        fields=["name", "to_number", "message_type", "content", 
                "template_name", "template_language", "template_parameters"],
        limit=100
    )
    
    for msg in queued_messages:
        try:
            if msg.message_type == "Template":
                parameters = json.loads(msg.template_parameters) if msg.template_parameters else []
                send_template(
                    to_number=msg.to_number,
                    template_name=frappe.db.get_value("WhatsApp Template", msg.template_name, "name_column"),
                    language=msg.template_language,
                    parameters=parameters,
                    message_doc=msg.name
                )
            else:
                send_message(
                    to_number=msg.to_number,
                    message_type=msg.message_type.lower(),
                    content=msg.content,
                    message_doc=msg.name
                )
        except Exception as e:
            frappe.log_error(
                title=f"Failed to send queued message: {msg.name}",
                message=str(e),
                reference_doctype="WhatsApp Message",
                reference_name=msg.name
            )


def update_message_status():
    """Update status of recently sent messages"""
    # This would require polling WhatsApp for message status
    # For now, status is updated via webhooks
    pass


def cleanup_old_messages():
    """Clean up old message records"""
    # Delete messages older than 90 days
    cutoff_date = frappe.utils.add_days(frappe.utils.now(), -90)
    
    frappe.db.sql("""
        DELETE FROM `tabWhatsApp Message`
        WHERE creation < %s AND status IN ('Delivered', 'Read')
    """, cutoff_date)


def generate_daily_report():
    """Generate daily WhatsApp activity report"""
    from datetime import date
    
    today = date.today()
    
    stats = {
        "date": today,
        "total_sent": frappe.db.count("WhatsApp Message", {
            "direction": "Outbound",
            "creation": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]]
        }),
        "total_received": frappe.db.count("WhatsApp Message", {
            "direction": "Inbound",
            "creation": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]]
        }),
        "failed": frappe.db.count("WhatsApp Message", {
            "status": "Failed",
            "creation": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]]
        })
    }
    
    frappe.log_error(
        title=f"WhatsApp Daily Report - {today}",
        message=json.dumps(stats, indent=2),
        reference_doctype="WhatsApp Settings"
    )


# ============================================================
# ERPNext Integration Hooks
# ============================================================

def on_sales_order_submit(doc, method):
    """Hook: Send order confirmation on Sales Order submit"""
    settings = get_settings()
    
    if not settings.get("is_active"):
        return
    
    # Get customer phone number
    phone = get_customer_phone(doc.customer)
    
    if not phone:
        frappe.log_error(
            title="WhatsApp: No phone number for customer",
            message=f"Customer: {doc.customer}",
            reference_doctype="Sales Order",
            reference_name=doc.name
        )
        return
    
    # Check for order confirmation template
    template_name = frappe.db.get_value(
        "WhatsApp Template",
        {"name_column": "order_confirmation", "status": "Approved"},
        "name_column"
    )
    
    if template_name:
        # Send template message
        parameters = [
            doc.customer_name,
            doc.name,
            frappe.utils.fmt_money(doc.grand_total, currency=doc.currency),
            doc.delivery_date or "TBD"
        ]
        
        frappe.enqueue(
            send_template,
            to_number=phone,
            template_name=template_name,
            language="en",
            parameters=parameters,
            customer=doc.customer,
            sales_order=doc.name
        )
    else:
        # Send simple text message
        message = f"Dear {doc.customer_name},\n\nYour order {doc.name} has been confirmed!\n\nTotal: {frappe.utils.fmt_money(doc.grand_total, currency=doc.currency)}\n\nThank you for your business!"
        
        frappe.enqueue(
            send_message,
            to_number=phone,
            message_type="text",
            content=message,
            customer=doc.customer,
            sales_order=doc.name
        )


def on_sales_order_cancel(doc, method):
    """Hook: Notify customer on Sales Order cancel"""
    settings = get_settings()
    
    if not settings.get("is_active"):
        return
    
    phone = get_customer_phone(doc.customer)
    
    if phone:
        message = f"Dear {doc.customer_name},\n\nYour order {doc.name} has been cancelled. Please contact us for any queries."
        
        frappe.enqueue(
            send_message,
            to_number=phone,
            message_type="text",
            content=message,
            customer=doc.customer,
            sales_order=doc.name
        )


def on_sales_invoice_submit(doc, method):
    """Hook: Send invoice notification on Sales Invoice submit"""
    settings = get_settings()
    
    if not settings.get("is_active"):
        return
    
    phone = get_customer_phone(doc.customer)
    
    if not phone:
        return
    
    # Check for invoice template
    template_name = frappe.db.get_value(
        "WhatsApp Template",
        {"name_column": "invoice_notification", "status": "Approved"},
        "name_column"
    )
    
    if template_name:
        parameters = [
            doc.customer_name,
            doc.name,
            frappe.utils.fmt_money(doc.grand_total, currency=doc.currency),
            doc.due_date or "TBD"
        ]
        
        frappe.enqueue(
            send_template,
            to_number=phone,
            template_name=template_name,
            language="en",
            parameters=parameters,
            customer=doc.customer,
            sales_invoice=doc.name
        )


def on_sales_invoice_cancel(doc, method):
    """Hook: Notify customer on Sales Invoice cancel"""
    settings = get_settings()
    
    if not settings.get("is_active"):
        return
    
    phone = get_customer_phone(doc.customer)
    
    if phone:
        message = f"Dear {doc.customer_name},\n\nInvoice {doc.name} has been cancelled. Please contact us for any queries."
        
        frappe.enqueue(
            send_message,
            to_number=phone,
            message_type="text",
            content=message,
            customer=doc.customer,
            sales_invoice=doc.name
        )


def on_delivery_note_submit(doc, method):
    """Hook: Send delivery notification"""
    settings = get_settings()
    
    if not settings.get("is_active"):
        return
    
    phone = get_customer_phone(doc.customer)
    
    if not phone:
        return
    
    # Check for delivery template
    template_name = frappe.db.get_value(
        "WhatsApp Template",
        {"name_column": "delivery_notification", "status": "Approved"},
        "name_column"
    )
    
    if template_name:
        parameters = [
            doc.customer_name,
            doc.name,
            doc.posting_date
        ]
        
        frappe.enqueue(
            send_template,
            to_number=phone,
            template_name=template_name,
            language="en",
            parameters=parameters,
            customer=doc.customer,
            delivery_note=doc.name
        )
    else:
        message = f"Dear {doc.customer_name},\n\nGreat news! Your delivery {doc.name} has been dispatched and will arrive soon.\n\nThank you for your business!"
        
        frappe.enqueue(
            send_message,
            to_number=phone,
            message_type="text",
            content=message,
            customer=doc.customer,
            delivery_note=doc.name
        )


def on_payment_entry_submit(doc, method):
    """Hook: Send payment confirmation"""
    settings = get_settings()
    
    if not settings.get("is_active"):
        return
    
    # Get party phone
    phone = None
    if doc.party_type == "Customer":
        phone = get_customer_phone(doc.party)
    
    if not phone:
        return
    
    message = f"Dear Customer,\n\nThank you for your payment of {frappe.utils.fmt_money(doc.paid_amount, currency=doc.paid_from_account_currency)}!\n\nReceipt No: {doc.name}\n\nWe appreciate your business!"
    
    frappe.enqueue(
        send_message,
        to_number=phone,
        message_type="text",
        content=message,
        customer=doc.party if doc.party_type == "Customer" else None
    )


def on_customer_update(doc, method):
    """Hook: Sync customer phone number with conversation"""
    if not doc.mobile_no and not doc.phone:
        return
    
    phone = doc.mobile_no or doc.phone
    
    # Check if conversation exists
    conversation = frappe.db.get_value(
        "WhatsApp Conversation",
        {"phone_number": format_phone_number(phone)},
        "name"
    )
    
    if conversation:
        frappe.db.set_value("WhatsApp Conversation", conversation, "customer", doc.name)


# ============================================================
# Convenience Functions for External Use
# ============================================================

@frappe.whitelist()
def send_order_confirmation(sales_order: str) -> dict:
    """
    Send order confirmation for a Sales Order
    
    Args:
        sales_order: Sales Order name
        
    Returns:
        dict: Send result
    """
    doc = frappe.get_doc("Sales Order", sales_order)
    
    phone = get_customer_phone(doc.customer)
    
    if not phone:
        return {"success": False, "error": "No phone number found for customer"}
    
    message = f"Dear {doc.customer_name},\n\nYour order {doc.name} has been confirmed!\n\nTotal: {frappe.utils.fmt_money(doc.grand_total, currency=doc.currency)}\n\nThank you for your business!"
    
    return send_message(
        to_number=phone,
        message_type="text",
        content=message,
        customer=doc.customer,
        sales_order=doc.name
    )


@frappe.whitelist()
def send_payment_reminder(sales_invoice: str) -> dict:
    """
    Send payment reminder for a Sales Invoice
    
    Args:
        sales_invoice: Sales Invoice name
        
    Returns:
        dict: Send result
    """
    doc = frappe.get_doc("Sales Invoice", sales_invoice)
    
    phone = get_customer_phone(doc.customer)
    
    if not phone:
        return {"success": False, "error": "No phone number found for customer"}
    
    days_overdue = (frappe.utils.nowdate() - doc.due_date).days if doc.due_date else 0
    
    message = f"Dear {doc.customer_name},\n\nThis is a friendly reminder that Invoice {doc.name} for {frappe.utils.fmt_money(doc.outstanding_amount, currency=doc.currency)} is overdue by {days_overdue} days.\n\nPlease make payment at your earliest convenience.\n\nThank you!"
    
    return send_message(
        to_number=phone,
        message_type="text",
        content=message,
        customer=doc.customer,
        sales_invoice=doc.name
    )


@frappe.whitelist()
def send_delivery_notification(delivery_note: str, tracking_url: str = None) -> dict:
    """
    Send delivery notification with optional tracking URL
    
    Args:
        delivery_note: Delivery Note name
        tracking_url: Optional tracking URL
        
    Returns:
        dict: Send result
    """
    doc = frappe.get_doc("Delivery Note", delivery_note)
    
    phone = get_customer_phone(doc.customer)
    
    if not phone:
        return {"success": False, "error": "No phone number found for customer"}
    
    message = f"Dear {doc.customer_name},\n\nGreat news! Your delivery {doc.name} is on its way!"
    
    if tracking_url:
        message += f"\n\nTrack your order: {tracking_url}"
    
    message += "\n\nThank you for your business!"
    
    return send_message(
        to_number=phone,
        message_type="text",
        content=message,
        customer=doc.customer,
        delivery_note=doc.name
    )


def get_customer_phone(customer: str) -> Optional[str]:
    """
    Get customer phone number
    
    Args:
        customer: Customer name/ID
        
    Returns:
        Optional[str]: Phone number or None
    """
    # First try to get from Customer
    customer_doc = frappe.get_doc("Customer", customer)
    
    # Try to get phone from linked Contact
    contacts = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Customer",
            "link_name": customer,
            "parenttype": "Contact"
        },
        fields=["parent"]
    )
    
    for contact in contacts:
        phone = frappe.db.get_value(
            "Contact Phone",
            {"parent": contact.parent, "is_primary": 1},
            "phone"
        )
        if phone:
            return phone
        
        # Try mobile
        phone = frappe.db.get_value(
            "Contact",
            contact.parent,
            "mobile_no"
        )
        if phone:
            return phone
    
    return None


# ============================================================
# Dashboard Data Functions
# ============================================================

@frappe.whitelist()
def get_dashboard_data() -> dict:
    """
    Get WhatsApp dashboard statistics
    
    Returns:
        dict: Dashboard data
    """
    today = frappe.utils.today()
    this_month_start = frappe.utils.get_first_day(today)
    
    data = {
        "overview": {
            "total_messages": frappe.db.count("WhatsApp Message"),
            "total_conversations": frappe.db.count("WhatsApp Conversation"),
            "active_conversations": frappe.db.count("WhatsApp Conversation", {
                "status": ["in", ["Open", "Pending"]]
            }),
            "unread_messages": frappe.db.sql("""
                SELECT SUM(unread_count) FROM `tabWhatsApp Conversation`
            """)[0][0] or 0
        },
        "today": {
            "sent": frappe.db.count("WhatsApp Message", {
                "direction": "Outbound",
                "creation": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]]
            }),
            "received": frappe.db.count("WhatsApp Message", {
                "direction": "Inbound",
                "creation": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]]
            }),
            "failed": frappe.db.count("WhatsApp Message", {
                "status": "Failed",
                "creation": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]]
            })
        },
        "this_month": {
            "sent": frappe.db.count("WhatsApp Message", {
                "direction": "Outbound",
                "creation": [">=", this_month_start]
            }),
            "received": frappe.db.count("WhatsApp Message", {
                "direction": "Inbound",
                "creation": [">=", this_month_start]
            })
        },
        "templates": {
            "total": frappe.db.count("WhatsApp Template"),
            "approved": frappe.db.count("WhatsApp Template", {"status": "Approved"}),
            "pending": frappe.db.count("WhatsApp Template", {"status": "Pending"})
        },
        "recent_conversations": frappe.get_all(
            "WhatsApp Conversation",
            filters={"status": ["in", ["Open", "Pending"]]},
            fields=["name", "phone_number", "customer", "contact_name", 
                    "last_message_time", "unread_count", "status"],
            order_by="last_message_time desc",
            limit=10
        )
    }
    
    return data
