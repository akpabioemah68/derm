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
# Load All Product Templates
# ---------------------------
template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search', [[]]
)

templates = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [template_ids],
    {'fields': ['id', 'name', 'active']}
)

# ---------------------------
# Load All Product Variants
# ---------------------------
product_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'search', [[]]
)

products = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'read',
    [product_ids],
    {'fields': ['id', 'name', 'product_tmpl_id']}
)

# ---------------------------
# Build Mapping: Template ID → List of Variants
# ---------------------------
from collections import defaultdict

tmpl_to_variants = defaultdict(list)

for product in products:
    tmpl_id = product['product_tmpl_id'][0] if product['product_tmpl_id'] else None
    if tmpl_id:
        tmpl_to_variants[tmpl_id].append(product)

# ---------------------------
# Separate Templates With and Without Variants
# ---------------------------
templates_with_variants = []
templates_without_variants = []

for tmpl in templates:
    tmpl_id = tmpl['id']
    if tmpl_id in tmpl_to_variants:
        templates_with_variants.append({
            'id': tmpl_id,
            'name': tmpl['name'],
            'variants': tmpl_to_variants[tmpl_id]
        })
    else:
        templates_without_variants.append(tmpl)

# ---------------------------
# Display Results
# ---------------------------
print("\n✅ Templates WITH variants:")
for tmpl in templates_with_variants:
    print(f"\n- {tmpl['name']} (ID: {tmpl['id']})")
    for variant in tmpl['variants']:
        print(f"   - Variant: {variant['name']} (ID: {variant['id']})")

print("\n🚫 Templates WITHOUT variants:")
for tmpl in templates_without_variants:
    print(f" - {tmpl['name']} (ID: {tmpl['id']})")

# ---------------------------
# Summary
# ---------------------------
print("\n📊 Summary:")
print(f"Total product.template records: {len(templates)}")
print(f"Templates WITH variants: {len(templates_with_variants)}")
print(f"Templates WITHOUT variants: {len(templates_without_variants)}")
