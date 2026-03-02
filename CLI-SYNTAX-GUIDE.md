# RDS Diagnostics Tool - CLI Syntax Guide

## Important: Global Options Must Come BEFORE Subcommands

The RDS Diagnostics Tool uses Click's command group structure, which requires global options (like `--profile`, `--region`, `--verbose`) to be specified BEFORE the subcommand.

## Correct Syntax

```bash
rds-diag [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

### Global Options (must come BEFORE subcommand)
- `--profile` / `-p`: AWS CLI profile name
- `--region` / `-r`: AWS region
- `--config` / `-c`: Path to configuration file
- `--verbose` / `-v`: Enable verbose output

## Examples

### ✅ CORRECT Usage

```bash
# List instances with profile
rds-diag --profile DM-PRD list

# Diagnose with profile and verbose
rds-diag --profile LT-SIT --verbose diagnose --instance my-db

# Generate report with profile and region
rds-diag --profile LT-PRD --region us-east-1 report --instance my-db --time-range 24h

# Multiple global options
rds-diag --profile DM-PRD --region ap-southeast-1 --verbose list
```

### ❌ INCORRECT Usage (Will Fail)

```bash
# DON'T put --profile after subcommand
rds-diag list --profile DM-PRD
# Error: No such option: --profile

# DON'T put --verbose after subcommand
rds-diag diagnose --instance my-db --verbose
# Error: No such option: --verbose

# DON'T mix global and command options
rds-diag --profile DM-PRD diagnose --region us-east-1 --instance my-db
# Error: No such option: --region
```

## Command-Specific Options

Command-specific options (like `--instance`, `--time-range`, `--output`) should come AFTER the subcommand:

```bash
# Correct order: global options → subcommand → command options
rds-diag --profile LT-PRD report --instance my-db --time-range 24h --output report.txt
```

## Quick Reference

### List Command
```bash
# Basic
rds-diag list

# With profile
rds-diag --profile DM-PRD list

# With profile and region
rds-diag --profile DM-PRD --region us-east-1 list
```

### Diagnose Command
```bash
# Basic
rds-diag diagnose --instance my-db

# With profile
rds-diag --profile LT-SIT diagnose --instance my-db

# With profile and time range
rds-diag --profile LT-SIT diagnose --instance my-db --time-range 24h

# With all options
rds-diag --profile LT-SIT --verbose diagnose --instance my-db --time-range 24h
```

### Report Command
```bash
# Basic
rds-diag report --instance my-db

# With profile
rds-diag --profile LT-PRD report --instance my-db

# With profile and options
rds-diag --profile LT-PRD report --instance my-db --time-range 24h --report-type technical

# Full example
rds-diag --profile LT-PRD --verbose report --instance my-db --time-range 24h --report-type technical --format json --output report.json
```

### Check Permissions Command
```bash
# Basic
rds-diag check-permissions

# With profile
rds-diag --profile DM-PRD check-permissions
```

## Using Batch Scripts (Windows)

The provided batch scripts (rds-list.bat, rds-diagnose.bat, rds-report.bat) handle the option ordering for you:

```bash
# These batch scripts automatically put options in the correct order
rds-list.bat --profile DM-PRD
rds-diagnose.bat --instance my-db --profile LT-SIT
rds-report.bat --instance my-db --profile LT-PRD --output report.txt
```

The batch scripts internally convert these to the correct syntax:
```bash
rds-diag --profile DM-PRD list
rds-diag --profile LT-SIT diagnose --instance my-db
rds-diag --profile LT-PRD report --instance my-db --output report.txt
```

## Why This Syntax?

This is a standard Click (Python CLI framework) behavior for command groups with global options. Global options must be parsed before the subcommand is determined, so they must appear first in the command line.

## Getting Help

```bash
# Main help (shows global options and subcommands)
rds-diag --help

# Subcommand help (shows command-specific options)
rds-diag list --help
rds-diag diagnose --help
rds-diag report --help
rds-diag check-permissions --help
```

## Summary

**Remember:** Global options (--profile, --region, --verbose, --config) ALWAYS come BEFORE the subcommand!

```
rds-diag [GLOBAL] COMMAND [COMMAND-SPECIFIC]
         ↑                ↑
         First            Second
```
