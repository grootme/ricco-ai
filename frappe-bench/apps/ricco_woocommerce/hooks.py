app_name = "ricco_woocommerce"
app_title = "RICCO WooCommerce"
app_publisher = "RICCO Team"
app_description = "WooCommerce E-commerce Integration"
app_icon = "octicon octicon-globe"
app_color = "#9B59B6"
app_email = "team@riccoerp.com"
app_license = "MIT"
required_apps = ["frappe", "erpnext"]

app_include_js = "/assets/ricco_woocommerce/js/woocommerce.js"

doc_events = {
    "Item": {
        "on_update": "ricco_woocommerce.overrides.item.sync_to_woocommerce",
        "on_trash": "ricco_woocommerce.overrides.item.delete_from_woocommerce"
    },
    "Sales Order": {
        "on_submit": "ricco_woocommerce.overrides.sales_order.update_woocommerce_order"
    }
}

scheduler_events = {
    "all": ["ricco_woocommerce.tasks.sync_orders"],
    "hourly": ["ricco_woocommerce.tasks.sync_products", "ricco_woocommerce.tasks.sync_inventory"]
}
