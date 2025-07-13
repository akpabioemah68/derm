import xmlrpc.client
from collections import defaultdict

# === Odoo Server Credentials ===
ODOO_URL = 'https://skinpulse.online'
ODOO_DB = 'new2'
ODOO_USERNAME = 'oga@skinpulse.online'
ODOO_PASSWORD = 'pr355ON@2020'

# === Connect to Odoo ===
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
if not uid:
    raise Exception("Authentication failed")

models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

# === Step 1: Get all internal quants ===
internal_quants = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'stock.quant', 'search_read',
    [[('location_id.usage', '=', 'internal')]],
    {'fields': ['product_id', 'quantity'], 'limit': 1000}
)

# === Step 2: Group total quantity per product ===
product_quant_totals = defaultdict(float)
for q in internal_quants:
    if q['product_id']:
        pid = q['product_id'][0]
        product_quant_totals[pid] += q['quantity']

# === Step 3: Find discrepancies with qty_available ===
discrepant_products = []

for pid, quant_total in product_quant_totals.items():
    product_data = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.product', 'read',
        [pid], {'fields': ['qty_available', 'name']}
    )
    if not product_data:
        continue

    name = product_data[0]['name']
    qoh = product_data[0]['qty_available']

    if abs(qoh - quant_total) > 0.01:
        discrepant_products.append({
            'id': pid,
            'name': name,
            'qty_available': qoh,
            'quant_total': quant_total
        })

# === Step 4: Output and fix ===
print("\n🔍 Products with QOH mismatch:")
for p in discrepant_products:
    print(f"- {p['name']} (ID {p['id']}): QOH={p['qty_available']} vs Quant Total={p['quant_total']}")

# === Step 5: Trigger recompute via dummy write ===
print("\n🔁 Forcing QOH recompute by updating product names temporarily...")

for p in discrepant_products:
    temp_name = p['name'] + ' '
    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'product.product', 'write', [[p['id']], {'name': temp_name}])
    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'product.product', 'write', [[p['id']], {'name': p['name']}])

print("✅ Done. QOH should be updated.")

           
