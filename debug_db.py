#!/usr/bin/env python3
"""
Debug database state
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.pool import get_conn, put_conn

def debug_database():
    """Debug database state"""
    print("🔍 Debugging database state...")
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Check tables
        print("\n📋 Checking tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check API specs
        print("\n🌐 Checking API specs...")
        cur.execute("SELECT COUNT(*) FROM api_specs")
        api_count = cur.fetchone()[0]
        print(f"  - API specs count: {api_count}")
        
        if api_count > 0:
            cur.execute("SELECT id, method, path FROM api_specs LIMIT 5")
            apis = cur.fetchall()
            for api in apis:
                print(f"    - ID {api[0]}: {api[1]} {api[2]}")
        
        # Check test cases
        print("\n🧪 Checking test cases...")
        cur.execute("SELECT COUNT(*) FROM test_cases")
        test_count = cur.fetchone()[0]
        print(f"  - Test cases count: {test_count}")
        
        if test_count > 0:
            cur.execute("SELECT id, api_id, name, test_type FROM test_cases LIMIT 5")
            tests = cur.fetchall()
            for test in tests:
                print(f"    - ID {test[0]}: API {test[1]} - {test[2]} ({test[3]})")
        
        # Check test runs
        print("\n🏃 Checking test runs...")
        cur.execute("SELECT COUNT(*) FROM test_runs")
        run_count = cur.fetchone()[0]
        print(f"  - Test runs count: {run_count}")
        
        if run_count > 0:
            cur.execute("SELECT id, name, status, total_tests FROM test_runs LIMIT 5")
            runs = cur.fetchall()
            for run in runs:
                print(f"    - ID {run[0]}: {run[1]} - {run[2]} ({run[3]} tests)")
        
        # Check test results
        print("\n📊 Checking test results...")
        cur.execute("SELECT COUNT(*) FROM test_results")
        result_count = cur.fetchone()[0]
        print(f"  - Test results count: {result_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)

if __name__ == "__main__":
    debug_database()
