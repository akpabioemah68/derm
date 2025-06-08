import xmlrpc.client
import requests
import json

# ---------------------------
# Configuration
# ---------------------------
ODOO_URL = 'https://dermaky.com'
ODOO_DB = 'derm'
ODOO_USERNAME = 'mailesom@gmail.com'
ODOO_PASSWORD = 'almond.2'

WC_BASE_URL = "https://dermaky.com/wp-json/wc/v3"
WC_CONSUMER_KEY = "ck_191d2768e3e355cce69d59f7fb7a9f79e01d0f34"
WC_CONSUMER_SECRET = "cs_f4df20d3f7ba2fc5d70545ea36e294c8918124fb"

HEADERS = {'Content-Type': 'application/json'}

# ---------------------------
# Connect to Odoo
# ---------------------------
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

# ---------------------------
# Get Categories from Odoo
# ---------------------------
category_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'product.category', 'search', [[]])
categories = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.category', 'read',
    [category_ids],
    {'fields': ['id', 'name', 'parent_id']}
)

# ---------------------------
# Fetch Existing WooCommerce Categories
# ---------------------------
response = requests.get(
    f"{WC_BASE_URL}/products/categories?per_page=100",
    auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
    headers=HEADERS
)
if response.status_code != 200:
    print("Failed to fetch WooCommerce categories")
    exit(1)

wc_categories = response.json()
wc_category_map = {cat['name'].strip().lower(): cat['id'] for cat in wc_categories}

# ---------------------------
# Create Missing Categories on WooCommerce
# ---------------------------
odoo_to_wc_category_map = {}

for category in categories:
    category_name = category['name'].strip()
    category_name_lower = category_name.lower()

    if category_name_lower in wc_category_map:
        wc_id = wc_category_map[category_name_lower]
        print(f"Odoo category '{category_name}' already exists on WooCommerce.")
    else:
        payload = {"name": category_name}
        create_response = requests.post(
            f"{WC_BASE_URL}/products/categories",
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
            headers=HEADERS,
            data=json.dumps(payload)
        )
        if create_response.status_code in [200, 201]:
            wc_id = create_response.json()['id']
            wc_category_map[category_name_lower] = wc_id
            print(f"Created category '{category_name}' on WooCommerce.")
        else:
            print(f"Failed to create category '{category_name}': {create_response.text}")
            continue

    odoo_to_wc_category_map[category['id']] = wc_id

# ---------------------------
# Get Products from Odoo
# ---------------------------
product_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search',
    [['&', ('woocommerce_product_id', '!=', False), ('active', '=', True)]]
)

products = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [product_ids],
    {'fields': ['name', 'categ_id', 'woocommerce_product_id']}
)

# ---------------------------
# Assign Categories to WooCommerce Products
# ---------------------------
for product in products:
    try:
        wc_product_id = product.get('woocommerce_product_id')
        if not wc_product_id:
            continue

        categ_id = product.get('categ_id')
        if not categ_id:
            print(f"Product '{product['name']}' has no category, skipping.")
            continue

        odoo_cat_id = categ_id[0]
        wc_cat_id = odoo_to_wc_category_map.get(odoo_cat_id)

        if not wc_cat_id:
            print(f"No WooCommerce category found for '{categ_id[1]}', skipping product '{product['name']}'.")
            continue

        update_data = {"categories": [{"id": wc_cat_id}]}
        update_response = requests.put(
            f"{WC_BASE_URL}/products/{wc_product_id}",
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
            headers=HEADERS,
            data=json.dumps(update_data)
        )

        if update_response.status_code == 200:
            print(f"Updated product '{product['name']}' with category '{categ_id[1]}'.")
        else:
            print(f"Failed to update product '{product['name']}': {update_response.text}")

    except Exception as e:
        print(f"Error processing product '{product.get('name', '')}': {e}")
