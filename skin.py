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
# Load All product.template
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
# Load All product.product and Map to Template
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

from collections import defaultdict

tmpl_to_variants = defaultdict(list)
for product in products:
    tmpl_id = product['product_tmpl_id'][0] if product['product_tmpl_id'] else None
    if tmpl_id:
        tmpl_to_variants[tmpl_id].append(product)

# ---------------------------
# Trigger Variant Creation for Templates Without Any
# ---------------------------
templates_missing_variants = []

for tmpl in templates:
    tmpl_id = tmpl['id']
    if tmpl_id not in tmpl_to_variants:
        # Add to list for reporting
        templates_missing_variants.append(tmpl)

        # Trigger Odoo to generate a variant (write with empty dict)
        try:
            models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'write',
                [[tmpl_id], {}]
            )
            print(f"✅ Created variant for: {tmpl['name']} (Template ID: {tmpl_id})")
        except Exception as e:
            print(f"❌ Failed to create variant for: {tmpl['name']} (ID: {tmpl_id}) - {e}")

# ---------------------------
# Summary
# ---------------------------
print("\n📊 Variant Creation Summary:")
print(f"Total templates without variants before fix: {len(templates_missing_variants)}")
