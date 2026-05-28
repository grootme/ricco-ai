# -*- coding: utf-8 -*-
"""
WooCommerce Webhook Handler
This module handles incoming webhooks from WooCommerce.
"""

import frappe
from frappe import _
import json
import hmac
import hashlib


@frappe.whitelist(allow_guest=True)
def handle_webhook():
	"""
	Handle incoming webhook from WooCommerce.
	This endpoint is called by WooCommerce when events occur.
	"""
	# Get request data
	webhook_data = frappe.request.get_json(silent=True)

	if not webhook_data:
		return {'status': 'error', 'message': 'No data received'}

	# Get headers
	headers = dict(frappe.request.headers)

	# Extract webhook topic
	topic = headers.get('X-Wc-Webhook-Topic', '')

	if not topic:
		return {'status': 'error', 'message': 'Missing webhook topic'}

	# Get active settings
	settings_name = frappe.db.get_value('WooCommerce Settings', {'is_active': 1})

	if not settings_name:
		return {'status': 'error', 'message': 'No active WooCommerce settings'}

	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	# Verify webhook is enabled
	if not settings.enable_webhooks:
		return {'status': 'error', 'message': 'Webhooks are disabled'}

	# Verify signature
	signature = headers.get('X-Wc-Webhook-Signature', '')

	if settings.webhook_secret:
		secret = settings.get_password('webhook_secret')
		payload_body = frappe.request.get_data(as_text=True)

		if not verify_webhook_signature(payload_body, signature, secret):
			frappe.log_error(
				title="Invalid WooCommerce Webhook Signature",
				message=f"Topic: {topic}\nSignature: {signature}"
			)
			return {'status': 'error', 'message': 'Invalid signature'}

	# Create webhook log
	from ricco_woocommerce.doctype.woocommerce_webhook_log.woocommerce_webhook_log import create_webhook_log

	log = create_webhook_log(topic, webhook_data, headers, settings_name)

	# Process webhook asynchronously
	frappe.enqueue(
		'ricco_woocommerce.doctype.woocommerce_webhook_log.woocommerce_webhook_log.process_webhook_log',
		log_name=log.name,
		queue='short',
		timeout=300
	)

	return {'status': 'success', 'message': 'Webhook received', 'log_id': log.name}


def verify_webhook_signature(payload, signature, secret):
	"""
	Verify webhook signature using HMAC-SHA256.
	"""
	if not signature or not secret:
		return False

	expected_signature = hmac.new(
		secret.encode('utf-8'),
		payload.encode('utf-8'),
		hashlib.sha256
	).hexdigest()

	return hmac.compare_digest(signature, expected_signature)


@frappe.whitelist()
def get_webhook_endpoints():
	"""
	Get available webhook endpoints for configuration.
	"""
	site_url = frappe.utils.get_url()

	return {
		'webhook_url': f"{site_url}/api/method/ricco_woocommerce.api.webhook_handler.handle_webhook",
		'topics': [
			'order.created',
			'order.updated',
			'order.deleted',
			'order.restored',
			'order.refunded',
			'product.created',
			'product.updated',
			'product.deleted',
			'product.restored',
			'customer.created',
			'customer.updated',
			'customer.deleted',
			'customer.restore',
			'coupon.created',
			'coupon.updated',
			'coupon.deleted'
		]
	}


@frappe.whitelist()
def register_webhooks(settings_name):
	"""
	Register webhooks with WooCommerce.
	"""
	settings = frappe.get_doc('WooCommerce Settings', settings_name)

	if not settings.is_active:
		frappe.throw(_("WooCommerce Settings must be active to register webhooks"))

	if not settings.webhook_secret:
		frappe.throw(_("Webhook secret is required"))

	settings.register_webhooks()

	return {'success': True, 'message': _('Webhooks registered successfully')}
