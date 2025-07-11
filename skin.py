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
# Get Last 26 Product Templates (Sorted by ID DESC)
# ---------------------------
template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search',
    [[]],
    {'order': 'id desc', 'limit': 26}
)

templates = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [template_ids],
    {'fields': ['id', 'name', 'standard_price']}
)

# ---------------------------
# Get Product Variants for These Templates
# ---------------------------
template_to_variant = {}

for tmpl in templates:
    tmpl_id = tmpl['id']
    variant_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.product', 'search',
        [[('product_tmpl_id', '=', tmpl_id)]]
    )

    if not variant_ids:
        print(f"⚠️ No variant found for template '{tmpl['name']}' (ID: {tmpl_id})")
        continue

    template_to_variant[tmpl_id] = {
        'template': tmpl,
        'variants': variant_ids
    }

# ---------------------------
# Update Variant Cost from Template Cost
# ---------------------------
updated = 0

for tmpl_id, info in template_to_variant.items():
    template = info['template']
    variant_ids = info['variants']
    cost = template['standard_price']

    try:
        success = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'write',
            [variant_ids, {'standard_price': cost}]
        )
        print(f"✅ Updated cost on {len(variant_ids)} variant(s) of '{template['name']}' to {cost}")
        updated += len(variant_ids)
    except Exception as e:
        print(f"❌ Error updating cost for template '{template['name']}' - {e}")

# ---------------------------
# Summary
# ---------------------------
print(f"\n📊 Updated cost on {updated} variants across {len(template_to_variant)} templates.")
