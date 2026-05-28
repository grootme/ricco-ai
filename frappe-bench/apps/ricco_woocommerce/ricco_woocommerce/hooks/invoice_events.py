# -*- coding: utf-8 -*-
"""
Sales Invoice Event Handlers
These handlers are triggered on Sales Invoice events in ERPNext.
"""

import frappe
from frappe import _


def on_submit(doc, method=None):
	"""
	Handle Sales Invoice on_submit event.
	Update WooCommerce order status when invoice is submitted.
	"""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	# Get WooCommerce settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if not settings_name:
		return

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	if not settings.create_sales_invoice:
		return

	# Get the Sales Order from the Sales Invoice
	so_name = None
	for item in doc.items:
		if item.sales_order:
			so_name = item.sales_order
			break

	if not so_name:
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
	wc_status = status_mapping.get('invoiced', 'processing')

	# Update WooCommerce order status
	from ricco_woocommerce.api.sync_api import sync_order_status

	result = sync_order_status(so_name, wc_status)

	if result.get('success'):
		# Update WooCommerce Order record
		wc_order = frappe.get_doc('WooCommerce Order', wc_order_name)

		# Also add a note to the WooCommerce order
		from ricco_woocommerce.api.sync_api import get_wc_api_client

		try:
			wcapi = get_wc_api_client(settings.name)

			# Add order note
			note_data = {
				'note': f"Invoice {doc.name} created in ERPNext",
				'customer_note': False
			}

			wcapi.post(f"orders/{wc_order.wc_order_id}/notes", note_data)

		except Exception as e:
			frappe.log_error(
				title=f"Failed to add order note: {wc_order.wc_order_id}",
				message=str(e)
			)

		if settings.debug_mode:
			frappe.msgprint(
				_("WooCommerce order updated with invoice information")
			)
	else:
		frappe.log_error(
			title=f"Failed to update WooCommerce order status on invoice: {so_name}",
			message=result.get('message', 'Unknown error')
		)
