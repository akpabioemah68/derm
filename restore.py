import psycopg2

# Configuration
DB_NAME = "new2"
DB_USER = "postgres"
DB_PASSWORD = "almond.2"
DB_HOST = "localhost"
DB_PORT = "5432"
NEW_OWNER = "odoo"

def reassign_ownership():
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

        print("\n🔧 Reassigning ownership of tables in 'public' schema...")
        cur.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
                EXECUTE 'ALTER TABLE public.' || quote_ident(r.tablename) || ' OWNER TO """ + NEW_OWNER + """';
            END LOOP;

            FOR r IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public' LOOP
                EXECUTE 'ALTER SEQUENCE public.' || quote_ident(r.sequence_name) || ' OWNER TO """ + NEW_OWNER + """';
            END LOOP;

            FOR r IN SELECT table_name FROM information_schema.views WHERE table_schema = 'public' LOOP
                EXECUTE 'ALTER VIEW public.' || quote_ident(r.table_name) || ' OWNER TO """ + NEW_OWNER + """';
            END LOOP;
        END $$;
        """)

        print("✅ Ownership reassigned to user:", NEW_OWNER)

    except Exception as e:
        print("❌ Error:", e)

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    reassign_ownership()
    
