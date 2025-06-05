import xmlrpc.client
import pandas as pd
import os

# Load Excel file
file_name = 'Stock.xlsx'
file_path = os.path.join(os.path.dirname(__file__), file_name)
df = pd.read_excel(file_path)

# Odoo connection details
url = 'https://dermaky.xyz'     # ← Replace with your URL
db = 'derm'                  # ← Replace with your DB
username = 'mailesom@gmail.com'                 # ← Replace with your username
password = 'almomd.2'                 # ← Replace with your password

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Get default internal location (WH/Stock)
location_id = 1

# Get or create category
def get_or_create_category(name):
    cat = models.execute_kw(db, uid, password, 'product.category', 'search_read', [[['name', '=', name]]], {'limit': 1})
    if cat:
        return cat[0]['id']
    return models.execute_kw(db, uid, password, 'product.category', 'create', [{'name': name}])

# Process each row
for index, row in df.iterrows():
    name = row['Product Name']
    sale_price = row['Sale Price']
    supplier_cost = row['Suppier Cost price NGN Naira']
    qty = row['Quantity On Hold']
    category_name = row['Category']

    # Find product by name
    product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['name', '=', name]]], {'limit': 1})
    if not product_ids:
        print(f"Product not found: {name}")
        continue
    product_id = product_ids[0]

    # Update pricing and category
    category_id = get_or_create_category(category_name)
    models.execute_kw(db, uid, password, 'product.product', 'write', [[product_id], {
        'list_price': sale_price,
        'standard_price': supplier_cost,
        'categ_id': category_id,
    }])

    # Update quantity via stock.quant
    quant_ids = models.execute_kw(db, uid, password,
        'stock.quant', 'search',
        [[['product_id', '=', product_id], ['location_id', '=', location_id]]],
        {'limit': 1})

    if quant_ids:
        models.execute_kw(db, uid, password,
            'stock.quant', 'write',
            [[quant_ids[0]], {'quantity': qty}])
    else:
        models.execute_kw(db, uid, password,
            'stock.quant', 'create',
            [{
                'product_id': product_id,
                'location_id': location_id,
                'quantity': qty,
            }])

    print(f" Updated: {name}")

print(" All done.")
