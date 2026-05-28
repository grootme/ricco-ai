# -*- coding: utf-8 -*-
"""
Item Event Handlers
These handlers are triggered on Item events in ERPNext.
"""

import frappe
from frappe import _


def on_update(doc, method=None):
	"""
	Handle Item on_update event.
	Sync item to WooCommerce when it's updated in ERPNext.
	"""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	# Only sync sales items
	if not doc.is_sales_item:
		return

	# Check if item is linked to WooCommerce Product
	from ricco_woocommerce.doctype.woocommerce_product.woocommerce_product import get_product_by_item_code

	wc_product = get_product_by_item_code(doc.item_code)

	# Get active WooCommerce settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if not settings_name:
		return

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	if not settings.sync_products or not settings.sync_on_update:
		return

	if wc_product:
		# Update existing WooCommerce product
		_update_wc_product_from_item(doc, wc_product, settings)
	else:
		# Create new WooCommerce product if auto-sync is enabled
		if settings.auto_sync_enabled:
			_create_wc_product_from_item(doc, settings)


def on_trash(doc, method=None):
	"""
	Handle Item on_trash event.
	Delete or mark as inactive in WooCommerce when item is trashed.
	"""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	# Check if item is linked to WooCommerce Product
	from ricco_woocommerce.doctype.woocommerce_product.woocommerce_product import get_product_by_item_code

	wc_product = get_product_by_item_code(doc.item_code)

	if not wc_product:
		return

	# Get WooCommerce settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if not settings_name:
		return

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	# Update WooCommerce product status
	from ricco_woocommerce.api.sync_api import get_wc_api_client

	try:
		wcapi = get_wc_api_client(settings.name)

		# Instead of deleting, mark as 'private' or unpublish
		response = wcapi.put(f"products/{wc_product.wc_product_id}", {
			'status': 'private'
		})

		if response.status_code == 200:
			frappe.msgprint(
				_("WooCommerce product {0} has been unpublished").format(wc_product.wc_product_id)
			)
		else:
			frappe.log_error(
				title=f"Failed to unpublish WooCommerce product: {wc_product.wc_product_id}",
				message=response.text
			)

	except Exception as e:
		frappe.log_error(
			title="WooCommerce Product Unpublish Error",
			message=str(e)
		)


def _update_wc_product_from_item(item, wc_product, settings):
	"""Update WooCommerce product from ERPNext Item."""
	from ricco_woocommerce.api.sync_api import get_wc_api_client

	try:
		wcapi = get_wc_api_client(settings.name)

		product_data = {
			'name': item.item_name,
			'sku': item.item_code,
			'description': item.description or '',
			'short_description': (item.description[:200] if item.description else '')
		}

		# Update price if price list is configured
		if settings.default_price_list:
			price = frappe.db.get_value(
				'Item Price',
				{
					'item_code': item.name,
					'price_list': settings.default_price_list
				},
				'price_list_rate'
			)
			if price:
				product_data['regular_price'] = str(price)

		# Update stock if warehouse is configured
		if settings.default_warehouse and wc_product.stock_sync:
			from erpnext.stock.utils import get_stock_balance
			stock = get_stock_balance(item.name, settings.default_warehouse)
			product_data['stock_quantity'] = stock
			product_data['manage_stock'] = True

		# Update image if changed
		if item.image:
			product_data['images'] = [{'src': item.image}]

		response = wcapi.put(f"products/{wc_product.wc_product_id}", product_data)

		if response.status_code == 200:
			wc_data = response.json()
			wc_product.update_from_wc_data(wc_data)
			wc_product.mark_synced()

			if settings.debug_mode:
				frappe.msgprint(
					_("WooCommerce product {0} updated successfully").format(wc_product.wc_product_id)
				)
		else:
			wc_product.mark_failed(f"API Error: {response.text}")

	except Exception as e:
		wc_product.mark_failed(str(e))
		frappe.log_error(
			title=f"WooCommerce Product Update Error: {item.item_code}",
			message=str(e)
		)


def _create_wc_product_from_item(item, settings):
	"""Create new WooCommerce product from ERPNext Item."""
	from ricco_woocommerce.api.sync_api import get_wc_api_client
	from ricco_woocommerce.doctype.woocommerce_product.woocommerce_product import create_or_update_product

	try:
		wcapi = get_wc_api_client(settings.name)

		product_data = {
			'name': item.item_name,
			'sku': item.item_code,
			'type': 'simple',
			'status': 'publish',
			'description': item.description or '',
			'short_description': (item.description[:200] if item.description else '')
		}

		# Set price if price list is configured
		if settings.default_price_list:
			price = frappe.db.get_value(
				'Item Price',
				{
					'item_code': item.name,
					'price_list': settings.default_price_list
				},
				'price_list_rate'
			)
			if price:
				product_data['regular_price'] = str(price)

		# Set stock if warehouse is configured
		if settings.default_warehouse:
			from erpnext.stock.utils import get_stock_balance
			stock = get_stock_balance(item.name, settings.default_warehouse)
			product_data['stock_quantity'] = stock
			product_data['manage_stock'] = True

		# Set image if available
		if item.image:
			product_data['images'] = [{'src': item.image}]

		response = wcapi.post("products", product_data)

		if response.status_code == 201:
			wc_data = response.json()

			# Create WooCommerce Product record
			wc_product = create_or_update_product(wc_data, settings.name)
			wc_product.item_code = item.item_code
			wc_product.stock_sync = 1
			wc_product.price_sync = 1
			wc_product.mark_synced()

			if settings.debug_mode:
				frappe.msgprint(
					_("WooCommerce product {0} created successfully").format(wc_product.wc_product_id)
				)
		else:
			frappe.log_error(
				title=f"Failed to create WooCommerce product: {item.item_code}",
				message=response.text
			)

	except Exception as e:
		frappe.log_error(
			title=f"WooCommerce Product Creation Error: {item.item_code}",
			message=str(e)
		)
