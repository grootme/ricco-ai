# -*- coding: utf-8 -*-
"""
Stock Event Handlers
These handlers are triggered on Stock Entry events in ERPNext.
"""

import frappe
from frappe import _


def on_submit(doc, method=None):
	"""
	Handle Stock Entry on_submit event.
	Update WooCommerce inventory when stock entry is submitted.
	"""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	# Only process stock entries that affect inventory
	if doc.purpose not in ['Material Issue', 'Material Receipt', 'Material Transfer', 'Manufacture']:
		return

	# Get active WooCommerce settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if not settings_name:
		return

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	if not settings.sync_inventory or not settings.sync_on_update:
		return

	# Get items that need stock sync
	from ricco_woocommerce.api.sync_api import get_wc_api_client
	from ricco_woocommerce.doctype.woocommerce_product.woocommerce_product import get_product_by_item_code

	wcapi = get_wc_api_client(settings.name)

	for item in doc.items:
		# Check if item is linked to WooCommerce Product
		wc_product = get_product_by_item_code(item.item_code)

		if not wc_product or not wc_product.stock_sync:
			continue

		# Get updated stock balance
		if settings.default_warehouse:
			from erpnext.stock.utils import get_stock_balance
			stock = get_stock_balance(item.item_code, settings.default_warehouse)
		else:
			# Use the warehouse from the stock entry
			from erpnext.stock.utils import get_stock_balance
			warehouse = doc.to_warehouse if doc.purpose in ['Material Receipt', 'Material Transfer', 'Manufacture'] else doc.from_warehouse
			if warehouse:
				stock = get_stock_balance(item.item_code, warehouse)
			else:
				continue

		try:
			# Update WooCommerce stock
			response = wcapi.put(f"products/{wc_product.wc_product_id}", {
				'stock_quantity': stock,
				'manage_stock': True,
				'stock_status': 'instock' if stock > 0 else 'outofstock'
			})

			if response.status_code == 200:
				wc_product.stock_quantity = stock
				wc_product.wc_stock_quantity = stock
				wc_product.last_stock_sync = frappe.utils.now_datetime()
				wc_product.save()

				if settings.debug_mode:
					frappe.msgprint(
						_("WooCommerce stock updated for {0}: {1}").format(
							item.item_code, stock
						)
					)
			else:
				frappe.log_error(
					title=f"Failed to update WooCommerce stock: {item.item_code}",
					message=response.text
				)

		except Exception as e:
			frappe.log_error(
				title=f"WooCommerce Stock Update Error: {item.item_code}",
				message=str(e)
			)
