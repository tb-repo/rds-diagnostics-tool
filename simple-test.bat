@echo off
REM Simple test to check if we can get SQL queries from Performance Insights

echo ================================================================================
echo Simple Performance Insights Test
echo ================================================================================
echo.
echo This is a minimal test to check if we can retrieve SQL queries at all.
echo.
echo Press any key to start...
pause > nul

python simple_test.py

echo.
pause
