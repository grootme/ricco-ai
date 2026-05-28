# -*- coding: utf-8 -*-
"""
Ricco WooCommerce Hooks Module
This module contains all hook handlers for ERPNext integration.
"""

from .sales_order_events import on_submit, on_cancel, on_update_after_submit
from .item_events import on_update, on_trash
from .customer_events import on_update as customer_on_update, on_trash as customer_on_trash
from .stock_events import on_submit as stock_on_submit
from .delivery_events import on_submit as delivery_on_submit
from .invoice_events import on_submit as invoice_on_submit

__all__ = [
	'on_submit',
	'on_cancel',
	'on_update_after_submit',
	'on_update',
	'on_trash',
	'customer_on_update',
	'customer_on_trash',
	'stock_on_submit',
	'delivery_on_submit',
	'invoice_on_submit'
]
