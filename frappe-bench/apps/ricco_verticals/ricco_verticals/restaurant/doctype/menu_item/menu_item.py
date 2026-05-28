# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class MenuItem(Document):
	def validate(self):
		self.calculate_profit_margin()
		self.validate_variants()
		self.sync_with_erpnext()
	
	def calculate_profit_margin(self):
		"""Calculate profit margin"""
		if self.price and self.cost_price:
			self.profit_margin = flt((self.price - self.cost_price) / self.cost_price * 100, 2)
	
	def validate_variants(self):
		"""Validate variant configuration"""
		if self.has_variants and not self.variant_attribute:
			frappe.throw(_("Variant attribute is required when item has variants"))
		
		if not self.has_variants and self.variant_of:
			self.variant_attribute = None
	
	def sync_with_erpnext(self):
		"""Sync menu item with ERPNext Item"""
		if not self.sync_with_erpnext:
			return
		
		if self.item:
			# Update existing item
			item = frappe.get_doc("Item", self.item)
			item.item_code = self.item_code
			item.item_name = self.item_name
			item.item_group = self.item_group
			item.stock_uom = self.uom or "Nos"
			item.save()
		else:
			# Create new item
			item = frappe.new_doc("Item")
			item.item_code = self.item_code
			item.item_name = self.item_name
			item.item_group = self.item_group or "Products"
			item.stock_uom = self.uom or "Nos"
			item.is_stock_item = 0
			item.is_sales_item = 1
			item.save()
			self.item = item.name
		
		# Update Item Price
		self.update_item_price()
	
	def update_item_price(self):
		"""Update item price in ERPNext"""
		if not self.item or not self.price:
			return
		
		price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
		
		existing_price = frappe.db.get_value("Item Price", {
			"item_code": self.item,
			"price_list": price_list
		}, "name")
		
		if existing_price:
			price_doc = frappe.get_doc("Item Price", existing_price)
			price_doc.price_list_rate = self.price
			price_doc.save()
		else:
			price_doc = frappe.new_doc("Item Price")
			price_doc.item_code = self.item
			price_doc.price_list = price_list
			price_doc.price_list_rate = self.price
			price_doc.save()
