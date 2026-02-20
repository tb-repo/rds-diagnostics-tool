@echo off
REM Advanced script to diagnose an RDS instance with optional profile override
REM Usage: rds-diagnose-advanced.bat <instance-id> [time-range] [profile]
REM Example: rds-diagnose-advanced.bat my-db-instance 24h LT-PRD

if "%1"=="" (
    echo Usage: rds-diagnose-advanced.bat ^<instance-id^> [time-range] [profile]
    echo Example: rds-diagnose-advanced.bat my-db-instance 24h LT-PRD
    echo.
    echo If profile is not specified, uses the profile from config.yaml (LT-DEV)
    exit /b 1
)

set INSTANCE=%1
set TIME_RANGE=%2
set PROFILE=%3

if "%TIME_RANGE%"=="" set TIME_RANGE=1h

if "%PROFILE%"=="" (
    echo Using profile from config.yaml...
    rds-diag --config config.yaml diagnose --instance %INSTANCE% --time-range %TIME_RANGE%
) else (
    echo Using profile: %PROFILE%
    rds-diag --config config.yaml --profile %PROFILE% diagnose --instance %INSTANCE% --time-range %TIME_RANGE%
)
