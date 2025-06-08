import requests
import json
import pandas as pd

# ---------------------------
# Configuration
# ---------------------------
WC_BASE_URL = "https://dermaky.com/wp-json/wc/v3"
WC_CONSUMER_KEY = "ck_191d2768e3e355cce69d59f7fb7a9f79e01d0f34"
WC_CONSUMER_SECRET = "cs_f4df20d3f7ba2fc5d70545ea36e294c8918124fb"
HEADERS = {'Content-Type': 'application/json'}
EXCEL_FILE = 'Stock.xlsx'

# ---------------------------
# Load Excel File
# ---------------------------
def load_excel_data(file_path):
    df = pd.read_excel(file_path)
    df = df[['Product Name', 'Category', 'Quantity On Hold']]
    df.dropna(subset=['Product Name'], inplace=True)
    df['Product Name'] = df['Product Name'].str.strip().str.lower()
    return df

# ---------------------------
# Fetch WooCommerce Categories
# ---------------------------
def fetch_wc_categories():
    page = 1
    categories = []
    while True:
        response = requests.get(
            f"{WC_BASE_URL}/products/categories?per_page=100&page={page}&hide_empty=false",
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
            headers=HEADERS
        )
        if response.status_code != 200 or not response.json():
            break
        categories.extend(response.json())
        page += 1
    return {cat['name'].strip().lower(): cat['id'] for cat in categories}

# ---------------------------
# Fetch WooCommerce Products
# ---------------------------
def fetch_wc_products():
    page = 1
    products = []
    while True:
        response = requests.get(
            f"{WC_BASE_URL}/products?per_page=100&page={page}",
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
            headers=HEADERS
        )
        if response.status_code != 200 or not response.json():
            break
        products.extend(response.json())
        page += 1
    return {prod['name'].strip().lower(): prod for prod in products}

# ---------------------------
# Create Category if Missing
# ---------------------------
def get_or_create_category_id(name, wc_category_map):
    name_lower = name.strip().lower()
    if name_lower in wc_category_map:
        return wc_category_map[name_lower]

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
        cat_id = response.json()['id']
        wc_category_map[name_lower] = cat_id
        print(f"✅ Created category: {name}")
        return cat_id
    else:
        print(f"❌ Failed to create category '{name}': {response.text}")
        return None

# ---------------------------
# Update WooCommerce Product
# ---------------------------
def update_wc_product(prod_id, cat_id, quantity):
    payload = {
        "categories": [{"id": cat_id}],
        "stock_quantity": int(quantity),
        "manage_stock": True
    }

    response = requests.put(
        f"{WC_BASE_URL}/products/{prod_id}",
        auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
        headers=HEADERS,
        data=json.dumps(payload)
    )

    return response.status_code == 200

# ---------------------------
# Main Update Logic
# ---------------------------
def main():
    print("📥 Loading Excel data...")
    excel_data = load_excel_data(EXCEL_FILE)

    print("🔄 Fetching WooCommerce categories...")
    wc_category_map = fetch_wc_categories()

    print("🔄 Fetching WooCommerce products...")
    wc_product_map = fetch_wc_products()

    print("🚀 Updating products...")
    for _, row in excel_data.iterrows():
        prod_name = row['Product Name']
        category = row['Category']
        quantity = row['Quantity On Hold']

        wc_product = wc_product_map.get(prod_name)
        if not wc_product:
            print(f"⚠️ Product '{prod_name}' not found in WooCommerce.")
            continue

        cat_id = get_or_create_category_id(category, wc_category_map)
        if not cat_id:
            continue

        success = update_wc_product(wc_product['id'], cat_id, quantity)
        if success:
            print(f"✅ Updated '{prod_name}': Category = '{category}', Quantity = {quantity}")
        else:
            print(f"❌ Failed to update '{prod_name}'")

if __name__ == '__main__':
    main()
