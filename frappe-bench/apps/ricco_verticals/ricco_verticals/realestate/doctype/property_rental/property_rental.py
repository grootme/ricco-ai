# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_months, date_diff

class PropertyRental(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_duration()
		self.calculate_total_charges()
		self.fetch_property_details()
	
	def validate_dates(self):
		"""Validate rental dates"""
		if getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("End date must be after start date"))
	
	def calculate_duration(self):
		"""Calculate rental duration in months"""
		if self.start_date and self.end_date:
			self.duration_months = date_diff(self.end_date, self.start_date) // 30
	
	def calculate_total_charges(self):
		"""Calculate total monthly charges"""
		self.total_monthly_charges = flt(self.monthly_rent) + flt(self.maintenance_charges) + \
			flt(self.utility_charges) + flt(self.other_charges)
	
	def fetch_property_details(self):
		"""Fetch property and tenant details"""
		if self.property_listing:
			property = frappe.get_doc("Property Listing", self.property_listing)
			self.property_name = property.property_name
			self.property_type = property.property_type
		
		if self.tenant:
			tenant = frappe.get_doc("Tenant", self.tenant)
			self.tenant_name = f"{tenant.first_name} {tenant.last_name}"
			self.tenant_contact = tenant.mobile
			self.tenant_email = tenant.email
	
	def on_submit(self):
		"""Handle rental activation"""
		self.update_property_status()
		self.create_recurring_entry()
	
	def on_cancel(self):
		"""Handle rental cancellation"""
		self.release_property()
	
	def update_property_status(self):
		"""Update property availability status"""
		if self.property_listing:
			frappe.db.set_value("Property Listing", self.property_listing, "availability_status", "Rented")
	
	def release_property(self):
		"""Release property on rental termination"""
		if self.property_listing:
			frappe.db.set_value("Property Listing", self.property_listing, "availability_status", "Available")
	
	def create_recurring_entry(self):
		"""Create recurring invoice entry in ERPNext"""
		if self.customer and self.monthly_rent:
			# This would create a recurring Sales Invoice
			pass
