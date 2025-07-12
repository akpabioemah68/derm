import os
import subprocess
import datetime
import glob
import shutil

# ---------------------------
# Configuration
# ---------------------------
ODOO_DB = "new2"
BACKUP_DIR = "/var/log/odoo"
PG_ADMIN_USER = "postgres"  # Superuser to manage databases
ODOO_DB_OWNER = "odoo"      # Owner to assign to the restored DB

# ---------------------------
# Find Backup from 20 Days Ago
# ---------------------------
def find_backup(days_ago=20):
    target_date = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).strftime('%Y%m%d')
    pattern = os.path.join(BACKUP_DIR, f"{ODOO_DB}_backup_{target_date}*.zip")
    files = glob.glob(pattern)
    if not files:
        print(f"❌ No backup found for {days_ago} days ago (pattern: {pattern})")
        return None
    return sorted(files)[-1]  # Use latest of the day if multiple

# ---------------------------
# Drop and Restore Database
# ---------------------------
def restore_database():
    backup_file = find_backup()

    if not backup_file:
        return

    print(f"📦 Found backup: {backup_file}")

    # Step 1: Drop database if it exists
    print(f"🗑 Dropping database '{ODOO_DB}' (if exists)...")
    subprocess.run(["dropdb", "--if-exists", "--username=postgres", ODOO_DB], check=True)

    # Step 2: Extract the zip
    temp_extract_dir = "/tmp/odoo_restore"
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
    os.makedirs(temp_extract_dir)

    print("📂 Extracting backup...")
    shutil.unpack_archive(backup_file, temp_extract_dir)

    dump_sql = os.path.join(temp_extract_dir, "dump.sql")

    if not os.path.exists(dump_sql):
        print("❌ dump.sql not found in extracted archive.")
        return

    # Step 3: Create empty database with odoo as owner
    print(f"🆕 Creating new database '{ODOO_DB}' with owner '{ODOO_DB_OWNER}'...")
    subprocess.run([
        "createdb",
        "--username=postgres",
        "--owner=" + ODOO_DB_OWNER,
        ODOO_DB
    ], check=True)

    # Step 4: Restore the SQL dump into the new database
    print("📥 Restoring SQL dump into the new database...")
    subprocess.run([
        "psql",
        "--username=postgres",
        "--dbname", ODOO_DB,
        "--file", dump_sql
    ], check=True)

    print("✅ Database restored successfully from backup.")

if __name__ == "__main__":
    restore_database()
  
