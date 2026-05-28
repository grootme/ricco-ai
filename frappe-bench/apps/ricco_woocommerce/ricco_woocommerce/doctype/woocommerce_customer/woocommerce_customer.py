# -*- coding: utf-8 -*-
# Copyright (c) 2024, Ricco and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime
import json


class WooCommerceCustomer(Document):
	"""WooCommerce Customer DocType for tracking customer synchronization."""

	def validate(self):
		"""Validate the WooCommerce Customer document."""
		self.validate_wc_customer_id()
		self.validate_email()
		self.update_modified_at()

	def before_save(self):
		"""Actions before saving the document."""
		if self.is_new():
			self.created_at = datetime.now()
		self.modified_at = datetime.now()

	def validate_wc_customer_id(self):
		"""Validate WooCommerce Customer ID is unique."""
		if self.wc_customer_id:
			existing = frappe.db.exists(
				'WooCommerce Customer',
				{
					'wc_customer_id': self.wc_customer_id,
					'name': ['!=', self.name]
				}
			)
			if existing:
				frappe.throw(
					_("WooCommerce Customer with ID {0} already exists").format(self.wc_customer_id)
				)

	def validate_email(self):
		"""Validate email format."""
		if self.email:
			from frappe.utils import validate_email_address
			validate_email_address(self.email, throw=True)

	def update_modified_at(self):
		"""Update the modified timestamp."""
		self.modified_at = datetime.now()

	def mark_synced(self, customer=None):
		"""Mark customer as synced successfully."""
		self.sync_status = 'Synced'
		self.last_sync_at = datetime.now()
		self.sync_attempts = (self.sync_attempts or 0) + 1
		self.sync_error = None
		self.last_sync_error = None

		if customer:
			self.customer = customer

		self.save()
		frappe.db.commit()

	def mark_failed(self, error_message):
		"""Mark customer sync as failed with error message."""
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
				title=f"WooCommerce Customer Sync Failed: {self.wc_customer_id}",
				message=error_message
			)

	def mark_processing(self):
		"""Mark customer as currently processing."""
		self.sync_status = 'Processing'
		self.save()
		frappe.db.commit()

	def update_from_wc_data(self, wc_data):
		"""Update customer from WooCommerce data."""
		self.first_name = wc_data.get('first_name', self.first_name)
		self.last_name = wc_data.get('last_name', self.last_name)
		self.email = wc_data.get('email', self.email)
		self.username = wc_data.get('username', self.username)
		self.phone = wc_data.get('phone') or wc_data.get('billing', {}).get('phone')
		self.date_created = wc_data.get('date_created', self.date_created)
		self.date_modified = wc_data.get('date_modified', self.date_modified)

		# Billing address
		billing = wc_data.get('billing', {})
		if billing:
			self.billing_first_name = billing.get('first_name')
			self.billing_last_name = billing.get('last_name')
			self.billing_company = billing.get('company')
			self.billing_address_1 = billing.get('address_1')
			self.billing_address_2 = billing.get('address_2')
			self.billing_city = billing.get('city')
			self.billing_state = billing.get('state')
			self.billing_postcode = billing.get('postcode')
			self.billing_country = billing.get('country')
			self.billing_phone = billing.get('phone')
			self.billing_email = billing.get('email')

		# Shipping address
		shipping = wc_data.get('shipping', {})
		if shipping:
			self.shipping_first_name = shipping.get('first_name')
			self.shipping_last_name = shipping.get('last_name')
			self.shipping_company = shipping.get('company')
			self.shipping_address_1 = shipping.get('address_1')
			self.shipping_address_2 = shipping.get('address_2')
			self.shipping_city = shipping.get('city')
			self.shipping_state = shipping.get('state')
			self.shipping_postcode = shipping.get('postcode')
			self.shipping_country = shipping.get('country')
			self.shipping_phone = shipping.get('phone')

		# Statistics
		stats = wc_data.get('orders_count', 0)
		self.total_orders = stats
		self.total_spent = wc_data.get('total_spent', 0)
		if self.total_orders > 0 and self.total_spent:
			self.average_order_value = float(self.total_spent) / self.total_orders

		self.save()

	def get_full_name(self):
		"""Get customer full name."""
		return f"{self.first_name or ''} {self.last_name or ''}".strip()

	def create_erpnext_customer(self):
		"""Create ERPNext Customer from WooCommerce Customer data."""
		if self.customer:
			return frappe.get_doc('Customer', self.customer)

		settings = frappe.get_single('WooCommerce Settings')

		# Create new customer
		customer = frappe.new_doc('Customer')
		customer.customer_name = self.get_full_name() or self.email or f"WC Customer {self.wc_customer_id}"
		customer.customer_type = 'Individual'
		customer.customer_group = settings.default_customer_group or frappe.db.get_value('Customer Group', {'is_group': 0})
		customer.territory = settings.default_territory or frappe.db.get_value('Territory', {'is_group': 0})
		customer.email_id = self.email
		customer.mobile_no = self.phone

		# Add customer address
		if self.billing_address_1 or self.billing_city:
			address = frappe.new_doc('Address')
			address.address_title = customer.customer_name
			address.address_type = 'Billing'
			address.address_line1 = self.billing_address_1
			address.address_line2 = self.billing_address_2
			address.city = self.billing_city
			address.state = self.billing_state
			address.pincode = self.billing_postcode
			address.country = self.billing_country
			address.phone = self.billing_phone
			address.email_id = self.billing_email or self.email
			address.append('links', {
				'link_doctype': 'Customer',
				'link_name': customer.name
			})
			address.insert()

		# Add shipping address if different
		if self.shipping_address_1 and self.shipping_address_1 != self.billing_address_1:
			shipping_address = frappe.new_doc('Address')
			shipping_address.address_title = f"{customer.customer_name} - Shipping"
			shipping_address.address_type = 'Shipping'
			shipping_address.address_line1 = self.shipping_address_1
			shipping_address.address_line2 = self.shipping_address_2
			shipping_address.city = self.shipping_city
			shipping_address.state = self.shipping_state
			shipping_address.pincode = self.shipping_postcode
			shipping_address.country = self.shipping_country
			shipping_address.phone = self.shipping_phone
			shipping_address.append('links', {
				'link_doctype': 'Customer',
				'link_name': customer.name
			})
			shipping_address.insert()

		customer.insert()

		self.customer = customer.name
		self.save()

		return customer

	def can_retry(self):
		"""Check if sync can be retried."""
		settings = frappe.get_single('WooCommerce Settings')
		max_attempts = settings.max_retry_attempts or 3
		return self.sync_attempts < max_attempts


def get_customer_by_wc_id(wc_customer_id):
	"""Get WooCommerce Customer by WooCommerce Customer ID."""
	customer_name = frappe.db.get_value(
		'WooCommerce Customer',
		{'wc_customer_id': wc_customer_id}
	)
	if customer_name:
		return frappe.get_doc('WooCommerce Customer', customer_name)
	return None


def get_customer_by_email(email):
	"""Get WooCommerce Customer by email."""
	customer_name = frappe.db.get_value(
		'WooCommerce Customer',
		{'email': email}
	)
	if customer_name:
		return frappe.get_doc('WooCommerce Customer', customer_name)
	return None


def get_customer_by_erpnext_customer(customer_name):
	"""Get WooCommerce Customer by ERPNext Customer."""
	wc_customer_name = frappe.db.get_value(
		'WooCommerce Customer',
		{'customer': customer_name}
	)
	if wc_customer_name:
		return frappe.get_doc('WooCommerce Customer', wc_customer_name)
	return None


def create_or_update_customer(wc_data, settings_name=None):
	"""Create or update WooCommerce Customer from WooCommerce data."""
	wc_customer_id = str(wc_data.get('id'))

	customer = get_customer_by_wc_id(wc_customer_id)

	if not customer:
		# Try to find by email
		email = wc_data.get('email')
		if email:
			customer = get_customer_by_email(email)

	if not customer:
		customer = frappe.new_doc('WooCommerce Customer')
		customer.wc_customer_id = wc_customer_id

	customer.woocommerce_settings = settings_name or frappe.db.get_value(
		'WooCommerce Settings', {'is_active': 1}
	)

	customer.update_from_wc_data(wc_data)
	customer.save()

	return customer


@frappe.whitelist()
def get_sync_status(wc_customer_id):
	"""Get sync status for a WooCommerce Customer."""
	customer = get_customer_by_wc_id(wc_customer_id)
	if customer:
		return {
			'status': customer.sync_status,
			'last_sync': customer.last_sync_at,
			'attempts': customer.sync_attempts,
			'error': customer.sync_error,
			'erpnext_customer': customer.customer
		}
	return None


@frappe.whitelist()
def get_pending_customers():
	"""Get all customers pending synchronization."""
	return frappe.get_all(
		'WooCommerce Customer',
		filters={'sync_status': 'Pending'},
		fields=['name', 'wc_customer_id', 'email', 'first_name', 'last_name']
	)


@frappe.whitelist()
def get_customers_without_erpnext():
	"""Get WooCommerce customers without ERPNext customer link."""
	return frappe.get_all(
		'WooCommerce Customer',
		filters={'customer': ['is', 'not set']},
		fields=['name', 'wc_customer_id', 'email', 'first_name', 'last_name']
	)
