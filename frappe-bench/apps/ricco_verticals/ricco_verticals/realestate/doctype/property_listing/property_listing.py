# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class PropertyListing(Document):
	def validate(self):
		self.calculate_price_per_unit()
		self.validate_property_specs()
		self.create_customer()
	
	def calculate_price_per_unit(self):
		"""Calculate price per unit area"""
		if self.expected_price and self.total_area:
			self.price_per_unit = flt(self.expected_price / self.total_area, 2)
	
	def validate_property_specs(self):
		"""Validate property specifications"""
		if self.built_up_area and self.total_area:
			if self.built_up_area > self.total_area:
				frappe.throw(_("Built-up area cannot exceed total area"))
	
	def create_customer(self):
		"""Create or update linked Customer for owner"""
		if self.owner_name and not self.customer:
			customer = frappe.new_doc("Customer")
			customer.customer_name = self.owner_name
			customer.customer_type = "Individual"
			customer.mobile_no = self.owner_contact
			customer.email_id = self.owner_email
			customer.save()
			self.customer = customer.name
	
	def on_update(self):
		"""Update availability status"""
		self.update_availability()
	
	def update_availability(self):
		"""Update availability status based on linked rentals"""
		active_rentals = frappe.db.count("Property Rental", {
			"property_listing": self.name,
			"status": "Active"
		})
		
		if active_rentals > 0 and self.availability_status == "Available":
			self.availability_status = "Rented"
