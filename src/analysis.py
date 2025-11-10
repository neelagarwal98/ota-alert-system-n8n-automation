"""
Alert Analysis and Detection Logic
"""

import pandas as pd
import numpy as np
import logging
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertAnalyzer:
    """Analyzes listing performance and generates alerts"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.config = config
    
    def analyze_listing(self, id_listing):
        """Analyze a single listing and calculate severity score"""
        # Get historical data
        history = self.db.get_listing_history(id_listing, weeks=5)
        
        if len(history) < 2:
            return None  # Not enough data
        
        # Sort by date
        history = history.sort_values('week_start')
        latest = history.iloc[-1]
        previous = history.iloc[-2] if len(history) >= 2 else latest
        
        # Calculate averages (excluding latest week)
        historical = history.iloc[:-1]
        avg_appearances = historical['appearance_in_search'].mean()
        avg_views = historical['total_listing_views'].mean()
        avg_bookings = historical['bookings'].mean()
        
        # Calculate rates
        latest_view_rate = latest['total_listing_views'] / max(latest['appearance_in_search'], 1)
        latest_conversion = latest['bookings'] / max(latest['total_listing_views'], 1)
        avg_view_rate = historical['total_listing_views'].sum() / max(historical['appearance_in_search'].sum(), 1)
        avg_conversion = historical['bookings'].sum() / max(historical['total_listing_views'].sum(), 1)
        
        # Initialize scoring
        score = 0
        issues = []
        severity_level = 'LOW'
        
        # CRITICAL: Zero appearances
        if latest['appearance_in_search'] == 0:
            score += self.config.CRITICAL_THRESHOLD
            issues.append("🔴 CRITICAL: Zero search appearances - listing may be inactive")
            severity_level = 'CRITICAL'
        
        # HIGH: No bookings despite high visibility
        if (latest['appearance_in_search'] > self.config.MIN_APPEARANCES_FOR_HIGH_ALERT 
            and latest['bookings'] == 0):
            score += self.config.HIGH_THRESHOLD
            issues.append(f"🟠 HIGH: No bookings despite {int(latest['appearance_in_search'])} search appearances")
            if severity_level not in ['CRITICAL']:
                severity_level = 'HIGH'
        
        # MEDIUM: View rate collapse
        if latest_view_rate < avg_view_rate * self.config.VIEW_RATE_DROP_THRESHOLD and avg_view_rate > 0.01:
            drop_pct = ((avg_view_rate - latest_view_rate) / avg_view_rate) * 100
            score += self.config.MEDIUM_THRESHOLD
            issues.append(f"🟡 MEDIUM: View rate dropped {drop_pct:.0f}% vs historical average")
            if severity_level not in ['CRITICAL', 'HIGH']:
                severity_level = 'MEDIUM'
        
        # MEDIUM: Conversion rate collapse
        if latest_conversion < avg_conversion * self.config.CONVERSION_RATE_DROP_THRESHOLD and avg_conversion > 0.01:
            drop_pct = ((avg_conversion - latest_conversion) / avg_conversion) * 100
            score += self.config.MEDIUM_THRESHOLD
            issues.append(f"🟡 MEDIUM: Conversion rate dropped {drop_pct:.0f}% vs historical average")
            if severity_level not in ['CRITICAL', 'HIGH']:
                severity_level = 'MEDIUM'
        
        # LOW: Week-over-week decline
        wow_change = ((latest['appearance_in_search'] - previous['appearance_in_search']) / 
                      max(previous['appearance_in_search'], 1)) * 100
        if wow_change < self.config.WOW_DECLINE_THRESHOLD:
            score += self.config.LOW_THRESHOLD
            issues.append(f"🔵 LOW: Search appearances down {abs(wow_change):.0f}% week-over-week")
        
        if score == 0:
            return None  # No issues
        
        return {
            'id_listing': id_listing,
            'alert_date': latest['week_start'],
            'severity_score': score,
            'severity_level': severity_level,
            'issues': '\n'.join(issues),
            'latest_appearances': int(latest['appearance_in_search']),
            'latest_views': int(latest['total_listing_views']),
            'latest_bookings': int(latest['bookings']),
            'latest_view_rate': round(latest_view_rate, 4),
            'latest_conversion_rate': round(latest_conversion, 4),
            'avg_appearances': round(avg_appearances, 1),
            'avg_bookings': round(avg_bookings, 1),
            'wow_change_pct': round(wow_change, 1)
        }
    
    def run_analysis(self):
        """Analyze all listings and generate alerts"""
        logger.info("="*80)
        logger.info("🔍 ANALYZING ALL LISTINGS")
        logger.info("="*80)
        
        # Get all unique listings
        listings = self.db.get_all_listings()
        logger.info(f"Found {len(listings)} unique listings to analyze")
        
        alerts = []
        for idx, row in listings.iterrows():
            id_listing = row['id_listing']
            alert = self.analyze_listing(id_listing)
            if alert:
                alerts.append(alert)
        
        if len(alerts) == 0:
            logger.info("✅ No issues detected")
            return pd.DataFrame()
        
        alerts_df = pd.DataFrame(alerts)
        alerts_df = alerts_df.sort_values('severity_score', ascending=False)
        
        # Summary
        logger.info(f"\n⚠️ Found {len(alerts_df)} listings with issues:")
        logger.info(f"  - CRITICAL: {len(alerts_df[alerts_df['severity_level']=='CRITICAL'])}")
        logger.info(f"  - HIGH: {len(alerts_df[alerts_df['severity_level']=='HIGH'])}")
        logger.info(f"  - MEDIUM: {len(alerts_df[alerts_df['severity_level']=='MEDIUM'])}")
        logger.info(f"  - LOW: {len(alerts_df[alerts_df['severity_level']=='LOW'])}")
        
        return alerts_df
    
    def save_alerts(self, alerts_df):
        """Save alerts to database"""
        if len(alerts_df) == 0:
            return
        
        # Prepare for database
        db_alerts = alerts_df[['id_listing', 'alert_date', 'severity_score', 
                               'severity_level', 'issues']].copy()
        
        # Add metadata
        db_alerts['recommended_actions'] = ''
        db_alerts['alert_sent_to'] = 'slack'
        
        self.db.insert_dataframe(db_alerts, 'alerts', if_exists='append')
        logger.info(f"✅ Saved {len(db_alerts)} alerts to database")