# -*- coding: utf-8 -*-
"""
Delivery Note Event Handlers
These handlers are triggered on Delivery Note events in ERPNext.
"""

import frappe
from frappe import _


def on_submit(doc, method=None):
	"""
	Handle Delivery Note on_submit event.
	Update WooCommerce order status when delivery is made.
	"""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	# Get WooCommerce settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if not settings_name:
		return

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	if not settings.create_delivery_note:
		return

	# Get the Sales Order from the Delivery Note
	for item in doc.items:
		if item.against_sales_order:
			so_name = item.against_sales_order
			break
	else:
		return

	# Check if this is a WooCommerce order
	wc_order_name = frappe.db.get_value(
		'WooCommerce Order',
		{'erpnext_order': so_name}
	)

	if not wc_order_name:
		return

	# Get status mapping
	status_mapping = settings.get_order_status_mapping()
	wc_status = status_mapping.get('delivered', 'completed')

	# Update WooCommerce order status
	from ricco_woocommerce.api.sync_api import sync_order_status

	result = sync_order_status(so_name, wc_status)

	if result.get('success'):
		# Update WooCommerce Order record
		wc_order = frappe.get_doc('WooCommerce Order', wc_order_name)
		wc_order.status = wc_status
		wc_order.save()

		if settings.debug_mode:
			frappe.msgprint(
				_("WooCommerce order status updated to {0}").format(wc_status)
			)
	else:
		frappe.log_error(
			title=f"Failed to update WooCommerce order status on delivery: {so_name}",
			message=result.get('message', 'Unknown error')
		)
