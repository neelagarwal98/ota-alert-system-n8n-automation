from src.database import DatabaseManager
from src.analysis import AlertAnalyzer
from src.slack_notifier import SlackNotifier

# Initialize
db = DatabaseManager()
analyzer = AlertAnalyzer(db)
notifier = SlackNotifier()

print("🔍 Running analysis...")
# Run fresh analysis (creates DataFrame with ALL columns)
alerts = analyzer.run_analysis()

print(f"📊 Found {len(alerts)} alerts")

# Send to Slack
if len(alerts) > 0:
    print("📤 Sending to Slack...")
    notifier.send_alerts(alerts)
    print("✅ Slack notification sent! Check #ota-alerts")
else:
    print("✅ No alerts to send")

db.close()