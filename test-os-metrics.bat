@echo off
REM Test OS metrics collection

echo ================================================================================
echo Testing OS Metrics Collection
echo ================================================================================
echo.
echo This will run a diagnostic report with OS-level metrics collection.
echo.
echo Instance: ielts-ses-sit-v1-clusterinstance1
echo Profile: LT-SIT
echo Time Range: 1h (for faster testing)
echo.

rds-diag --verbose --profile LT-SIT report --instance ielts-ses-sit-v1-clusterinstance1 --time-range 1h --report-type technical

echo.
echo ================================================================================
echo Test completed!
echo ================================================================================
echo.
echo Check the report above for the new "OS-LEVEL PERFORMANCE METRICS" section.
echo.
echo Key metrics to look for:
echo   - CPU I/O Wait (should show if database is waiting for disk)
echo   - Read/Write Latency (key metrics for performance analysis)
echo   - Disk Queue Depth (I/O bottleneck indicator)
echo   - Temp Blocks (queries spilling to disk)
echo.
pause
