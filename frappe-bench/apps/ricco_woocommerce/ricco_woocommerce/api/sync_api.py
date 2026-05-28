# -*- coding: utf-8 -*-
"""
Ricco WooCommerce Sync API
This module contains all synchronization functions for WooCommerce integration.
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, now_datetime, add_days
import json
from datetime import datetime
import traceback

# Initialize WooCommerce API client cache
_wc_api_clients = {}


def get_wc_api_client(settings_name=None):
	"""Get or create WooCommerce API client."""
	global _wc_api_clients

	if not settings_name:
		settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})

	if not settings_name:
		frappe.throw(_("No active WooCommerce Settings found"))

	if settings_name not in _wc_api_clients:
		from woocommerce import API
		settings = frappe.get_doc('WooCommerce Settings', settings_name)

		_wc_api_clients[settings_name] = API(
			url=settings.store_url,
			consumer_key=settings.get_password('consumer_key'),
			consumer_secret=settings.get_password('consumer_secret'),
			version=settings.api_version,
			timeout=settings.timeout or 30,
			verify_ssl=settings.verify_ssl
		)

	return _wc_api_clients[settings_name]


def get_settings(settings_name=None):
	"""Get WooCommerce settings."""
	if not settings_name:
		settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})

	if settings_name:
		return frappe.get_doc('WooCommerce Settings', settings_name)
	return None


# ======== PRODUCT SYNC ========

@frappe.whitelist()
def sync_products(direction="to_wc", settings_name=None, limit=100):
	"""
	Bi-directional product sync between ERPNext and WooCommerce.

	Args:
		direction: "to_wc" - Sync ERPNext items to WooCommerce
				   "from_wc" - Import WooCommerce products to ERPNext
		settings_name: WooCommerce Settings document name
		limit: Maximum number of products to sync

	Returns:
		dict: Sync results with counts and errors
	"""
	results = {
		'success': True,
		'direction': direction,
		'synced': 0,
		'created': 0,
		'updated': 0,
		'failed': 0,
		'errors': []
	}

	settings = get_settings(settings_name)
	if not settings or not settings.sync_products:
		results['success'] = False
		results['message'] = _("Product sync is disabled")
		return results

	try:
		if direction == "to_wc":
			results = _sync_products_to_wc(settings, limit)
		elif direction == "from_wc":
			results = _sync_products_from_wc(settings, limit)
		else:
			results['success'] = False
			results['message'] = _("Invalid sync direction: {0}").format(direction)

	except Exception as e:
		results['success'] = False
		results['message'] = str(e)
		frappe.log_error(
			title="WooCommerce Product Sync Error",
			message=f"{str(e)}\n\n{traceback.format_exc()}"
		)

	return results


def _sync_products_to_wc(settings, limit=100):
	"""Sync ERPNext items to WooCommerce."""
	results = {
		'success': True,
		'direction': 'to_wc',
		'synced': 0,
		'created': 0,
		'updated': 0,
		'failed': 0,
		'errors': []
	}

	wcapi = get_wc_api_client(settings.name)

	# Get items that need sync
	items = frappe.get_all(
		'Item',
		filters={
			'is_sales_item': 1,
			'disabled': 0
		},
		fields=['name', 'item_code', 'item_name', 'description', 'stock_uom', 'image'],
		limit=limit
	)

	for item in items:
		try:
			# Check if product already exists
			wc_product = frappe.db.get_value(
				'WooCommerce Product',
				{'item_code': item.name}
			)

			product_data = _prepare_product_data_from_item(item, settings)

			if wc_product:
				# Update existing product
				wc_product_doc = frappe.get_doc('WooCommerce Product', wc_product)
				response = wcapi.put(f"products/{wc_product_doc.wc_product_id}", product_data)
				action = 'updated'
			else:
				# Create new product
				response = wcapi.post("products", product_data)
				action = 'created'

			if response.status_code in [200, 201]:
				wc_data = response.json()
				_update_wc_product_record(wc_data, item.name, settings.name)
				results['synced'] += 1
				if action == 'created':
					results['created'] += 1
				else:
					results['updated'] += 1
			else:
				results['failed'] += 1
				results['errors'].append({
					'item': item.item_code,
					'error': response.text
				})

		except Exception as e:
			results['failed'] += 1
			results['errors'].append({
				'item': item.item_code,
				'error': str(e)
			})

	return results


def _sync_products_from_wc(settings, limit=100):
	"""Import WooCommerce products to ERPNext."""
	results = {
		'success': True,
		'direction': 'from_wc',
		'synced': 0,
		'created': 0,
		'updated': 0,
		'failed': 0,
		'errors': []
	}

	wcapi = get_wc_api_client(settings.name)
	page = 1
	per_page = min(settings.batch_size or 100, limit)

	while True:
		response = wcapi.get("products", params={
			'per_page': per_page,
			'page': page
		})

		if response.status_code != 200:
			results['success'] = False
			results['message'] = f"API Error: {response.text}"
			break

		products = response.json()

		if not products:
			break

		for wc_product in products:
			try:
				item_code = _create_or_update_item_from_wc(wc_product, settings)

				# Update WooCommerce Product record
				from ricco_woocommerce.doctype.woocommerce_product.woocommerce_product import create_or_update_product
				create_or_update_product(wc_product, settings.name)

				results['synced'] += 1
				if item_code.get('created'):
					results['created'] += 1
				else:
					results['updated'] += 1

			except Exception as e:
				results['failed'] += 1
				results['errors'].append({
					'product_id': wc_product.get('id'),
					'error': str(e)
				})

		if len(products) < per_page:
			break

		page += 1

		if results['synced'] >= limit:
			break

	return results


def _prepare_product_data_from_item(item, settings):
	"""Prepare WooCommerce product data from ERPNext Item."""
	product_data = {
		'name': item.item_name,
		'sku': item.item_code,
		'type': 'simple',
		'description': item.description or '',
		'short_description': item.description[:200] if item.description else ''
	}

	# Get price
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

	# Get stock
	if settings.default_warehouse:
		from erpnext.stock.utils import get_stock_balance
		stock = get_stock_balance(item.name, settings.default_warehouse)
		product_data['manage_stock'] = True
		product_data['stock_quantity'] = stock

	# Image
	if item.image:
		product_data['images'] = [{'src': item.image}]

	return product_data


def _create_or_update_item_from_wc(wc_product, settings):
	"""Create or update ERPNext Item from WooCommerce product."""
	sku = wc_product.get('sku') or f"WC-{wc_product.get('id')}"
	created = False

	# Check if item exists
	item_exists = frappe.db.exists('Item', {'item_code': sku})

	if item_exists:
		item = frappe.get_doc('Item', sku)
	else:
		# Create new item
		item = frappe.new_doc('Item')
		item.item_code = sku
		item.item_name = wc_product.get('name', sku)
		item.item_group = frappe.db.get_value('Item Group', {'is_group': 0}) or 'Products'
		item.stock_uom = 'Nos'
		item.is_sales_item = 1
		item.description = wc_product.get('description', '') or wc_product.get('short_description', '')
		created = True

	# Update prices
	if wc_product.get('regular_price') and settings.default_price_list:
		price = flt(wc_product.get('regular_price'))

		item_price_exists = frappe.db.exists(
			'Item Price',
			{
				'item_code': item.item_code,
				'price_list': settings.default_price_list
			}
		)

		if item_price_exists:
			frappe.db.set_value('Item Price', item_price_exists, 'price_list_rate', price)
		else:
			price_doc = frappe.new_doc('Item Price')
			price_doc.item_code = item.item_code
			price_doc.price_list = settings.default_price_list
			price_doc.price_list_rate = price
			price_doc.insert()

	item.save()

	return {'item_code': item.item_code, 'created': created}


def _update_wc_product_record(wc_data, item_code, settings_name):
	"""Update or create WooCommerce Product record."""
	from ricco_woocommerce.doctype.woocommerce_product.woocommerce_product import create_or_update_product

	product = create_or_update_product(wc_data, settings_name)

	if not product.item_code:
		product.item_code = item_code
		product.save()

	product.mark_synced()


# ======== ORDER SYNC ========

@frappe.whitelist()
def sync_orders(status="any", settings_name=None, limit=100, from_date=None):
	"""
	Import orders from WooCommerce.

	Args:
		status: Order status to filter (any, pending, processing, completed, etc.)
		settings_name: WooCommerce Settings document name
		limit: Maximum number of orders to sync
		from_date: Only sync orders modified after this date

	Returns:
		dict: Sync results
	"""
	results = {
		'success': True,
		'synced': 0,
		'created': 0,
		'updated': 0,
		'failed': 0,
		'errors': []
	}

	settings = get_settings(settings_name)
	if not settings or not settings.sync_orders:
		results['success'] = False
		results['message'] = _("Order sync is disabled")
		return results

	try:
		wcapi = get_wc_api_client(settings.name)
		page = 1
		per_page = min(settings.batch_size or 100, limit)

		params = {
			'per_page': per_page,
			'page': page
		}

		if status != 'any':
			params['status'] = status

		if from_date:
			params['after'] = from_date

		while True:
			response = wcapi.get("orders", params=params)

			if response.status_code != 200:
				results['success'] = False
				results['message'] = f"API Error: {response.text}"
				break

			orders = response.json()

			if not orders:
				break

			for wc_order in orders:
				try:
					result = _import_wc_order(wc_order, settings)
					results['synced'] += 1
					if result.get('created'):
						results['created'] += 1
					else:
						results['updated'] += 1

				except Exception as e:
					results['failed'] += 1
					results['errors'].append({
						'order_id': wc_order.get('id'),
						'error': str(e)
					})

			if len(orders) < per_page:
				break

			page += 1
			params['page'] = page

			if results['synced'] >= limit:
				break

	except Exception as e:
		results['success'] = False
		results['message'] = str(e)
		frappe.log_error(
			title="WooCommerce Order Sync Error",
			message=f"{str(e)}\n\n{traceback.format_exc()}"
		)

	return results


def _import_wc_order(wc_order, settings):
	"""Import a single WooCommerce order."""
	from ricco_woocommerce.doctype.woocommerce_order.woocommerce_order import create_or_update_order

	# Create/update WooCommerce Order record
	wc_order_doc = create_or_update_order(wc_order, settings.name)

	# Get or create customer
	customer = _get_or_create_customer_for_order(wc_order, settings)

	if customer:
		wc_order_doc.customer = customer

	# Check if Sales Order already exists
	created = False
	if wc_order_doc.erpnext_order:
		so = frappe.get_doc('Sales Order', wc_order_doc.erpnext_order)
	else:
		# Create Sales Order
		so = _create_sales_order(wc_order, settings, customer)
		if so:
			wc_order_doc.erpnext_order = so.name
			created = True

	wc_order_doc.mark_synced(so.name if so else None)

	return {'created': created, 'so_name': so.name if so else None}


def _get_or_create_customer_for_order(wc_order, settings):
	"""Get or create customer for WooCommerce order."""
	customer_id = wc_order.get('customer_id')

	if customer_id and customer_id > 0:
		# Check if WooCommerce Customer exists
		from ricco_woocommerce.doctype.woocommerce_customer.woocommerce_customer import get_customer_by_wc_id

		wc_customer = get_customer_by_wc_id(str(customer_id))

		if wc_customer and wc_customer.customer:
			return wc_customer.customer

	# Create customer from order data
	billing = wc_order.get('billing', {})
	email = billing.get('email')

	if not email:
		return None

	# Check if customer exists by email
	customer = frappe.db.get_value('Customer', {'email_id': email})

	if customer:
		return customer

	# Create new customer
	customer_doc = frappe.new_doc('Customer')
	customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
	if not customer_name:
		customer_name = email

	customer_doc.customer_name = customer_name
	customer_doc.customer_type = 'Individual'
	customer_doc.customer_group = settings.default_customer_group or frappe.db.get_value('Customer Group', {'is_group': 0})
	customer_doc.territory = settings.default_territory or frappe.db.get_value('Territory', {'is_group': 0})
	customer_doc.email_id = email
	customer_doc.mobile_no = billing.get('phone')

	customer_doc.insert()

	# Create address
	if billing.get('address_1') or billing.get('city'):
		address = frappe.new_doc('Address')
		address.address_title = customer_name
		address.address_type = 'Billing'
		address.address_line1 = billing.get('address_1', '')
		address.address_line2 = billing.get('address_2', '')
		address.city = billing.get('city', '')
		address.state = billing.get('state', '')
		address.pincode = billing.get('postcode', '')
		address.country = billing.get('country', '')
		address.phone = billing.get('phone', '')
		address.email_id = email
		address.append('links', {
			'link_doctype': 'Customer',
			'link_name': customer_doc.name
		})
		address.insert()

	return customer_doc.name


def _create_sales_order(wc_order, settings, customer):
	"""Create Sales Order from WooCommerce order."""
	if not customer:
		return None

	so = frappe.new_doc('Sales Order')
	so.customer = customer
	so.transaction_date = wc_order.get('date_created', '').split('T')[0] if wc_order.get('date_created') else frappe.utils.today()

	# Set naming series
	if settings.default_naming_series:
		so.naming_series = settings.default_naming_series

	# Add items
	for line_item in wc_order.get('line_items', []):
		sku = line_item.get('sku')
		item_code = None

		if sku:
			item_code = frappe.db.get_value('Item', {'item_code': sku})

		if not item_code:
			# Create item from product
			item_code = _create_item_from_line_item(line_item, settings)

		if item_code:
			so.append('items', {
				'item_code': item_code,
				'qty': line_item.get('quantity', 1),
				'rate': line_item.get('price', 0),
				'warehouse': settings.default_warehouse
			})

	if not so.items:
		return None

	# Set warehouse
	if settings.default_warehouse:
		so.set_warehouse = settings.default_warehouse

	so.insert()

	# Submit if settings say so
	if settings.sync_on_submit:
		so.submit()

	return so


def _create_item_from_line_item(line_item, settings):
	"""Create Item from WooCommerce line item."""
	sku = line_item.get('sku') or f"WC-{line_item.get('product_id')}"

	# Check if item exists
	if frappe.db.exists('Item', {'item_code': sku}):
		return sku

	item = frappe.new_doc('Item')
	item.item_code = sku
	item.item_name = line_item.get('name', sku)
	item.item_group = frappe.db.get_value('Item Group', {'is_group': 0}) or 'Products'
	item.stock_uom = 'Nos'
	item.is_sales_item = 1
	item.insert()

	return item.item_code


@frappe.whitelist()
def sync_single_order(wc_order_name):
	"""Sync a single WooCommerce Order."""
	from ricco_woocommerce.doctype.woocommerce_order.woocommerce_order import WooCommerceOrder

	wc_order = frappe.get_doc('WooCommerce Order', wc_order_name)

	# Fetch latest data from WooCommerce
	wc_data = wc_order.get_wc_order_data()

	settings = get_settings(wc_order.woocommerce_settings)

	return _import_wc_order(wc_data, settings)


# ======== CUSTOMER SYNC ========

@frappe.whitelist()
def sync_customers(settings_name=None, limit=100):
	"""
	Import/update customers from WooCommerce.

	Args:
		settings_name: WooCommerce Settings document name
		limit: Maximum number of customers to sync

	Returns:
		dict: Sync results
	"""
	results = {
		'success': True,
		'synced': 0,
		'created': 0,
		'updated': 0,
		'failed': 0,
		'errors': []
	}

	settings = get_settings(settings_name)
	if not settings or not settings.sync_customers:
		results['success'] = False
		results['message'] = _("Customer sync is disabled")
		return results

	try:
		wcapi = get_wc_api_client(settings.name)
		page = 1
		per_page = min(settings.batch_size or 100, limit)

		while True:
			response = wcapi.get("customers", params={
				'per_page': per_page,
				'page': page
			})

			if response.status_code != 200:
				results['success'] = False
				results['message'] = f"API Error: {response.text}"
				break

			customers = response.json()

			if not customers:
				break

			for wc_customer in customers:
				try:
					from ricco_woocommerce.doctype.woocommerce_customer.woocommerce_customer import create_or_update_customer

					wc_customer_doc = create_or_update_customer(wc_customer, settings.name)

					# Create ERPNext Customer if not linked
					if not wc_customer_doc.customer:
						customer = wc_customer_doc.create_erpnext_customer()
						wc_customer_doc.mark_synced(customer.name)
						results['created'] += 1
					else:
						wc_customer_doc.mark_synced()
						results['updated'] += 1

					results['synced'] += 1

				except Exception as e:
					results['failed'] += 1
					results['errors'].append({
						'customer_id': wc_customer.get('id'),
						'error': str(e)
					})

			if len(customers) < per_page:
				break

			page += 1

			if results['synced'] >= limit:
				break

	except Exception as e:
		results['success'] = False
		results['message'] = str(e)
		frappe.log_error(
			title="WooCommerce Customer Sync Error",
			message=f"{str(e)}\n\n{traceback.format_exc()}"
		)

	return results


# ======== INVENTORY SYNC ========

@frappe.whitelist()
def sync_inventory(item_code=None, settings_name=None):
	"""
	Update stock levels between ERPNext and WooCommerce.

	Args:
		item_code: Specific item to sync, or None for all items
		settings_name: WooCommerce Settings document name

	Returns:
		dict: Sync results
	"""
	results = {
		'success': True,
		'synced': 0,
		'failed': 0,
		'errors': []
	}

	settings = get_settings(settings_name)
	if not settings or not settings.sync_inventory:
		results['success'] = False
		results['message'] = _("Inventory sync is disabled")
		return results

	try:
		if item_code:
			# Sync single item
			_sync_single_item_inventory(item_code, settings, results)
		else:
			# Sync all items with stock sync enabled
			products = frappe.get_all(
				'WooCommerce Product',
				filters={
					'stock_sync': 1,
					'item_code': ['is', 'set']
				},
				fields=['name', 'item_code', 'wc_product_id']
			)

			for product in products:
				_sync_single_item_inventory(product.item_code, settings, results)

	except Exception as e:
		results['success'] = False
		results['message'] = str(e)
		frappe.log_error(
			title="WooCommerce Inventory Sync Error",
			message=f"{str(e)}\n\n{traceback.format_exc()}"
		)

	return results


def _sync_single_item_inventory(item_code, settings, results):
	"""Sync inventory for a single item."""
	from ricco_woocommerce.doctype.woocommerce_product.woocommerce_product import get_product_by_item_code

	product = get_product_by_item_code(item_code)

	if not product:
		return

	# Get ERPNext stock
	if settings.default_warehouse:
		from erpnext.stock.utils import get_stock_balance
		stock = get_stock_balance(item_code, settings.default_warehouse)
	else:
		stock = 0

	product.stock_quantity = stock
	product.save()

	# Sync to WooCommerce based on direction
	direction = settings.inventory_sync_direction

	if direction in ['to_wc', 'both']:
		try:
			product.sync_stock_to_wc()
			results['synced'] += 1
		except Exception as e:
			results['failed'] += 1
			results['errors'].append({
				'item': item_code,
				'error': str(e)
			})


# ======== ORDER STATUS SYNC ========

@frappe.whitelist()
def sync_order_status(order_name, status):
	"""
	Update WooCommerce order status.

	Args:
		order_name: ERPNext Sales Order name
		status: New WooCommerce status

	Returns:
		dict: Sync result
	"""
	result = {
		'success': False,
		'message': ''
	}

	# Get WooCommerce Order record
	wc_order_name = frappe.db.get_value(
		'WooCommerce Order',
		{'erpnext_order': order_name}
	)

	if not wc_order_name:
		result['message'] = _("No WooCommerce Order found for this Sales Order")
		return result

	wc_order = frappe.get_doc('WooCommerce Order', wc_order_name)
	settings = get_settings(wc_order.woocommerce_settings)

	if not settings:
		result['message'] = _("WooCommerce Settings not found")
		return result

	try:
		wcapi = get_wc_api_client(settings.name)

		response = wcapi.put(f"orders/{wc_order.wc_order_id}", {
			'status': status
		})

		if response.status_code == 200:
			wc_order.status = status
			wc_order.save()
			result['success'] = True
			result['message'] = _("Order status updated successfully")
		else:
			result['message'] = f"API Error: {response.text}"

	except Exception as e:
		result['message'] = str(e)
		frappe.log_error(
			title="WooCommerce Order Status Update Error",
			message=f"{str(e)}\n\n{traceback.format_exc()}"
		)

	return result


# ======== WEBHOOK PROCESSING ========

@frappe.whitelist()
def process_webhook(topic, payload):
	"""
	Handle webhook events from WooCommerce.

	Args:
		topic: Webhook topic (e.g., order.created, product.updated)
		payload: Webhook payload data

	Returns:
		dict: Processing result
	"""
	result = {
		'success': False,
		'message': '',
		'doctype': None,
		'docname': None
	}

	if isinstance(payload, str):
		payload = json.loads(payload)

	try:
		resource, event = topic.split('.')

		if resource == 'order':
			result = _process_order_webhook(event, payload)
		elif resource == 'product':
			result = _process_product_webhook(event, payload)
		elif resource == 'customer':
			result = _process_customer_webhook(event, payload)
		else:
			result['message'] = f"Unsupported webhook resource: {resource}"

	except Exception as e:
		result['error'] = str(e)
		result['details'] = {'traceback': frappe.get_traceback()}
		frappe.log_error(
			title=f"WooCommerce Webhook Processing Error: {topic}",
			message=f"{str(e)}\n\nPayload: {json.dumps(payload, indent=2)}\n\n{traceback.format_exc()}"
		)

	return result


def _process_order_webhook(event, payload):
	"""Process order webhook events."""
	result = {'success': False, 'message': ''}

	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	settings = get_settings(settings_name)

	if event in ['created', 'updated']:
		# Import/update order
		sync_result = _import_wc_order(payload, settings)
		result['success'] = True
		result['message'] = f"Order {event} successfully"
		result['doctype'] = 'Sales Order'
		result['docname'] = sync_result.get('so_name')

	elif event == 'deleted':
		# Mark order as cancelled
		from ricco_woocommerce.doctype.woocommerce_order.woocommerce_order import get_order_by_wc_id

		wc_order = get_order_by_wc_id(str(payload.get('id')))

		if wc_order:
			wc_order.status = 'cancelled'
			wc_order.save()

			if wc_order.erpnext_order:
				so = frappe.get_doc('Sales Order', wc_order.erpnext_order)
				if so.docstatus == 1:
					so.cancel()

		result['success'] = True
		result['message'] = "Order marked as cancelled"

	elif event == 'restored':
		# Re-import order
		sync_result = _import_wc_order(payload, settings)
		result['success'] = True
		result['message'] = "Order restored successfully"

	return result


def _process_product_webhook(event, payload):
	"""Process product webhook events."""
	result = {'success': False, 'message': ''}

	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	settings = get_settings(settings_name)

	if event in ['created', 'updated']:
		# Import/update product
		from ricco_woocommerce.doctype.woocommerce_product.woocommerce_product import create_or_update_product

		wc_product = create_or_update_product(payload, settings_name)

		# Create/update ERPNext Item
		item_result = _create_or_update_item_from_wc(payload, settings)

		if not wc_product.item_code:
			wc_product.item_code = item_result['item_code']
			wc_product.save()

		wc_product.mark_synced()

		result['success'] = True
		result['message'] = f"Product {event} successfully"
		result['doctype'] = 'Item'
		result['docname'] = item_result['item_code']

	elif event == 'deleted':
		# Mark product as inactive
		from ricco_woocommerce.doctype.woocommerce_product.woocommerce_product import get_product_by_wc_id

		wc_product = get_product_by_wc_id(str(payload.get('id')))

		if wc_product and wc_product.item_code:
			item = frappe.get_doc('Item', wc_product.item_code)
			item.disabled = 1
			item.save()

		result['success'] = True
		result['message'] = "Product marked as inactive"

	return result


def _process_customer_webhook(event, payload):
	"""Process customer webhook events."""
	result = {'success': False, 'message': ''}

	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	settings = get_settings(settings_name)

	if event in ['created', 'updated']:
		# Import/update customer
		from ricco_woocommerce.doctype.woocommerce_customer.woocommerce_customer import create_or_update_customer

		wc_customer = create_or_update_customer(payload, settings_name)

		# Create/update ERPNext Customer
		if not wc_customer.customer:
			customer = wc_customer.create_erpnext_customer()
		else:
			customer = frappe.get_doc('Customer', wc_customer.customer)

		wc_customer.mark_synced(customer.name if customer else None)

		result['success'] = True
		result['message'] = f"Customer {event} successfully"
		result['doctype'] = 'Customer'
		result['docname'] = wc_customer.customer

	elif event == 'deleted':
		# Mark customer as inactive
		from ricco_woocommerce.doctype.woocommerce_customer.woocommerce_customer import get_customer_by_wc_id

		wc_customer = get_customer_by_wc_id(str(payload.get('id')))

		if wc_customer and wc_customer.customer:
			customer = frappe.get_doc('Customer', wc_customer.customer)
			customer.disabled = 1
			customer.save()

		result['success'] = True
		result['message'] = "Customer marked as inactive"

	return result


# ======== SCHEDULED JOBS ========

def process_webhook_queue():
	"""Process pending webhook logs."""
	pending_logs = frappe.get_all(
		'WooCommerce Webhook Log',
		filters={'status': 'Received'},
		fields=['name'],
		limit=50
	)

	for log in pending_logs:
		from ricco_woocommerce.doctype.woocommerce_webhook_log.woocommerce_webhook_log import process_webhook_log
		process_webhook_log(log.name)


def sync_pending_orders():
	"""Sync orders pending synchronization."""
	pending_orders = frappe.get_all(
		'WooCommerce Order',
		filters={'sync_status': 'Pending'},
		fields=['name'],
		limit=50
	)

	for order in pending_orders:
		try:
			sync_single_order(order.name)
		except Exception as e:
			frappe.log_error(f"Failed to sync order {order.name}: {str(e)}")


def sync_pending_customers():
	"""Sync customers pending synchronization."""
	pending_customers = frappe.get_all(
		'WooCommerce Customer',
		filters={'sync_status': 'Pending'},
		fields=['name'],
		limit=50
	)

	from ricco_woocommerce.doctype.woocommerce_customer.woocommerce_customer import WooCommerceCustomer

	for customer in pending_customers:
		try:
			wc_customer = frappe.get_doc('WooCommerce Customer', customer.name)
			if not wc_customer.customer:
				wc_customer.create_erpnext_customer()
			wc_customer.mark_synced()
		except Exception as e:
			frappe.log_error(f"Failed to sync customer {customer.name}: {str(e)}")


def retry_failed_syncs():
	"""Retry failed sync operations."""
	# Retry failed orders
	failed_orders = frappe.get_all(
		'WooCommerce Order',
		filters={'sync_status': 'Failed'},
		fields=['name'],
		limit=20
	)

	for order in failed_orders:
		try:
			sync_single_order(order.name)
		except Exception as e:
			frappe.log_error(f"Retry failed for order {order.name}: {str(e)}")

	# Retry failed customers
	failed_customers = frappe.get_all(
		'WooCommerce Customer',
		filters={'sync_status': 'Failed'},
		fields=['name'],
		limit=20
	)

	for customer in failed_customers:
		try:
			wc_customer = frappe.get_doc('WooCommerce Customer', customer.name)
			if not wc_customer.customer:
				wc_customer.create_erpnext_customer()
			wc_customer.mark_synced()
		except Exception as e:
			frappe.log_error(f"Retry failed for customer {customer.name}: {str(e)}")


def sync_all_products():
	"""Scheduled job to sync all products."""
	settings = get_settings()
	if settings and settings.sync_products:
		sync_products(direction="both", limit=500)


def sync_all_inventory():
	"""Scheduled job to sync all inventory."""
	settings = get_settings()
	if settings and settings.sync_inventory:
		sync_inventory()


def sync_all_customers():
	"""Scheduled job to sync all customers."""
	settings = get_settings()
	if settings and settings.sync_customers:
		sync_customers(limit=500)


def cleanup_old_logs():
	"""Cleanup old webhook logs."""
	from ricco_woocommerce.doctype.woocommerce_webhook_log.woocommerce_webhook_log import cleanup_old_logs

	settings = get_settings()
	days = 30
	if settings:
		days = getattr(settings, 'log_retention_days', 30)

	cleanup_old_logs(days)


# ======== UTILITY FUNCTIONS ========

@frappe.whitelist()
def get_sync_status(doctype=None):
	"""Get overall sync status."""
	status = {
		'products': {
			'total': frappe.db.count('WooCommerce Product'),
			'synced': frappe.db.count('WooCommerce Product', {'sync_status': 'Synced'}),
			'pending': frappe.db.count('WooCommerce Product', {'sync_status': 'Pending'}),
			'failed': frappe.db.count('WooCommerce Product', {'sync_status': 'Failed'})
		},
		'orders': {
			'total': frappe.db.count('WooCommerce Order'),
			'synced': frappe.db.count('WooCommerce Order', {'sync_status': 'Synced'}),
			'pending': frappe.db.count('WooCommerce Order', {'sync_status': 'Pending'}),
			'failed': frappe.db.count('WooCommerce Order', {'sync_status': 'Failed'})
		},
		'customers': {
			'total': frappe.db.count('WooCommerce Customer'),
			'synced': frappe.db.count('WooCommerce Customer', {'sync_status': 'Synced'}),
			'pending': frappe.db.count('WooCommerce Customer', {'sync_status': 'Pending'}),
			'failed': frappe.db.count('WooCommerce Customer', {'sync_status': 'Failed'})
		}
	}

	return status


@frappe.whitelist()
def manual_sync(sync_type, direction=None, limit=100):
	"""Trigger manual sync from UI."""
	if sync_type == 'products':
		return sync_products(direction=direction or 'both', limit=limit)
	elif sync_type == 'orders':
		return sync_orders(limit=limit)
	elif sync_type == 'customers':
		return sync_customers(limit=limit)
	elif sync_type == 'inventory':
		return sync_inventory()
	else:
		return {'success': False, 'message': f"Unknown sync type: {sync_type}"}


@frappe.whitelist()
def test_connection(settings_name=None):
	"""Test WooCommerce API connection."""
	try:
		settings = get_settings(settings_name)
		if not settings:
			return {'success': False, 'message': 'No active WooCommerce Settings found'}

		wcapi = get_wc_api_client(settings.name)
		response = wcapi.get('system_status')

		if response.status_code == 200:
			data = response.json()
			return {
				'success': True,
				'message': 'Connection successful',
				'store_info': {
					'version': data.get('environment', {}).get('version'),
					'wc_version': data.get('environment', {}).get('woocommerce_version'),
					'site_name': data.get('environment', {}).get('site_name')
				}
			}
		else:
			return {
				'success': False,
				'message': f"API Error: {response.text}"
			}

	except Exception as e:
		return {
			'success': False,
			'message': str(e)
		}
