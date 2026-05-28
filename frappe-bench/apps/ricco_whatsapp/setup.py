# Copyright (c) 2024, Ricco Technologies and contributors
# For license information, please see license.txt

from setuptools import setup, find_packages

setup(
	name='ricco_whatsapp',
	version='1.0.0',
	description='WhatsApp Business API Integration for Frappe/ERPNext',
	author='Ricco Technologies',
	author_email='support@ricco.tech',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=[
		'requests>=2.28.0',
		'cryptography>=38.0.0',
	]
)
