# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RestaurantSettings(Document):
	def validate(self):
		self.validate_times()
		self.validate_reservation_settings()
	
	def validate_times(self):
		"""Validate opening and closing times"""
		if self.opening_time and self.closing_time:
			if self.opening_time >= self.closing_time:
				frappe.throw(_("Opening time must be before closing time"))
	
	def validate_reservation_settings(self):
		"""Validate reservation settings"""
		if self.reservation_deposit_required and not self.deposit_amount:
			frappe.throw(_("Deposit amount is required when deposit is required"))
		
		if self.send_reminder and not self.reminder_hours_before:
			frappe.throw(_("Reminder hours before is required when sending reminders"))
