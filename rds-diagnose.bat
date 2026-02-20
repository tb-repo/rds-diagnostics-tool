@echo off
REM Quick script to diagnose an RDS instance
REM Usage: rds-diagnose.bat [--profile PROFILE] [--region REGION] --instance INSTANCE [--time-range TIME]
REM Example: rds-diagnose.bat --profile LT-SIT --instance my-db --time-range 24h

setlocal enabledelayedexpansion

set "PROFILE_ARG="
set "REGION_ARG="
set "INSTANCE_ARG="
set "TIME_ARG="

:parse
if "%~1"=="" goto endparse
if /i "%~1"=="--profile" (
    set "PROFILE_ARG=--profile %~2"
    shift
    shift
    goto parse
)
if /i "%~1"=="--region" (
    set "REGION_ARG=--region %~2"
    shift
    shift
    goto parse
)
if /i "%~1"=="--instance" (
    set "INSTANCE_ARG=--instance %~2"
    shift
    shift
    goto parse
)
if /i "%~1"=="--time-range" (
    set "TIME_ARG=--time-range %~2"
    shift
    shift
    goto parse
)
shift
goto parse

:endparse

if "%INSTANCE_ARG%"=="" (
    echo Error: --instance is required
    echo Usage: rds-diagnose.bat [--profile PROFILE] [--region REGION] --instance INSTANCE [--time-range TIME]
    echo Example: rds-diagnose.bat --profile LT-SIT --instance my-db --time-range 24h
    exit /b 1
)

rds-diag --config config.yaml %PROFILE_ARG% %REGION_ARG% diagnose %INSTANCE_ARG% %TIME_ARG%
