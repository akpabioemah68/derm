import xmlrpc.client

# === Odoo server credentials ===
ODOO_URL = 'https://skinpulse.online'
SRC_DB = 'new2'
DST_DB = 'testdb'

# Source DB credentials
SRC_USERNAME = 'oga@skinpulse.online'
SRC_PASSWORD = 'pr355ON@2020'

# Destination DB credentials
DST_USERNAME = 'mailesom@gmail.com'
DST_PASSWORD = 'almond.2'

# === Connect to Odoo ===
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
src_uid = common.authenticate(SRC_DB, SRC_USERNAME, SRC_PASSWORD, {})
dst_uid = common.authenticate(DST_DB, DST_USERNAME, DST_PASSWORD, {})

if not src_uid or not dst_uid:
    raise Exception("❌ Failed to authenticate to one of the databases")

src_models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
dst_models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

# === Step 1: Read product categories ===
src_categories = src_models.execute_kw(
    SRC_DB, src_uid, SRC_PASSWORD,
    'product.category', 'search_read',
    [[('active', '=', True)]],
    {'fields': ['name']}
)

# === Step 2: Read system parameters ===
src_params = src_models.execute_kw(
    SRC_DB, src_uid, SRC_PASSWORD,
    'ir.config_parameter', 'search_read',
    [[]],
    {'fields': ['key', 'value']}
)

# === Step 3: Read storable, active products ===
src_products = src_models.execute_kw(
    SRC_DB, src_uid, SRC_PASSWORD,
    'product.template', 'search_read',
    [[('active', '=', True), ('detailed_type', '=', 'product')]],
    {'fields': ['name', 'image_1920', 'categ_id', 'category_ids']}
)

# === Step 4: Create categories in destination ===
category_map = {}
for cat in src_categories:
    cat_id = dst_models.execute_kw(
        DST_DB, dst_uid, DST_PASSWORD,
        'product.category', 'create',
        [{'name': cat['name']}]
    )
    category_map[cat['name']] = cat_id

# === Step 5: Create system parameters in destination ===
for param in src_params:
    dst_models.execute_kw(
        DST_DB, dst_uid, DST_PASSWORD,
        'ir.config_parameter', 'set_param',
        [param['key'], param['value']]
    )

# === Step 6: Get and create product tags ===
tag_map = {}
# Collect all unique tag IDs
all_tag_ids = set()
for prod in src_products:
    all_tag_ids.update(prod.get('category_ids', []))

# Read tag names from source
if all_tag_ids:
    tag_data = src_models.execute_kw(
        SRC_DB, src_uid, SRC_PASSWORD,
        'product.tag', 'read',
        list(all_tag_ids), {'fields': ['name']}
    )
    for tag in tag_data:
        tag_id = dst_models.execute_kw(
            DST_DB, dst_uid, DST_PASSWORD,
            'product.tag', 'create',
            [{'name': tag['name']}]
        )
        tag_map[tag['name']] = tag_id

# === Step 7: Create products in destination ===
for prod in src_products:
    # Map category
    categ_id = None
    if prod['categ_id']:
        categ_name = prod['categ_id'][1]
        categ_id = category_map.get(categ_name)

    # Map tags
    tag_ids = []
    for tag_id in prod['category_ids']:
        tag_name = src_models.execute_kw(
            SRC_DB, src_uid, SRC_PASSWORD,
            'product.tag', 'read',
            [tag_id], {'fields': ['name']}
        )[0]['name']
        if tag_name in tag_map:
            tag_ids.append(tag_map[tag_name])

    # Create product
    dst_models.execute_kw(
        DST_DB, dst_uid, DST_PASSWORD,
        'product.template', 'create',
        [{
            'name': prod['name'],
            'image_1920': prod['image_1920'],
            'categ_id': categ_id,
            'category_ids': [(6, 0, tag_ids)],
            'detailed_type': 'product',
        }]
    )

print("Migration complete: categories, tags, parameters, and storable products copied.")
