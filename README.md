# Kasa OTA Monitoring System

**Automated performance monitoring and alerting for Airbnb listings**

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![MySQL](https://img.shields.io/badge/mysql-9.5+-orange.svg)](https://www.mysql.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Alert Logic](#alert-logic)
- [Database Schema](#database-schema)
- [Deployment](#deployment)

## Overview

This automation system monitors hundreds of Airbnb listing performance metrics, detects anomalies, and alerts revenue teams before significant revenue loss occurs. Built for Kasa Living's property management portfolio.

**Problem being addressed:** Manual monitoring of 100+ listings across OTAs is time-consuming and misses critical issues until revenue is already lost.

**Solution:** Automated weekly pipeline that:
1. Extracts performance data from Excel exports
2. Calculates derived metrics and trends
3. Detects underperformance using rule-based + statistical analysis
4. Generates AI-powered insights via Claude API
5. Sends prioritized alerts to Slack

**Business Impact:**
- ⏱️ Reduces detection time from days/weeks to hours
- 💰 Prevents revenue loss through early intervention
- 🤖 Eliminates 80% of manual QA work
- 📊 Provides data-driven action prioritization

## Features

### Core Capabilities

- **📊 Multi-Week Analysis**: Tracks performance trends across weeks of historical data
- **🎯 Smart Alert Scoring**: Cumulative severity scoring (0-200) captures compound issues
- **🤖 AI-Powered Insights**: Claude API generates root cause hypotheses and potential action items
- **💬 Slack Integration**: Rich alerts with direct links to listings
- **⚡ Automated Scheduling**: n8n workflow triggers weekly runs automatically
- **📈 Historical Tracking**: All alerts stored in MySQL for trend analysis
- **🔧 Configurable Thresholds**: Easily adjust sensitivity without code changes

### Alert Types

| Severity | Trigger | Business Impact |
|----------|---------|----------------|
| 🔴 **CRITICAL** | Zero search appearances | Listing invisible - immediate revenue loss |
| 🟠 **HIGH** | No bookings despite 50+ appearances | High visibility but zero conversion |
| 🟡 **MEDIUM** | 50%+ drop in view or conversion rate | Significant performance degradation |
| 🔵 **LOW** | 30%+ week-over-week decline | Early warning signal |

## Architecture

### System Components

![architecture-flow.jpg](attachment:https://github.com/neelagarwal98/ota-alert-system-n8n-automation/blob/main/architecture-flow.jpg)

### Technology Stack

- **Workflow Orchestration**: n8n (open-source automation, self-hosted for demo)
- **Data Processing**: Python 3.14 (pandas, numpy)
- **Database**: MySQL 9.5 (sqlalchemy)
- **AI**: Anthropic Claude API (Sonnet 4)
- **Notifications**: Slack (webhook integration)
- **Deployment**: Docker-ready, cron-compatible

## Installation

### Prerequisites

- Python 3.14
- MySQL 9.5 (Homebrew)
- n8n (optional for scheduling and automated run)
- Slack workspace with webhook access
- Anthropic API key

### Step 1: Clone Repository

```bash
git clone https://github.com/neelagarwal98/ota-alert-system-n8n-automation.git
cd kasa-ota-monitoring
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Database Setup

```bash
# Create database
mysql -u root -p < database_schema.sql

# Or manually:
mysql -u root -p
CREATE DATABASE kasa_ota_monitoring;
USE kasa_ota_monitoring;
SOURCE database_schema.sql;
```

### Step 4: Configure Environment Variables

```bash
# Edit .env with your credentials
nano .env
```

Required environment variables:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=kasa_ota_monitoring
DB_USER=kasa_user
DB_PASSWORD=your_secure_password

# Or use DATABASE_URL for cloud databases (e.g., PlanetScale)
# DATABASE_URL=mysql+pymysql://user:password@host:port/database

# API Keys
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#ota-alerts

# Alert Thresholds (optional - defaults provided)
CRITICAL_THRESHOLD=100
HIGH_THRESHOLD=75
MEDIUM_THRESHOLD=50
LOW_THRESHOLD=25
```

### Step 5: Test Installation

```bash
# Run basic test
python main.py --file data/sample.xlsx

# Test with all features
python main.py --file data/sample.xlsx --send-slack --use-ai
```

## Configuration

### Alert Threshold Customization

Edit `config.py` or set environment variables to adjust sensitivity:

```python
# config.py
class Config:
    # Severity scores (cumulative)
    CRITICAL_THRESHOLD = 100  # Zero appearances
    HIGH_THRESHOLD = 75       # No bookings + high visibility
    MEDIUM_THRESHOLD = 50     # Rate collapses
    LOW_THRESHOLD = 25        # WoW declines
    
    # Detection parameters
    MIN_APPEARANCES_FOR_HIGH_ALERT = 50  # Minimum search volume
    VIEW_RATE_DROP_THRESHOLD = 0.5       # 50% drop triggers alert
    CONVERSION_RATE_DROP_THRESHOLD = 0.5 # 50% drop triggers alert
    WOW_DECLINE_THRESHOLD = -30.0        # -30% WoW change
    HISTORICAL_WEEKS = 4                 # Rolling average window
```

### Slack Notification Customization

Modify `slack_notifier.py` to change message format:

```python
# slack_notifier.py
def format_alert_message(self, alerts_df, ai_summary=None):
    # Customize blocks, emojis, button text, etc.
    pass
```

### n8n Workflow Setup

1. Import `n8n-workflow.json` into your n8n instance
2. Configure schedule trigger (default: Monday 9 AM)
3. Update file path in Execute Command node
4. Test workflow manually before activating

## Usage

### Command Line Interface

```bash
# Basic run (no notifications)
python main.py --file path/to/data.xlsx

# Full production run
python main.py --file path/to/data.xlsx --send-slack --use-ai

# Help
python main.py --help
```

### Available Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--file` | Path to Excel data file | Required |
| `--send-slack` | Send Slack notifications | False |
| `--use-ai` | Generate AI insights | False |

### Typical Workflows

**Weekly Automated Run (via n8n):**
```bash
# This runs automatically every Monday at 9 AM
cd /path/to/kasa-ota-monitoring
source venv/bin/activate
python main.py --file "data/latest_report.xlsx" --send-slack --use-ai
```

**Manual Investigation:**
```bash
# Run analysis without sending alerts
python main.py --file data/latest_report.xlsx

# Check database for active alerts
mysql -u kasa_user -p kasa_ota_monitoring
SELECT * FROM alerts WHERE resolved = FALSE ORDER BY severity_score DESC LIMIT 10;
```

**Testing Changes:**
```bash
# Test without AI (faster)
python main.py --file data/test_data.xlsx

# Test with mock Slack webhook (won't actually send)
SLACK_WEBHOOK_URL=http://localhost:8080/mock python main.py --file data/test_data.xlsx --send-slack
```

## Project Structure

```
kasa-ota-monitoring/
│
├── main.py                 # Main execution script
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                  # Your environment variables (git-ignored)
│
├── src/                  # Source code modules
│   ├── __init__.py
│   ├── database.py       # Database connection & queries
│   ├── etl.py           # Data extraction, transformation, loading
│   ├── analysis.py      # Alert detection logic
│   ├── ai_insights.py   # Claude API integration
│   └── slack_notifier.py # Slack webhook integration
│
├── data/                 # Data files (git-ignored)
│   ├── sample.xlsx
│   └── archive/
│
├── logs/                 # Application logs (git-ignored)
│   └── pipeline.log
│
├── database_schema.sql   # MySQL schema definition
├── n8n-workflow.json    # n8n workflow export
│
├── tests/               # Unit tests
│   ├── test_etl.py
│   ├── test_analysis.py
│   ├── test_ai.py
│   └── test_slack.py
│
├── docs/                # Documentation
│   ├── PROJECT_MEMO.md
│
└── README.md            # This file
```

## Alert Logic

### How Alerts Are Generated

1. **Historical Data Retrieval**: Fetch last 5 weeks for each listing
2. **Metric Calculation**: 
   - View rate = views / appearances
   - Conversion rate = bookings / views
   - Week-over-week change = (current - previous) / previous
3. **Rule Evaluation**: Apply severity rules in sequence
4. **Score Accumulation**: Sum all triggered rule scores
5. **Severity Classification**: Assign CRITICAL/HIGH/MEDIUM/LOW based on score
6. **Issue Description**: Generate human-readable problem statements

### Alert Rules

```python
# Pseudocode for alert logic
score = 0
issues = []

if appearances == 0:
    score += 100  # CRITICAL
    issues.append("Listing invisible in search")

if appearances > 50 AND bookings == 0:
    score += 75   # HIGH
    issues.append("High visibility but zero conversions")

if view_rate < historical_avg * 0.5:
    score += 50   # MEDIUM
    issues.append("View rate collapsed")

if conversion_rate < historical_avg * 0.5:
    score += 50   # MEDIUM
    issues.append("Conversion rate collapsed")

if wow_change < -30%:
    score += 25   # LOW
    issues.append("Search visibility declining")

return Alert(score, issues)
```

### Example Scenarios

**Scenario 1: Booking System Failure**
- Appearances: 829 (high) ✅
- Views: 5 (extremely low) ❌
- Bookings: 0 ❌
- **Score: 200** (HIGH + 2×MEDIUM + LOW)
- **Diagnosis**: Likely technical issue preventing bookings

**Scenario 2: Pricing Too High**
- Appearances: 450 (good) ✅
- Views: 200 (good) ✅
- Bookings: 0 ❌
- **Score: 75** (HIGH only)
- **Diagnosis**: Guests viewing but not converting - check pricing

**Scenario 3: Search Rank Drop**
- Appearances: 50 → 30 (down 40%) ❌
- Views: 20 → 15 (proportional) ✅
- Bookings: 2 → 1 (proportional) ✅
- **Score: 25** (LOW only)
- **Diagnosis**: Search visibility declining - monitor closely

## Database Schema

### Key Tables

**raw_listing_performance**
- Stores weekly metrics from OTA platforms
- Columns: id_listing, week_start, appearance_in_search, total_listing_views, bookings

**listing_metrics**
- Calculated derived metrics
- Columns: view_rate, conversion_rate, rolling averages, WoW changes

**alerts**
- Generated alerts with full context
- Columns: severity_score, severity_level, issues, recommended_actions, resolved status

**listing_metadata**
- Property information (location, type, amenities) - for future enhancement and lookup (unpopulated)

### Useful Queries

```sql
-- View current week's underperformers
SELECT * FROM v_current_week_performance 
WHERE alert_status != 'NONE' 
ORDER BY alert_score DESC 
LIMIT 20;

-- Get listing history
CALL sp_get_listing_trend(680523499995195758, 5);

-- Active alerts summary
SELECT * FROM v_active_alerts;

-- Mark alert resolved
UPDATE alerts SET resolved = TRUE, resolved_at = NOW() 
WHERE id = 123;
```

## Deployment

### Production Deployment Options (beyond this PoC)

#### Option 1: Cron Job (Simple)

```bash
# Add to crontab
crontab -e

# Run every Monday at 9 AM
0 9 * * 1 cd /path/to/kasa-ota-monitoring && ./venv/bin/python main.py --file data/latest.xlsx --send-slack --use-ai >> logs/cron.log 2>&1
```

#### Option 2: n8n Workflow (Recommended)

1. Self-host n8n on your infrastructure
2. Import `n8n-workflow.json`
3. Configure schedule trigger
4. Monitor execution logs in n8n UI

#### Option 3: Docker Container

```dockerfile
# Dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py", "--file", "data/latest.xlsx", "--send-slack", "--use-ai"]
```

```bash
# Build and run
docker build -t kasa-ota-monitoring .
docker run -d --env-file .env kasa-ota-monitoring
```

#### Option 4: Cloud Functions

Deploy as AWS Lambda, Google Cloud Function, or similar:
- Trigger: CloudWatch Events (weekly schedule)
- Upload data to S3/GCS
- Lambda reads data, processes, sends alerts
- Serverless = no server maintenance

### Environment-Specific Configs

**Development:**
```env
DB_HOST=localhost
SLACK_WEBHOOK_URL=http://localhost:8080/mock  # Mock endpoint
ANTHROPIC_API_KEY=test-key  # Use test credits
```

**Staging:**
```env
DB_HOST=staging-db.internal
SLACK_CHANNEL=#ota-alerts-staging
```

**Production:**
```env
DB_HOST=prod-db.internal  # Or PlanetScale URL
SLACK_CHANNEL=#ota-alerts
# Use environment secrets for API keys
```

## License

This project is licensed under the MIT License - Neel Agarwal.

## Acknowledgments

- **Anthropic**: Claude API for AI-powered insights
- **n8n**: Open-source automation platform
- **Kasa Living**: Case study opportunity

## Contact

**Author**: Neel Agarwal   
**Email**: neelagarwal98@gmail.com

**LinkedIn**: [LinkedIn](https://www.linkedin.com/in/neelagarwal/)  
**GitHub**: [GitHub](https://github.com/neelagarwal98/)

---

**November 2025**
