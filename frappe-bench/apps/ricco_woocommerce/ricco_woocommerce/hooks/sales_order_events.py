# -*- coding: utf-8 -*-
"""
Sales Order Event Handlers
These handlers are triggered on Sales Order events in ERPNext.
"""

import frappe
from frappe import _


def on_submit(doc, method=None):
	"""
	Handle Sales Order on_submit event.
	Update WooCommerce order status when Sales Order is submitted.
	"""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	# Check if this is a WooCommerce order
	wc_order_name = frappe.db.get_value(
		'WooCommerce Order',
		{'erpnext_order': doc.name}
	)

	if not wc_order_name:
		return

	# Get WooCommerce settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if not settings_name:
		return

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	if not settings.sync_on_submit:
		return

	# Get status mapping
	status_mapping = settings.get_order_status_mapping()
	wc_status = status_mapping.get('submitted', 'processing')

	# Update WooCommerce order status
	from ricco_woocommerce.api.sync_api import sync_order_status

	result = sync_order_status(doc.name, wc_status)

	if not result.get('success'):
		frappe.log_error(
			title=f"Failed to update WooCommerce order status: {doc.name}",
			message=result.get('message', 'Unknown error')
		)


def on_cancel(doc, method=None):
	"""
	Handle Sales Order on_cancel event.
	Update WooCommerce order status when Sales Order is cancelled.
	"""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	# Check if this is a WooCommerce order
	wc_order_name = frappe.db.get_value(
		'WooCommerce Order',
		{'erpnext_order': doc.name}
	)

	if not wc_order_name:
		return

	# Get WooCommerce settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if not settings_name:
		return

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	# Get status mapping
	status_mapping = settings.get_order_status_mapping()
	wc_status = status_mapping.get('cancelled', 'cancelled')

	# Update WooCommerce order status
	from ricco_woocommerce.api.sync_api import sync_order_status

	result = sync_order_status(doc.name, wc_status)

	if not result.get('success'):
		frappe.log_error(
			title=f"Failed to update WooCommerce order status on cancel: {doc.name}",
			message=result.get('message', 'Unknown error')
		)

	# Update WooCommerce Order record
	wc_order = frappe.get_doc('WooCommerce Order', wc_order_name)
	wc_order.status = wc_status
	wc_order.save()


def on_update_after_submit(doc, method=None):
	"""
	Handle Sales Order on_update_after_submit event.
	Sync any updates to WooCommerce order.
	"""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	# Check if this is a WooCommerce order
	wc_order_name = frappe.db.get_value(
		'WooCommerce Order',
		{'erpnext_order': doc.name}
	)

	if not wc_order_name:
		return

	# Get WooCommerce settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if not settings_name:
		return

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	if not settings.sync_on_update:
		return

	# Check if there are status changes that need to be synced
	# For example, if delivery status changed
	if doc.delivery_status == 'Delivered':
		status_mapping = settings.get_order_status_mapping()
		wc_status = status_mapping.get('delivered', 'completed')

		from ricco_woocommerce.api.sync_api import sync_order_status
		result = sync_order_status(doc.name, wc_status)

		if not result.get('success'):
			frappe.log_error(
				title=f"Failed to update WooCommerce order status on update: {doc.name}",
				message=result.get('message', 'Unknown error')
			)
