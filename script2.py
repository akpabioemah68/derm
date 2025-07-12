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
# Step 1: Fetch all purchase order lines
# ---------------------------
print("🔍 Scanning all purchase.order.line records...")

po_lines = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'purchase.order.line', 'search_read',
    [[]],
    {'fields': ['id', 'product_id', 'order_id']}
)

relinked_count = 0

for line in po_lines:
    pol_id = line['id']
    product_data = line.get('product_id')
    order_id = line.get('order_id')[0] if line.get('order_id') else None

    if not product_data:
        print(f"❌ POL ID {pol_id} has no product_id — skipping.")
        continue

    variant_id = product_data[0]

    # Try to read the variant to confirm it still exists
    try:
        variant = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'read',
            [variant_id],
            {'fields': ['id', 'product_tmpl_id', 'name']}
        )[0]
        # Variant exists, all good
        continue
    except:
        # Broken link — product.product record deleted
        print(f"⚠️ POL ID {pol_id} references missing variant ID {variant_id} → attempting repair...")

        # Get template_id from purchase.order.line's name or original data (not always available)
        # Here we assume it had a link to a template with same ID (or via backup)
        # So we find the closest match by assuming variant_id == template_id (fallback)
        # In real-world, we would store this somewhere safer

        # Check if template with same ID as variant exists
        template_id = variant_id

        template_exists = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'search',
            [[['id', '=', template_id]]]
        )

        if not template_exists:
            print(f"  🚫 product.template ID {template_id} not found. Cannot repair POL {pol_id}.")
            continue

        # Read template info
        template = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'read',
            [template_id],
            {'fields': ['name']}
        )[0]

        # Recreate variant
        new_variant_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'create',
            [{
                'product_tmpl_id': template_id,
                'name': template['name'],
            }]
        )

        print(f"  ✅ Created new variant ID {new_variant_id} for template {template_id} ({template['name']})")

        # Update purchase order line with new variant
        models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'purchase.order.line', 'write',
            [[pol_id], {'product_id': new_variant_id}]
        )

        print(f"  🔁 Re-linked POL ID {pol_id} to new variant ID {new_variant_id}")
        relinked_count += 1

print(f"\n✅ Repair complete. Total PO lines re-linked: {relinked_count}")
