# Inspect specific listing
from src.database import DatabaseManager

db = DatabaseManager()

listing_id = 680523499995195758  # Top severity from analysis

history = db.get_listing_history(listing_id, 5)
print(history)

# Verify calculations match alert logic