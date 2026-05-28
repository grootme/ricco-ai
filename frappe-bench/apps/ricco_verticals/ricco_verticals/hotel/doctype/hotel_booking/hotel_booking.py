# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, date_diff, getdate

class HotelBooking(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_nights()
		self.calculate_totals()
		self.check_room_availability()
		self.fetch_room_details()
	
	def validate_dates(self):
		"""Validate booking dates"""
		if getdate(self.check_out_date) <= getdate(self.check_in_date):
			frappe.throw(_("Check-out date must be after check-in date"))
		
		if getdate(self.check_in_date) < getdate():
			frappe.throw(_("Check-in date cannot be in the past"))
	
	def calculate_nights(self):
		"""Calculate number of nights"""
		if self.check_in_date and self.check_out_date:
			self.nights = date_diff(self.check_out_date, self.check_in_date)
	
	def calculate_totals(self):
		"""Calculate total booking amount"""
		room_total = flt(self.room_rate) * flt(self.nights)
		self.room_charges = room_total
		
		total = flt(self.room_charges) + flt(self.meal_charges) + flt(self.additional_charges)
		discount_amount = flt(total) * flt(self.discount) / 100
		self.total_amount = total - discount_amount + flt(self.taxes)
		
		self.balance_due = flt(self.total_amount) - flt(self.amount_paid)
	
	def check_room_availability(self):
		"""Check if room is available for the dates"""
		if self.hotel_room:
			existing = frappe.db.sql("""
				SELECT name FROM `tabHotel Booking`
				WHERE hotel_room = %s
				AND status NOT IN ('Cancelled', 'No Show')
				AND (
					(check_in_date <= %s AND check_out_date > %s)
					OR (check_in_date < %s AND check_out_date >= %s)
				)
				AND name != %s
			""", (self.hotel_room, self.check_in_date, self.check_in_date, 
				  self.check_out_date, self.check_out_date, self.name or ""))
			
			if existing:
				frappe.throw(_("Room is not available for the selected dates"))
	
	def fetch_room_details(self):
		"""Fetch room details"""
		if self.hotel_room:
			room = frappe.get_doc("Hotel Room", self.hotel_room)
			self.room_type = room.room_type
			self.floor = room.floor
			if not self.room_rate:
				self.room_rate = room.base_rate
	
	def on_submit(self):
		"""Handle booking confirmation"""
		self.reserve_room()
		self.create_sales_order()
	
	def on_cancel(self):
		"""Handle booking cancellation"""
		self.release_room()
	
	def reserve_room(self):
		"""Reserve the room"""
		if self.hotel_room:
			room = frappe.get_doc("Hotel Room", self.hotel_room)
			room.status = "Reserved"
			room.current_booking = self.name
			room.current_guest = self.guest_name
			room.check_in_date = self.check_in_date
			room.expected_checkout = self.check_out_date
			room.save()
	
	def release_room(self):
		"""Release the room reservation"""
		if self.hotel_room:
			room = frappe.get_doc("Hotel Room", self.hotel_room)
			if room.current_booking == self.name:
				room.status = "Available"
				room.current_booking = ""
				room.current_guest = ""
				room.save()
	
	def create_sales_order(self):
		"""Create Sales Order in ERPNext"""
		if self.customer:
			so = frappe.new_doc("Sales Order")
			so.customer = self.customer
			so.company = self.company
			so.delivery_date = self.check_in_date
			
			# Add room charge
			so.append("items", {
				"item_code": self.hotel_room,
				"item_name": f"Room {self.hotel_room} - {self.nights} nights",
				"qty": self.nights,
				"rate": self.room_rate
			})
			
			so.save()
			self.sales_order = so.name
