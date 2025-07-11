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
    {'fields': ['id', 'name', 'default_code', 'type', 'uom_id', 'uom_po_id', 'list_price', 'standard_price', 'categ_id']}
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
# Build Mapping: template_id → variants
# ---------------------------
from collections import defaultdict

tmpl_to_variants = defaultdict(list)
for prod in products:
    tmpl_id = prod['product_tmpl_id'][0] if prod['product_tmpl_id'] else None
    if tmpl_id:
        tmpl_to_variants[tmpl_id].append(prod)

# ---------------------------
# Identify Templates Without Variants and Create Them
# ---------------------------
created_count = 0

for tmpl in templates:
    tmpl_id = tmpl['id']
    if tmpl_id not in tmpl_to_variants:
        try:
            variant_id = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'product.product', 'create',
                [{
                    'product_tmpl_id': tmpl_id,
                    'name': tmpl['name'],
                    'default_code': tmpl.get('default_code', False),
                    'type': tmpl.get('type', 'product'),
                    'uom_id': tmpl['uom_id'][0] if tmpl['uom_id'] else None,
                    'uom_po_id': tmpl['uom_po_id'][0] if tmpl['uom_po_id'] else None,
                    'list_price': tmpl['list_price'],
                    'standard_price': tmpl['standard_price'],
                    'categ_id': tmpl['categ_id'][0] if tmpl['categ_id'] else None,
                }]
            )
            print(f"✅ Created variant for template '{tmpl['name']}' (Template ID: {tmpl_id}) → Variant ID: {variant_id}")
            created_count += 1
        except Exception as e:
            print(f"❌ Failed to create variant for template '{tmpl['name']}' (ID: {tmpl_id}) - {e}")

# ---------------------------
# Summary
# ---------------------------
print(f"\n📊 Summary: Created {created_count} missing variants.")
            
