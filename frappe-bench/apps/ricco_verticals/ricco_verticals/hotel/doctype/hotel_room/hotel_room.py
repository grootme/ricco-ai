# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class HotelRoom(Document):
	def validate(self):
		self.calculate_total_capacity()
		self.sync_with_erpnext()
	
	def calculate_total_capacity(self):
		"""Calculate total room capacity"""
		self.total_capacity = self.max_occupancy or 0
		if self.extra_bed_available and self.extra_bed_count:
			self.total_capacity += self.extra_bed_count
	
	def sync_with_erpnext(self):
		"""Create or update linked Item in ERPNext"""
		if not self.item:
			item = frappe.new_doc("Item")
			item.item_code = self.room_number
			item.item_name = self.room_name or f"Room {self.room_number}"
			item.item_group = "Services"
			item.is_stock_item = 0
			item.is_sales_item = 1
			item.save()
			self.item = item.name
			
			# Create item price
			if self.base_rate:
				price = frappe.new_doc("Item Price")
				price.item_code = item.name
				price.price_list_rate = self.base_rate
				price.save()
	
	def update_status(self, status, booking=None, guest=None):
		"""Update room status"""
		self.status = status
		if booking:
			self.current_booking = booking
		if guest:
			self.current_guest = guest
		self.save()
	
	def mark_clean(self):
		"""Mark room as clean"""
		self.housekeeping_status = "Clean"
		self.last_cleaned = frappe.utils.now_datetime()
		self.save()
