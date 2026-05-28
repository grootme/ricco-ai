# -*- coding: utf-8 -*-
# Copyright (c) 2024, Ricco and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime
import json
import hashlib
import hmac
import time


class WooCommerceWebhookLog(Document):
	"""WooCommerce Webhook Log DocType for logging and processing webhook events."""

	def before_save(self):
		"""Actions before saving the document."""
		if self.is_new() and not self.processed_at:
			self.processed_at = datetime.now()

	def mark_processing(self):
		"""Mark webhook as processing."""
		self.status = 'Processing'
		self.save()
		frappe.db.commit()

	def mark_processed(self, result_message=None, related_doctype=None, related_docname=None):
		"""Mark webhook as successfully processed."""
		self.status = 'Processed'
		self.processed_at = datetime.now()
		if result_message:
			self.result_message = result_message
		if related_doctype:
			self.related_doctype = related_doctype
		if related_docname:
			self.related_docname = related_docname
		self.save()
		frappe.db.commit()

	def mark_failed(self, error_message, error_details=None):
		"""Mark webhook as failed."""
		self.status = 'Failed'
		self.processed_at = datetime.now()
		self.result_message = error_message
		if error_details:
			self.error_details = json.dumps(error_details, indent=2) if isinstance(error_details, dict) else str(error_details)
		self.save()
		frappe.db.commit()

		# Log error
		frappe.log_error(
			title=f"WooCommerce Webhook Failed: {self.topic}",
			message=f"Error: {error_message}\nPayload: {self.payload}"
		)

		# Notify if enabled
		self.notify_error()

	def mark_ignored(self, reason=None):
		"""Mark webhook as ignored."""
		self.status = 'Ignored'
		self.processed_at = datetime.now()
		if reason:
			self.result_message = reason
		self.save()
		frappe.db.commit()

	def notify_error(self):
		"""Send notification for webhook error."""
		settings = frappe.get_single('WooCommerce Settings')
		if settings.notify_on_webhook_error and settings.webhook_error_email:
			try:
				frappe.sendmail(
					recipients=settings.webhook_error_email,
					subject=f"WooCommerce Webhook Error: {self.topic}",
					message=f"""
						<h3>Webhook Processing Failed</h3>
						<p><strong>Topic:</strong> {self.topic}</p>
						<p><strong>Error:</strong> {self.result_message}</p>
						<p><strong>Delivery ID:</strong> {self.delivery_id}</p>
						<p><strong>Time:</strong> {self.processed_at}</p>
						<p>Please check the WooCommerce Webhook Log for details.</p>
					"""
				)
			except Exception as e:
				frappe.log_error(f"Failed to send webhook error notification: {str(e)}")

	def verify_signature(self, payload_body, signature, secret):
		"""Verify the webhook signature."""
		if not signature or not secret:
			return False

		expected_signature = hmac.new(
			secret.encode('utf-8'),
			payload_body.encode('utf-8'),
			hashlib.sha256
		).hexdigest()

		return hmac.compare_digest(signature, expected_signature)

	def get_payload_data(self):
		"""Parse and return payload data."""
		if self.payload:
			try:
				return json.loads(self.payload)
			except:
				return None
		return None

	def parse_topic(self):
		"""Parse topic into resource and event."""
		if self.topic:
			parts = self.topic.split('.')
			if len(parts) == 2:
				self.resource = parts[0]
				self.event = parts[1]
		return self.resource, self.event


def create_webhook_log(topic, payload, headers=None, settings_name=None):
	"""Create a new webhook log entry."""
	log = frappe.new_doc('WooCommerce Webhook Log')
	log.topic = topic
	log.payload = json.dumps(payload, indent=2) if isinstance(payload, dict) else str(payload)
	log.woocommerce_settings = settings_name or frappe.db.get_value('WooCommerce Settings', {'is_active': 1})

	# Parse topic
	log.parse_topic()

	# Extract headers
	if headers:
		log.source_ip = headers.get('X-Forwarded-For', headers.get('REMOTE_ADDR', ''))
		log.user_agent = headers.get('User-Agent', '')
		log.delivery_id = headers.get('X-WC-Webhook-Delivery-ID', '')
		log.webhook_id = headers.get('X-WC-Webhook-ID', '')
		signature = headers.get('X-WC-Webhook-Signature', '')

		if signature:
			log.signature = signature

			# Verify signature
			settings = frappe.get_doc('WooCommerce Settings', log.woocommerce_settings) if log.woocommerce_settings else frappe.get_single('WooCommerce Settings')
			if settings and settings.webhook_secret:
				secret = settings.get_password('webhook_secret')
				log.signature_valid = 1 if log.verify_signature(log.payload, signature, secret) else 0

	log.insert()
	frappe.db.commit()

	return log


def process_webhook_log(log_name):
	"""Process a webhook log entry."""
	log = frappe.get_doc('WooCommerce Webhook Log', log_name)

	start_time = time.time()

	try:
		log.mark_processing()

		# Verify signature if required
		settings = frappe.get_single('WooCommerce Settings')
		if settings.enable_webhooks and not log.signature_valid:
			log.mark_failed("Invalid webhook signature")
			return False

		# Parse payload
		payload_data = log.get_payload_data()
		if not payload_data:
			log.mark_failed("Invalid payload data")
			return False

		# Process based on topic
		from ricco_woocommerce.api.sync_api import process_webhook

		result = process_webhook(log.topic, payload_data)

		processing_time = int((time.time() - start_time) * 1000)
		log.processing_time_ms = processing_time

		if result.get('success'):
			log.mark_processed(
				result_message=result.get('message'),
				related_doctype=result.get('doctype'),
				related_docname=result.get('docname')
			)
			return True
		else:
			log.mark_failed(
				result.get('error', 'Unknown error'),
				result.get('details')
			)
			return False

	except Exception as e:
		processing_time = int((time.time() - start_time) * 1000)
		log.processing_time_ms = processing_time
		log.mark_failed(str(e), {'exception': str(e), 'traceback': frappe.get_traceback()})
		return False


@frappe.whitelist()
def get_webhook_logs(status=None, topic=None, limit=50):
	"""Get webhook logs with optional filtering."""
	filters = {}
	if status:
		filters['status'] = status
	if topic:
		filters['topic'] = topic

	return frappe.get_all(
		'WooCommerce Webhook Log',
		filters=filters,
		fields=['name', 'topic', 'status', 'processed_at', 'result_message', 'related_doctype', 'related_docname'],
		order_by='creation desc',
		limit=limit
	)


@frappe.whitelist()
def retry_webhook(log_name):
	"""Retry processing a failed webhook."""
	log = frappe.get_doc('WooCommerce Webhook Log', log_name)

	if log.status != 'Failed':
		frappe.throw(_("Can only retry failed webhooks"))

	return process_webhook_log(log.name)


@frappe.whitelist()
def get_webhook_stats():
	"""Get webhook processing statistics."""
	stats = {
		'total': frappe.db.count('WooCommerce Webhook Log'),
		'processed': frappe.db.count('WooCommerce Webhook Log', {'status': 'Processed'}),
		'failed': frappe.db.count('WooCommerce Webhook Log', {'status': 'Failed'}),
		'pending': frappe.db.count('WooCommerce Webhook Log', {'status': 'Received'}),
		'ignored': frappe.db.count('WooCommerce Webhook Log', {'status': 'Ignored'})
	}

	# Get topic breakdown
	topic_stats = frappe.db.sql("""
		SELECT topic, COUNT(*) as count
		FROM `tabWooCommerce Webhook Log`
		GROUP BY topic
		ORDER BY count DESC
	""", as_dict=True)

	stats['by_topic'] = topic_stats

	return stats


def cleanup_old_logs(days=30):
	"""Clean up old webhook logs."""
	from frappe.utils import add_days, today

	cutoff_date = add_days(today(), -days)

	deleted = frappe.db.sql("""
		DELETE FROM `tabWooCommerce Webhook Log`
		WHERE creation < %s
		AND status IN ('Processed', 'Ignored')
	""", (cutoff_date,))

	frappe.db.commit()

	return deleted
