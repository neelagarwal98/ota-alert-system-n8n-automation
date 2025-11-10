from src.database import DatabaseManager
from src.analysis import AlertAnalyzer
from src.slack_notifier import SlackNotifier

# Get alerts from database
db = DatabaseManager()
query = "SELECT * FROM alerts WHERE resolved = FALSE ORDER BY severity_score DESC LIMIT 10"
alerts = db.read_query(query)

# Send to Slack
notifier = SlackNotifier()
notifier.send_alerts(alerts)

print("✅ Check your Slack channel!")

db.close()