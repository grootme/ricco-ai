# -*- coding: utf-8 -*-
# Copyright (c) 2024, Ricco and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import requests
import json
from datetime import datetime


class WooCommerceSettings(Document):
	"""WooCommerce Settings DocType for managing store configuration and sync settings."""

	def validate(self):
		"""Validate WooCommerce settings before saving."""
		self.validate_store_url()
		self.validate_api_credentials()
		self.validate_default_values()
		self.validate_webhook_settings()

	def on_update(self):
		"""Actions to perform when settings are updated."""
		self.clear_cache()
		if self.enable_webhooks and self.is_active:
			self.register_webhooks()

	def validate_store_url(self):
		"""Validate and normalize the store URL."""
		if self.store_url:
			# Remove trailing slash
			self.store_url = self.store_url.rstrip('/')
			# Ensure URL has protocol
			if not self.store_url.startswith(('http://', 'https://')):
				self.store_url = 'https://' + self.store_url

	def validate_api_credentials(self):
		"""Validate API credentials by making a test request."""
		if self.is_active and self.consumer_key and self.consumer_secret:
			try:
				self.test_connection()
			except Exception as e:
				frappe.msgprint(
					_("Warning: Could not validate API credentials: {0}").format(str(e)),
					indicator='yellow'
				)

	def validate_default_values(self):
		"""Validate default values are set for required fields."""
		if self.sync_orders:
			if not self.default_warehouse:
				frappe.msgprint(
					_("Warning: Default Warehouse is recommended for order sync"),
					indicator='yellow'
				)
			if not self.default_price_list:
				frappe.msgprint(
					_("Warning: Default Price List is recommended for order sync"),
					indicator='yellow'
				)

	def validate_webhook_settings(self):
		"""Validate webhook configuration."""
		if self.enable_webhooks:
			if not self.webhook_secret:
				frappe.throw(_("Webhook Secret is required when webhooks are enabled"))

	def get_api_client(self):
		"""Get WooCommerce API client instance."""
		from woocommerce import API

		return API(
			url=self.store_url,
			consumer_key=self.get_password('consumer_key'),
			consumer_secret=self.get_password('consumer_secret'),
			version=self.api_version,
			timeout=self.timeout,
			verify_ssl=self.verify_ssl
		)

	def test_connection(self):
		"""Test connection to WooCommerce store."""
		wcapi = self.get_api_client()
		response = wcapi.get('system_status')

		if response.status_code != 200:
			raise Exception(_("Failed to connect to WooCommerce: {0}").format(
				response.text
			))

		return response.json()

	def register_webhooks(self):
		"""Register webhooks with WooCommerce store."""
		wcapi = self.get_api_client()
		webhook_url = self.webhook_delivery_url or self.get_default_webhook_url()

		webhooks_to_register = [
			{
				"name": "Order Created",
				"topic": "order.created",
				"delivery_url": webhook_url,
				"secret": self.get_password('webhook_secret')
			},
			{
				"name": "Order Updated",
				"topic": "order.updated",
				"delivery_url": webhook_url,
				"secret": self.get_password('webhook_secret')
			},
			{
				"name": "Order Deleted",
				"topic": "order.deleted",
				"delivery_url": webhook_url,
				"secret": self.get_password('webhook_secret')
			},
			{
				"name": "Product Created",
				"topic": "product.created",
				"delivery_url": webhook_url,
				"secret": self.get_password('webhook_secret')
			},
			{
				"name": "Product Updated",
				"topic": "product.updated",
				"delivery_url": webhook_url,
				"secret": self.get_password('webhook_secret')
			},
			{
				"name": "Customer Created",
				"topic": "customer.created",
				"delivery_url": webhook_url,
				"secret": self.get_password('webhook_secret')
			},
			{
				"name": "Customer Updated",
				"topic": "customer.updated",
				"delivery_url": webhook_url,
				"secret": self.get_password('webhook_secret')
			}
		]

		for webhook_data in webhooks_to_register:
			try:
				wcapi.post('webhooks', webhook_data)
			except Exception as e:
				if self.debug_mode:
					frappe.log_error(
						f"Failed to register webhook {webhook_data['name']}: {str(e)}",
						"WooCommerce Webhook Registration"
					)

	def get_default_webhook_url(self):
		"""Get default webhook URL for this site."""
		site_url = frappe.utils.get_url()
		return f"{site_url}/api/method/ricco_woocommerce.api.webhook_handler.handle_webhook"

	def clear_cache(self):
		"""Clear cached settings."""
		frappe.cache().delete_key('woocommerce_settings')

	@staticmethod
	def get_settings():
		"""Get WooCommerce settings from cache or database."""
		settings = frappe.cache().get_value('woocommerce_settings')
		if settings is None:
			settings = frappe.get_single('WooCommerce Settings')
			frappe.cache().set_value('woocommerce_settings', settings, expires_in_sec=3600)
		return settings

	def get_order_status_mapping(self):
		"""Get order status mapping as dictionary."""
		mapping = {}
		if self.order_status_mapping:
			for row in self.order_status_mapping:
				mapping[row.woocommerce_status] = row.erpnext_status
		return mapping

	def get_multi_store_mapping(self):
		"""Get multi-store mapping if enabled."""
		if not self.enable_multi_store:
			return None

		mapping = {}
		if self.multi_store_mapping:
			for row in self.multi_store_mapping:
				mapping[row.store_id] = {
					'warehouse': row.warehouse,
					'price_list': row.price_list,
					'cost_center': row.cost_center
				}
		return mapping


@frappe.whitelist()
def test_woocommerce_connection(settings_name=None):
	"""Test WooCommerce connection from UI."""
	if not settings_name:
		settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})

	if not settings_name:
		frappe.throw(_("No active WooCommerce Settings found"))

	settings = frappe.get_doc('WooCommerce Settings', settings_name)
	result = settings.test_connection()

	return {
		'success': True,
		'message': _("Connection successful"),
		'store_info': {
			'version': result.get('environment', {}).get('version', 'Unknown'),
			'wc_version': result.get('environment', {}).get('woocommerce_version', 'Unknown')
		}
	}


@frappe.whitelist()
def get_active_settings():
	"""Get all active WooCommerce settings for multi-store support."""
	settings_list = frappe.get_all(
		'WooCommerce Settings',
		filters={'is_active': 1},
		fields=['name', 'store_name', 'store_url']
	)
	return settings_list


def get_default_settings():
	"""Get default (first active) WooCommerce settings."""
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if settings_name:
		return frappe.get_doc('WooCommerce Settings', settings_name)
	return None
