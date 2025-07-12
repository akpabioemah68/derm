import psycopg2

# --- Configuration ---
ODOO_DB = "new2"
PG_ADMIN_USER = "postgres"       # Superuser
PG_ADMIN_PASSWORD = "almond.2"
ODOO_DB_OWNER = "odoo"
PG_HOST = "localhost"
PG_PORT = "5432"

def reassign_table_owners():
    try:
        conn = psycopg2.connect(
            dbname=ODOO_DB,
            user=PG_ADMIN_USER,
            password=PG_ADMIN_PASSWORD,
            host=PG_HOST,
            port=PG_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()

        print("🔧 Changing ownership of specific known tables...")
        cur.execute(f"ALTER TABLE public.res_users OWNER TO {ODOO_DB_OWNER};")
        cur.execute(f"ALTER TABLE public.audit_rule OWNER TO {ODOO_DB_OWNER};")

        print("🔧 Changing ownership of all tables in schema 'public'...")
        cur.execute(f"""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
                EXECUTE 'ALTER TABLE public.' || quote_ident(r.tablename) || ' OWNER TO {ODOO_DB_OWNER}';
            END LOOP;
        END $$;
        """)

        print("✅ All table ownership reassigned to:", ODOO_DB_OWNER)
        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print("❌ PostgreSQL error:", e)

if __name__ == "__main__":
    reassign_table_owners()
    
