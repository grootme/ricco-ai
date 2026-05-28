# -*- coding: utf-8 -*-
"""
Customer Event Handlers
These handlers are triggered on Customer events in ERPNext.
"""

import frappe
from frappe import _


def on_update(doc, method=None):
	"""
	Handle Customer on_update event.
	Sync customer to WooCommerce when it's updated in ERPNext.
	"""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	# Check if customer is linked to WooCommerce Customer
	from ricco_woocommerce.doctype.woocommerce_customer.woocommerce_customer import get_customer_by_erpnext_customer

	wc_customer = get_customer_by_erpnext_customer(doc.name)

	# Get active WooCommerce settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if not settings_name:
		return

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	if not settings.sync_customers or not settings.sync_on_update:
		return

	if wc_customer:
		# Update existing WooCommerce customer
		_update_wc_customer_from_erpnext(doc, wc_customer, settings)
	else:
		# Create new WooCommerce customer if auto-sync is enabled
		if settings.auto_sync_enabled:
			_create_wc_customer_from_erpnext(doc, settings)


def on_trash(doc, method=None):
	"""
	Handle Customer on_trash event.
	Delete or mark as inactive in WooCommerce when customer is trashed.
	"""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	# Check if customer is linked to WooCommerce Customer
	from ricco_woocommerce.doctype.woocommerce_customer.woocommerce_customer import get_customer_by_erpnext_customer

	wc_customer = get_customer_by_erpnext_customer(doc.name)

	if not wc_customer:
		return

	# Get WooCommerce settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})
	if not settings_name:
		return

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	# Update WooCommerce customer status
	from ricco_woocommerce.api.sync_api import get_wc_api_client

	try:
		wcapi = get_wc_api_client(settings.name)

		# Delete customer from WooCommerce
		response = wcapi.delete(f"customers/{wc_customer.wc_customer_id}", params={
			'force': True
		})

		if response.status_code == 200:
			frappe.msgprint(
				_("WooCommerce customer {0} has been deleted").format(wc_customer.wc_customer_id)
			)
		else:
			frappe.log_error(
				title=f"Failed to delete WooCommerce customer: {wc_customer.wc_customer_id}",
				message=response.text
			)

	except Exception as e:
		frappe.log_error(
			title="WooCommerce Customer Delete Error",
			message=str(e)
		)


def _update_wc_customer_from_erpnext(customer, wc_customer, settings):
	"""Update WooCommerce customer from ERPNext Customer."""
	from ricco_woocommerce.api.sync_api import get_wc_api_client

	try:
		wcapi = get_wc_api_client(settings.name)

		# Get customer name parts
		name_parts = customer.customer_name.split(' ', 1)
		first_name = name_parts[0]
		last_name = name_parts[1] if len(name_parts) > 1 else ''

		customer_data = {
			'first_name': first_name,
			'last_name': last_name,
			'email': customer.email_id or wc_customer.email,
			'phone': customer.mobile_no or customer.phone
		}

		# Get billing address
		billing_address = _get_customer_address(customer.name, 'Billing')
		if billing_address:
			customer_data['billing'] = {
				'first_name': first_name,
				'last_name': last_name,
				'company': customer.customer_name if customer.customer_type == 'Company' else '',
				'address_1': billing_address.get('address_line1', ''),
				'address_2': billing_address.get('address_line2', ''),
				'city': billing_address.get('city', ''),
				'state': billing_address.get('state', ''),
				'postcode': billing_address.get('pincode', ''),
				'country': billing_address.get('country', ''),
				'phone': billing_address.get('phone', ''),
				'email': customer.email_id or ''
			}

		# Get shipping address
		shipping_address = _get_customer_address(customer.name, 'Shipping')
		if shipping_address:
			customer_data['shipping'] = {
				'first_name': first_name,
				'last_name': last_name,
				'company': customer.customer_name if customer.customer_type == 'Company' else '',
				'address_1': shipping_address.get('address_line1', ''),
				'address_2': shipping_address.get('address_line2', ''),
				'city': shipping_address.get('city', ''),
				'state': shipping_address.get('state', ''),
				'postcode': shipping_address.get('pincode', ''),
				'country': shipping_address.get('country', ''),
				'phone': shipping_address.get('phone', '')
			}

		response = wcapi.put(f"customers/{wc_customer.wc_customer_id}", customer_data)

		if response.status_code == 200:
			wc_data = response.json()
			wc_customer.update_from_wc_data(wc_data)
			wc_customer.mark_synced()

			if settings.debug_mode:
				frappe.msgprint(
					_("WooCommerce customer {0} updated successfully").format(wc_customer.wc_customer_id)
				)
		else:
			wc_customer.mark_failed(f"API Error: {response.text}")

	except Exception as e:
		wc_customer.mark_failed(str(e))
		frappe.log_error(
			title=f"WooCommerce Customer Update Error: {customer.name}",
			message=str(e)
		)


def _create_wc_customer_from_erpnext(customer, settings):
	"""Create new WooCommerce customer from ERPNext Customer."""
	from ricco_woocommerce.api.sync_api import get_wc_api_client
	from ricco_woocommerce.doctype.woocommerce_customer.woocommerce_customer import create_or_update_customer

	try:
		wcapi = get_wc_api_client(settings.name)

		# Get customer name parts
		name_parts = customer.customer_name.split(' ', 1)
		first_name = name_parts[0]
		last_name = name_parts[1] if len(name_parts) > 1 else ''

		customer_data = {
			'first_name': first_name,
			'last_name': last_name,
			'email': customer.email_id,
			'phone': customer.mobile_no or customer.phone,
			'username': customer.email_id.split('@')[0] if customer.email_id else None
		}

		# Get billing address
		billing_address = _get_customer_address(customer.name, 'Billing')
		if billing_address:
			customer_data['billing'] = {
				'first_name': first_name,
				'last_name': last_name,
				'company': customer.customer_name if customer.customer_type == 'Company' else '',
				'address_1': billing_address.get('address_line1', ''),
				'address_2': billing_address.get('address_line2', ''),
				'city': billing_address.get('city', ''),
				'state': billing_address.get('state', ''),
				'postcode': billing_address.get('pincode', ''),
				'country': billing_address.get('country', ''),
				'phone': billing_address.get('phone', ''),
				'email': customer.email_id or ''
			}

		# Get shipping address
		shipping_address = _get_customer_address(customer.name, 'Shipping')
		if shipping_address:
			customer_data['shipping'] = {
				'first_name': first_name,
				'last_name': last_name,
				'company': customer.customer_name if customer.customer_type == 'Company' else '',
				'address_1': shipping_address.get('address_line1', ''),
				'address_2': shipping_address.get('address_line2', ''),
				'city': shipping_address.get('city', ''),
				'state': shipping_address.get('state', ''),
				'postcode': shipping_address.get('pincode', ''),
				'country': shipping_address.get('country', ''),
				'phone': shipping_address.get('phone', '')
			}

		response = wcapi.post("customers", customer_data)

		if response.status_code == 201:
			wc_data = response.json()

			# Create WooCommerce Customer record
			wc_customer = create_or_update_customer(wc_data, settings.name)
			wc_customer.customer = customer.name
			wc_customer.mark_synced()

			if settings.debug_mode:
				frappe.msgprint(
					_("WooCommerce customer {0} created successfully").format(wc_customer.wc_customer_id)
				)
		else:
			frappe.log_error(
				title=f"Failed to create WooCommerce customer: {customer.name}",
				message=response.text
			)

	except Exception as e:
		frappe.log_error(
			title=f"WooCommerce Customer Creation Error: {customer.name}",
			message=str(e)
		)


def _get_customer_address(customer_name, address_type):
	"""Get customer address by type."""
	address = frappe.db.sql("""
		SELECT a.*
		FROM `tabAddress` a
		INNER JOIN `tabDynamic Link` dl ON dl.parent = a.name
		WHERE dl.link_doctype = 'Customer'
		AND dl.link_name = %s
		AND a.address_type = %s
		LIMIT 1
	""", (customer_name, address_type), as_dict=True)

	return address[0] if address else None
