from src.database import DatabaseManager
from src.ai_insights import AIInsightGenerator

# Get alerts
db = DatabaseManager()
query = "SELECT * FROM alerts WHERE resolved = FALSE ORDER BY severity_score DESC"
alerts = db.read_query(query)

# Generate insights
ai = AIInsightGenerator()
summary = ai.generate_summary(alerts)

print("\n🤖 AI-GENERATED INSIGHTS:")
print("="*80)
print(summary)
print("="*80)

db.close()