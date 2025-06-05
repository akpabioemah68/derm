import xmlrpc.client
import pandas as pd
import os

# Load Excel file from same directory
file_name = 'stock.xlsx'
file_path = os.path.join(os.path.dirname(__file__), file_name)
df = pd.read_excel(file_path)

# Odoo XML-RPC connection details (change to match your instance)
url = 'https://your-odoo-instance.com'     # ← Replace
db = 'derm'                  # ← Replace
username = 'mailesom@gmail.com'                 # ← Replace
password = 'almond.2'                 # ← Replace

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Helper: Get or create category
def get_or_create_category(name):
    cat = models.execute_kw(db, uid, password, 'product.category', 'search_read', [[['name', '=', name]]], {'limit': 1})
    if cat:
        return cat[0]['id']
    return models.execute_kw(db, uid, password, 'product.category', 'create', [{'name': name}])

# Loop through rows and update products
for index, row in df.iterrows():
    name = row['Product Name']
    sale_price = row['Sale Price']
    supplier_cost = row['Suppier Cost price NGN Naira']
    qty = row['Quantity On Hold']
    category_name = row['Category']

    # Find product by name
    product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['name', '=', name]]], {'limit': 1})
    if not product_ids:
        print(f" Product not found: {name}")
        continue
    product_id = product_ids[0]

    # Get or create category
    category_id = get_or_create_category(category_name)

    # Update product info
    models.execute_kw(db, uid, password, 'product.product', 'write', [[product_id], {
        'list_price': sale_price,
        'standard_price': supplier_cost,
        'categ_id': category_id,
    }])

    # Inventory adjustment: set quantity on hand
    inventory_id = models.execute_kw(db, uid, password, 'stock.inventory', 'create', [{
        'name': f'Stock Update for {name}',
        'product_ids': [(6, 0, [product_id])],
    }])
    models.execute_kw(db, uid, password, 'stock.inventory', 'action_start', [inventory_id])

    print(f"Updated: {name}")

print("All matching products processed.")
