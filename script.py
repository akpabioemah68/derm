import xmlrpc.client

# ---------------- ODOO CONNECTION DETAILS ----------------
odoo_url = "https://dermaky.xyz"
db = "derm"
username = "mailesom@gmail.com"
password = "almond.2"

# ---------------- CONNECT TO ODOO ----------------
common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(odoo_url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(odoo_url))

# ---------------- HARDCODED DATA FROM EXCEL ----------------
products_data = [
    {
        "name": "COSRX Advanced Snail 92 All in One Cream (100g)",
        "cost": 13000,
        "price": 17,
        "quantity": 3
    },
    {
        "name": "COSRX Advanced Snail Radiance Dual Essence (80ml)",
        "cost": 20500,
        "price": 23,
        "quantity": 5
    },
    {
        "name": "COSRX Advanced Snail 96 Mucin Power Essence (100ml)",
        "cost": 12800,
        "price": 17,
        "quantity": 5
    },
    {
        "name": "COSRX Full Fit Propolis Light Cream (65ml)",
        "cost": 20500,
        "price": 18,
        "quantity": 5
    },
    {
        "name": "COSRX Hyaluronic Acid Hydra Power Essence (100ml)",
        "cost": 13100,
        "price": 16,
        "quantity": 5
    },
]

# ---------------- UPDATE PRODUCTS IN ODOO ----------------
for product in products_data:
    name = product["name"]
    cost = float(str(product["cost"]).replace(",", "").replace("/", ""))
    price = float(product["price"])
    quantity = float(product["quantity"])

    product_ids = models.execute_kw(db, uid, password,
        'product.template', 'search',
        [[['name', '=', name]]])

    if product_ids:
        product_id = product_ids[0]

        models.execute_kw(db, uid, password, 'product.template', 'write',
            [[product_id], {
                'standard_price': cost,
                'list_price': price
            }])

        product_variant_ids = models.execute_kw(db, uid, password,
            'product.product', 'search',
            [[['product_tmpl_id', '=', product_id]]])

        if product_variant_ids:
            product_variant_id = product_variant_ids[0]

            models.execute_kw(db, uid, password, 'stock.change.product.qty', 'create', [{
                'product_id': product_variant_id,
                'new_quantity': quantity
            }])

            print("Updated: {}".format(name))
        else:
            print("Variant not found for: {}".format(name))
    else:
        print("Product not found: {}".format(name))
