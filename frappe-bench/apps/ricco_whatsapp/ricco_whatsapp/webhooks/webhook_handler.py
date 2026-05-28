# Copyright (c) 2024, Ricco Technologies and contributors
# For license information, please see license.txt

"""
WhatsApp Webhook Handler
========================

Handles incoming webhooks from WhatsApp Business API.
This module processes all webhook events including messages, status updates,
and template updates.
"""

import frappe
from frappe import _
import json
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Optional, List


# ============================================================
# Main Webhook Handler
# ============================================================

@frappe.whitelist(allow_guest=True)
def handle_webhook():
    """
    Main webhook handler for WhatsApp Business API
    
    Handles GET requests for webhook verification
    Handles POST requests for webhook events
    
    Returns:
        Response object with appropriate status code
    """
    from frappe import request
    
    if request.method == "GET":
        return verify_webhook()
    elif request.method == "POST":
        return process_webhook()
    
    return frappe.Response(
        response=json.dumps({"error": "Method not allowed"}),
        status=405,
        headers={"Content-Type": "application/json"}
    )


@frappe.whitelist(allow_guest=True)
def verify_webhook():
    """
    Verify webhook for Meta/Facebook configuration
    
    This is called by Meta when setting up the webhook.
    It verifies the webhook URL by responding to a challenge.
    
    Query Parameters:
        hub.mode: Should be 'subscribe'
        hub.challenge: Challenge string to echo back
        hub.verify_token: Token to verify
        
    Returns:
        Response with challenge string or error
    """
    from flask import request
    
    mode = request.args.get("hub.mode")
    challenge = request.args.get("hub.challenge")
    verify_token = request.args.get("hub.verify_token")
    
    # Get verify token from settings
    settings = frappe.get_single("WhatsApp Settings")
    expected_token = settings.webhook_verify_token
    
    if mode == "subscribe" and verify_token == expected_token:
        frappe.log_error(
            title="WhatsApp Webhook Verified",
            message="Webhook verification successful"
        )
        return frappe.Response(
            response=challenge,
            status=200
        )
    
    frappe.log_error(
        title="WhatsApp Webhook Verification Failed",
        message=f"Mode: {mode}, Token: {verify_token}, Expected: {expected_token}"
    )
    
    return frappe.Response(
        response=json.dumps({"error": "Verification failed"}),
        status=403,
        headers={"Content-Type": "application/json"}
    )


def process_webhook():
    """
    Process incoming webhook events from WhatsApp
    
    Handles all webhook event types:
    - messages: Incoming messages
    - message_status: Status updates for sent messages
    - template_status: Template approval updates
    - phone_number_status: Phone number status updates
    """
    from flask import request
    
    # Get raw body for signature verification
    raw_body = request.get_data()
    
    # Verify signature
    if not verify_signature(raw_body, request.headers.get("X-Hub-Signature-256", "")):
        frappe.log_error(
            title="WhatsApp Webhook Signature Verification Failed",
            message="Invalid signature received"
        )
        return frappe.Response(
            response=json.dumps({"error": "Invalid signature"}),
            status=401,
            headers={"Content-Type": "application/json"}
        )
    
    # Parse JSON body
    try:
        data = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as e:
        frappe.log_error(
            title="WhatsApp Webhook JSON Error",
            message=str(e)
        )
        return frappe.Response(
            response=json.dumps({"error": "Invalid JSON"}),
            status=400,
            headers={"Content-Type": "application/json"}
        )
    
    # Log webhook data for debugging
    frappe.log_error(
        title="WhatsApp Webhook Received",
        message=json.dumps(data, indent=2)[:10000]  # Limit log size
    )
    
    # Process the webhook data
    try:
        result = process_webhook_data(data)
        return frappe.Response(
            response=json.dumps(result),
            status=200,
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        frappe.log_error(
            title="WhatsApp Webhook Processing Error",
            message=str(e)
        )
        return frappe.Response(
            response=json.dumps({"error": str(e)}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


def verify_signature(payload: bytes, signature: str) -> bool:
    """
    Verify webhook signature using app secret
    
    Args:
        payload: Raw request body as bytes
        signature: X-Hub-Signature-256 header value
        
    Returns:
        bool: True if signature is valid
    """
    settings = frappe.get_single("WhatsApp Settings")
    app_secret = settings.app_secret
    
    if not app_secret:
        # If app secret is not configured, skip verification
        return True
    
    if not signature:
        return False
    
    # Remove 'sha256=' prefix
    if signature.startswith("sha256="):
        signature = signature[7:]
    
    # Calculate expected signature
    expected_signature = hmac.new(
        app_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


def process_webhook_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process webhook data and route to appropriate handlers
    
    Args:
        data: Webhook data dictionary
        
    Returns:
        Dict with processing result
    """
    entry = data.get("entry", [])
    
    results = []
    
    for entry_item in entry:
        entry_id = entry_item.get("id")
        
        # Process changes
        changes = entry_item.get("changes", [])
        
        for change in changes:
            field = change.get("field")
            value = change.get("value", {})
            
            if field == "messages":
                # Handle incoming messages
                result = handle_incoming_message(value)
                results.append(result)
            
            elif field == "message_status":
                # Handle message status updates
                result = handle_message_status(value)
                results.append(result)
            
            elif field == "template_status":
                # Handle template status updates
                result = handle_template_status(value)
                results.append(result)
            
            elif field == "phone_number_status":
                # Handle phone number status updates
                result = handle_phone_number_status(value)
                results.append(result)
            
            else:
                frappe.log_error(
                    title=f"Unknown Webhook Field: {field}",
                    message=json.dumps(value, indent=2)
                )
    
    return {"status": "processed", "results": results}


# ============================================================
# Message Handlers
# ============================================================

def handle_incoming_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming message from WhatsApp
    
    Args:
        data: Message data from webhook
        
    Returns:
        Dict with processing result
    """
    contacts = data.get("contacts", [])
    messages = data.get("messages", [])
    
    results = []
    
    for message in messages:
        try:
            # Extract message details
            message_id = message.get("id")
            message_type = message.get("type")
            from_number = message.get("from")
            timestamp = message.get("timestamp")
            
            # Get contact info
            contact_name = None
            for contact in contacts:
                if contact.get("wa_id") == from_number:
                    profile = contact.get("profile", {})
                    contact_name = profile.get("name")
                    break
            
            # Extract content based on message type
            content = None
            media_url = None
            media_type = None
            
            if message_type == "text":
                text_data = message.get("text", {})
                content = text_data.get("body")
            
            elif message_type == "image":
                image_data = message.get("image", {})
                media_id = image_data.get("id")
                content = image_data.get("caption")
                media_type = "image"
                # Would need to download media using media_id
            
            elif message_type == "video":
                video_data = message.get("video", {})
                media_id = video_data.get("id")
                content = video_data.get("caption")
                media_type = "video"
            
            elif message_type == "audio":
                audio_data = message.get("audio", {})
                media_id = audio_data.get("id")
                media_type = "audio"
            
            elif message_type == "document":
                doc_data = message.get("document", {})
                media_id = doc_data.get("id")
                content = doc_data.get("caption")
                media_type = "document"
            
            elif message_type == "location":
                loc_data = message.get("location", {})
                content = f"Location: {loc_data.get('name', 'Unknown')}"
            
            elif message_type == "contacts":
                contacts_data = message.get("contacts", [])
                content = "Shared contact(s)"
            
            elif message_type == "interactive":
                interactive = message.get("interactive", {})
                interactive_type = interactive.get("type")
                
                if interactive_type == "button_reply":
                    button = interactive.get("button_reply", {})
                    content = button.get("title")
                
                elif interactive_type == "list_reply":
                    list_item = interactive.get("list_reply", {})
                    content = list_item.get("title")
            
            # Check if message already exists
            existing = frappe.db.get_value(
                "WhatsApp Message",
                {"whatsapp_message_id": message_id},
                "name"
            )
            
            if existing:
                results.append({
                    "message_id": message_id,
                    "status": "duplicate",
                    "existing_doc": existing
                })
                continue
            
            # Get customer from phone number
            customer = find_customer_by_phone(from_number)
            
            # Create message document
            doc = frappe.get_doc({
                "doctype": "WhatsApp Message",
                "message_type": message_type.capitalize(),
                "direction": "Inbound",
                "from_number": from_number,
                "to_number": frappe.db.get_single_value("WhatsApp Settings", "phone_number_id"),
                "content": content,
                "status": "Received",
                "whatsapp_message_id": message_id,
                "timestamp": datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S") if timestamp else None,
                "customer": customer
            })
            doc.insert(ignore_permissions=True)
            
            # Update or create conversation
            update_conversation(from_number, doc, contact_name)
            
            # Handle auto-reply
            handle_auto_reply(from_number, message, doc)
            
            results.append({
                "message_id": message_id,
                "status": "created",
                "docname": doc.name
            })
            
        except Exception as e:
            frappe.log_error(
                title="Error processing incoming message",
                message=f"Message ID: {message.get('id')}\nError: {str(e)}"
            )
            results.append({
                "message_id": message.get("id"),
                "status": "error",
                "error": str(e)
            })
    
    return {"messages": results}


def handle_message_status(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle message status updates from WhatsApp
    
    Args:
        data: Status data from webhook
        
    Returns:
        Dict with processing result
    """
    statuses = data.get("statuses", [])
    
    results = []
    
    for status_data in statuses:
        try:
            message_id = status_data.get("id")
            status = status_data.get("status")
            timestamp = status_data.get("timestamp")
            conversation = status_data.get("conversation", {})
            pricing = status_data.get("pricing", {})
            errors = status_data.get("errors", [])
            
            # Find message document
            docname = frappe.db.get_value(
                "WhatsApp Message",
                {"whatsapp_message_id": message_id},
                "name"
            )
            
            if docname:
                # Map WhatsApp status to internal status
                status_map = {
                    "sent": "Sent",
                    "delivered": "Delivered",
                    "read": "Read",
                    "failed": "Failed",
                    "deleted": "Failed",
                    "undelivered": "Failed"
                }
                
                internal_status = status_map.get(status, status.capitalize())
                
                # Update message document
                update_data = {
                    "status": internal_status,
                    "conversation_id": conversation.get("id"),
                    "pricing_model": pricing.get("category")
                }
                
                if errors:
                    error = errors[0]
                    update_data["error_code"] = str(error.get("code"))
                    update_data["error_message"] = error.get("title")
                
                frappe.db.set_value("WhatsApp Message", docname, update_data)
                
                results.append({
                    "message_id": message_id,
                    "status": "updated",
                    "new_status": internal_status,
                    "docname": docname
                })
            else:
                results.append({
                    "message_id": message_id,
                    "status": "not_found"
                })
        
        except Exception as e:
            frappe.log_error(
                title="Error processing message status",
                message=f"Message ID: {status_data.get('id')}\nError: {str(e)}"
            )
            results.append({
                "message_id": status_data.get("id"),
                "status": "error",
                "error": str(e)
            })
    
    return {"statuses": results}


def handle_template_status(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle template status updates from WhatsApp
    
    Args:
        data: Template status data from webhook
        
    Returns:
        Dict with processing result
    """
    # Template status updates come in different format
    # This would contain template_id, event, message_template, etc.
    
    try:
        template_id = data.get("message_template_id")
        event = data.get("event")
        template_name = data.get("message_template_name")
        language = data.get("message_template_language")
        
        # Find template document
        docname = frappe.db.get_value(
            "WhatsApp Template",
            {"template_id": template_id},
            "name"
        )
        
        if not docname:
            # Try by name and language
            docname = frappe.db.get_value(
                "WhatsApp Template",
                {"name_column": template_name, "language": language},
                "name"
            )
        
        if docname:
            # Map event to status
            event_map = {
                "APPROVED": "Approved",
                "REJECTED": "Rejected",
                "PENDING": "Pending",
                "FLAGGED": "Pending",
                "DISABLED": "Disabled"
            }
            
            status = event_map.get(event, event.capitalize())
            
            # Update template document
            frappe.db.set_value("WhatsApp Template", docname, {
                "status": status,
                "approval_status": status
            })
            
            return {
                "template_id": template_id,
                "status": "updated",
                "new_status": status
            }
        
        return {
            "template_id": template_id,
            "status": "not_found"
        }
    
    except Exception as e:
        frappe.log_error(
            title="Error processing template status",
            message=f"Error: {str(e)}"
        )
        return {
            "status": "error",
            "error": str(e)
        }


def handle_phone_number_status(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle phone number status updates from WhatsApp
    
    Args:
        data: Phone number status data
        
    Returns:
        Dict with processing result
    """
    # Phone number status updates contain display_phone_number, status, etc.
    
    try:
        phone_number = data.get("display_phone_number")
        status = data.get("status")
        
        # Log the status update
        frappe.log_error(
            title="WhatsApp Phone Number Status Update",
            message=f"Phone: {phone_number}, Status: {status}"
        )
        
        return {
            "phone_number": phone_number,
            "status": status
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ============================================================
# Helper Functions
# ============================================================

def find_customer_by_phone(phone_number: str) -> Optional[str]:
    """
    Find customer by phone number
    
    Args:
        phone_number: Phone number to search
        
    Returns:
        Customer ID or None
    """
    # Clean phone number
    clean_number = ''.join(c for c in str(phone_number) if c.isdigit())
    
    # Try to find by last 9 digits (more flexible matching)
    if len(clean_number) >= 9:
        search_number = clean_number[-9:]
        
        # Search in Contact Phone
        contact = frappe.db.get_value(
            "Contact Phone",
            {"phone": ["like", f"%{search_number}%"]},
            "parent"
        )
        
        if contact:
            # Get linked customer
            link = frappe.db.get_value(
                "Dynamic Link",
                {
                    "parenttype": "Contact",
                    "parent": contact,
                    "link_doctype": "Customer"
                },
                "link_name"
            )
            
            if link:
                return link
    
    return None


def update_conversation(
    phone_number: str,
    message_doc,
    contact_name: str = None
) -> None:
    """
    Update or create conversation for incoming message
    
    Args:
        phone_number: Customer phone number
        message_doc: WhatsApp Message document
        contact_name: Optional contact name from WhatsApp profile
    """
    from ricco_whatsapp.doctype.whatsapp_conversation.whatsapp_conversation import WhatsAppConversation
    
    # Get or create conversation
    conversation = WhatsAppConversation.get_or_create(phone_number)
    
    # Update contact name if provided
    if contact_name and not conversation.contact_name:
        conversation.contact_name = contact_name
    
    # Add message to conversation
    conversation.add_message(message_doc)
    
    # Save customer if found
    if message_doc.customer and not conversation.customer:
        conversation.customer = message_doc.customer
        conversation.save()


def handle_auto_reply(
    phone_number: str,
    message_data: Dict[str, Any],
    message_doc
) -> None:
    """
    Handle auto-reply for incoming messages
    
    Args:
        phone_number: Customer phone number
        message_data: Raw message data from webhook
        message_doc: WhatsApp Message document
    """
    settings = frappe.get_single("WhatsApp Settings")
    
    if not settings.auto_reply_enabled:
        return
    
    auto_reply_message = settings.auto_reply_message
    
    if not auto_reply_message:
        return
    
    # Check business hours if enabled
    if settings.business_hours_only:
        # Would need to check against business hours
        # For now, skip auto-reply outside business hours
        from datetime import datetime
        now = datetime.now()
        
        # Simple check: 9 AM to 6 PM
        if not (9 <= now.hour < 18):
            return
    
    # Check if outside 24-hour window for free-form messages
    # If outside, must use template
    from ricco_whatsapp.api.whatsapp_api import send_message, send_template
    
    try:
        # Check if there's a template for auto-reply
        template_name = frappe.db.get_value(
            "WhatsApp Template",
            {"name_column": "auto_reply", "status": "Approved"},
            "name_column"
        )
        
        if template_name:
            send_template(
                to_number=phone_number,
                template_name=template_name,
                language="en",
                parameters=[]
            )
        else:
            # Send free-form message (only works within 24-hour window)
            send_message(
                to_number=phone_number,
                message_type="text",
                content=auto_reply_message
            )
    
    except Exception as e:
        frappe.log_error(
            title="Auto-reply failed",
            message=str(e)
        )


# ============================================================
# Webhook Testing
# ============================================================

@frappe.whitelist()
def test_webhook():
    """
    Test webhook endpoint connectivity
    
    Returns:
        Dict with test result
    """
    settings = frappe.get_single("WhatsApp Settings")
    
    return {
        "webhook_url": settings.webhook_url,
        "verify_token_set": bool(settings.webhook_verify_token),
        "app_secret_set": bool(settings.app_secret),
        "is_active": settings.is_active
    }


@frappe.whitelist()
def send_test_webhook():
    """
    Simulate a test webhook for debugging
    
    Returns:
        Dict with simulated webhook result
    """
    test_data = {
        "entry": [{
            "id": "test_business_account",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "1234567890",
                        "phone_number_id": "test_phone_id"
                    },
                    "contacts": [{
                        "profile": {
                            "name": "Test Contact"
                        },
                        "wa_id": "9876543210"
                    }],
                    "messages": [{
                        "from": "9876543210",
                        "id": "test_message_id_123",
                        "timestamp": str(int(datetime.now().timestamp())),
                        "text": {
                            "body": "This is a test message"
                        },
                        "type": "text"
                    }]
                }
            }]
        }]
    }
    
    return process_webhook_data(test_data)
