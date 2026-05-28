# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PatientRecord(Document):
	def validate(self):
		self.validate_contact_info()
		self.create_customer()
		self.update_visit_stats()
	
	def validate_contact_info(self):
		"""Validate contact information"""
		if not self.mobile:
			frappe.throw(_("Mobile number is required"))
	
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
	
	def update_visit_stats(self):
		"""Update patient visit statistics"""
		if self.name:
			self.total_visits = frappe.db.count("Appointment Booking", {
				"patient": self.name,
				"status": "Completed"
			})
			
			last_visit = frappe.db.get_value("Appointment Booking", {
				"patient": self.name,
				"status": "Completed"
			}, "appointment_date", order_by="appointment_date desc")
			
			if last_visit:
				self.last_visit_date = last_visit
	
	def on_update(self):
		"""Update patient ID"""
		if not self.patient_id:
			self.patient_id = self.name
