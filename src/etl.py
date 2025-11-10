"""
ETL Pipeline for OTA Performance Data
"""

import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OTADataETL:
    """Extract, Transform, Load pipeline for OTA data"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def extract_from_excel(self, file_path):
        """Extract data from multi-sheet Excel file"""
        xl = pd.ExcelFile(file_path)
        all_data = []
        
        logger.info(f"📥 Extracting data from {len(xl.sheet_names)} sheets...")
        
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Parse week period
            try:
                week_parts = sheet_name.split(' to ')
                if len(week_parts) == 2:
                    week_start = pd.to_datetime(week_parts[0], format='%m.%d.%y')
                    week_end = pd.to_datetime(week_parts[1], format='%m.%d.%y')
                else:
                    week_start = datetime.now().date()
                    week_end = datetime.now().date()
            except:
                logger.warning(f"Could not parse dates from sheet: {sheet_name}")
                week_start = datetime.now().date()
                week_end = datetime.now().date()
            
            df['week_start'] = week_start
            df['week_end'] = week_end
            df['week_period'] = sheet_name
            df['data_source'] = 'airbnb'
            
            all_data.append(df)
            logger.info(f"  ✅ {sheet_name}: {len(df)} listings")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"✅ Extracted {len(combined_df)} total records from {len(xl.sheet_names)} weeks")
        return combined_df
    
    def transform_data(self, df):
        """Calculate derived metrics"""
        logger.info("🔄 Transforming data and calculating metrics...")
        
        # Avoid division by zero
        df['view_rate'] = df['total_listing_views'] / df['appearance_in_search'].replace(0, 1)
        df['conversion_rate'] = df['bookings'] / df['total_listing_views'].replace(0, 1)
        df['search_to_booking_rate'] = df['bookings'] / df['appearance_in_search'].replace(0, 1)
        
        # Replace infinity with 0
        df = df.replace([float('inf'), -float('inf')], 0)
        
        # Ensure numeric types
        numeric_cols = ['appearance_in_search', 'total_listing_views', 'bookings']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        logger.info(f"✅ Transformed data with calculated metrics")
        return df
    
    def load_to_database(self, df):
        """Load data into MySQL"""
        logger.info("💾 Loading data to database...")
        
        # Prepare raw data
        raw_cols = ['id_listing', 'id_host', 'week_start', 'week_end', 'week_period',
                   'appearance_in_search', 'total_listing_views', 'bookings', 'data_source']
        raw_df = df[raw_cols].copy()
        
        # Load raw data
        try:
            self.db.insert_dataframe(raw_df, 'raw_listing_performance', if_exists='append')
        except Exception as e:
            logger.warning(f"⚠️ Some records may already exist: {str(e)[:100]}")
        
        # Prepare metrics
        metrics_df = df[['id_listing', 'week_start', 'view_rate', 'conversion_rate', 
                        'search_to_booking_rate']].copy()
        
        # Load metrics
        try:
            self.db.insert_dataframe(metrics_df, 'listing_metrics', if_exists='append')
        except Exception as e:
            logger.warning(f"⚠️ Some metrics may already exist: {str(e)[:100]}")
        
        logger.info(f"✅ Loaded {len(df)} records to database")
        return True
    
    def run_pipeline(self, file_path):
        """Execute full ETL pipeline"""
        logger.info("="*80)
        logger.info("🚀 STARTING ETL PIPELINE")
        logger.info("="*80)
        
        # Extract
        df = self.extract_from_excel(file_path)
        
        # Transform
        df = self.transform_data(df)
        
        # Load
        self.load_to_database(df)
        
        logger.info("="*80)
        logger.info("✅ ETL PIPELINE COMPLETE")
        logger.info("="*80)
        return df
