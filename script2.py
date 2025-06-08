import pandas as pd
import xmlrpc.client
import os

# ==== Odoo Credentials ====
odoo_url = "https://dermaky.xyz"
db = "derm"
username = "mailesom@gmail.com"
password = "almond.2"

# ==== Connect to Odoo ====
common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object")

# ==== Load Excel ====
file_path = os.path.join(os.path.dirname(__file__), 'Stock.xlsx')
df = pd.read_excel(file_path)

# ==== Get Default Internal Location ====
location_ids = models.execute_kw(db, uid, password,
    'stock.location', 'search', [[['usage', '=', 'internal']]], {'limit': 1})
if not location_ids:
    print("❌ No internal location found.")
    exit()
location_id = location_ids[0]

# ==== Process Each Row ====
for index, row in df.iterrows():
    product_name = row.get('Product Name')
    qty_on_hold = row.get('Quantity On Hold', 0)
    qty_ordered = row.get('quantity_ordered', 0)

    if pd.isna(product_name) or qty_ordered <= 0:
        continue

    print(f"\n▶ Processing: {product_name}")

    # Search for product by name
    product_ids = models.execute_kw(db, uid, password,
        'product.product', 'search', [[['name', '=', product_name]]], {'limit': 1})
    if not product_ids:
        print(f"❌ Product not found: {product_name}")
        continue
    product_id = product_ids[0]

    # Search for stock.quant
    quant_ids = models.execute_kw(db, uid, password,
        'stock.quant', 'search', [[
            ['product_id', '=', product_id],
            ['location_id', '=', location_id]
        ]], {'limit': 1})

    if quant_ids:
        # Update existing quant
        quant_id = quant_ids[0]
        quant_data = models.execute_kw(db, uid, password,
            'stock.quant', 'read', [quant_ids], {'fields': ['quantity']})
        current_qty = quant_data[0]['quantity']
        new_qty = max(0, current_qty - qty_ordered)

        models.execute_kw(db, uid, password,
            'stock.quant', 'write', [[quant_id], {'quantity': new_qty}])

        print(f"✅ Updated stock: {product_name} | {current_qty} → {new_qty}")

    else:
        # Create quant with adjusted quantity
        initial_qty = max(0, qty_on_hold - qty_ordered)
        quant_id = models.execute_kw(db, uid, password,
            'stock.quant', 'create', [{
                'product_id': product_id,
                'location_id': location_id,
                'quantity': initial_qty
            }])

        print(f"✅ Created stock.quant for {product_name} with quantity {initial_qty}")

print("\n✅ Stock update process complete.")
        
