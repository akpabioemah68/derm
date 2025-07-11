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
# Step 1: Load all product.template records
# ---------------------------
template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search', [[]]
)
templates = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [template_ids],
    {'fields': ['name', 'active']}
)

print(f"🔢 Total product.template records: {len(templates)}")

# ---------------------------
# Step 2: Load all product.product records (variants)
# ---------------------------
product_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'search', [[]]
)
products = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'read',
    [product_ids],
    {'fields': ['id', 'product_tmpl_id', 'name', 'default_code', 'active']}
)

print(f"🔢 Total product.product (variant) records: {len(products)}")

# ---------------------------
# Step 3: Build reverse index: template_id → list of variants
# ---------------------------
tmpl_to_products = {}
for prod in products:
    tmpl_id = prod['product_tmpl_id'][0] if prod['product_tmpl_id'] else None
    if tmpl_id:
        tmpl_to_products.setdefault(tmpl_id, []).append(prod)

# ---------------------------
# Step 4: Analyze missing or invalid variants
# ---------------------------
missing_variant_templates = []
inactive_variant_templates = []
invalid_variant_templates = []

for tmpl in templates:
    tmpl_id = tmpl['id']
    tmpl_name = tmpl['name']
    tmpl_active = tmpl['active']
    linked_variants = tmpl_to_products.get(tmpl_id, [])

    if not linked_variants:
        missing_variant_templates.append(tmpl)
    else:
        has_active = any(p['active'] for p in linked_variants)
        has_searchable = any(p['name'] or p['default_code'] for p in linked_variants)

        if not has_active:
            inactive_variant_templates.append(tmpl)
        elif not has_searchable:
            invalid_variant_templates.append(tmpl)

# ---------------------------
# Step 5: Report Results
# ---------------------------
print("\n🚫 Templates with NO variants:")
for tmpl in missing_variant_templates:
    print(f" - {tmpl['name']} (ID: {tmpl['id']})")

print("\n⚠ Templates with only INACTIVE variants:")
for tmpl in inactive_variant_templates:
    print(f" - {tmpl['name']} (ID: {tmpl['id']})")

print("\n⚠ Templates with variants missing name/default_code:")
for tmpl in invalid_variant_templates:
    print(f" - {tmpl['name']} (ID: {tmpl['id']})")

# ---------------------------
# Summary
# ---------------------------
print(f"\nSummary:")
print(f"❌ Missing variants: {len(missing_variant_templates)}")
print(f"🟡 Inactive variants: {len(inactive_variant_templates)}")
print(f"🟠 Variants missing name/code: {len(invalid_variant_templates)}")
print(f"✅ Valid templates with good variants: {len(template_ids) - len(missing_variant_templates) - len(inactive_variant_templates) - len(invalid_variant_templates)}")
