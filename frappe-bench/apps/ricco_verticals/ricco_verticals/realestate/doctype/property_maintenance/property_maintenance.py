# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, get_datetime

class PropertyMaintenance(Document):
	def validate(self):
		self.fetch_property_details()
		self.fetch_tenant_details()
		self.validate_dates()
	
	def fetch_property_details(self):
		"""Fetch property details"""
		if self.property:
			property = frappe.get_doc("Property Listing", self.property)
			self.property_name = property.property_name
			self.property_address = f"{property.address_line1}, {property.city}"
	
	def fetch_tenant_details(self):
		"""Fetch tenant details"""
		if self.tenant:
			tenant = frappe.get_doc("Tenant", self.tenant)
			self.tenant_name = f"{tenant.first_name} {tenant.last_name}"
			self.tenant_contact = tenant.mobile
			self.tenant_email = tenant.email
	
	def validate_dates(self):
		"""Validate maintenance dates"""
		if self.completion_date and getdate(self.completion_date) < getdate(self.request_date):
			frappe.throw(_("Completion date cannot be before request date"))
		
		if self.scheduled_date and getdate(self.scheduled_date) < getdate(self.request_date):
			frappe.throw(_("Scheduled date cannot be before request date"))
	
	def on_update(self):
		"""Handle status changes"""
		self.handle_status_change()
	
	def handle_status_change(self):
		"""Handle maintenance request status changes"""
		if self.status == "Completed":
			if not self.completion_date:
				self.completion_date = getdate()
		
		if self.status == "Scheduled" and not self.assigned_date:
			self.assigned_date = getdate()
	
	def create_sales_invoice(self):
		"""Create Sales Invoice for billable maintenance"""
		if self.billable and self.billing_amount:
			si = frappe.new_doc("Sales Invoice")
			si.customer = frappe.db.get_value("Property Rental", {
				"property_listing": self.property,
				"status": "Active"
			}, "customer")
			
			if si.customer:
				si.append("items", {
					"item_code": "Property Maintenance Service",
					"item_name": f"Maintenance - {self.issue_type}",
					"qty": 1,
					"rate": self.billing_amount,
					"description": self.issue_description
				})
				si.save()
				self.sales_invoice = si.name
