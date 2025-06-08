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

# ==== Process Each Row ====
for index, row in df.iterrows():
    product_name = row.get('Product Name')
    qty_on_hold = row.get('Quantity On Hold', 0)
    qty_ordered = row.get('Quantity On Hold', 0)

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

    # Search for internal location
    location_ids = models.execute_kw(db, uid, password,
        'stock.location', 'search', [[['usage', '=', 'internal']]], {'limit': 1})
    if not location_ids:
        print(f"❌ No internal location found for: {product_name}")
        continue
    location_id = location_ids[0]

    # Search for stock.quant
    quant_ids = models.execute_kw(db, uid, password,
        'stock.quant', 'search', [[
            ['product_id', '=', product_id],
            ['location_id', '=', location_id]
        ]], {'limit': 1})

    if quant_ids:
        quant_id = quant_ids[0]

        # Read current quantity
        quant_data = models.execute_kw(db, uid, password,
            'stock.quant', 'read', [quant_ids], {'fields': ['quantity']})
        current_qty = quant_data[0]['quantity']
        new_qty = max(0, current_qty - qty_ordered)

        # Update quantity
        models.execute_kw(db, uid, password,
            'stock.quant', 'write', [[quant_id], {'quantity': new_qty}])

        print(f"✅ Updated stock: {product_name} | {current_qty} → {new_qty}")
    else:
        print(f"⚠️ No stock.quant found for: {product_name}")

print("\n✅ Stock update process complete.")
        
