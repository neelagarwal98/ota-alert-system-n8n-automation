from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Get connection string from .env
DB_URL = os.getenv('DATABASE_URL')

print(f"🔗 Connecting to database...")

try:
    engine = create_engine(DB_URL)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        print(result.fetchone())
        
        # Also show which database
        result = conn.execute(text("SELECT DATABASE() as db"))
        db_name = result.fetchone()[0]
        print(f"✅ Connected to: {db_name}")
        
        # Show tables
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        print(f"✅ Tables found: {len(tables)}")
        for table in tables:
            print(f"   - {table}")
            
except Exception as e:
    print(f"❌ Connection failed: {e}")