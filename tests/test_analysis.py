from src.database import DatabaseManager
from src.analysis import AlertAnalyzer

db = DatabaseManager()
analyzer = AlertAnalyzer(db)

# Run analysis
alerts = analyzer.run_analysis()

print(f"\n✅ Found {len(alerts)} alerts")
print("\nTop 5 severity:")
print(alerts.head()[['id_listing', 'severity_score', 'severity_level']])

# Save alerts
analyzer.save_alerts(alerts)

db.close()