# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, get_datetime

class HotelCheckin(Document):
	def validate(self):
		self.fetch_booking_details()
		self.fetch_room_details()
		self.calculate_totals()
	
	def fetch_booking_details(self):
		"""Fetch booking details"""
		if self.booking:
			booking = frappe.get_doc("Hotel Booking", self.booking)
			self.customer = booking.customer
			self.guest_name = booking.guest_name
			self.expected_checkout = booking.check_out_date
	
	def fetch_room_details(self):
		"""Fetch room details"""
		if self.room:
			room = frappe.get_doc("Hotel Room", self.room)
			self.room_type = room.room_type
			self.floor = room.floor
			self.room_rate = room.base_rate
	
	def calculate_totals(self):
		"""Calculate billing totals"""
		self.total_charges = flt(self.room_charges) + flt(self.additional_charges) + flt(self.taxes) - flt(self.discount_applied)
		self.balance_due = flt(self.total_charges) - flt(self.amount_paid)
	
	def on_update(self):
		"""Handle status changes"""
		self.handle_status_change()
	
	def handle_status_change(self):
		"""Handle check-in status changes"""
		if self.status == "Checked In":
			self.occupy_room()
		elif self.status == "Checked Out":
			self.vacate_room()
			self.finalize_billing()
	
	def occupy_room(self):
		"""Mark room as occupied"""
		if self.room:
			room = frappe.get_doc("Hotel Room", self.room)
			room.status = "Occupied"
			room.current_booking = self.booking
			room.current_guest = self.guest_name
			room.check_in_date = getdate(self.check_in_datetime)
			room.save()
	
	def vacate_room(self):
		"""Mark room as vacant"""
		if self.room:
			room = frappe.get_doc("Hotel Room", self.room)
			room.status = "Cleaning"
			room.current_booking = ""
			room.current_guest = ""
			room.save()
	
	def finalize_billing(self):
		"""Create final Sales Invoice"""
		if self.customer and self.total_charges > 0:
			si = frappe.new_doc("Sales Invoice")
			si.customer = self.customer
			si.company = self.company
			
			# Add room charges
			if self.room_charges:
				si.append("items", {
					"item_code": "Room Charges",
					"qty": 1,
					"rate": self.room_charges
				})
			
			# Add additional charges
			if self.additional_charges:
				si.append("items", {
					"item_code": "Additional Charges",
					"qty": 1,
					"rate": self.additional_charges
				})
			
			si.save()
			self.sales_invoice = si.name
	
	def add_charge(self, item_code, amount, description=None):
		"""Add a charge to the folio"""
		self.append("charges", {
			"item_code": item_code,
			"amount": amount,
			"description": description,
			"date": get_datetime()
		})
		self.calculate_totals()
		self.save()
