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

print("🔗 Connected to Odoo\n")

# ---------------------------
# Step 1: Get last created product.template
# ---------------------------
last_template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search',
    [[]],
    {'order': 'id desc', 'limit': 1}
)

if not last_template_ids:
    print("❌ No product templates found.")
    exit()

template_id = last_template_ids[0]

template = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [template_id],
    {'fields': ['name', 'type', 'active', 'tracking']}
)[0]

print(f"🆔 Last Product Template ID: {template_id}")
print(f"📦 Name: {template['name']}")
print(f"📂 Type: {template['type']}")
print(f"✅ Active: {template['active']}")
print(f"🔁 Tracking: {template['tracking']}\n")

# ---------------------------
# Step 2: Check associated product.product variants
# ---------------------------
variant_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'search',
    [[['product_tmpl_id', '=', template_id]]]
)

if not variant_ids:
    print("❌ No product.product variant found for this template.")
    print("🚫 This is the likely cause of the Purchase Order error.")
    print("💡 You should create a variant for this product template.")
else:
    print(f"✅ {len(variant_ids)} variant(s) found for this template.")

    for variant_id in variant_ids:
        variant = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'read',
            [variant_id],
            {'fields': ['id', 'default_code', 'active', 'qty_available']}
        )[0]

        print(f"   ➤ Variant ID: {variant['id']}, Internal Ref: {variant.get('default_code')}, Qty On Hand: {variant['qty_available']}, Active: {variant['active']}")

# ---------------------------
# Optional: Suggest fix
# ---------------------------
if not variant_ids:
    print("\n🔧 Suggested Fix:")
    print("Use the following code to create a missing variant:\n")
    print(f"""models.execute_kw(
    '{ODOO_DB}', uid, '{ODOO_PASSWORD}',
    'product.product', 'create',
    [{{
        'product_tmpl_id': {template_id},
        'name': '{template['name']}',
    }}]
)""")

print("\n✅ Diagnosis complete.")
