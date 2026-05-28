# Copyright (c) 2023, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

import gameplan
from gameplan.utils import url_safe_slug


class GPPage(Document):
	def before_save(self):
		self.slug = url_safe_slug(self.title)


def has_permission(doc, ptype="read", user=None):
	user = user or frappe.session.user

	if gameplan.is_guest(user):
		if not doc.project:
			return doc.owner == user
		return bool(frappe.db.exists("GP Guest Access", {"user": user, "project": doc.project}))

	if doc.project:
		# pages in projects accessible by everyone
		return True
	if doc.owner == user:
		# private pages
		return True
	return False


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user

	if not gameplan.is_guest(user):
		return None

	escaped_user = frappe.db.escape(user)
	return f"""(
		`tabGP Page`.project in (
			select `tabGP Guest Access`.project
			from `tabGP Guest Access`
			where `tabGP Guest Access`.user = {escaped_user}
		)
		or (`tabGP Page`.project is null and `tabGP Page`.owner = {escaped_user})
	)"""
