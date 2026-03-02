@echo off
REM Debug script for Performance Insights collection
REM This will show detailed information about what's happening

echo ================================================================================
echo Performance Insights Debug Script
echo ================================================================================
echo.
echo This script will test Performance Insights data collection and show
echo detailed debug information to help identify why SQL queries are not appearing.
echo.
echo Instance: ielts-ses-sit-v1-clusterinstance1
echo Profile: LT-SIT
echo Time Range: Last 24 hours
echo.
echo Press any key to start...
pause > nul

python debug_pi_collection.py

echo.
echo ================================================================================
echo Debug script completed
echo ================================================================================
echo.
echo Please review the output above and share it with me.
echo Look for any ERROR or FAILED messages.
echo.
pause
