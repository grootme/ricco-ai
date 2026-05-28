# -*- coding: utf-8 -*-
"""
Permission Handlers for WooCommerce Integration
"""

import frappe
from frappe import _


def get_permission_query_conditions(user=None, doctype=None):
	"""
	Get permission query conditions for WooCommerce DocTypes.
	This allows filtering records based on user permissions.
	"""
	if not user:
		user = frappe.session.user

	# System Manager has full access
	if frappe.has_permission(doctype, ptype='read', user=user, raise_exception=False):
		return None

	# Sales users can see records based on their customer permissions
	if doctype in ['WooCommerce Order', 'WooCommerce Customer']:
		# Get customers this user has access to
		customers = frappe.get_all(
			'Customer',
			filters={
				'owner': user
			},
			pluck='name'
		)

		if customers:
			customer_list = ', '.join([f"'{c}'" for c in customers])
			if doctype == 'WooCommerce Order':
				return f"`tabWooCommerce Order`.customer in ({customer_list})"
			elif doctype == 'WooCommerce Customer':
				return f"`tabWooCommerce Customer`.customer in ({customer_list})"

	# Item Manager can see product records
	if doctype == 'WooCommerce Product':
		if frappe.has_permission('Item', 'read', user=user):
			return None

	return None


def has_permission(doc, user=None, ptype=None):
	"""
	Check if user has permission for a specific document.
	"""
	if not user:
		user = frappe.session.user

	# System Manager has full access
	if frappe.has_permission(doc.doctype, ptype=ptype, user=user, raise_exception=False):
		return True

	# Check based on linked documents
	if doc.doctype == 'WooCommerce Order':
		if doc.customer:
			return frappe.has_permission('Customer', ptype, doc.customer, user=user)
		elif doc.erpnext_order:
			return frappe.has_permission('Sales Order', ptype, doc.erpnext_order, user=user)

	elif doc.doctype == 'WooCommerce Product':
		if doc.item_code:
			return frappe.has_permission('Item', ptype, doc.item_code, user=user)

	elif doc.doctype == 'WooCommerce Customer':
		if doc.customer:
			return frappe.has_permission('Customer', ptype, doc.customer, user=user)

	return False
