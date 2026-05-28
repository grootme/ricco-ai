// Ricco WooCommerce Integration - JavaScript
// This file contains client-side functionality for the WooCommerce integration

frappe.provide('ricco_woocommerce');

// Sync Status Badge
ricco_woocommerce.get_sync_status_badge = function(status) {
	const status_colors = {
		'Pending': 'orange',
		'Synced': 'green',
		'Failed': 'red',
		'Processing': 'blue'
	};

	return `<span class="indicator ${status_colors[status] || 'gray'}">${status}</span>`;
};

// Manual Sync Function
ricco_woocommerce.manual_sync = function(sync_type, direction) {
	frappe.call({
		method: 'ricco_woocommerce.api.sync_api.manual_sync',
		args: {
			sync_type: sync_type,
			direction: direction
		},
		freeze: true,
		freeze_message: __('Syncing {0}...', [sync_type]),
		callback: function(r) {
			if (r.message) {
				if (r.message.success) {
					frappe.show_alert({
						message: __('Sync completed: {0} synced, {1} failed', [
							r.message.synced || r.message.created + r.message.updated,
							r.message.failed
						]),
						indicator: 'green'
					}, 5);

					// Refresh the page if on a list view
					if (cur_list) {
						cur_list.refresh();
					}
				} else {
					frappe.show_alert({
						message: __('Sync failed: {0}', [r.message.message]),
						indicator: 'red'
					}, 5);
				}
			}
		}
	});
};

// Test Connection
ricco_woocommerce.test_connection = function(settings_name) {
	frappe.call({
		method: 'ricco_woocommerce.api.sync_api.test_connection',
		args: {
			settings_name: settings_name
		},
		freeze: true,
		freeze_message: __('Testing connection...'),
		callback: function(r) {
			if (r.message) {
				if (r.message.success) {
					let msg = __('Connection successful!');
					if (r.message.store_info) {
						msg += '<br><br>';
						msg += __('Store: {0}', [r.message.store_info.site_name || 'N/A']) + '<br>';
						msg += __('WooCommerce Version: {0}', [r.message.store_info.wc_version || 'N/A']);
					}
					frappe.msgprint({
						title: __('Connection Successful'),
						message: msg,
						indicator: 'green'
					});
				} else {
					frappe.msgprint({
						title: __('Connection Failed'),
						message: r.message.message,
						indicator: 'red'
					});
				}
			}
		}
	});
};

// Retry Sync
ricco_woocommerce.retry_sync = function(doctype, docname) {
	frappe.call({
		method: 'ricco_woocommerce.api.sync_api.retry_sync',
		args: {
			wc_order_id: docname
		},
		freeze: true,
		freeze_message: __('Retrying sync...'),
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.show_alert({
					message: __('Sync successful'),
					indicator: 'green'
				}, 5);
				if (cur_frm) {
					cur_frm.reload_doc();
				}
			}
		}
	});
};

// Sync Status Update
ricco_woocommerce.update_sync_status = function() {
	frappe.call({
		method: 'ricco_woocommerce.api.sync_api.get_sync_status',
		callback: function(r) {
			if (r.message) {
				ricco_woocommerce.sync_status = r.message;
			}
		}
	});
};

// Add custom buttons to Sales Order
frappe.ui.form.on('Sales Order', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			// Check if linked to WooCommerce
			frappe.db.get_value('WooCommerce Order', {'erpnext_order': frm.doc.name}, 'name')
				.then(r => {
					if (r.message && r.message.name) {
						// Add WooCommerce button
						frm.add_custom_button(__('WooCommerce Order'), function() {
							frappe.set_route('Form', 'WooCommerce Order', r.message.name);
						}, __('View'));

						// Add update status button
						frm.add_custom_button(__('Update WooCommerce Status'), function() {
							frappe.prompt([
								{
									fieldname: 'status',
									label: __('Status'),
									fieldtype: 'Select',
									options: 'pending\nprocessing\non-hold\ncompleted\ncancelled\nrefunded\nfailed',
									reqd: 1
								}
							], function(values) {
								frappe.call({
									method: 'ricco_woocommerce.api.sync_api.sync_order_status',
									args: {
										order_name: frm.doc.name,
										status: values.status
									},
									freeze: true,
									callback: function(r) {
										if (r.message && r.message.success) {
											frappe.show_alert({
												message: __('Status updated'),
												indicator: 'green'
											}, 5);
										}
									}
								});
							}, __('Update WooCommerce Status'), __('Update'));
						}, __('Actions'));
					}
				});
		}
	}
});

// Add custom buttons to Item
frappe.ui.form.on('Item', {
	refresh: function(frm) {
		if (frm.doc.is_sales_item) {
			// Check if linked to WooCommerce
			frappe.db.get_value('WooCommerce Product', {'item_code': frm.doc.item_code}, ['name', 'sync_status', 'wc_product_id'])
				.then(r => {
					if (r.message && r.message.name) {
						// Add WooCommerce button
						frm.add_custom_button(__('WooCommerce Product'), function() {
							frappe.set_route('Form', 'WooCommerce Product', r.message.name);
						}, __('View'));

						// Add sync buttons
						if (r.message.sync_status === 'Failed') {
							frm.add_custom_button(__('Retry Sync'), function() {
								ricco_woocommerce.retry_sync('WooCommerce Product', r.message.name);
							}, __('Actions'));
						}

						// Sync stock button
						frm.add_custom_button(__('Sync Stock to WooCommerce'), function() {
							frappe.call({
								method: 'ricco_woocommerce.api.sync_api.sync_inventory',
								args: {
									item_code: frm.doc.item_code
								},
								freeze: true,
								callback: function(r) {
									if (r.message && r.message.success) {
										frappe.show_alert({
											message: __('Stock synced'),
											indicator: 'green'
										}, 5);
									}
								}
							});
						}, __('Actions'));
					} else {
						// Add create product button
						frm.add_custom_button(__('Create in WooCommerce'), function() {
							frappe.confirm(
								__('Create this item as a product in WooCommerce?'),
								function() {
									frappe.call({
										method: 'ricco_woocommerce.api.sync_api.sync_products',
										args: {
											direction: 'to_wc',
											limit: 1
										},
										freeze: true,
										callback: function(r) {
											if (r.message && r.message.success) {
												frappe.show_alert({
													message: __('Product created in WooCommerce'),
													indicator: 'green'
												}, 5);
												frm.reload_doc();
											}
										}
									});
								}
							);
						}, __('Actions'));
					}
				});
		}
	}
});

// Add custom buttons to Customer
frappe.ui.form.on('Customer', {
	refresh: function(frm) {
		// Check if linked to WooCommerce
		frappe.db.get_value('WooCommerce Customer', {'customer': frm.doc.name}, ['name', 'sync_status', 'wc_customer_id'])
			.then(r => {
				if (r.message && r.message.name) {
					// Add WooCommerce button
					frm.add_custom_button(__('WooCommerce Customer'), function() {
						frappe.set_route('Form', 'WooCommerce Customer', r.message.name);
					}, __('View'));
				}
			});
	}
});

// WooCommerce Settings form
frappe.ui.form.on('WooCommerce Settings', {
	refresh: function(frm) {
		// Add test connection button
		frm.add_custom_button(__('Test Connection'), function() {
			ricco_woocommerce.test_connection(frm.doc.name);
		}, __('Actions'));

		// Add sync buttons
		if (frm.doc.is_active) {
			frm.add_custom_button(__('Sync Products'), function() {
				ricco_woocommerce.manual_sync('products', 'both');
			}, __('Sync'));

			frm.add_custom_button(__('Sync Orders'), function() {
				ricco_woocommerce.manual_sync('orders');
			}, __('Sync'));

			frm.add_custom_button(__('Sync Customers'), function() {
				ricco_woocommerce.manual_sync('customers');
			}, __('Sync'));

			frm.add_custom_button(__('Sync Inventory'), function() {
				ricco_woocommerce.manual_sync('inventory');
			}, __('Sync'));

			// Register webhooks
			if (frm.doc.enable_webhooks) {
				frm.add_custom_button(__('Register Webhooks'), function() {
					frappe.call({
						method: 'ricco_woocommerce.api.webhook_handler.register_webhooks',
						args: {
							settings_name: frm.doc.name
						},
						freeze: true,
						callback: function(r) {
							if (r.message && r.message.success) {
								frappe.show_alert({
									message: __('Webhooks registered'),
									indicator: 'green'
								}, 5);
							}
						}
					});
				}, __('Actions'));
			}
		}

		// Show webhook endpoints
		if (frm.doc.enable_webhooks) {
			frm.add_custom_button(__('Get Webhook Endpoints'), function() {
				frappe.call({
					method: 'ricco_woocommerce.api.webhook_handler.get_webhook_endpoints',
					callback: function(r) {
						if (r.message) {
							frappe.msgprint({
								title: __('Webhook Configuration'),
								message: `
									<p><strong>Webhook URL:</strong><br>
									<code>${r.message.webhook_url}</code></p>
									<p><strong>Available Topics:</strong></p>
									<ul>
										${r.message.topics.map(t => `<li>${t}</li>`).join('')}
									</ul>
								`,
								indicator: 'blue'
							});
						}
					}
				});
			}, __('Actions'));
		}
	}
});

// Console log for debugging
console.log('Ricco WooCommerce Integration loaded');
