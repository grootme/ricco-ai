# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Tenant(Document):
	def validate(self):
		self.validate_contact_info()
		self.create_customer()
	
	def validate_contact_info(self):
		"""Validate contact information"""
		if not self.email and not self.mobile:
			frappe.throw(_("At least one contact method (email or mobile) is required"))
	
	def create_customer(self):
		"""Create or update linked Customer in ERPNext"""
		if not self.customer:
			customer = frappe.new_doc("Customer")
			customer.customer_name = f"{self.first_name} {self.last_name}"
			customer.customer_type = "Individual"
			customer.customer_group = self.customer_group or "Individual"
			customer.territory = self.territory
			customer.mobile_no = self.mobile
			customer.email_id = self.email
			customer.save()
			self.customer = customer.name
		else:
			# Update existing customer
			customer = frappe.get_doc("Customer", self.customer)
			customer.customer_name = f"{self.first_name} {self.last_name}"
			customer.mobile_no = self.mobile
			customer.email_id = self.email
			customer.save()
	
	def on_update(self):
		"""Update tenant ID"""
		if not self.tenant_id:
			self.tenant_id = self.name
