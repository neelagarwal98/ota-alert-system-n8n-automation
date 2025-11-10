"""
Slack Notification Integration
"""

import requests
import json
import logging
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SlackNotifier:
    """Sends formatted alerts to Slack"""
    
    def __init__(self):
        self.webhook_url = config.SLACK_WEBHOOK_URL
        self.channel = config.SLACK_CHANNEL
    
    def format_alert_message(self, alerts_df, ai_summary=None):
        """Create rich Slack message with blocks"""
        severity_emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🔵'
        }
        
        # Header
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ Kasa OTA Performance Alerts",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(alerts_df)} listings* need attention"
                }
            },
            {"type": "divider"}
        ]
        
        # AI Summary
        if ai_summary:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🤖 AI Analysis*\n```{ai_summary}```"
                }
            })
            blocks.append({"type": "divider"})
        
        # Top 10 alerts
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Top Priority Listings:*"
            }
        })
        
        for idx, row in alerts_df.head(10).iterrows():
            emoji = severity_emoji.get(row['severity_level'], '⚪')
            
            issues_short = row['issues'].replace('\n', ' • ')
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *Listing {row['id_listing']}* | Score: {row['severity_score']}\n" +
                           f"Appearances: {row['latest_appearances']} | Views: {row['latest_views']} | Bookings: {row['latest_bookings']}\n" +
                           f"_{issues_short}_"
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Listing"},
                    "url": f"https://www.airbnb.com/rooms/{row['id_listing']}"
                }
            })
        
        # Footer
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"📊 Critical: {len(alerts_df[alerts_df['severity_level']=='CRITICAL'])} | " +
                       f"High: {len(alerts_df[alerts_df['severity_level']=='HIGH'])} | " +
                       f"Medium: {len(alerts_df[alerts_df['severity_level']=='MEDIUM'])} | " +
                       f"Low: {len(alerts_df[alerts_df['severity_level']=='LOW'])}"
            }]
        })
        
        return {
            "channel": self.channel,
            "text": f"OTA Alerts: {len(alerts_df)} listings need attention",
            "blocks": blocks
        }
    
    def send_message(self, message):
        """Send message to Slack"""
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Slack notification sent successfully")
                return True
            else:
                logger.error(f"❌ Slack error: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Failed to send Slack message: {e}")
            return False
    
    def send_alerts(self, alerts_df, ai_summary=None):
        """Format and send alerts"""
        if len(alerts_df) == 0:
            # All clear message
            message = {
                "channel": self.channel,
                "text": "✅ All OTA listings performing well",
                "blocks": [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "✅ *All Clear!*\nAll OTA listings are performing within normal parameters."
                    }
                }]
            }
            return self.send_message(message)
        
        message = self.format_alert_message(alerts_df, ai_summary)
        return self.send_message(message)