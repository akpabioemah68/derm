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
# Find product.template records with NO variants
# ---------------------------
# Step 1: Get all product.template IDs
template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search', [[]]
)

print(f"🔍 Total product templates found: {len(template_ids)}")

# Step 2: Loop through templates and find those without variants
template_ids_no_variant = []

for template_id in template_ids:
    variant_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.product', 'search',
        [[('product_tmpl_id', '=', template_id)]]
    )
    if not variant_ids:
        template_ids_no_variant.append(template_id)

print(f"⚠ Templates with NO variants: {len(template_ids_no_variant)}")

# Step 3: Read product.template records without variants
templates_without_variants = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [template_ids_no_variant],
    {'fields': ['name', 'default_code', 'attribute_line_ids', 'type']}
)

# Step 4: Display info and potential issues
print("\n🟠 List of product.template records without variants:")
for template in templates_without_variants:
    name = template.get('name')
    code = template.get('default_code', 'N/A')
    attr_lines = template.get('attribute_line_ids', [])
    product_type = template.get('type', 'N/A')

    reason = "❌ No attribute lines" if not attr_lines else "⚠ Variants not generated"
    
    print(f"- Name: {name}, Code: {code}, Type: {product_type}")
    print(f"  ⛔ Reason: {reason}")
    print("")

# ---------------------------
# Summary
# ---------------------------
print("✅ Done. You may consider regenerating variants via UI or code if needed.")
