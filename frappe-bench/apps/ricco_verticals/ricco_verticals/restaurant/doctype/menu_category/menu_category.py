# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class MenuCategory(Document):
	def validate(self):
		self.validate_availability_times()
		self.sync_item_group()
	
	def validate_availability_times(self):
		"""Validate availability times"""
		if not self.available_all_day:
			if self.available_from and self.available_to:
				if self.available_from >= self.available_to:
					frappe.throw(_("Available from time must be before available to time"))
	
	def sync_item_group(self):
		"""Create or update linked Item Group in ERPNext"""
		if self.item_group:
			item_group = frappe.get_doc("Item Group", self.item_group)
			item_group.item_group_name = self.category_name
			item_group.save()
		else:
			# Create new Item Group
			item_group = frappe.new_doc("Item Group")
			item_group.item_group_name = self.category_name
			item_group.parent_item_group = "Products"
			item_group.save()
			self.item_group = item_group.name
