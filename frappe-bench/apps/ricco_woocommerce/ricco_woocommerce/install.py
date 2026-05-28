# -*- coding: utf-8 -*-
"""
Installation functions for Ricco WooCommerce Integration
"""

import frappe
from frappe import _


def after_install():
	"""
	Actions to perform after app installation.
	"""
	create_default_woocommerce_settings()
	create_custom_fields()
	create_order_status_mapping_child_table()
	create_multi_store_mapping_child_table()


def after_migrate():
	"""
	Actions to perform after migration.
	"""
	# Ensure custom fields exist
	create_custom_fields()


def create_default_woocommerce_settings():
	"""
	Create default WooCommerce Settings if not exists.
	"""
	if not frappe.db.exists('WooCommerce Settings', 'Default'):
		settings = frappe.new_doc('WooCommerce Settings')
		settings.store_name = 'Default Store'
		settings.is_active = 0
		settings.insert()


def create_custom_fields():
	"""
	Create custom fields in ERPNext DocTypes for WooCommerce integration.
	"""
	custom_fields = {
		'Item': [
			{
				'fieldname': 'woocommerce_section',
				'fieldtype': 'Section Break',
				'label': 'WooCommerce',
				'insert_after': 'weight_uom'
			},
			{
				'fieldname': 'sync_to_woocommerce',
				'fieldtype': 'Check',
				'label': 'Sync to WooCommerce',
				'insert_after': 'woocommerce_section',
				'default': 0
			},
			{
				'fieldname': 'woocommerce_product',
				'fieldtype': 'Link',
				'label': 'WooCommerce Product',
				'options': 'WooCommerce Product',
				'insert_after': 'sync_to_woocommerce',
				'read_only': 1
			}
		],
		'Customer': [
			{
				'fieldname': 'woocommerce_section',
				'fieldtype': 'Section Break',
				'label': 'WooCommerce',
				'insert_after': 'customer_primary_contact'
			},
			{
				'fieldname': 'sync_to_woocommerce',
				'fieldtype': 'Check',
				'label': 'Sync to WooCommerce',
				'insert_after': 'woocommerce_section',
				'default': 0
			},
			{
				'fieldname': 'woocommerce_customer',
				'fieldtype': 'Link',
				'label': 'WooCommerce Customer',
				'options': 'WooCommerce Customer',
				'insert_after': 'sync_to_woocommerce',
				'read_only': 1
			}
		],
		'Sales Order': [
			{
				'fieldname': 'woocommerce_section',
				'fieldtype': 'Section Break',
				'label': 'WooCommerce',
				'insert_after': 'terms'
			},
			{
				'fieldname': 'woocommerce_order',
				'fieldtype': 'Link',
				'label': 'WooCommerce Order',
				'options': 'WooCommerce Order',
				'insert_after': 'woocommerce_section',
				'read_only': 1
			},
			{
				'fieldname': 'wc_order_id',
				'fieldtype': 'Data',
				'label': 'WooCommerce Order ID',
				'insert_after': 'woocommerce_order',
				'read_only': 1
			}
		]
	}

	for doctype, fields in custom_fields.items():
		# Check if custom fields already exist
		existing_fields = frappe.get_all(
			'Custom Field',
			filters={
				'dt': doctype,
				'fieldname': ['in', [f['fieldname'] for f in fields]]
			},
			pluck='fieldname'
		)

		for field in fields:
			if field['fieldname'] not in existing_fields:
				try:
					cf = frappe.new_doc('Custom Field')
					cf.dt = doctype
					cf.update(field)
					cf.insert()
				except Exception as e:
					frappe.log_error(
						f"Failed to create custom field {field['fieldname']} in {doctype}: {str(e)}"
					)

	frappe.db.commit()


def create_order_status_mapping_child_table():
	"""
	Create child table for Order Status Mapping.
	"""
	if not frappe.db.exists('DocType', 'WooCommerce Order Status Mapping'):
		dt = frappe.new_doc('DocType')
		dt.module = 'WooCommerce Settings'
		dt.custom = 0
		dt.istable = 1
		dt.name = 'WooCommerce Order Status Mapping'

		dt.fields = [
			{
				'fieldname': 'woocommerce_status',
				'fieldtype': 'Select',
				'label': 'WooCommerce Status',
				'options': 'pending\nprocessing\non-hold\ncompleted\ncancelled\nrefunded\nfailed',
				'reqd': 1
			},
			{
				'fieldname': 'erpnext_status',
				'fieldtype': 'Data',
				'label': 'ERPNext Status',
				'reqd': 1
			},
			{
				'fieldname': 'update_wc',
				'fieldtype': 'Check',
				'label': 'Update WooCommerce',
				'default': 1
			}
		]

		dt.insert()


def create_multi_store_mapping_child_table():
	"""
	Create child table for Multi-Store Mapping.
	"""
	if not frappe.db.exists('DocType', 'WooCommerce Multi Store Mapping'):
		dt = frappe.new_doc('DocType')
		dt.module = 'WooCommerce Settings'
		dt.custom = 0
		dt.istable = 1
		dt.name = 'WooCommerce Multi Store Mapping'

		dt.fields = [
			{
				'fieldname': 'store_id',
				'fieldtype': 'Data',
				'label': 'Store ID',
				'reqd': 1
			},
			{
				'fieldname': 'store_name',
				'fieldtype': 'Data',
				'label': 'Store Name'
			},
			{
				'fieldname': 'warehouse',
				'fieldtype': 'Link',
				'label': 'Warehouse',
				'options': 'Warehouse'
			},
			{
				'fieldname': 'price_list',
				'fieldtype': 'Link',
				'label': 'Price List',
				'options': 'Price List'
			},
			{
				'fieldname': 'cost_center',
				'fieldtype': 'Link',
				'label': 'Cost Center',
				'options': 'Cost Center'
			}
		]

		dt.insert()
