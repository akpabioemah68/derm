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
PG_ADMIN_USER = "postgres"       # User that owns PostgreSQL server
ODOO_DB_OWNER = "odoo"           # Database user that Odoo uses
TEMP_DIR = "/tmp/odoo_restore"   # Where backup will be extracted

# ---------------------------
# Step 1: Find .zip Backup From 20 Days Ago
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
# Step 2: Drop Existing DB
# ---------------------------
def drop_database():
    print(f"🗑 Dropping database '{ODOO_DB}' (if it exists)...")
    try:
        subprocess.run(
            ["dropdb", "--if-exists", "--username", PG_ADMIN_USER, ODOO_DB],
            check=True
        )
        print("✅ Database dropped successfully.")
    except subprocess.CalledProcessError:
        print("❌ Failed to drop database.")
        sys.exit(1)

# ---------------------------
# Step 3: Create New Empty DB
# ---------------------------
def create_database():
    print(f"🆕 Creating new database '{ODOO_DB}' with owner '{ODOO_DB_OWNER}'...")
    try:
        subprocess.run(
            ["createdb", "--username", PG_ADMIN_USER, "--owner", ODOO_DB_OWNER, ODOO_DB],
            check=True
        )
        print("✅ Database created successfully.")
    except subprocess.CalledProcessError:
        print("❌ Failed to create database.")
        sys.exit(1)

# ---------------------------
# Step 4: Extract ZIP Archive
# ---------------------------
def extract_backup(backup_file):
    print(f"📂 Extracting backup: {backup_file}")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    try:
        shutil.unpack_archive(backup_file, TEMP_DIR)
    except Exception as e:
        print(f"❌ Failed to extract archive: {e}")
        sys.exit(1)

    dump_sql = os.path.join(TEMP_DIR, "dump.sql")
    if not os.path.isfile(dump_sql):
        print("❌ dump.sql not found in extracted backup.")
        sys.exit(1)
    print("✅ dump.sql found.")
    return dump_sql

# ---------------------------
# Step 5: Restore SQL Into New DB
# ---------------------------
def restore_dump(dump_sql):
    print("📥 Restoring SQL dump into new database...")
    try:
        subprocess.run(
            ["psql", "--username", PG_ADMIN_USER, "--dbname", ODOO_DB, "--file", dump_sql],
            check=True
        )
        print("✅ Restore completed successfully.")
    except subprocess.CalledProcessError:
        print("❌ Failed to restore SQL dump.")
        sys.exit(1)

# ---------------------------
# Main Execution Flow
# ---------------------------
def main():
    backup_file = find_backup(days_ago=20)
    drop_database()
    create_database()
    dump_sql = extract_backup(backup_file)
    restore_dump(dump_sql)
    print("\n🎯 DONE: Odoo database restored from backup 20 days ago.")

if __name__ == "__main__":
    main()
    
