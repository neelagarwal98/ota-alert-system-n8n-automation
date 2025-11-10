from src.database import DatabaseManager

db = DatabaseManager()
print("✅ DatabaseManager initialized")

# Test query
result = db.read_query("SELECT DATABASE()")
print(f"Connected to: {result.iloc[0, 0]}")

db.close()