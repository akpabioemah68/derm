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
    'product.template', 'search', [[]])

products = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'read',
    [product_ids],
    {'fields': ['name', 'list_price', 'default_code', 'qty_available', 'categ_id', 'active', 'woocommerce_product_id']}
)

# ---------------------------
# Sync Products to WooCommerce
# ---------------------------
for product in products:
    try:
        product_name = product['name']
        category_name = product['categ_id'][1].strip()
        category_name_lower = category_name.lower()

        # Get or create category in WooCommerce
        if category_name_lower in wc_category_map:
            category_id = wc_category_map[category_name_lower]
        else:
            payload = {"name": category_name}
            create_response = requests.post(
                f"{WC_BASE_URL}/products/categories",
                auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
                headers=HEADERS,
                data=json.dumps(payload)
            )
            if create_response.status_code in [200, 201]:
                category_id = create_response.json()['id']
                wc_category_map[category_name_lower] = category_id
                print(f"Created category '{category_name}' on WooCommerce.")
            else:
                print(f"Failed to create category '{category_name}': {create_response.text}")
                continue

        # Prepare product data
        categories = [{"id": category_id}]
        product_data = {
            "name": product_name,
            "type": "simple",
            "regular_price": str(product['list_price']),
            "sku": product['default_code'] or '',
            "stock_quantity": int(product['qty_available']),
            "manage_stock": True,
            "categories": categories,
            "status": "draft" if not product['active'] else "publish",
        }

        wc_product_id = product.get('woocommerce_product_id')
        wc_product_url = f"{WC_BASE_URL}/products/{wc_product_id}" if wc_product_id else f"{WC_BASE_URL}/products"

        if wc_product_id:
            get_response = requests.get(
                wc_product_url,
                auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
                headers=HEADERS
            )
            if get_response.status_code == 200:
                wc_product_data = get_response.json()

                # Check for differences before updating
                update_needed = any(
                    wc_product_data.get(field) != product_data[field]
                    for field in ["name", "regular_price", "sku", "stock_quantity", "status", "categories"]
                )

                if update_needed:
                    put_response = requests.put(
                        wc_product_url,
                        auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
                        headers=HEADERS,
                        data=json.dumps(product_data)
                    )
                    if put_response.status_code == 200:
                        print(f"Updated product '{product_name}' in WooCommerce.")
                    else:
                        print(f"Failed to update product '{product_name}': {put_response.text}")
            else:
                wc_product_id = None  # Trigger product creation

        if not wc_product_id:
            post_response = requests.post(
                f"{WC_BASE_URL}/products",
                auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
                headers=HEADERS,
                data=json.dumps(product_data)
            )
            if post_response.status_code in [200, 201]:
                print(f"Created product '{product_name}' in WooCommerce.")
                # Optional: store the new product ID back in Odoo
                new_wc_id = post_response.json()['id']
                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                    'product.template', 'write',
                    [[product['id']], {'woocommerce_product_id': new_wc_id}]
                )
            else:
                print(f"Failed to create product '{product_name}': {post_response.text}")

    except Exception as e:
        print(f"Error processing product '{product.get('name', '')}': {e}")
