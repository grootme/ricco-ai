# -*- coding: utf-8 -*-
# Copyright (c) 2024, Ricco and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime
import json


class WooCommerceProduct(Document):
	"""WooCommerce Product DocType for tracking product synchronization."""

	def validate(self):
		"""Validate the WooCommerce Product document."""
		self.validate_wc_product_id()
		self.validate_sku()
		self.update_modified_at()

	def before_save(self):
		"""Actions before saving the document."""
		if self.is_new():
			self.created_at = datetime.now()
		self.modified_at = datetime.now()

	def validate_wc_product_id(self):
		"""Validate WooCommerce Product ID is unique."""
		if self.wc_product_id:
			existing = frappe.db.exists(
				'WooCommerce Product',
				{
					'wc_product_id': self.wc_product_id,
					'name': ['!=', self.name]
				}
			)
			if existing:
				frappe.throw(
					_("WooCommerce Product with ID {0} already exists").format(self.wc_product_id)
				)

	def validate_sku(self):
		"""Validate SKU matches ERPNext Item."""
		if self.item_code and not self.sku:
			self.sku = self.item_code

	def update_modified_at(self):
		"""Update the modified timestamp."""
		self.modified_at = datetime.now()

	def mark_synced(self):
		"""Mark product as synced successfully."""
		self.sync_status = 'Synced'
		self.last_sync_at = datetime.now()
		self.sync_attempts = (self.sync_attempts or 0) + 1
		self.last_sync_error = None

		self.save()
		frappe.db.commit()

	def mark_failed(self, error_message):
		"""Mark product sync as failed with error message."""
		self.sync_status = 'Failed'
		self.sync_attempts = (self.sync_attempts or 0) + 1
		self.last_sync_error = error_message
		self.last_sync_at = datetime.now()

		self.save()
		frappe.db.commit()

		# Log error if enabled
		settings = frappe.get_single('WooCommerce Settings')
		if settings.enable_error_logging:
			frappe.log_error(
				title=f"WooCommerce Product Sync Failed: {self.wc_product_id}",
				message=error_message
			)

	def mark_processing(self):
		"""Mark product as currently processing."""
		self.sync_status = 'Processing'
		self.save()
		frappe.db.commit()

	def update_from_wc_data(self, wc_data):
		"""Update product from WooCommerce data."""
		self.product_name = wc_data.get('name', self.product_name)
		self.sku = wc_data.get('sku', self.sku) or self.sku
		self.product_type = wc_data.get('type', self.product_type)
		self.manage_stock = 1 if wc_data.get('manage_stock') else 0
		self.stock_status = wc_data.get('stock_status', self.stock_status)
		self.backorders = wc_data.get('backorders', self.backorders)

		# Stock
		self.wc_stock_quantity = wc_data.get('stock_quantity', 0)

		# Prices
		self.wc_regular_price = wc_data.get('regular_price')
		self.wc_sale_price = wc_data.get('sale_price')

		# Dimensions
		dimensions = wc_data.get('dimensions', {})
		self.length = dimensions.get('length')
		self.width = dimensions.get('width')
		self.height = dimensions.get('height')
		self.weight = wc_data.get('weight')

		# Description
		self.product_description = wc_data.get('description')
		self.short_description = wc_data.get('short_description')

		# Categories
		categories = wc_data.get('categories', [])
		if categories:
			self.categories = json.dumps([c.get('name') for c in categories])

		# Image
		images = wc_data.get('images', [])
		if images:
			self.image_url = images[0].get('src')

		# Store raw data
		self.wc_data = json.dumps(wc_data, indent=2)

		self.save()

	def update_stock_from_erpnext(self, warehouse=None):
		"""Update stock quantity from ERPNext Item."""
		if not self.item_code:
			return

		if not warehouse:
			settings = frappe.get_single('WooCommerce Settings')
			warehouse = settings.default_warehouse

		if warehouse:
			from erpnext.stock.utils import get_stock_balance
			self.stock_quantity = get_stock_balance(self.item_code, warehouse)
			self.save()

	def sync_stock_to_wc(self):
		"""Sync stock quantity to WooCommerce."""
		if not self.stock_sync:
			return

		from ricco_woocommerce.api.sync_api import get_wc_api_client

		settings = self.woocommerce_settings or frappe.db.get_value(
			'WooCommerce Settings', {'is_active': 1}
		)
		wcapi = get_wc_api_client(settings)

		data = {
			'stock_quantity': self.stock_quantity,
			'manage_stock': True if self.manage_stock else False,
			'stock_status': 'instock' if self.stock_quantity > 0 else 'outofstock'
		}

		response = wcapi.put(f'products/{self.wc_product_id}', data)

		if response.status_code == 200:
			self.wc_stock_quantity = self.stock_quantity
			self.last_stock_sync = datetime.now()
			self.save()
			return True
		else:
			raise Exception(f"Failed to update stock: {response.text}")

	def sync_price_to_wc(self):
		"""Sync price to WooCommerce."""
		if not self.price_sync:
			return

		from ricco_woocommerce.api.sync_api import get_wc_api_client

		settings = self.woocommerce_settings or frappe.db.get_value(
			'WooCommerce Settings', {'is_active': 1}
		)
		wcapi = get_wc_api_client(settings)

		data = {
			'regular_price': str(self.regular_price) if self.regular_price else '',
			'sale_price': str(self.sale_price) if self.sale_price else ''
		}

		response = wcapi.put(f'products/{self.wc_product_id}', data)

		if response.status_code == 200:
			self.wc_regular_price = self.regular_price
			self.wc_sale_price = self.sale_price
			self.last_price_sync = datetime.now()
			self.save()
			return True
		else:
			raise Exception(f"Failed to update price: {response.text}")

	def can_retry(self):
		"""Check if sync can be retried."""
		settings = frappe.get_single('WooCommerce Settings')
		max_attempts = settings.max_retry_attempts or 3
		return self.sync_attempts < max_attempts


def get_product_by_wc_id(wc_product_id):
	"""Get WooCommerce Product by WooCommerce Product ID."""
	product_name = frappe.db.get_value(
		'WooCommerce Product',
		{'wc_product_id': wc_product_id}
	)
	if product_name:
		return frappe.get_doc('WooCommerce Product', product_name)
	return None


def get_product_by_sku(sku):
	"""Get WooCommerce Product by SKU."""
	product_name = frappe.db.get_value(
		'WooCommerce Product',
		{'sku': sku}
	)
	if product_name:
		return frappe.get_doc('WooCommerce Product', product_name)
	return None


def get_product_by_item_code(item_code):
	"""Get WooCommerce Product by ERPNext Item Code."""
	product_name = frappe.db.get_value(
		'WooCommerce Product',
		{'item_code': item_code}
	)
	if product_name:
		return frappe.get_doc('WooCommerce Product', product_name)
	return None


def create_or_update_product(wc_data, settings_name=None):
	"""Create or update WooCommerce Product from WooCommerce data."""
	wc_product_id = str(wc_data.get('id'))

	product = get_product_by_wc_id(wc_product_id)

	if not product:
		# Try to find by SKU
		sku = wc_data.get('sku')
		if sku:
			product = get_product_by_sku(sku)

	if not product:
		product = frappe.new_doc('WooCommerce Product')
		product.wc_product_id = wc_product_id

	product.woocommerce_settings = settings_name or frappe.db.get_value(
		'WooCommerce Settings', {'is_active': 1}
	)
	product.sku = wc_data.get('sku') or product.sku

	product.update_from_wc_data(wc_data)
	product.save()

	return product


@frappe.whitelist()
def get_sync_status(wc_product_id):
	"""Get sync status for a WooCommerce Product."""
	product = get_product_by_wc_id(wc_product_id)
	if product:
		return {
			'status': product.sync_status,
			'last_sync': product.last_sync_at,
			'attempts': product.sync_attempts,
			'error': product.last_sync_error,
			'stock': {
				'erpnext': product.stock_quantity,
				'wc': product.wc_stock_quantity,
				'last_sync': product.last_stock_sync
			}
		}
	return None


@frappe.whitelist()
def sync_stock(wc_product_id):
	"""Manually sync stock for a product."""
	product = get_product_by_wc_id(wc_product_id)
	if not product:
		frappe.throw(_("WooCommerce Product not found"))

	product.update_stock_from_erpnext()
	return product.sync_stock_to_wc()


@frappe.whitelist()
def get_pending_products():
	"""Get all products pending synchronization."""
	return frappe.get_all(
		'WooCommerce Product',
		filters={'sync_status': 'Pending'},
		fields=['name', 'wc_product_id', 'sku', 'product_name']
	)


@frappe.whitelist()
def get_products_with_stock_changes():
	"""Get products with stock changes to sync."""
	products = frappe.get_all(
		'WooCommerce Product',
		filters={
			'stock_sync': 1,
			'sync_stock_on_update': 1
		},
		fields=['name', 'wc_product_id', 'item_code', 'stock_quantity', 'wc_stock_quantity']
	)

	changed_products = []
	for p in products:
		if p.stock_quantity != p.wc_stock_quantity:
			changed_products.append(p)

	return changed_products
