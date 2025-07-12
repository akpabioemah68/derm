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

print("🔍 Scanning product variants for archiving...\n")

# ---------------------------
# Get all product.product variants
# ---------------------------
variant_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'search',
    [[]]
)

archived_count = 0
in_use_count = 0

for vid in variant_ids:
    # Check if this variant is used in any PO lines
    usage_count = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'purchase.order.line', 'search_count',
        [[['product_id', '=', vid]]]
    )

    if usage_count == 0:
        # Archive it
        models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'write',
            [[vid], {'active': False}]
        )
        print(f"✅ Archived unused variant ID {vid}")
        archived_count += 1
    else:
        in_use_count += 1
        print(f"⏩ Skipped variant ID {vid} — still in use by {usage_count} PO line(s)")

print("\n🎯 Archive Summary:")
print(f"   🔒 Archived: {archived_count} variant(s)")
print(f"   📦 In Use:   {in_use_count} variant(s)")
print("✅ Done.")
