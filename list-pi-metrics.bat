@echo off
REM List all available Performance Insights metrics for PostgreSQL

echo ================================================================================
echo Performance Insights Metrics Discovery
echo ================================================================================
echo.
echo This script will comprehensively test what metrics are available from
echo Performance Insights API for your Aurora PostgreSQL 17.5 instance.
echo.
echo Instance: ielts-ses-sit-v1-clusterinstance1
echo Profile: LT-SIT
echo Region: ap-southeast-1
echo.
echo This will take about 30-60 seconds to complete...
echo.

python list_all_pi_metrics.py

echo.
echo ================================================================================
echo Script completed!
echo ================================================================================
echo.
echo The output above shows:
echo   1. All available dimension groups (db.sql, db.user, etc.)
echo   2. All available resource metrics (db.load, os.*, etc.)
echo   3. Which dimension groups work and which don't
echo   4. Sample data from each working metric type
echo   5. Summary of what's available vs. what's not
echo.
pause
