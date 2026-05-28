# -*- coding: utf-8 -*-
"""
Uninstallation functions for Ricco WooCommerce Integration
"""

import frappe
from frappe import _


def before_uninstall():
	"""
	Actions to perform before app uninstallation.
	"""
	remove_custom_fields()
	frappe.msgprint(_("WooCommerce custom fields have been removed"))


def remove_custom_fields():
	"""
	Remove custom fields created by the app.
	"""
	custom_field_prefixes = [
		'sync_to_woocommerce',
		'woocommerce_product',
		'woocommerce_customer',
		'woocommerce_order',
		'wc_order_id',
		'woocommerce_section'
	]

	for prefix in custom_field_prefixes:
		frappe.db.delete('Custom Field', {
			'fieldname': prefix
		})

	frappe.db.commit()
