import psycopg2
import os
import uuid

def test_rls():
    db_url = "postgresql://techdetector:localdev123@localhost:5432/techdetector"
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # 1. Create a non-superuser specifically for RLS testing
        print("Creating rls_test_user...")
        cursor.execute("DROP ROLE IF EXISTS rls_test_user;")
        cursor.execute("CREATE ROLE rls_test_user WITH LOGIN PASSWORD 'test123';")
        cursor.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO rls_test_user;")
        cursor.execute("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO rls_test_user;")
        
        # 2. Re-connect as the limited user
        test_db_url = "postgresql://rls_test_user:test123@localhost:5432/techdetector"
        test_conn = psycopg2.connect(test_db_url)
        test_cursor = test_conn.cursor()

        # Define Orgs
        org_a = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        org_b = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'

        print(f"Testing RLS for Org B ({org_b})...")
        # Set context to Org B
        test_cursor.execute(f"SELECT set_org_context('{org_b}');")
        test_cursor.execute("SELECT COUNT(*) FROM scanned_companies;")
        count_b = test_cursor.fetchone()[0]
        print(f"Org B count: {count_b}")

        print(f"Testing RLS for Org A ({org_a})...")
        # Set context to Org A
        test_cursor.execute(f"SELECT set_org_context('{org_a}');")
        test_cursor.execute("SELECT COUNT(*) FROM scanned_companies;")
        count_a = test_cursor.fetchone()[0]
        print(f"Org A count: {count_a}")

        if count_b == 0 and count_a >= 2:
            print("\nSUCCESS: RLS is isolating data correctly!")
        else:
            print(f"\nFAILURE: RLS isolation failed. Org B saw {count_b} records, Org A saw {count_a} records.")

        test_conn.close()
    except Exception as e:
        print(f"Error during RLS test: {e}")
    finally:
        # Cleanup
        try:
            cursor.execute("DROP ROLE IF EXISTS rls_test_user;")
        except:
            pass
        conn.close()

if __name__ == "__main__":
    test_rls()
