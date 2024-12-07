import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

def check_knowledge_bases():
    """Quick check if knowledge bases are populated"""
    # First check if data files exist
    data_dir = Path("democracy/data")
    expected_files = ["bills.json", "records.json", "reports.json"]
    
    print("\nData File Status:")
    print("----------------")
    for file in expected_files:
        path = data_dir / file
        status = "✓" if path.exists() else "✗"
        print(f"{status} {file}")
    
    # Then check database tables
    conn = psycopg2.connect("postgresql://ai:ai@localhost:5532/ai")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\nKnowledge Base Status:")
    print("---------------------")
    
    # Update table names to match historical_agent.py
    table_checks = [
        ('congress_docs', 'Congress Bills'),
        ('congress_records', 'Congressional Records'),
        ('congress_reports', 'Committee Reports'),
        ('constitutional_docs', 'Constitutional Documents'),
        ('congress_knowledge', 'Combined Knowledge')
    ]
    
    for table, description in table_checks:
        try:
            # First check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'ai' 
                    AND table_name = %s
                )
            """, (table,))
            exists = cur.fetchone()['exists']
            
            if exists:
                # If table exists, count records
                cur.execute(f"SELECT COUNT(*) as count FROM ai.{table}")
                count = cur.fetchone()['count']
                status = "✓" if count > 0 else "!"  # Use ! for empty tables
                print(f"{status} {description}: {count} documents")
            else:
                print(f"✗ {description}: Table not found")
                
        except psycopg2.Error as e:
            print(f"✗ {description}: Error checking table")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_knowledge_bases() 