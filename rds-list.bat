@echo off
REM Quick script to list RDS instances
REM Usage: rds-list.bat [--profile PROFILE] [--region REGION]
REM Example: rds-list.bat --profile LT-SIT --region ap-southeast-1

rds-diag --config config.yaml %* list
