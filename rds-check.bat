@echo off
REM Quick script to check AWS permissions
REM Usage: rds-check.bat [--profile PROFILE] [--region REGION]
REM Example: rds-check.bat --profile LT-SIT --region ap-southeast-1

rds-diag --config config.yaml %* check-permissions
