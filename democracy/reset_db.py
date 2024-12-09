import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def reset_database():
    """Drop all tables related to the congress analysis project"""
    
    # Database connection
    conn = psycopg2.connect("postgresql://ai:ai@localhost:5532/ai")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Tables to drop
    tables = [
        'congress_docs',
        'congress_records',
        'congress_reports',
        'congress_members',
        'congress_committees',
        'committee_meetings',
        'congress_hearings',
        'congress_nominations',
        'congress_knowledge',
        'constitutional_docs',
        'congress_agent_sessions',
        'constitutional_summaries',
        'federalism_knowledge',
        'bill_of_rights_knowledge',
        'agent_memory',
        'congress_workflows'
    ]
    
    print("\nDropping tables...")
    print("------------------")
    
    for table in tables:
        try:
            cur.execute(f"DROP TABLE IF EXISTS ai.{table} CASCADE")
            print(f"✓ Dropped {table}")
        except Exception as e:
            print(f"✗ Error dropping {table}: {str(e)}")
    
    # Clean up
    cur.close()
    conn.close()
    
    print("\nDatabase reset complete!")
    print("Run historical_agent.py with force_reload=True to rebuild knowledge bases")

if __name__ == "__main__":
    confirm = input("This will delete all congress analysis tables. Continue? (y/n): ")
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("Operation cancelled") 