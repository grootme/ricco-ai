# -*- coding: utf-8 -*-
"""
Ricco WooCommerce Integration Hooks
This file contains all the hooks for integrating WooCommerce with ERPNext
"""

from . import __version__ as app_version

app_name = "ricco_woocommerce"
app_title = "Ricco WooCommerce Integration"
app_publisher = "Ricco"
app_description = "WooCommerce e-commerce integration for ERPNext"
app_icon = "octicon octicon-repo"
app_color = "#4a90d9"
app_email = "support@ricco.com"
app_license = "MIT"

# Includes in <head>
# ------------------

app_include_js = "/assets/ricco_woocommerce/js/ricco_woocommerce.js"
app_include_css = "/assets/ricco_woocommerce/css/ricco_woocommerce.css"

# Domains
# -------
domains = ["WooCommerce"]

# Dependencies
# ------------
required_apps = ["erpnext"]

# DocTypes
# --------
doctype_list = [
	"WooCommerce Settings",
	"WooCommerce Order",
	"WooCommerce Product", 
	"WooCommerce Customer",
	"WooCommerce Webhook Log"
]

# ======== EVENT HOOKS ========

# DocType Events
# --------------
doc_events = {
	"Sales Order": {
		"on_submit": "ricco_woocommerce.hooks.sales_order_events.on_submit",
		"on_cancel": "ricco_woocommerce.hooks.sales_order_events.on_cancel",
		"on_update_after_submit": "ricco_woocommerce.hooks.sales_order_events.on_update_after_submit"
	},
	"Item": {
		"on_update": "ricco_woocommerce.hooks.item_events.on_update",
		"on_trash": "ricco_woocommerce.hooks.item_events.on_trash"
	},
	"Customer": {
		"on_update": "ricco_woocommerce.hooks.customer_events.on_update",
		"on_trash": "ricco_woocommerce.hooks.customer_events.on_trash"
	},
	"Stock Entry": {
		"on_submit": "ricco_woocommerce.hooks.stock_events.on_submit"
	},
	"Delivery Note": {
		"on_submit": "ricco_woocommerce.hooks.delivery_events.on_submit"
	},
	"Sales Invoice": {
		"on_submit": "ricco_woocommerce.hooks.invoice_events.on_submit"
	}
}

# ======== SCHEDULED JOBS ========

scheduler_events = {
	"all": [
		"ricco_woocommerce.api.sync_api.process_webhook_queue"
	],
	"hourly": [
		"ricco_woocommerce.api.sync_api.sync_pending_orders",
		"ricco_woocommerce.api.sync_api.sync_pending_customers",
		"ricco_woocommerce.api.sync_api.retry_failed_syncs"
	],
	"daily": [
		"ricco_woocommerce.api.sync_api.sync_all_products",
		"ricco_woocommerce.api.sync_api.sync_all_inventory",
		"ricco_woocommerce.api.sync_api.cleanup_old_logs"
	],
	"weekly": [
		"ricco_woocommerce.api.sync_api.sync_all_customers"
	]
}

# ======== PERMISSIONS ========

permission_query_conditions = {
	"WooCommerce Order": "ricco_woocommerce.permissions.get_permission_query_conditions",
	"WooCommerce Product": "ricco_woocommerce.permissions.get_permission_query_conditions",
	"WooCommerce Customer": "ricco_woocommerce.permissions.get_permission_query_conditions",
	"WooCommerce Webhook Log": "ricco_woocommerce.permissions.get_permission_query_conditions"
}

# ======== WHITELISTED METHODS ========

whitelisted_methods = [
	"ricco_woocommerce.api.sync_api.sync_products",
	"ricco_woocommerce.api.sync_api.sync_orders",
	"ricco_woocommerce.api.sync_api.sync_customers",
	"ricco_woocommerce.api.sync_api.sync_inventory",
	"ricco_woocommerce.api.sync_api.sync_order_status",
	"ricco_woocommerce.api.sync_api.process_webhook",
	"ricco_woocommerce.api.sync_api.get_sync_status",
	"ricco_woocommerce.api.sync_api.manual_sync",
	"ricco_woocommerce.api.sync_api.test_connection"
]

# ======== BOOT INFO ========

app_include_js = [
	"assets/ricco_woocommerce/js/ricco_woocommerce.bundle.js"
]

# ======== INSTALLATION ========

after_install = "ricco_woocommerce.install.after_install"
after_migrate = "ricco_woocommerce.install.after_migrate"

# ======== UNINSTALL ========

before_uninstall = "ricco_woocommerce.uninstall.before_uninstall"

# ======== WEBSITE ROUTES ========

website_route_rules = [
	{
		"from_route": "/woocommerce/webhook",
		"to_route": "woocommerce_webhook_handler"
	}
]

# ======== API WHITELIST ========

# Allow guest access to webhook endpoint
guest_allowed_methods = [
	"ricco_woocommerce.api.webhook_handler.handle_webhook"
]

# ======== USER DATA PROTECTION ========

user_data_fields = [
	{
		"doctype": "WooCommerce Customer",
		"fields": [
			{"field_name": "email", "is_personal_data": 1},
			{"field_name": "first_name", "is_personal_data": 1},
			{"field_name": "last_name", "is_personal_data": 1}
		]
	},
	{
		"doctype": "WooCommerce Order",
		"fields": [
			{"field_name": "billing_email", "is_personal_data": 1},
			{"field_name": "billing_phone", "is_personal_data": 1},
			{"field_name": "shipping_phone", "is_personal_data": 1}
		]
	}
]

# ======== ONDEMAND JOB ========

background_workers = {
	"long": 1,
	"short": 2,
	"default": 1
}

# ======== LOGGING ========

log_settings = {
	"max_logs_per_file": 10000,
	"max_log_age_days": 30
}
