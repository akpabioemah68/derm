import os
import subprocess
import datetime
import glob
import shutil
import sys

# ---------------------------
# Configuration
# ---------------------------
ODOO_DB = "new2"
BACKUP_DIR = "/var/log/odoo"
PG_ADMIN_USER = "postgres"       # PostgreSQL superuser
ODOO_DB_OWNER = "odoo"           # DB owner used by Odoo
ODOO_SERVICE_NAME = "odoo"       # Your systemd service name
TEMP_DIR = "/tmp/odoo_restore"   # Temp extraction directory

# ---------------------------
# Utility: Run Shell Command
# ---------------------------
def run(command, error_msg, **kwargs):
    try:
        subprocess.run(command, check=True, **kwargs)
    except subprocess.CalledProcessError:
        print(f"❌ {error_msg}")
        sys.exit(1)

# ---------------------------
# Step 1: Stop Odoo
# ---------------------------
def stop_odoo():
    print(f"🛑 Stopping Odoo service: {ODOO_SERVICE_NAME}")
    run(["sudo", "systemctl", "stop", ODOO_SERVICE_NAME], "Failed to stop Odoo service")

# ---------------------------
# Step 2: Find Backup File
# ---------------------------
def find_backup(days_ago=20):
    target_date = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).strftime('%Y%m%d')
    pattern = os.path.join(BACKUP_DIR, f"{ODOO_DB}_backup_{target_date}*.zip")
    matches = glob.glob(pattern)
    if not matches:
        print(f"❌ No backup found for {days_ago} days ago. (Looking for: {pattern})")
        sys.exit(1)
    return sorted(matches)[-1]

# ---------------------------
# Step 3: Drop Old DB
# ---------------------------
def drop_database():
    print(f"🗑 Dropping old database '{ODOO_DB}'...")
    run(["dropdb", "--if-exists", "--username", PG_ADMIN_USER, ODOO_DB], "Failed to drop database")

# ---------------------------
# Step 4: Create Clean DB
# ---------------------------
def create_database():
    print(f"🆕 Creating new database '{ODOO_DB}' with owner '{ODOO_DB_OWNER}'...")
    run(["createdb", "--username", PG_ADMIN_USER, "--owner", ODOO_DB_OWNER, ODOO_DB], "Failed to create database")

# ---------------------------
# Step 5: Extract the .zip
# ---------------------------
def extract_backup(backup_file):
    print(f"📦 Extracting backup: {backup_file}")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    shutil.unpack_archive(backup_file, TEMP_DIR)
    dump_sql = os.path.join(TEMP_DIR, "dump.sql")
    if not os.path.isfile(dump_sql):
        print("❌ dump.sql not found in extracted backup.")
        sys.exit(1)
    return dump_sql

# ---------------------------
# Step 6: Check DB is Clean
# ---------------------------
def ensure_db_empty():
    print("🔍 Ensuring new DB is completely empty...")
    result = subprocess.run(
        ["psql", "--username", PG_ADMIN_USER, "--dbname", ODOO_DB, "-tAc",
         "SELECT COUNT(*) FROM pg_class WHERE relkind IN ('r','S','v') AND relnamespace NOT IN (SELECT oid FROM pg_namespace WHERE nspname IN ('pg_catalog','information_schema'))"],
        capture_output=True, text=True
    )
    object_count = int(result.stdout.strip())
    if object_count != 0:
        print("❌ New database is not empty. Aborting to avoid conflicts (tables or sequences already exist).")
        sys.exit(1)
    print("✅ DB is clean. Proceeding with restore.")

# ---------------------------
# Step 7: Restore SQL Dump
# ---------------------------
def restore_sql(dump_sql):
    print("📥 Restoring SQL dump...")
    run(["psql", "--username", PG_ADMIN_USER, "--dbname", ODOO_DB, "--file", dump_sql], "Failed to restore SQL")

# ---------------------------
# Step 8: Restart Odoo
# ---------------------------
def start_odoo():
    print(f"🚀 Restarting Odoo service: {ODOO_SERVICE_NAME}")
    run(["sudo", "systemctl", "start", ODOO_SERVICE_NAME], "Failed to start Odoo service")

# ---------------------------
# Main Process
# ---------------------------
def main():
    stop_odoo()
    backup_file = find_backup(days_ago=20)
    drop_database()
    create_database()
    dump_sql = extract_backup(backup_file)
    ensure_db_empty()
    restore_sql(dump_sql)
    start_odoo()
    print("\n🎉 DONE: Odoo database restored successfully from backup (20 days ago).")

if __name__ == "__main__":
    main()
    
