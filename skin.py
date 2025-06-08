import xmlrpc.client

# ---------------------------
# Odoo Configuration
# ---------------------------
ODOO_URL = 'https://skinpulse.online'
ODOO_DB = 'new2'
ODOO_USERNAME = 'oga@skinpulse.online'
ODOO_PASSWORD = 'pr355ON@2020'

# ---------------------------
# Connect to Odoo
# ---------------------------
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

# ---------------------------
# Fetch Purchase Orders (RFQ or Confirmed)
# ---------------------------
# You can change 'purchase' to 'draft' to include RFQs
po_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'purchase.order', 'search',
    [[('state', 'in', ['purchase', 'done'])]]  # or add 'draft'
)

purchase_orders = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'purchase.order', 'read',
    [po_ids],
    {'fields': ['name', 'order_line']}
)

# ---------------------------
# Process Each Purchase Order
# ---------------------------
for po in purchase_orders:
    print(f"Processing PO: {po['name']}")
    for line_id in po['order_line']:
        line_data = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'purchase.order.line', 'read',
            [[line_id]],
            {'fields': ['product_id', 'product_qty', 'price_unit']}
        )[0]

        product_id, product_name = line_data['product_id']
        purchase_qty = line_data['product_qty']
        cost = line_data['price_unit']
        sale_price = cost * 1.5  # Optional: markup logic

        # Fetch existing product data
        product_data = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'read',
            [[product_id]],
            {'fields': ['qty_available', 'standard_price', 'list_price']}
        )[0]

        updated_qty = product_data['qty_available'] + purchase_qty

        # Update the product with new values
        update_success = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'write',
            [[product_id], {
                'standard_price': cost,
                'list_price': sale_price,
                # NOTE: Do not update qty_available directly in production
            }]
        )

        print(f"✔ Updated '{product_name}': Qty +{purchase_qty}, Cost = {cost}, Sale = {sale_price}")

        # Simulate quantity update log (informational)
        print(f"ℹ Current stock: {product_data['qty_available']} → New: {updated_qty}")

