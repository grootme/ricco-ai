# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def prevent_customer_deletion(doc, method):
	"""Prevent deletion of customers linked to verticals"""
	# Check for linked records
	links = []
	
	if frappe.db.exists("Gym Member", {"customer": doc.name}):
		links.append("Gym Member")
	
	if frappe.db.exists("Tenant", {"customer": doc.name}):
		links.append("Tenant")
	
	if frappe.db.exists("Patient Record", {"customer": doc.name}):
		links.append("Patient Record")
	
	if frappe.db.exists("Property Listing", {"customer": doc.name}):
		links.append("Property Listing")
	
	if links:
		frappe.throw(_("Cannot delete customer. Linked to: {0}").format(", ".join(links)))

def handle_invoice_submit(doc, method):
	"""Handle Sales Invoice submission for vertical-specific updates"""
	# Update related records based on invoice
	for item in doc.items:
		# Check for restaurant reservation
		if item.restaurant_reservation:
			frappe.db.set_value("Restaurant Reservation", item.restaurant_reservation, {
				"sales_invoice": doc.name,
				"deposit_paid": 1,
				"payment_date": doc.posting_date
			})
		
		# Check for hotel booking
		if item.hotel_booking:
			booking = frappe.get_doc("Hotel Booking", item.hotel_booking)
			booking.amount_paid = (booking.amount_paid or 0) + item.amount
			booking.balance_due = booking.total_amount - booking.amount_paid
			if booking.balance_due <= 0:
				booking.payment_status = "Paid"
			booking.sales_invoice = doc.name
			booking.save()

def set_boot_session(bootinfo):
	"""Set additional session information"""
	bootinfo.ricco_verticals = {
		"restaurant_enabled": frappe.db.get_single_value("Restaurant Settings", "enable_reservations"),
		"gym_enabled": True,
		"realestate_enabled": True,
		"healthcare_enabled": True,
		"hotel_enabled": True
	}
	return bootinfo

def get_notification_config():
	"""Get notification configuration"""
	return {
		"for_doctype": {
			"Restaurant Reservation": {"status": "Pending"},
			"Gym Member": {"status": "Expired"},
			"Property Rental": {"status": "Pending Renewal"},
			"Appointment Booking": {"status": "Scheduled"},
			"Hotel Booking": {"status": "Pending"},
			"Property Maintenance": {"status": "Open", "priority": "High"}
		}
	}

def shell_context(context):
	"""Add custom shell commands"""
	context.update({
		"get_restaurant_settings": lambda: frappe.get_single("Restaurant Settings"),
		"get_active_gym_members": lambda: frappe.get_all("Gym Member", filters={"status": "Active"}),
		"get_available_rooms": lambda: frappe.get_all("Hotel Room", filters={"status": "Available"})
	})
