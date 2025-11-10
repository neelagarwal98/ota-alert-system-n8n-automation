"""
AI-Powered Insights using Claude
"""

import anthropic
import logging
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIInsightGenerator:
    """Generates AI-powered insights using Claude API"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    
    def generate_summary(self, alerts_df):
        """Generate AI-powered summary and recommendations"""
        if len(alerts_df) == 0:
            return "✅ No issues detected this week. All listings performing within normal parameters."
        
        # Prepare context
        context = self._prepare_context(alerts_df)
        
        prompt = f"""You are an OTA performance analyst for Kasa Living, a property management company managing hundreds of Airbnb listings.

Analyze the following listing performance issues and provide:
1. A brief executive summary (2-3 sentences max)
2. Top 3 root cause hypotheses
3. Top 3 immediate action items (prioritized by impact)

Be concise and actionable. Focus on business impact.

PERFORMANCE DATA:
{context}

Respond in this exact format:

SUMMARY:
[Your 2-3 sentence summary]

ROOT CAUSES:
1. [Hypothesis 1]
2. [Hypothesis 2]
3. [Hypothesis 3]

ACTION ITEMS:
1. [Priority 1 action]
2. [Priority 2 action]
3. [Priority 3 action]
"""
        
        try:
            logger.info("🤖 Generating AI insights...")
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            summary = message.content[0].text
            logger.info("✅ AI insights generated successfully")
            return summary
        
        except Exception as e:
            logger.error(f"❌ AI generation failed: {e}")
            return "AI analysis temporarily unavailable. Please review data manually."
    
    def _prepare_context(self, alerts_df):
        """Format alerts data for Claude"""
        # Overall stats
        context = f"Total alerts: {len(alerts_df)}\n"
        context += f"  - Critical: {len(alerts_df[alerts_df['severity_level']=='CRITICAL'])}\n"
        context += f"  - High: {len(alerts_df[alerts_df['severity_level']=='HIGH'])}\n"
        context += f"  - Medium: {len(alerts_df[alerts_df['severity_level']=='MEDIUM'])}\n"
        context += f"  - Low: {len(alerts_df[alerts_df['severity_level']=='LOW'])}\n\n"
        
        # Top 5 issues
        context += "TOP 5 MOST SEVERE ISSUES:\n"
        for idx, row in alerts_df.head(5).iterrows():
            context += f"\nListing {row['id_listing']} (Score: {row['severity_score']}):\n"
            context += f"  - Search Appearances: {row['latest_appearances']}\n"
            context += f"  - Views: {row['latest_views']}\n"
            context += f"  - Bookings: {row['latest_bookings']}\n"
            context += f"  - View Rate: {row['latest_view_rate']:.2%}\n"
            context += f"  - Conversion Rate: {row['latest_conversion_rate']:.2%}\n"
            context += f"  - Issues: {row['issues']}\n"
        
        return context
