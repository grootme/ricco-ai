# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in ricco_woocommerce/__init__.py
from ricco_woocommerce import __version__ as version

setup(
	name='ricco_woocommerce',
	version=version,
	description='WooCommerce e-commerce integration for ERPNext',
	author='Ricco',
	author_email='support@ricco.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
	entry_points={
		'frappe.app': [
			'ricco_woocommerce = ricco_woocommerce'
		]
	}
)
