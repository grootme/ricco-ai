# -*- coding: utf-8 -*-
# Copyright (c) 2024, RICCO Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class MedicalRecord(Document):
	def validate(self):
		self.fetch_patient_details()
		self.calculate_bmi()
		self.validate_vitals()
	
	def fetch_patient_details(self):
		"""Fetch patient details"""
		if self.patient:
			patient = frappe.get_doc("Patient Record", self.patient)
			self.patient_name = f"{patient.first_name} {patient.last_name}"
			self.patient_dob = patient.date_of_birth
			self.patient_gender = patient.gender
	
	def calculate_bmi(self):
		"""Calculate BMI from height and weight"""
		if self.height and self.weight:
			height_m = flt(self.height) / 100  # Convert cm to m
			self.bmi = flt(self.weight / (height_m ** 2), 1)
	
	def validate_vitals(self):
		"""Validate vital signs are within normal range"""
		if self.blood_pressure_systolic and self.blood_pressure_systolic > 180:
			frappe.msgprint(_("Warning: Blood pressure is critically high"), indicator="red")
		
		if self.heart_rate and (self.heart_rate < 40 or self.heart_rate > 150):
			frappe.msgprint(_("Warning: Heart rate is abnormal"), indicator="red")
		
		if self.oxygen_saturation and self.oxygen_saturation < 90:
			frappe.msgprint(_("Warning: Oxygen saturation is low"), indicator="red")
	
	def on_submit(self):
		"""Handle medical record finalization"""
		self.create_follow_up_appointment()
	
	def create_follow_up_appointment(self):
		"""Create follow-up appointment if required"""
		if self.follow_up_required and self.follow_up_date and self.patient:
			appointment = frappe.new_doc("Appointment Booking")
			appointment.patient = self.patient
			appointment.practitioner = self.practitioner
			appointment.appointment_date = self.follow_up_date
			appointment.appointment_type = "Follow-up"
			appointment.visit_type = "Follow-up"
			appointment.follow_up_from = self.name
			appointment.status = "Scheduled"
			appointment.save()
