"""
Configuration management for Kasa OTA Monitoring System
Author: Neel Agarwal
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Central configuration class for the application
    All sensitive data should be stored in .env file
    """
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'kasa_ota_monitoring')
    DB_USER = os.getenv('DB_USER', 'kasa_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # For cloud databases (PlanetScale, AWS RDS, etc.)
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    
    # API Keys
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    # Slack Configuration
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
    SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#ota-alerts')
    
    # Alert Thresholds
    CRITICAL_THRESHOLD = int(os.getenv('CRITICAL_THRESHOLD', 100))
    HIGH_THRESHOLD = int(os.getenv('HIGH_THRESHOLD', 75))
    MEDIUM_THRESHOLD = int(os.getenv('MEDIUM_THRESHOLD', 50))
    LOW_THRESHOLD = int(os.getenv('LOW_THRESHOLD', 25))
    
    # Analysis Parameters
    HISTORICAL_WEEKS = int(os.getenv('HISTORICAL_WEEKS', 4))
    MIN_APPEARANCES_FOR_HIGH_ALERT = int(os.getenv('MIN_APPEARANCES_FOR_HIGH_ALERT', 50))
    VIEW_RATE_DROP_THRESHOLD = float(os.getenv('VIEW_RATE_DROP_THRESHOLD', 0.5))  # 50% drop
    CONVERSION_RATE_DROP_THRESHOLD = float(os.getenv('CONVERSION_RATE_DROP_THRESHOLD', 0.5))
    WOW_DECLINE_THRESHOLD = float(os.getenv('WOW_DECLINE_THRESHOLD', -30.0))  # -30% WoW
    
    @property
    def database_url(self):
        """
        Construct database URL for SQLAlchemy
        If DATABASE_URL is provided (e.g., from PlanetScale), use it
        Otherwise, construct from individual components
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def validate(self):
        """
        Validate that all required configuration is present
        """
        errors = []
        
        if not self.database_url:
            errors.append("Database configuration missing")
        
        if not self.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY not set (required for AI insights)")
        
        if not self.SLACK_WEBHOOK_URL:
            errors.append("SLACK_WEBHOOK_URL not set (required for notifications)")
        
        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True


# Create global config instance
config = Config()
