"""
Database management module for Kasa OTA Monitoring
Handles all database operations using SQLAlchemy
Author: Neel Agarwal
"""

import pymysql
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import pandas as pd
from typing import Optional, Dict, Any
import logging
from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections and operations
    """
    
    def __init__(self):
        """
        Initialize database connection
        """
        self.config = config
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.config.database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL debugging
        )
        
        # Create session factory
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Test connection
        self._test_connection()
        
        logger.info("✅ Database connection established")
    
    def _test_connection(self):
        """
        Test database connection on initialization
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """
        Execute a SQL query (INSERT, UPDATE, DELETE)
        
        Args:
            query: SQL query string
            params: Dictionary of query parameters
        
        Returns:
            SQLAlchemy result object
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                connection.commit()
                logger.debug(f"✅ Query executed successfully")
                return result
        except Exception as e:
            logger.error(f"❌ Query execution failed: {e}")
            raise
    
    def read_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Execute a SELECT query and return results as pandas DataFrame
        
        Args:
            query: SQL SELECT query
            params: Dictionary of query parameters
        
        Returns:
            pandas DataFrame with query results
        """
        try:
            df = pd.read_sql(text(query), self.engine, params=params)
            logger.debug(f"✅ Query returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"❌ Query read failed: {e}")
            raise
    
    def insert_dataframe(self, df: pd.DataFrame, table_name: str, if_exists: str = 'append'):
        """
        Insert pandas DataFrame into database table
        
        Args:
            df: pandas DataFrame to insert
            table_name: Target table name
            if_exists: What to do if table exists ('fail', 'replace', 'append')
        """
        try:
            rows_inserted = df.to_sql(
                table_name,
                self.engine,
                if_exists=if_exists,
                index=False,
                chunksize=1000,  # Insert in batches for performance
                method='multi'  # Use multi-row INSERT
            )
            logger.info(f"✅ Inserted {len(df)} rows into {table_name}")
            return rows_inserted
        except Exception as e:
            logger.error(f"❌ DataFrame insertion failed: {e}")
            # If duplicate key error, that's often expected
            if "Duplicate entry" in str(e):
                logger.warning(f"⚠️ Some records already exist in {table_name}")
            else:
                raise
    
    def get_listing_history(self, id_listing: int, weeks: int = 5) -> pd.DataFrame:
        """
        Get historical performance data for a specific listing
        
        Args:
            id_listing: Listing ID to query
            weeks: Number of weeks of history to retrieve
        
        Returns:
            DataFrame with listing history
        """
        query = """
        SELECT 
            id_listing,
            week_start,
            week_end,
            week_period,
            appearance_in_search,
            total_listing_views,
            bookings
        FROM raw_listing_performance
        WHERE id_listing = :id_listing
        ORDER BY week_start DESC
        LIMIT :weeks
        """
        
        return self.read_query(query, {'id_listing': id_listing, 'weeks': weeks})
    
    def get_all_listings(self) -> pd.DataFrame:
        """
        Get list of all unique listings in the database
        
        Returns:
            DataFrame with listing IDs
        """
        query = """
        SELECT DISTINCT 
            id_listing,
            MAX(week_start) as last_updated
        FROM raw_listing_performance
        GROUP BY id_listing
        ORDER BY last_updated DESC
        """
        
        return self.read_query(query)
    
    def get_alerts(self, 
                  resolved: bool = False, 
                  limit: int = 100,
                  min_severity: str = 'LOW') -> pd.DataFrame:
        """
        Get alerts from database
        
        Args:
            resolved: Filter by resolved status
            limit: Maximum number of alerts to return
            min_severity: Minimum severity level ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
        
        Returns:
            DataFrame with alerts
        """
        severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        min_level = severity_order.get(min_severity, 1)
        
        query = """
        SELECT 
            id,
            id_listing,
            alert_date,
            severity_score,
            severity_level,
            issues,
            recommended_actions,
            created_at,
            resolved,
            resolved_at
        FROM alerts
        WHERE resolved = :resolved
          AND CASE severity_level
              WHEN 'CRITICAL' THEN 4
              WHEN 'HIGH' THEN 3
              WHEN 'MEDIUM' THEN 2
              WHEN 'LOW' THEN 1
              ELSE 0
          END >= :min_level
        ORDER BY severity_score DESC, created_at DESC
        LIMIT :limit
        """
        
        return self.read_query(query, {
            'resolved': resolved,
            'min_level': min_level,
            'limit': limit
        })
    
    def mark_alert_resolved(self, alert_id: int, notes: str = ""):
        """
        Mark an alert as resolved
        
        Args:
            alert_id: ID of the alert to resolve
            notes: Optional resolution notes
        """
        query = """
        UPDATE alerts
        SET resolved = TRUE,
            resolved_at = CURRENT_TIMESTAMP,
            resolved_notes = :notes
        WHERE id = :alert_id
        """
        
        self.execute_query(query, {'alert_id': alert_id, 'notes': notes})
        logger.info(f"✅ Alert {alert_id} marked as resolved")
    
    def get_weekly_summary(self) -> pd.DataFrame:
        """
        Get summary statistics for each week
        
        Returns:
            DataFrame with weekly performance metrics
        """
        query = """
        SELECT 
            week_period,
            week_start,
            COUNT(DISTINCT id_listing) as total_listings,
            SUM(appearance_in_search) as total_appearances,
            SUM(total_listing_views) as total_views,
            SUM(bookings) as total_bookings,
            AVG(total_listing_views * 1.0 / NULLIF(appearance_in_search, 0)) as avg_view_rate,
            AVG(bookings * 1.0 / NULLIF(total_listing_views, 0)) as avg_conversion_rate
        FROM raw_listing_performance
        GROUP BY week_period, week_start
        ORDER BY week_start DESC
        """
        
        return self.read_query(query)
    
    def close(self):
        """
        Close database connections
        """
        try:
            self.session.close()
            self.engine.dispose()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing connections: {e}")
    
    def __enter__(self):
        """
        Context manager entry
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - ensure connections are closed
        """
        self.close()


# Example usage
if __name__ == "__main__":
    # Test database connection
    with DatabaseManager() as db:
        # Test basic query
        result = db.read_query("SELECT DATABASE() as current_db")
        print(f"Connected to database: {result.iloc[0]['current_db']}")
        
        # Get weekly summary
        summary = db.get_weekly_summary()
        print(f"\nWeekly Summary:\n{summary}")
