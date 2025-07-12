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
# Get Last 26 Product Templates
# ---------------------------
template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search',
    [[]],
    {'order': 'id desc', 'limit': 26}
)

# ---------------------------
# Inspect Each Template
# ---------------------------
for template_id in template_ids:
    template = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.template', 'read',
        [template_id],
        {'fields': ['name', 'type', 'qty_available', 'purchase_count', 'tracking']}
    )[0]

    print("\n============================")
    print(f"Template ID: {template_id}")
    print(f"Name: {template['name']}")
    print(f"Type: {template['type']}")
    print(f"Tracking: {template['tracking']}")
    print(f"Qty On Hand: {template['qty_available']}")
    print(f"Units Purchased: {template['purchase_count']}")

    if template['type'] != 'product':
        print("⚠️  Not a storable product (type != 'product')")
        continue

    # Get product.product variant(s) for this template
    variant_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.product', 'search',
        [[['product_tmpl_id', '=', template_id]]]
    )

    if not variant_ids:
        print("❌ No product variants found.")
        continue

    for variant_id in variant_ids:
        variant = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'read',
            [variant_id],
            {'fields': ['default_code', 'qty_available']}
        )[0]

        print(f"  ➤ Variant ID: {variant_id}, Internal Ref: {variant.get('default_code')}, Qty: {variant['qty_available']}")

        # Check stock.quant (per location)
        quant_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.quant', 'search_read',
            [[['product_id', '=', variant_id]]],
            {'fields': ['location_id', 'quantity']}
        )

        if not quant_ids:
            print("    ⚠️ No stock.quant entries.")
        else:
            for quant in quant_ids:
                location = quant['location_id'][1] if quant['location_id'] else 'Unknown'
                print(f"    🏬 Location: {location}, Quantity: {quant['quantity']}")

print("\n✅ Finished inventory diagnostics.")
