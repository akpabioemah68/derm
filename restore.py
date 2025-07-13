import xmlrpc.client

# === Configuration ===
url = "http://localhost:8069"  # Assuming script is run from server
dbname = "new2"
username = "mailesom@gmail.com"
password = "pr355ON@2020"
product_id = 200

# === Connect to Odoo ===
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(dbname, username, password, {})
if not uid:
    raise Exception("Failed to authenticate")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# === Step 1: Check if product is 'Storable' ===
product = models.execute_kw(
    dbname, uid, password,
    'product.product', 'read',
    [product_id],
    {'fields': ['name', 'type']}
)[0]

# === Step 2: Get Quantity on Hand from internal locations ===
quants = models.execute_kw(
    dbname, uid, password,
    'stock.quant', 'search_read',
    [[('product_id', '=', product_id), ('location_id.usage', '=', 'internal')]],
    {'fields': ['location_id', 'quantity']}
)
total_on_hand = sum(q['quantity'] for q in quants)

# === Step 3: Check receipts (stock.moves) ===
stock_moves = models.execute_kw(
    dbname, uid, password,
    'stock.move', 'search_read',
    [[
        ('product_id', '=', product_id),
        ('state', '=', 'done'),
        ('picking_type_id.code', '=', 'incoming')
    ]],
    {'fields': ['reference', 'product_uom_qty', 'location_dest_id', 'quantity_done', 'date'], 'order': 'date desc'}
)

# === Step 4: Check if quants are in incorrect locations (not internal) ===
all_quants = models.execute_kw(
    dbname, uid, password,
    'stock.quant', 'search_read',
    [[('product_id', '=', product_id)]],
    {'fields': ['location_id', 'quantity']}
)

total_non_internal = sum(q['quantity'] for q in all_quants if q['location_id'][1] not in [l['location_id'][1] for l in quants])

# === Output ===
report = {
    'Product Name': product['name'],
    'Product Type': product['type'],
    'Quantity On Hand (internal)': total_on_hand,
    'Received & Validated Moves': stock_moves,
    'All Quants': all_quants,
    'Qty Outside Internal Locations': total_non_internal
}

import pprint
pprint.pprint(report)
