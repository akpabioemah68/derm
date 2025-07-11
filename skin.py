# ---------------------------
# Find Templates Without Variants
# ---------------------------
# Step 1: Get all product.template IDs
template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search', [[]]
)

# Step 2: For each template, check how many variants (product.product) exist
template_ids_no_variant = []

for template_id in template_ids:
    variant_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.product', 'search',
        [[('product_tmpl_id', '=', template_id)]]
    )
    if not variant_ids:
        template_ids_no_variant.append(template_id)

# Step 3: Read template details
templates_without_variants = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [template_ids_no_variant],
    {'fields': ['name', 'default_code', 'attribute_line_ids']}
)

# Step 4: Print details
print("🟠 Templates with NO variants:")
for t in templates_without_variants:
    print(f"- {t['name']} (Code: {t.get('default_code', 'N/A')}, Attributes: {t['attribute_line_ids']})")

# Step 5: Optional analysis
print(f"\n🔎 Total templates: {len(template_ids)}")
print(f"❌ Templates with no variants: {len(template_ids_no_variant)}")
