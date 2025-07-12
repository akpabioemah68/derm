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

print("🔎 Scanning for product variants linked to PO lines...\n")

# ---------------------------
# Step 1: Get all product variants
# ---------------------------
variant_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'search',
    [[]]
)

linked_variants = 0
safe_variants = 0

for vid in variant_ids:
    # Count how many PO lines use this variant
    po_line_count = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'purchase.order.line', 'search_count',
        [[['product_id', '=', vid]]]
    )

    if po_line_count > 0:
        product = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'read',
            [vid],
            {'fields': ['name', 'product_tmpl_id']}
        )[0]

        tmpl_id = product['product_tmpl_id'][0]
        tmpl_name = product['name']

        print(f"❌ Variant ID {vid} (Name: {tmpl_name}) is still used in {po_line_count} PO line(s) → Template ID {tmpl_id}")
        linked_variants += 1
    else:
        safe_variants += 1

print(f"\n✅ Check complete. {linked_variants} variants are in use, {safe_variants} are unused.")
print("💡 Do NOT delete products in use. Archive them instead!")
