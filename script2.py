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
# Step 1: Get last created product.template
# ---------------------------
last_template_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search',
    [[]],
    {'order': 'id desc', 'limit': 1}
)

if not last_template_ids:
    print("❌ No product templates found.")
    exit()

template_id = last_template_ids[0]

template = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [template_id],
    {'fields': ['name', 'type', 'active', 'tracking']}
)[0]

print(f"🆔 Product Template ID: {template_id}")
print(f"📦 Name: {template['name']}")
print(f"📂 Type: {template['type']}")
print(f"✅ Active: {template['active']}")
print(f"🔁 Tracking: {template['tracking']}\n")

# ---------------------------
# Step 2: Get product.product variants
# ---------------------------
variant_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'search',
    [[['product_tmpl_id', '=', template_id]]]
)

if not variant_ids:
    print("❌ No product variant found — cannot check purchase.order.line references.")
    exit()

variant_id = variant_ids[0]
print(f"🔍 Checking PO Lines for Variant ID: {variant_id}\n")

# ---------------------------
# Step 3: Check purchase.order.line entries referencing the variant
# ---------------------------
po_lines = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'purchase.order.line', 'search_read',
    [[['product_id', '=', variant_id]]],
    {'fields': ['id', 'order_id', 'product_id']}
)

if not po_lines:
    print("✅ No Purchase Order Lines currently reference this product variant.")
else:
    print(f"⚠️ {len(po_lines)} Purchase Order Line(s) reference this product variant:")
    for line in po_lines:
        po_id = line['order_id'][0] if line['order_id'] else "❓ Unknown"
        print(f" - POL ID {line['id']} belongs to Purchase Order ID {po_id}")

print("\n✅ PO Line reference check complete.")
