@echo off
REM Quick script to generate an RDS report
REM Usage: rds-report.bat [--profile PROFILE] [--region REGION] --instance INSTANCE [--output FILE] [--time-range TIME] [--report-type TYPE] [--format FORMAT]
REM Example: rds-report.bat --profile LT-SIT --instance my-db --output report.txt --time-range 24h

setlocal enabledelayedexpansion

set "PROFILE_ARG="
set "REGION_ARG="
set "INSTANCE_ARG="
set "OUTPUT_ARG="
set "TIME_ARG="
set "REPORT_TYPE_ARG="
set "FORMAT_ARG="

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
if /i "%~1"=="--output" (
    set "OUTPUT_ARG=--output %~2"
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
if /i "%~1"=="--report-type" (
    set "REPORT_TYPE_ARG=--report-type %~2"
    shift
    shift
    goto parse
)
if /i "%~1"=="--format" (
    set "FORMAT_ARG=--format %~2"
    shift
    shift
    goto parse
)
shift
goto parse

:endparse

if "%INSTANCE_ARG%"=="" (
    echo Error: --instance is required
    echo Usage: rds-report.bat [--profile PROFILE] [--region REGION] --instance INSTANCE [--output FILE] [--time-range TIME]
    echo Example: rds-report.bat --profile LT-SIT --instance my-db --output report.txt --time-range 24h
    exit /b 1
)

rds-diag --config config.yaml %PROFILE_ARG% %REGION_ARG% report %INSTANCE_ARG% %OUTPUT_ARG% %TIME_ARG% %REPORT_TYPE_ARG% %FORMAT_ARG%
