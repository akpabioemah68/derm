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
# Fetch Odoo Categories
# ---------------------------
category_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'product.category', 'search', [[]])
categories = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.category', 'read',
    [category_ids],
    {'fields': ['id', 'name']}
)

# ---------------------------
# Fetch Existing WC Categories
# ---------------------------
page = 1
wc_categories = []
while True:
    response = requests.get(
        f"{WC_BASE_URL}/products/categories?per_page=100&page={page}&hide_empty=false",
        auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
        headers=HEADERS
    )
    if response.status_code != 200 or not response.json():
        break
    wc_categories.extend(response.json())
    page += 1

wc_category_map = {cat['name'].strip().lower(): cat['id'] for cat in wc_categories}

# ---------------------------
# Create Missing Categories on WC
# ---------------------------
odoo_to_wc_category_id = {}
for cat in categories:
    name = cat['name'].strip()
    name_lower = name.lower()
    if name_lower in wc_category_map:
        wc_id = wc_category_map[name_lower]
    else:
        payload = {
            "name": name,
            "slug": name_lower.replace(" ", "-")
        }
        response = requests.post(
            f"{WC_BASE_URL}/products/categories",
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
            headers=HEADERS,
            data=json.dumps(payload)
        )
        if response.status_code in [200, 201]:
            wc_id = response.json()['id']
            print(f"Created category '{name}' on WooCommerce.")
        else:
            print(f"Failed to create category '{name}': {response.text}")
            continue
    odoo_to_wc_category_id[cat['id']] = wc_id

# ---------------------------
# Fetch Odoo Products with WC IDs
# ---------------------------
product_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search',
    [[('woocommerce_product_id', '!=', False)]]
)
products = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [product_ids],
    {'fields': ['name', 'categ_id', 'woocommerce_product_id']}
)

# ---------------------------
# Assign WooCommerce Categories
# ---------------------------
for product in products:
    wc_product_id = product.get('woocommerce_product_id')
    categ_id = product.get('categ_id')

    if not wc_product_id or not categ_id:
        continue

    odoo_cat_id = categ_id[0]
    wc_cat_id = odoo_to_wc_category_id.get(odoo_cat_id)

    if not wc_cat_id:
        print(f"No WooCommerce category found for product '{product['name']}'")
        continue

    update_payload = {
        "categories": [{"id": wc_cat_id}]
    }

    response = requests.put(
        f"{WC_BASE_URL}/products/{wc_product_id}",
        auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
        headers=HEADERS,
        data=json.dumps(update_payload)
    )

    if response.status_code == 200:
        print(f"Assigned category '{categ_id[1]}' to product '{product['name']}'")
    else:
        print(f"Failed to assign category to product '{product['name']}': {response.text}")
