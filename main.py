"""
Main Execution Script for Kasa OTA Monitoring System
"""

#!/usr/bin/env python3

import sys
import argparse
import logging
from src.database import DatabaseManager
from src.etl import OTADataETL
from src.analysis import AlertAnalyzer
from src.ai_insights import AIInsightGenerator
from src.slack_notifier import SlackNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main pipeline execution"""
    parser = argparse.ArgumentParser(
        description='Kasa OTA Monitoring Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic run (no alerts sent)
  python main.py --file data/sample.xlsx
  
  # Full run with AI and Slack
  python main.py --file data/sample.xlsx --send-slack --use-ai
        """
    )
    parser.add_argument('--file', required=True, help='Path to Excel data file')
    parser.add_argument('--send-slack', action='store_true', help='Send Slack notifications')
    parser.add_argument('--use-ai', action='store_true', help='Generate AI insights')
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("🚀 KASA OTA MONITORING SYSTEM")
    logger.info("="*80)
    
    # Initialize
    db = DatabaseManager()
    etl = OTADataETL(db)
    analyzer = AlertAnalyzer(db)
    
    try:
        # Step 1: ETL
        logger.info("\n📊 STEP 1: Running ETL Pipeline...")
        # data = etl.run_pipeline(args.file)
        etl.run_pipeline(args.file)
        
        # Step 2: Analysis
        logger.info("\n🔍 STEP 2: Analyzing performance...")
        alerts = analyzer.run_analysis()
        
        if len(alerts) > 0:
            # Step 3: Save
            logger.info("\n💾 STEP 3: Saving alerts...")
            analyzer.save_alerts(alerts)
            
            # Step 4: AI (optional)
            ai_summary = None
            if args.use_ai:
                logger.info("\n🤖 STEP 4: Generating AI insights...")
                ai_generator = AIInsightGenerator()
                ai_summary = ai_generator.generate_summary(alerts)
                print(f"\n{ai_summary}\n")
            
            # Step 5: Slack (optional)
            if args.send_slack:
                logger.info("\n📱 STEP 5: Sending Slack notifications...")
                notifier = SlackNotifier()
                notifier.send_alerts(alerts, ai_summary)
        
        else:
            logger.info("\n✅ No issues detected!")
            if args.send_slack:
                notifier = SlackNotifier()
                notifier.send_alerts(alerts)
        
        logger.info("\n" + "="*80)
        logger.info("✅ PIPELINE COMPLETE!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

