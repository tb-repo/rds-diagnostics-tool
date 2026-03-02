@echo off
REM Test to discover what metrics are actually available from AWS Performance Insights

echo ================================================================================
echo Performance Insights Available Metrics Test
echo ================================================================================
echo.
echo This will show us:
echo   1. What metrics are available for Aurora PostgreSQL
echo   2. What the actual API response looks like
echo   3. Why our tool is showing N/A for everything
echo.
echo Press any key to start...
pause > nul

python test_actual_metrics.py > metrics-test-output.txt 2>&1

echo.
echo ================================================================================
echo Test completed!
echo ================================================================================
echo.
echo Output saved to: metrics-test-output.txt
echo.
echo Please share this file with me so I can see what metrics are available.
echo.
pause

type metrics-test-output.txt
