# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt


import frappe


def execute():
	"""Delete all GP Pinned Project records where the linked GP Project is archived"""
	GPPinnedProject = frappe.qb.DocType("GP Pinned Project")
	GPProject = frappe.qb.DocType("GP Project")

	# Find all pinned projects where the linked project is archived
	archived_pins = (
		frappe.qb.from_(GPPinnedProject)
		.inner_join(GPProject)
		.on(GPPinnedProject.project == GPProject.name)
		.select(GPPinnedProject.name)
		.where(GPProject.archived_at.isnotnull())
	).run(as_dict=True)

	for pin in archived_pins:
		frappe.delete_doc("GP Pinned Project", pin.name)
