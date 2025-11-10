from src.database import DatabaseManager
from src.etl import OTADataETL

db = DatabaseManager()
etl = OTADataETL(db)

# Run pipeline on sample data
df = etl.run_pipeline('data/Kasa_Living_Weekly_Conversion_Report_2025_(external).xlsx')

print(f"\n✅ Loaded {len(df)} records")
print(f"Unique listings: {df['id_listing'].nunique()}")
print(f"Date range: {df['week_start'].min()} to {df['week_start'].max()}")

db.close()