-- Kasa OTA Monitoring Database Schema
-- Author: Neel Agarwal
-- MySQL Database

-- Create database
CREATE DATABASE IF NOT EXISTS kasa_ota_monitoring;
USE kasa_ota_monitoring;

-- ============================================================================
-- Table 1: Raw Listing Performance Data
-- Stores raw weekly metrics from OTA platforms
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_listing_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_listing BIGINT NOT NULL COMMENT 'Listing ID from OTA platform',
    id_host BIGINT COMMENT 'Host/property manager ID',
    week_start DATE NOT NULL COMMENT 'Start date of reporting week',
    week_end DATE NOT NULL COMMENT 'End date of reporting week',
    week_period VARCHAR(50) COMMENT 'Human-readable week period (e.g., "7.21.25 to 7.28.25")',
    appearance_in_search INT DEFAULT 0 COMMENT 'Number of times listing appeared in search results',
    total_listing_views INT DEFAULT 0 COMMENT 'Number of times listing detail page was viewed',
    bookings INT DEFAULT 0 COMMENT 'Number of bookings received',
    data_source VARCHAR(20) DEFAULT 'airbnb' COMMENT 'Source OTA platform (airbnb, expedia, booking.com)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
    
    -- Indexes for performance
    INDEX idx_listing (id_listing),
    INDEX idx_week (week_start),
    INDEX idx_listing_week (id_listing, week_start),
    
    -- Ensure we don't duplicate data
    UNIQUE KEY unique_listing_week (id_listing, week_start, data_source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Raw weekly performance data from OTA platforms';

-- ============================================================================
-- Table 2: Calculated Metrics
-- Stores derived metrics and rolling averages
-- ============================================================================
CREATE TABLE IF NOT EXISTS listing_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_listing BIGINT NOT NULL,
    week_start DATE NOT NULL,
    
    -- Current week metrics
    view_rate DECIMAL(10, 6) COMMENT 'views / appearances',
    conversion_rate DECIMAL(10, 6) COMMENT 'bookings / views',
    search_to_booking_rate DECIMAL(10, 6) COMMENT 'bookings / appearances',
    
    -- Rolling averages (4-week historical)
    avg_appearance_4week DECIMAL(10, 2) COMMENT '4-week average appearances',
    avg_views_4week DECIMAL(10, 2) COMMENT '4-week average views',
    avg_bookings_4week DECIMAL(10, 2) COMMENT '4-week average bookings',
    
    -- Week-over-week changes
    wow_appearance_change_pct DECIMAL(10, 2) COMMENT 'Week-over-week % change in appearances',
    wow_view_change_pct DECIMAL(10, 2) COMMENT 'Week-over-week % change in views',
    wow_booking_change_pct DECIMAL(10, 2) COMMENT 'Week-over-week % change in bookings',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_listing (id_listing),
    INDEX idx_week (week_start),
    UNIQUE KEY unique_metric (id_listing, week_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Calculated performance metrics and rolling averages';

-- ============================================================================
-- Table 3: Alerts
-- Stores generated alerts for underperforming listings
-- ============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_listing BIGINT NOT NULL,
    alert_date DATE NOT NULL COMMENT 'Date of the performance issue',
    
    -- Severity
    severity_score INT NOT NULL COMMENT 'Numeric severity score (0-200)',
    severity_level ENUM('CRITICAL', 'HIGH', 'MEDIUM', 'LOW') NOT NULL COMMENT 'Alert severity category',
    
    -- Issue description
    issues TEXT NOT NULL COMMENT 'Detailed description of issues detected',
    
    -- Current week metrics (ADDED)
    latest_appearances INT COMMENT 'Search appearances in alert week',
    latest_views INT COMMENT 'Listing views in alert week',
    latest_bookings INT COMMENT 'Bookings in alert week',
    latest_view_rate DECIMAL(10, 6) COMMENT 'View rate in alert week',
    latest_conversion_rate DECIMAL(10, 6) COMMENT 'Conversion rate in alert week',
    
    -- Historical context (ADDED)
    avg_appearances DECIMAL(10, 2) COMMENT '4-week historical avg appearances',
    avg_bookings DECIMAL(10, 2) COMMENT '4-week historical avg bookings',
    wow_change_pct DECIMAL(10, 2) COMMENT 'Week-over-week change percentage',
    
    -- AI recommendations
    recommended_actions TEXT COMMENT 'AI-generated recommended actions',
    
    -- Alert delivery tracking
    alert_sent_to VARCHAR(100) COMMENT 'Where alert was sent (slack, email, etc.)',
    slack_message_ts VARCHAR(50) COMMENT 'Slack message timestamp for updates',
    
    -- Resolution tracking
    resolved BOOLEAN DEFAULT FALSE COMMENT 'Whether issue has been resolved',
    resolved_at TIMESTAMP NULL COMMENT 'When issue was resolved',
    resolved_notes TEXT COMMENT 'Notes about resolution',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_listing (id_listing),
    INDEX idx_severity (severity_score DESC),
    INDEX idx_date (alert_date DESC),
    INDEX idx_resolved (resolved, severity_score DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Generated alerts for listing performance issues';

-- ============================================================================
-- Table 4: Listing Metadata 
-- Stores additional information about listings
-- ============================================================================
CREATE TABLE IF NOT EXISTS listing_metadata (
    id_listing BIGINT PRIMARY KEY,
    property_name VARCHAR(255) COMMENT 'Property name',
    city VARCHAR(100) COMMENT 'City location',
    state VARCHAR(50) COMMENT 'State/province',
    country VARCHAR(50) DEFAULT 'USA',
    property_type VARCHAR(50) COMMENT 'apartment, house, studio, etc.',
    bedrooms INT COMMENT 'Number of bedrooms',
    bathrooms DECIMAL(3,1) COMMENT 'Number of bathrooms',
    max_guests INT COMMENT 'Maximum guest capacity',
    
    -- External links
    airbnb_url VARCHAR(500) COMMENT 'Direct link to Airbnb listing',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Whether listing is currently active',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Additional metadata about listings';

-- ============================================================================
-- Table 5: Alert History (For tracking over time)
-- Useful for understanding alert frequency and patterns
-- ============================================================================
CREATE TABLE IF NOT EXISTS alert_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_listing BIGINT NOT NULL,
    alert_month DATE NOT NULL COMMENT 'Month of alert (YYYY-MM-01)',
    total_alerts INT DEFAULT 0 COMMENT 'Total alerts this month',
    critical_alerts INT DEFAULT 0,
    high_alerts INT DEFAULT 0,
    medium_alerts INT DEFAULT 0,
    low_alerts INT DEFAULT 0,
    avg_severity_score DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_listing (id_listing),
    INDEX idx_month (alert_month DESC),
    UNIQUE KEY unique_listing_month (id_listing, alert_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Monthly alert summary for trend analysis';

-- ============================================================================
-- Useful Views
-- ============================================================================

-- View: Current Week Performance with Metrics
CREATE OR REPLACE VIEW v_current_week_performance AS
SELECT 
    r.id_listing,
    r.week_start,
    r.week_period,
    r.appearance_in_search,
    r.total_listing_views,
    r.bookings,
    m.view_rate,
    m.conversion_rate,
    m.search_to_booking_rate,
    COALESCE(a.severity_level, 'NONE') as alert_status,
    COALESCE(a.severity_score, 0) as alert_score
FROM raw_listing_performance r
LEFT JOIN listing_metrics m ON r.id_listing = m.id_listing AND r.week_start = m.week_start
LEFT JOIN alerts a ON r.id_listing = a.id_listing AND r.week_start = a.alert_date AND a.resolved = FALSE
WHERE r.week_start = (SELECT MAX(week_start) FROM raw_listing_performance)
ORDER BY alert_score DESC, r.appearance_in_search DESC;

-- View: Active Alerts Summary
CREATE OR REPLACE VIEW v_active_alerts AS
SELECT 
    a.severity_level,
    COUNT(*) as alert_count,
    AVG(a.severity_score) as avg_score,
    MIN(a.created_at) as oldest_alert,
    MAX(a.created_at) as newest_alert
FROM alerts a
WHERE a.resolved = FALSE
GROUP BY a.severity_level
ORDER BY 
    FIELD(a.severity_level, 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW');

-- ============================================================================
-- Stored Procedures
-- ============================================================================

DELIMITER //

-- Procedure to get listing performance trend
CREATE PROCEDURE IF NOT EXISTS sp_get_listing_trend(IN p_listing_id BIGINT, IN p_weeks INT)
BEGIN
    SELECT 
        week_start,
        appearance_in_search,
        total_listing_views,
        bookings,
        ROUND(total_listing_views * 100.0 / NULLIF(appearance_in_search, 0), 2) as view_rate_pct,
        ROUND(bookings * 100.0 / NULLIF(total_listing_views, 0), 2) as conversion_rate_pct
    FROM raw_listing_performance
    WHERE id_listing = p_listing_id
    ORDER BY week_start DESC
    LIMIT p_weeks;
END //

-- Procedure to mark old alerts as auto-resolved
CREATE PROCEDURE IF NOT EXISTS sp_auto_resolve_old_alerts(IN p_days_old INT)
BEGIN
    UPDATE alerts
    SET resolved = TRUE,
        resolved_at = CURRENT_TIMESTAMP,
        resolved_notes = 'Auto-resolved: No activity for X days'
    WHERE resolved = FALSE
      AND created_at < DATE_SUB(CURRENT_DATE, INTERVAL p_days_old DAY);
    
    SELECT ROW_COUNT() as alerts_resolved;
END //

DELIMITER ;

-- ============================================================================
-- Sample Data Queries
-- ============================================================================

-- Get top 10 underperforming listings
-- SELECT * FROM v_current_week_performance WHERE alert_status != 'NONE' LIMIT 10;

-- Get alert summary
-- SELECT * FROM v_active_alerts;

-- Get specific listing trend
-- CALL sp_get_listing_trend(680523499995195758, 5);

-- ============================================================================
-- Maintenance Queries
-- ============================================================================

-- Clean up very old resolved alerts (keep last 90 days)
-- DELETE FROM alerts WHERE resolved = TRUE AND resolved_at < DATE_SUB(CURRENT_DATE, INTERVAL 90 DAY);

-- Rebuild alert history summary
-- INSERT INTO alert_history (id_listing, alert_month, total_alerts, critical_alerts, high_alerts, medium_alerts, low_alerts, avg_severity_score)
-- SELECT 
--     id_listing,
--     DATE_FORMAT(alert_date, '%Y-%m-01') as alert_month,
--     COUNT(*) as total_alerts,
--     SUM(CASE WHEN severity_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_alerts,
--     SUM(CASE WHEN severity_level = 'HIGH' THEN 1 ELSE 0 END) as high_alerts,
--     SUM(CASE WHEN severity_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_alerts,
--     SUM(CASE WHEN severity_level = 'LOW' THEN 1 ELSE 0 END) as low_alerts,
--     AVG(severity_score) as avg_severity_score
-- FROM alerts
-- GROUP BY id_listing, DATE_FORMAT(alert_date, '%Y-%m-01')
-- ON DUPLICATE KEY UPDATE
--     total_alerts = VALUES(total_alerts),
--     critical_alerts = VALUES(critical_alerts),
--     high_alerts = VALUES(high_alerts),
--     medium_alerts = VALUES(medium_alerts),
--     low_alerts = VALUES(low_alerts),
--     avg_severity_score = VALUES(avg_severity_score);

-- ============================================================================
-- Grant Permissions (adjust as needed)
-- ============================================================================

-- GRANT SELECT, INSERT, UPDATE ON kasa_ota_monitoring.* TO 'kasa_user'@'%';
-- FLUSH PRIVILEGES;
