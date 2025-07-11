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
# Step 1: Get All product.template IDs
# ---------------------------
template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search', [[]]
)

print(f"🔍 Total product templates found: {len(template_ids)}")

# ---------------------------
# Step 2: Find Templates with Attributes but No Variants
# ---------------------------
templates_to_fix = []

for template_id in template_ids:
    variant_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.product', 'search',
        [[('product_tmpl_id', '=', template_id)]]
    )
    if not variant_ids:
        template_data = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'read',
            [[template_id]],
            {'fields': ['name', 'attribute_line_ids']}
        )[0]

        if template_data['attribute_line_ids']:
            templates_to_fix.append({
                'id': template_id,
                'name': template_data['name']
            })

print(f"⚙ Templates eligible for variant generation: {len(templates_to_fix)}")

# ---------------------------
# Step 3: Trigger Variant Generation
# ---------------------------
for template in templates_to_fix:
    # Perform a dummy write on attribute_line_ids to trigger recompute
    result = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.template', 'write',
        [[template['id']], {}]  # Empty write will trigger variant recompute
    )

    print(f"✅ Variants triggered for: {template['name']} (ID: {template['id']})")

# ---------------------------
# Done
# ---------------------------
print("🎉 Variant generation completed for all eligible templates.")
