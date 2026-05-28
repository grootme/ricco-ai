# -*- coding: utf-8 -*-
# Copyright (c) 2024, Ricco and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime
import json


class WooCommerceOrder(Document):
	"""WooCommerce Order DocType for tracking order synchronization."""

	def validate(self):
		"""Validate the WooCommerce Order document."""
		self.validate_wc_order_id()
		self.update_modified_at()

	def before_save(self):
		"""Actions before saving the document."""
		if self.is_new():
			self.created_at = datetime.now()
		self.modified_at = datetime.now()

	def validate_wc_order_id(self):
		"""Validate WooCommerce Order ID is unique."""
		if self.wc_order_id:
			existing = frappe.db.exists(
				'WooCommerce Order',
				{
					'wc_order_id': self.wc_order_id,
					'name': ['!=', self.name]
				}
			)
			if existing:
				frappe.throw(
					_("WooCommerce Order with ID {0} already exists").format(self.wc_order_id)
				)

	def update_modified_at(self):
		"""Update the modified timestamp."""
		self.modified_at = datetime.now()

	def mark_synced(self, erpnext_order=None):
		"""Mark order as synced successfully."""
		self.sync_status = 'Synced'
		self.last_sync_at = datetime.now()
		self.sync_attempts = (self.sync_attempts or 0) + 1
		self.sync_error = None
		self.last_sync_error = None

		if erpnext_order:
			self.erpnext_order = erpnext_order

		self.save()
		frappe.db.commit()

	def mark_failed(self, error_message):
		"""Mark order sync as failed with error message."""
		self.sync_status = 'Failed'
		self.sync_attempts = (self.sync_attempts or 0) + 1
		self.sync_error = error_message
		self.last_sync_error = error_message
		self.last_sync_at = datetime.now()

		self.save()
		frappe.db.commit()

		# Log error if enabled
		settings = frappe.get_single('WooCommerce Settings')
		if settings.enable_error_logging:
			frappe.log_error(
				title=f"WooCommerce Order Sync Failed: {self.wc_order_id}",
				message=error_message
			)

	def mark_processing(self):
		"""Mark order as currently processing."""
		self.sync_status = 'Processing'
		self.save()
		frappe.db.commit()

	def add_webhook_event(self, event_data):
		"""Add webhook event to the order's event history."""
		events = []
		if self.webhook_events:
			try:
				events = json.loads(self.webhook_events)
			except:
				events = []

		events.append({
			'timestamp': datetime.now().isoformat(),
			'data': event_data
		})

		# Keep only last 50 events
		if len(events) > 50:
			events = events[-50:]

		self.webhook_events = json.dumps(events, indent=2)
		self.save()

	def can_retry(self):
		"""Check if sync can be retried."""
		settings = frappe.get_single('WooCommerce Settings')
		max_attempts = settings.max_retry_attempts or 3
		return self.sync_attempts < max_attempts

	def get_wc_order_data(self):
		"""Fetch order data from WooCommerce."""
		from ricco_woocommerce.api.sync_api import get_wc_api_client

		settings = self.woocommerce_settings or frappe.db.get_value(
			'WooCommerce Settings', {'is_active': 1}
		)
		wcapi = get_wc_api_client(settings)

		response = wcapi.get(f'orders/{self.wc_order_id}')

		if response.status_code == 200:
			return response.json()
		else:
			raise Exception(f"Failed to fetch order: {response.text}")

	def update_from_wc_data(self, wc_data):
		"""Update order from WooCommerce data."""
		self.status = wc_data.get('status', self.status)
		self.order_total = wc_data.get('total', self.order_total)
		self.currency = wc_data.get('currency', self.currency)
		self.payment_method = wc_data.get('payment_method', self.payment_method)
		self.payment_method_title = wc_data.get('payment_method_title', self.payment_method_title)
		self.order_date = wc_data.get('date_created', self.order_date)
		self.order_modified_date = wc_data.get('date_modified', self.order_modified_date)
		self.item_count = len(wc_data.get('line_items', []))

		# Update customer info
		billing = wc_data.get('billing', {})
		self.billing_first_name = billing.get('first_name')
		self.billing_last_name = billing.get('last_name')
		self.billing_email = billing.get('email')
		self.billing_phone = billing.get('phone')
		self.billing_address_1 = billing.get('address_1')
		self.billing_address_2 = billing.get('address_2')
		self.billing_city = billing.get('city')
		self.billing_state = billing.get('state')
		self.billing_postcode = billing.get('postcode')
		self.billing_country = billing.get('country')

		shipping = wc_data.get('shipping', {})
		self.shipping_first_name = shipping.get('first_name')
		self.shipping_last_name = shipping.get('last_name')
		self.shipping_address_1 = shipping.get('address_1')
		self.shipping_address_2 = shipping.get('address_2')
		self.shipping_city = shipping.get('city')
		self.shipping_state = shipping.get('state')
		self.shipping_postcode = shipping.get('postcode')
		self.shipping_country = shipping.get('country')

		self.save()


def get_order_by_wc_id(wc_order_id):
	"""Get WooCommerce Order by WooCommerce Order ID."""
	order_name = frappe.db.get_value(
		'WooCommerce Order',
		{'wc_order_id': wc_order_id}
	)
	if order_name:
		return frappe.get_doc('WooCommerce Order', order_name)
	return None


def create_or_update_order(wc_data, settings_name=None):
	"""Create or update WooCommerce Order from WooCommerce data."""
	wc_order_id = str(wc_data.get('id'))

	order = get_order_by_wc_id(wc_order_id)

	if not order:
		order = frappe.new_doc('WooCommerce Order')
		order.wc_order_id = wc_order_id

	order.woocommerce_settings = settings_name or frappe.db.get_value(
		'WooCommerce Settings', {'is_active': 1}
	)
	order.customer_name = wc_data.get('billing', {}).get('first_name', '') + ' ' + \
		wc_data.get('billing', {}).get('last_name', '')
	order.wc_customer_id = wc_data.get('customer_id')

	order.update_from_wc_data(wc_data)
	order.save()

	return order


@frappe.whitelist()
def get_sync_status(wc_order_id):
	"""Get sync status for a WooCommerce Order."""
	order = get_order_by_wc_id(wc_order_id)
	if order:
		return {
			'status': order.sync_status,
			'last_sync': order.last_sync_at,
			'attempts': order.sync_attempts,
			'error': order.sync_error
		}
	return None


@frappe.whitelist()
def retry_sync(wc_order_id):
	"""Retry synchronization for a failed order."""
	order = get_order_by_wc_id(wc_order_id)
	if not order:
		frappe.throw(_("WooCommerce Order not found"))

	if not order.can_retry():
		frappe.throw(_("Maximum retry attempts reached"))

	from ricco_woocommerce.api.sync_api import sync_single_order

	return sync_single_order(order.name)


@frappe.whitelist()
def get_pending_orders():
	"""Get all orders pending synchronization."""
	return frappe.get_all(
		'WooCommerce Order',
		filters={'sync_status': 'Pending'},
		fields=['name', 'wc_order_id', 'status', 'order_total', 'customer_name']
	)


@frappe.whitelist()
def get_failed_orders():
	"""Get all orders with failed synchronization."""
	return frappe.get_all(
		'WooCommerce Order',
		filters={'sync_status': 'Failed'},
		fields=['name', 'wc_order_id', 'status', 'sync_attempts', 'last_sync_error']
	)
