import xmlrpc.client
import requests
import json

# ---------------------------
# Configuration
# ---------------------------
ODOO_URL = 'https://dermaky.xyz'
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
# Fetch WooCommerce Categories (Cache)
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
# Fetch Products from Odoo
# ---------------------------
product_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'search', [['&', ('woocommerce_product_id', '!=', False), ('active', '=', True)]])
products = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [product_ids],
    {'fields': ['name', 'categ_id', 'woocommerce_product_id']}
)

# ---------------------------
# Assign Categories in WooCommerce
# ---------------------------
for product in products:
    try:
        wc_product_id = product.get('woocommerce_product_id')
        if not wc_product_id:
            continue  # Skip if not linked to WooCommerce

        if not product.get('categ_id'):
            print(f"Product '{product['name']}' has no category, skipping.")
            continue

        category_name = product['categ_id'][1].strip()
        category_name_lower = category_name.lower()

        # Get or create WooCommerce category
        if category_name_lower in wc_category_map:
            category_id = wc_category_map[category_name_lower]
        else:
            create_response = requests.post(
                f"{WC_BASE_URL}/products/categories",
                auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
                headers=HEADERS,
                data=json.dumps({"name": category_name})
            )
            if create_response.status_code in [200, 201]:
                category_id = create_response.json()['id']
                wc_category_map[category_name_lower] = category_id
                print(f"Created category '{category_name}' on WooCommerce.")
            else:
                print(f"Failed to create category '{category_name}': {create_response.text}")
                continue

        # Update the WooCommerce product's category
        update_data = {"categories": [{"id": category_id}]}
        update_response = requests.put(
            f"{WC_BASE_URL}/products/{wc_product_id}",
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
            headers=HEADERS,
            data=json.dumps(update_data)
        )

        if update_response.status_code == 200:
            print(f"Updated product '{product['name']}' with category '{category_name}'.")
        else:
            print(f"Failed to update product '{product['name']}': {update_response.text}")

    except Exception as e:
        print(f"Error processing product '{product.get('name', '')}': {e}")
                
