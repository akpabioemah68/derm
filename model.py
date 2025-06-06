
import requests
import json
from odoo import models, fields, api
import base64
import os
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import logging
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)



class WooCommerceSync(models.Model):
    _name = 'woocommerce.sync'
    _description = 'WooCommerce Product and Inventory Sync'

    base_url = "https://skinpulse.ng/wp-json/wc/v3"
    consumer_key = "ck_191d2768e3e355cce69d59f7fb7a9f79e01d0f34"
    consumer_secret = "cs_f4df20d3f7ba2fc5d70545ea36e294c8918124fb"

    
    @api.model
    def sync_woocommerce_products(self):
        """Sync products to WooCommerce with updated attributes."""
        _logger.info("Starting WooCommerce product synchronization.")
        
        try:
            # Load all products, including archived ones
            products = self.env['product.template'].with_context(active_test=False).search([])
            headers = {'Content-Type': 'application/json'}

            for product in products:
                # Determine if the product exists on WooCommerce
                wc_product_url = f"{self.base_url}/products/{product.woocommerce_product_id}"
                wc_product_data = None
                if product.woocommerce_product_id:
                    response = requests.get(
                        wc_product_url,
                        auth=(self.consumer_key, self.consumer_secret),
                        headers=headers
                    )
                    if response.status_code == 200:
                        wc_product_data = response.json()
                    elif response.status_code == 404:
                        product.woocommerce_product_id = False  # Reset WooCommerce ID if not found

                # Prepare WooCommerce product data
                categories = []
                all_categories = product.category_ids  # Get all assigned categories
                if product.categ_id:  # Include default category
                    all_categories |= product.categ_id

                for category in all_categories:
                    if category.woocommerce_category_id:
                        categories.append({"id": category.woocommerce_category_id})
                    else:
                        category_id = self.sync_category_to_woocommerce(category)
                        if category_id:
                            category.woocommerce_category_id = category_id
                            categories.append({"id": category_id})

                _logger.info("Product "+product.name+", categories "+str(categories))


                product_data = {
                    "name": product.name,
                    "type": "simple",
                    "regular_price": str(product.list_price),
                    "sku": product.default_code or '',
                    "stock_quantity": int(product.qty_available),
                    "manage_stock": True,
                    "categories": categories,
                    "status": "draft" if not product.active else "publish",
                    "images": self._prepare_images(product),
                }

                if wc_product_data:
                    # Check for changes before updating
                    update_needed = any(
                        wc_product_data.get(field) != product_data[field]
                        for field in ["name", "regular_price", "sku", "stock_quantity", "status","categories"]
                    )
                    if update_needed:
                        response = requests.put(
                            wc_product_url,
                            auth=(self.consumer_key, self.consumer_secret),
                            headers=headers,
                            data=json.dumps(product_data)
                        )
                        if response.status_code == 200:
                            _logger.info(f"Updated product '{product.name}' on WooCommerce.")
                        else:
                            _logger.error(f"Failed to update product '{product.name}': {response.text}")
                else:
                    # Create the product on WooCommerce if it doesn't exist
                    wc_product_url = f"{self.base_url}/products"
                    response = requests.post(
                        wc_product_url,
                        auth=(self.consumer_key, self.consumer_secret),
                        headers=headers,
                        data=json.dumps(product_data)
                    )
                    if response.status_code in [200, 201]:
                        wc_product_id = response.json().get('id')
                        product.woocommerce_product_id = wc_product_id
                        _logger.info(f"Created product '{product.name}' on WooCommerce.")
                    else:
                        _logger.error(f"Failed to create product '{product.name}': {response.text}")

                # Handle archived Odoo products and WooCommerce status
                if not product.active and wc_product_data and wc_product_data.get("status") == "publish":
                    # Disable product on WooCommerce
                    response = requests.put(
                        wc_product_url,
                        auth=(self.consumer_key, self.consumer_secret),
                        headers=headers,
                        data=json.dumps({"status": "draft"})
                    )
                    if response.status_code == 200:
                        _logger.info(f"Disabled archived product '{product.name}' on WooCommerce.")
                elif product.active and wc_product_data and wc_product_data.get("status") == "draft":
                    # Re-enable product on WooCommerce
                    response = requests.put(
                        wc_product_url,
                        auth=(self.consumer_key, self.consumer_secret),
                        headers=headers,
                        data=json.dumps({"status": "publish"})
                    )
                    if response.status_code == 200:
                        _logger.info(f"Re-enabled active product '{product.name}' on WooCommerce.")

        except Exception as e:
            _logger.exception(f"Error synchronizing products to WooCommerce: {e}")





    

    def configure_cloudinary(self):
        """Fetch Cloudinary configuration from Odoo settings and configure the SDK."""
        # Fetch configuration from Odoo's system parameters
        cloud_name = self.env['ir.config_parameter'].sudo().get_param('cloudinary.cloud_name')
        api_key = self.env['ir.config_parameter'].sudo().get_param('cloudinary.api_key')
        api_secret = self.env['ir.config_parameter'].sudo().get_param('cloudinary.api_secret')

        # Validate keys
        if not all([cloud_name, api_key, api_secret]):
            raise ValueError("Cloudinary configuration is missing in Odoo settings.")

        # Configure Cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )

    def _prepare_images(self, product):
        """Prepare images for WooCommerce by uploading to Cloudinary."""
        # Ensure Cloudinary is configured
        self.configure_cloudinary()

        images = []
        if product.image_1920:
            try:
                # Decode the base64 image
                image_data = base64.b64decode(product.image_1920)
                filename = f"odoo_product_{product.id}_{product.name}.png"
                
                # Upload the image to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    image_data,
                    public_id=filename,
                    resource_type="image"
                )
                
                # Get the secure URL from Cloudinary
                image_url = upload_result.get("secure_url")

                if image_url:
                    # Append to WooCommerce images
                    images.append({
                        "src": image_url,
                        "alt": product.name,
                    })
            except Exception as e:
                _logger.error(f"Failed to upload image for product {product.name}: {str(e)}")
            
            return images

    def _get_or_create_and_map_woocommerce_category(self, category):
        """Retrieve or create a WooCommerce category and map it to the Odoo category."""
        try:
            # Skip category if the name is "All"
            if category.name.lower() == "all":
                _logger.info(f"Skipping category 'All'.")
                return None

            # Ensure the category is a leaf category
            child_categories = self.env['product.category'].search([('parent_id', '=', category.id)])
            if child_categories:
                _logger.info(f"Skipping category {category.name} as it is not a leaf category.")
                return None

            headers = {'Content-Type': 'application/json'}
            url = f"{self.base_url}/products/categories"

            # Check if the category has already been synchronized
            if category.woocommerce_category_id:
                _logger.info(f"Category {category.name} already mapped to WooCommerce ID {category.woocommerce_category_id}.")
                return category.woocommerce_category_id

            # Check if category exists in WooCommerce
            response = requests.get(
                url,
                auth=(self.consumer_key, self.consumer_secret),
                headers=headers,
                params={"search": category.name}
            )
            if response.status_code == 200:
                categories = response.json()
                if categories:
                    wc_category_id = categories[0].get('id')
                    category.woocommerce_category_id = wc_category_id  # Map to Odoo category
                    _logger.info(f"Mapped Odoo category {category.name} to WooCommerce ID {wc_category_id}.")
                    return wc_category_id

            # Create category in WooCommerce if it doesn't exist
            category_data = {"name": category.name}
            response = requests.post(
                url,
                auth=(self.consumer_key, self.consumer_secret),
                headers=headers,
                data=json.dumps(category_data)
            )
            if response.status_code in [200, 201]:
                response_data = response.json()
                wc_category_id = response_data.get('id')
                category.woocommerce_category_id = wc_category_id  # Map to Odoo category
                _logger.info(f"Created and mapped category {category.name} to WooCommerce ID {wc_category_id}.")
                return wc_category_id
            else:
                _logger.error(f"Failed to create category {category.name}. Response: {response.text}")

        except Exception as e:
            _logger.exception(f"Error handling category {category.name}: {e}")
        return None

    
    @api.model
    def update_stock_from_order(self, order_data):
        """Update stock in Odoo when an order is placed on WooCommerce."""
        update_success = False  # Flag to track if any stock was updated

        for line_item in order_data.get('line_items', []):
            woocommerce_product_id = line_item.get('product_id')
            _logger.info(f"Product ID from WooCommerce: {woocommerce_product_id}")

            # Search for the product template
            product_template = self.env['product.template'].search([('woocommerce_product_id', '=', woocommerce_product_id)], limit=1)

            if product_template:
                _logger.info("Product Template found.")

                # Get the product
                product = product_template.product_variant_id
                quantity_ordered = line_item.get('quantity', 0)

                if quantity_ordered > 0:
                    # Update stock.quant for the product
                    quant = self.env['stock.quant'].search([
                        ('product_id', '=', product.id),
                        ('location_id.usage', '=', 'internal')
                    ], limit=1)

                    if quant:
                        quant.quantity -= quantity_ordered
                        _logger.info(f"Updated stock for product {product.name}. New stock: {quant.quantity}")
                        update_success = True
                    else:
                        _logger.warning(f"No stock quant found for product {product.name}.")
                else:
                    _logger.warning(f"Invalid quantity ordered for product {product.name}. No stock update.")
            else:
                _logger.warning(f"Product with WooCommerce ID {woocommerce_product_id} not found.")

        return update_success


     


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    woocommerce_product_id = fields.Integer(
        string='WooCommerce Product ID',
        help='The product ID in WooCommerce',
        default=0  # or another sensible default
    )

    @api.model
    def action_update_quantity_on_hand(self):
        # Log a message when the method is called
        _logger.info('action_update_quantity_on_hand triggered for product template ID: %s', self.id)

        # Check if the context indicates it's from a quotation
        if not self.env.context.get('from_quotation', False):
            _logger.warning('Attempted to update quantity on hand without coming from a quotation for product template ID: %s', self.id)
            raise UserError('You can only update the quantity from a quotation.')

        # If coming from a quotation, allow the update
        _logger.info('Quantity update allowed for product template ID: %s', self.id)
        return super(ProductTemplate, self).action_update_quantity_on_hand()

    

class ProductCategory(models.Model):
    _inherit = 'product.category'

    woocommerce_category_id = fields.Char("WooCommerce Category ID", help="ID of the category in WooCommerce")
    
