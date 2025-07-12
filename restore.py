import psycopg2

# Configuration
DB_NAME = "new2"
DB_USER = "postgres"
DB_PASSWORD = "almond.2"
ODOO_USER = "odoo"
DB_HOST = "localhost"
DB_PORT = "5432"

def reassign_all_ownership():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()

        print("🔧 Reassigning ownership of all tables in public schema...")

        # Tables
        cur.execute(f"""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
                EXECUTE 'ALTER TABLE public.' || quote_ident(r.tablename) || ' OWNER TO {ODOO_USER}';
            END LOOP;
        END $$;
        """)

        print("✅ Tables reassigned.")

        # Sequences
        print("🔧 Reassigning ownership of sequences...")
        cur.execute(f"""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema='public' LOOP
                EXECUTE 'ALTER SEQUENCE public.' || quote_ident(r.sequence_name) || ' OWNER TO {ODOO_USER}';
            END LOOP;
        END $$;
        """)

        print("✅ Sequences reassigned.")

        cur.close()
        conn.close()

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    reassign_all_ownership()
    
