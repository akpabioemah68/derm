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
# Load product.template and product.product IDs
# ---------------------------
template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search', [[]]
)
product_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'search', [[]]
)

print(f"🔢 Total product.template records: {len(template_ids)}")
print(f"🔢 Total product.product records (variants): {len(product_ids)}")

# ---------------------------
# Get all template IDs linked to products
# ---------------------------
linked_template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'read',
    [product_ids],
    {'fields': ['product_tmpl_id']}
)

linked_ids = set(pt['product_tmpl_id'][0] for pt in linked_template_ids if pt['product_tmpl_id'])

# ---------------------------
# Find product.template IDs NOT in product.product
# ---------------------------
unlinked_template_ids = list(set(template_ids) - linked_ids)

print(f"❌ product.template records NOT linked to any product.product: {len(unlinked_template_ids)}")

# ---------------------------
# Fetch and Display Those Templates
# ---------------------------
templates_not_loaded = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [unlinked_template_ids],
    {'fields': ['name', 'default_code', 'active', 'type', 'attribute_line_ids']}
)

print("\n🛑 Templates missing variants and won't appear in product search:")
for tmpl in templates_not_loaded:
    status = "🟢 Active" if tmpl['active'] else "🔴 Inactive"
    reason = "❌ No attribute lines" if not tmpl['attribute_line_ids'] else "⚠ Variants not generated"
    print(f"- {tmpl['name']} (Code: {tmpl.get('default_code', 'N/A')}_
    
