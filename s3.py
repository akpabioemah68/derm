import xmlrpc.client
import pandas as pd
import os

# Load Excel file from current directory
file_name = 'stock.xlsx'
file_path = os.path.join(os.path.dirname(__file__), file_name)

# Read Excel
df = pd.read_excel(file_path)

# Odoo XML-RPC connection setup
url = 'https://dermaky.xyz'  # Change to your Odoo URL
db = 'derm'
username = 'mailesom@gmail.com'
password = 'almond.2'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Helper: Get category ID by name or create it
def get_or_create_category(name):
    category = models.execute_kw(db, uid, password,
        'product.category', 'search_read',
        [[['name', '=', name]]], {'limit': 1})
    if category:
        return category[0]['id']
    else:
        return models.execute_kw(db, uid, password,
            'product.category', 'create',
            [{'name': name}])

# Loop through each row in Excel
for index, row in df.iterrows():
    product_name = row['Product Name']
    sale_price = row['Sale Price']
    category_name = row['Category']
    supplier_cost = row['Suppier Cost']
    qty_on_hand = row['Quantity On Hand']

    # Find product by name
    product_ids = models.execute_kw(db, uid, password,
        'product.product', 'search',
        [[['name', '=', product_name]]], {'limit': 1})
    
    if not product_ids:
        print(f" Product not found: {product_name}")
        continue
    
    product_id = product_ids[0]

    # Get category ID (create if not exists)
    category_id = get_or_create_category(category_name)

    # Update product
    models.execute_kw(db, uid, password,
        'product.product', 'write',
        [[product_id], {
            'list_price': sale_price,
            'standard_price': supplier_cost,
            'categ_id': category_id,
        }])
    
    # Adjust inventory using `stock.quant` (Quantity On Hand)
    product = models.execute_kw(db, uid, password,
        'product.product', 'read',
        [product_ids], {'fields': ['id', 'name', 'type']})[0]

    inventory_adjustment = models.execute_kw(db, uid, password,
        'stock.inventory', 'create',
        [{
            'name': f'Update Qty for {product_name}',
            'product_ids': [(6, 0, [product_id])],
            'location_ids': [(6, 0, [])],  # Empty = all locations
        }])
    
    models.execute_kw(db, uid, password,
        'stock.inventory', 'action_start', [inventory_adjustment])

    print(f" Updated: {product_name}")

