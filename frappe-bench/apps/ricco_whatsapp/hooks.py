# Copyright (c) 2024, Ricco Technologies and contributors
# For license information, please see license.txt

"""
Hooks for Ricco WhatsApp - WhatsApp Business API Integration

This file contains all the hooks required for the app to function properly
within the Frappe/ERPNext ecosystem.
"""

from . import __version__

app_name = "ricco_whatsapp"
app_title = "Ricco WhatsApp"
app_publisher = "Ricco Technologies"
app_description = "WhatsApp Business API Integration for Frappe/ERPNext"
app_icon = "octicon octicon-comment-discussion"
app_color = "#25D366"  # WhatsApp green
app_email = "support@ricco.tech"
app_license = "MIT"

# Required Apps
# ------------------
required_apps = ["frappe", "erpnext"]

# Includes in <head>
# ------------------
# include js, css files in header of desk.html
# app_include_js = "/assets/ricco_whatsapp/js/ricco_whatsapp.js"
# app_include_css = "/assets/ricco_whatsapp/css/ricco_whatsapp.css"

# Includes in <head>
# ------------------
# include js, css files in header of web template
# web_include_js = "/assets/ricco_whatsapp/js/ricco_whatsapp_web.js"
# web_include_css = "/assets/ricco_whatsapp/css/ricco_whatsapp_web.css"

# Home Page
# ------------------
# home_page = "login"

# Generator for app homepage
# ------------------
# app_home_page = "whatsapp_dashboard"

# Website Route Rules
# ------------------
# Map URL patterns to Python functions for webhook handling
website_route_rules = [
    {
        "from_route": "/api/method/whatsapp_webhook",
        "to_route": "ricco_whatsapp.webhooks.webhook_handler.handle_webhook"
    },
    {
        "from_route": "/whatsapp/webhook",
        "to_route": "ricco_whatsapp.webhooks.webhook_handler.handle_webhook"
    }
]

# Whitelisted Functions
# ------------------
# Functions that can be called via API
whitelisted_functions = [
    "ricco_whatsapp.api.whatsapp_api.send_message",
    "ricco_whatsapp.api.whatsapp_api.send_template",
    "ricco_whatsapp.api.whatsapp_api.mark_as_read",
    "ricco_whatsapp.api.whatsapp_api.get_message_templates",
    "ricco_whatsapp.api.whatsapp_api.get_business_phone_numbers",
    "ricco_whatsapp.api.whatsapp_api.send_order_confirmation",
    "ricco_whatsapp.api.whatsapp_api.send_payment_reminder",
    "ricco_whatsapp.api.whatsapp_api.send_delivery_notification",
    "ricco_whatsapp.webhooks.webhook_handler.handle_webhook",
    "ricco_whatsapp.webhooks.webhook_handler.verify_webhook"
]

# Scheduler Events
# ------------------
# Schedule periodic tasks for message queue processing and status updates
scheduler_events = {
    # Events that run every minute
    "all": [
        "ricco_whatsapp.api.whatsapp_api.process_message_queue",
        "ricco_whatsapp.api.whatsapp_api.update_message_status"
    ],
    # Events that run every 5 minutes
    "cron": {
        "*/5 * * * *": [
            "ricco_whatsapp.api.whatsapp_api.sync_templates",
            "ricco_whatsapp.api.whatsapp_api.update_template_status"
        ],
        "0 * * * *": [
            "ricco_whatsapp.api.whatsapp_api.cleanup_old_messages"
        ],
        "0 0 * * *": [
            "ricco_whatsapp.api.whatsapp_api.generate_daily_report"
        ]
    }
}

# DocType Event Hooks
# ------------------
# Hook into DocType events for automation
doc_events = {
    "Sales Order": {
        "on_submit": "ricco_whatsapp.api.whatsapp_api.on_sales_order_submit",
        "on_cancel": "ricco_whatsapp.api.whatsapp_api.on_sales_order_cancel"
    },
    "Sales Invoice": {
        "on_submit": "ricco_whatsapp.api.whatsapp_api.on_sales_invoice_submit",
        "on_cancel": "ricco_whatsapp.api.whatsapp_api.on_sales_invoice_cancel"
    },
    "Delivery Note": {
        "on_submit": "ricco_whatsapp.api.whatsapp_api.on_delivery_note_submit"
    },
    "Payment Entry": {
        "on_submit": "ricco_whatsapp.api.whatsapp_api.on_payment_entry_submit"
    },
    "Customer": {
        "on_update": "ricco_whatsapp.api.whatsapp_api.on_customer_update"
    }
}

# Permission Queries
# ------------------
# Custom permission queries for DocTypes
# permission_query_conditions = {
#     "WhatsApp Message": "ricco_whatsapp.permissions.message_query",
#     "WhatsApp Conversation": "ricco_whatsapp.permissions.conversation_query"
# }

# User Data Protection
# ------------------
# Data that should be anonymized
# user_data_fields = [
#     {"doctype": "WhatsApp Message", "field": "content"},
#     {"doctype": "WhatsApp Conversation", "field": "last_message"}
# ]

# Email Alert Configuration
# ------------------
# Notification settings
# notification_config = "ricco_whatsapp.notifications.get_notification_config"

# Print Formats
# ------------------
# Custom print formats that use WhatsApp sharing
# print_format_data = [
#     {"doctype": "Sales Order", "format": "WhatsApp Order Confirmation"}
# ]

# On Session Creation
# ------------------
# Run when a user session is created
# on_session_creation = "ricco_whatsapp.api.whatsapp_api.on_session_creation"

# Boot Info
# ------------------
# Add custom data to boot info
# boot_info = "ricco_whatsapp.boot.get_boot_info"

# Portal Menu Items
# ------------------
# Add items to the portal menu
portal_menu_items = [
    {
        "title": "WhatsApp Messages",
        "route": "/whatsapp/messages",
        "reference_doctype": "WhatsApp Message",
        "role": "Customer"
    }
]

# Logging
# ------------------
# Configure logging for the app
# logging = {
#     "ricco_whatsapp": {
#         "level": "DEBUG",
#         "handler": "file",
#         "filename": "ricco_whatsapp.log"
#     }
# }

# Constants
# ------------------
WHATSAPP_API_VERSION = "v18.0"
WHATSAPP_API_BASE_URL = "https://graph.facebook.com/v18.0"
