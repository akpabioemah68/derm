#!/bin/bash

# === CONFIGURABLE VARIABLES ===
DB_NAME="wordpress_ip"
DB_USER="wpuser"
DB_PASS="YourStrongPassword"
DB_ROOT_PASS="your_mysql_root_password"  # Replace this before running

SITE_DIR="/var/www/ipsite"
WP_URL="https://wordpress.org/latest.tar.gz"

echo "=== Creating MySQL database and user ==="
mysql -u root -p"$DB_ROOT_PASS" <<MYSQL_SCRIPT
CREATE DATABASE IF NOT EXISTS $DB_NAME DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
MYSQL_SCRIPT

echo "=== Creating site directory ==="
sudo mkdir -p "$SITE_DIR"
sudo chown -R $USER:$USER "$SITE_DIR"

echo "=== Downloading and extracting WordPress ==="
cd /tmp
curl -O "$WP_URL"
tar -xzf latest.tar.gz
sudo rm -rf "$SITE_DIR"/*
sudo cp -r wordpress/* "$SITE_DIR"
rm -rf wordpress latest.tar.gz

echo "=== Configuring wp-config.php ==="
cd "$SITE_DIR"
cp wp-config-sample.php wp-config.php

# Replace DB settings
sed -i "s/database_name_here/$DB_NAME/" wp-config.php
sed -i "s/username_here/$DB_USER/" wp-config.php
sed -i "s/password_here/$DB_PASS/" wp-config.php

# Set site URL for IP access
echo "define('WP_HOME', 'http://199.188.203.246');" >> wp-config.php
echo "define('WP_SITEURL', 'http://199.188.203.246');" >> wp-config.php

# Generate secure salts
echo "=== Setting authentication keys ==="
SALT=$(curl -s https://api.wordpress.org/secret-key/1.1/salt/)
sed -i "/AUTH_KEY/d" wp-config.php
echo "$SALT" >> wp-config.php

# Permissions
echo "=== Setting permissions ==="
# Use 'nginx' or 'www-data' depending on your distro
if id "www-data" &>/dev/null; then
  sudo chown -R www-data:www-data "$SITE_DIR"
else
  sudo chown -R nginx:nginx "$SITE_DIR"
fi

sudo find "$SITE_DIR" -type d -exec chmod 755 {} \;
sudo find "$SITE_DIR" -type f -exec chmod 644 {} \;

echo "✅ WordPress installed at $SITE_DIR"
echo "🌐 Visit: http://199.188.203.246 to complete setup in browser"
