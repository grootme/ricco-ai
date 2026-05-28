# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, get_datetime, add_days

class RestaurantReservation(Document):
	def validate(self):
		self.validate_dates()
		self.validate_party_size()
		self.validate_table_availability()
		self.calculate_deposit()
	
	def validate_dates(self):
		"""Validate reservation date"""
		if getdate(self.reservation_date) < getdate():
			frappe.throw(_("Reservation date cannot be in the past"))
	
	def validate_party_size(self):
		"""Validate party size against table capacity"""
		if self.restaurant_table and self.party_size:
			table = frappe.get_doc("Restaurant Table", self.restaurant_table)
			if self.party_size > table.capacity:
				frappe.throw(_("Party size exceeds table capacity of {0}").format(table.capacity))
	
	def validate_table_availability(self):
		"""Check if table is available for the requested time"""
		if self.restaurant_table:
			existing = frappe.db.sql("""
				SELECT name FROM `tabRestaurant Reservation`
				WHERE restaurant_table = %s
				AND reservation_date = %s
				AND status NOT IN ('Cancelled', 'Completed', 'No Show')
				AND name != %s
			""", (self.restaurant_table, self.reservation_date, self.name or ""))
			
			if existing:
				frappe.throw(_("Table is already reserved for this date"))
	
	def calculate_deposit(self):
		"""Calculate deposit amount based on settings"""
		settings = frappe.get_single("Restaurant Settings")
		if settings.reservation_deposit_required and not self.deposit_amount:
			self.deposit_required = 1
			self.deposit_amount = settings.deposit_amount
	
	def on_submit(self):
		"""Actions on reservation confirmation"""
		self.update_table_status()
		self.create_sales_order()
	
	def on_cancel(self):
		"""Actions on reservation cancellation"""
		self.release_table()
	
	def update_table_status(self):
		"""Update table status to reserved"""
		if self.restaurant_table:
			table = frappe.get_doc("Restaurant Table", self.restaurant_table)
			table.status = "Reserved"
			table.current_reservation = self.name
			table.save()
	
	def release_table(self):
		"""Release the reserved table"""
		if self.restaurant_table:
			table = frappe.get_doc("Restaurant Table", self.restaurant_table)
			if table.current_reservation == self.name:
				table.status = "Available"
				table.current_reservation = ""
				table.save()
	
	def create_sales_order(self):
		"""Create Sales Order in ERPNext if pre-ordered items exist"""
		if self.pre_ordered_items and self.customer:
			settings = frappe.get_single("Restaurant Settings")
			if settings.sync_with_pos:
				so = frappe.new_doc("Sales Order")
				so.customer = self.customer
				so.company = self.company or settings.company
				so.delivery_date = self.reservation_date
				
				for item in self.pre_ordered_items:
					so.append("items", {
						"item_code": item.menu_item,
						"qty": item.quantity,
						"rate": item.rate
					})
				
				so.save()
				self.sales_order = so.name
