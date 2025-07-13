import xmlrpc.client

# ==== Configuration ====
ODOO_URL = 'https://skinpulse.online'
ODOO_DB = 'new2'
ODOO_USERNAME = 'oga@skinpulse.online'
ODOO_PASSWORD = 'pr355ON@2020'
PRODUCT_ID = 200

# ==== Connect to Odoo ====
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})

if not uid:
    raise Exception("Failed to authenticate to Odoo")

models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

# ==== 1. Get Product Info ====
product = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.product', 'read',
    [PRODUCT_ID],
    {'fields': ['name', 'type']}
)

if not product:
    raise Exception(f"Product with ID {PRODUCT_ID} not found")

product_name = product[0]['name']
product_type = product[0]['type']

if product_type != 'product':
    print(f"⚠️ Product {product_name} is not a storable product (type: {product_type}). Stock not tracked.")
    exit()

# ==== 2. Check Quantity On Hand in Internal Locations ====
quants = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'stock.quant', 'search_read',
    [[('product_id', '=', PRODUCT_ID), ('location_id.usage', '=', 'internal')]],
    {'fields': ['quantity', 'location_id']}
)
qty_on_hand = sum(q['quantity'] for q in quants)

# ==== 3. Check All Quants (even if not in internal locations) ====
all_quants = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'stock.quant', 'search_read',
    [[('product_id', '=', PRODUCT_ID)]],
    {'fields': ['quantity', 'location_id']}
)
qty_total_all_locations = sum(q['quantity'] for q in all_quants)

# ==== 4. Check Validated Incoming Stock Moves ====
stock_moves = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'stock.move', 'search_read',
    [[
        ('product_id', '=', PRODUCT_ID),
        ('state', '=', 'done'),
        ('picking_type_id.code', '=', 'incoming'),
    ]],
    {'fields': ['reference', 'product_uom_qty', 'location_dest_id', 'date'], 'order': 'date desc'}
)

# ==== 5. Print Summary ====
print(f"\n📦 Product: {product_name} (ID: {PRODUCT_ID})")
print(f"🧮 Quantity On Hand (Internal Locations): {qty_on_hand}")
print(f"🌐 Total Quantity Across All Locations: {qty_total_all_locations}")
print(f"📥 Validated Incoming Receipts (POs):")

if not stock_moves:
    print("❌ No validated stock moves (receipts) found.")
else:
    for move in stock_moves:
        print(f"  - {move['reference']} | Qty: {move['product_uom_qty']} → {move['location_dest_id'][1]} | {move['date']}")

if qty_on_hand == 0 and qty_total_all_locations > 0:
    print("\n⚠️ Inventory may be in the wrong location (not in an internal location).")
elif qty_on_hand == 0:
    print("\n❌ Stock has not been received or confirmed properly.")
else:
    print("\n✅ Stock is properly tracked in internal locations.")
        
