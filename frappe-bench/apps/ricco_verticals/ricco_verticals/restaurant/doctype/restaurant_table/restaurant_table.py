# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RestaurantTable(Document):
	def validate(self):
		self.validate_capacity()
		self.update_status()
	
	def validate_capacity(self):
		"""Validate seating capacity"""
		if self.capacity and self.capacity < 1:
			frappe.throw(_("Seating capacity must be at least 1"))
	
	def update_status(self):
		"""Update table status based on current reservation"""
		if self.current_reservation:
			self.status = "Reserved"
		elif self.linked_customer:
			self.status = "Occupied"
	
	def on_update(self):
		"""Sync with ERPNext if configured"""
		self.sync_with_erpnext()
	
	def sync_with_erpnext(self):
		"""Create or update linked customer for walk-ins"""
		if self.linked_customer:
			# Update existing customer
			customer = frappe.get_doc("Customer", self.linked_customer)
			customer.customer_name = f"Table {self.table_number}"
			customer.save()
