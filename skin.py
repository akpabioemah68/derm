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

# Get linked template IDs from product.product
linked_templates = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'read',
    [product_ids],
    {'fields': ['product_tmpl_id']}
)

linked_template_ids = set([x['product_tmpl_id'][0] for x in linked_templates if x['product_tmpl_id']])

# Find templates that are not linked
unlinked_template_ids = list(set(template_ids) - linked_template_ids)

print(f"🔍 Found {len(unlinked_template_ids)} product.template records with NO variants.")

# ---------------------------
# Generate Variants for Missing Templates
# ---------------------------
for tmpl_id in unlinked_template_ids:
    tmpl_data = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.template', 'read',
        [[tmpl_id]],
        {'fields': ['name', 'attribute_line_ids', 'active']}
    )[0]

    name = tmpl_data['name']
    attr_lines = tmpl_data['attribute_line_ids']
    active = tmpl_data['active']

    # Trigger variant generation by writing to attribute_line_ids (or even empty write)
    result = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.template', 'write',
        [[tmpl_id], {}]  # Empty write triggers recompute and variant generation
    )

    print(f"✅ Generated variants for: {name} (ID: {tmpl_id}) | Attributes: {'Yes' if attr_lines else 'No'} | {'Active' if active else 'Inactive'}")

# ---------------------------
# Final Check (Optional)
# ---------------------------
print("\n🎉 All missing variants generated. You can rerun the check script to confirm.")
