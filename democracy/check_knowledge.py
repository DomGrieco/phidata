import json
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

def check_data_freshness(file_path):
    """Check if data file is from today"""
    try:
        with open(file_path) as f:
            data = json.load(f)
            # Most Congress.gov responses include updateDate
            if 'updateDate' in data:
                last_update = datetime.strptime(data['updateDate'].split('T')[0], '%Y-%m-%d')
                return datetime.now().date() - last_update.date() <= timedelta(days=1)
            return False
    except:
        return False

def check_knowledge_bases():
    """Quick check if knowledge bases are populated and fresh"""
    data_dir = Path("democracy/data")
    expected_files = ["bills.json", "records.json", "reports.json"]
    
    print("\nData File Status:")
    print("----------------")
    for file in expected_files:
        path = data_dir / file
        exists = path.exists()
        fresh = check_data_freshness(path) if exists else False
        status = "✓" if exists and fresh else "!" if exists else "✗"
        freshness = "up-to-date" if fresh else "stale" if exists else "missing"
        print(f"{status} {file} ({freshness})")
    
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