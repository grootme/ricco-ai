import frappe
from frappe.query_builder import DocType


def execute():
	"""Set pin_scope to Global for all existing pinned discussions"""
	GPDiscussion = DocType("GP Discussion")

	frappe.qb.update(GPDiscussion).set(GPDiscussion.pin_scope, "Global").where(
		(GPDiscussion.pinned_at.isnotnull())
		& ((GPDiscussion.pin_scope.isnull()) | (GPDiscussion.pin_scope == ""))
	).run()
