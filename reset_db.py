#!/usr/bin/env python3
"""
Reset database schema for testing
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.pool import get_conn, put_conn
from app.repositories.api_specs import ensure_table

def reset_database():
    """Reset the database schema"""
    print("🔄 Resetting database schema...")
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Drop existing tables
        print("🗑️  Dropping existing tables...")
        cur.execute("DROP TABLE IF EXISTS test_results CASCADE")
        cur.execute("DROP TABLE IF EXISTS test_cases CASCADE")
        cur.execute("DROP TABLE IF EXISTS request_bodies CASCADE")
        cur.execute("DROP TABLE IF EXISTS test_runs CASCADE")
        cur.execute("DROP TABLE IF EXISTS api_specs CASCADE")
        
        # Recreate tables with new schema
        print("🏗️  Creating new tables...")
        ensure_table(cur)
        
        conn.commit()
        print("✅ Database schema reset successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error resetting database: {e}")
        raise
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)

if __name__ == "__main__":
    reset_database()
