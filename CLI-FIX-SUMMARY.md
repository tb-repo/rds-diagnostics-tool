# CLI Syntax Fix - Summary

## Problem

The command `rds-diag list --profile DM-PRD` was failing with error:
```
Error: No such option: --profile
```

## Root Cause

The RDS Diagnostics Tool uses Click's `@click.group()` decorator, which defines global options at the group level. In Click, global options must be specified BEFORE the subcommand, not after.

## Solution

### Correct Syntax
```bash
rds-diag --profile DM-PRD list
```

### Incorrect Syntax (was shown in examples)
```bash
rds-diag list --profile DM-PRD  # ❌ FAILS
```

## Changes Made

### 1. Updated `cli/main.py`

Fixed all docstring examples to show correct option ordering:

**Main CLI command (lines 145-162):**
- ✅ `rds-diag --profile lt-prd list`
- ✅ `rds-diag --profile lt-prd diagnose --instance my-db-instance`
- ✅ `rds-diag --profile lt-prd report --instance my-db --time-range 24h --report-type technical`

**List command (line 215):**
- ✅ `rds-diag --profile lt-prd --region us-east-1 list`

**Diagnose command (line 298):**
- ✅ `rds-diag --profile lt-prd diagnose --instance my-db --time-range 24h`
- ✅ `rds-diag --verbose diagnose -i my-db -t 7d`

**Check-permissions command (line 590):**
- ✅ `rds-diag --profile lt-prd check-permissions`

### 2. Updated `EXAMPLES.md`

Fixed direct `rds-diag` command example:
- ✅ `rds-diag --profile LT-PRD --config config.yaml report --instance prod-db --report-type management --format json --output management.json`

Note: The batch script examples (rds-list.bat, rds-diagnose.bat, etc.) were already correct as they handle option ordering internally.

### 3. Created Documentation

Created `CLI-SYNTAX-GUIDE.md` with:
- Clear explanation of correct syntax
- ✅ Correct usage examples
- ❌ Incorrect usage examples (what NOT to do)
- Quick reference for all commands
- Explanation of why this syntax is required

## Testing

Verified the fix works:

```bash
# Before fix
C:\Users\thiagarajan.b>rds-diag list --profile DM-PRD
Error: No such option: --profile

# After fix
C:\Users\thiagarajan.b>rds-diag --profile DM-PRD list
2026-03-02 16:57:26 - aws.clients - INFO - Created AWS session with profile: DM-PRD
2026-03-02 16:57:27 - core.app - INFO - Listing RDS instances in region ap-southeast-1
2026-03-02 16:57:28 - core.app - INFO - Found 0 RDS instances
No RDS instances found in this region.
```

## Key Takeaway

**Global options (--profile, --region, --verbose, --config) must ALWAYS come BEFORE the subcommand:**

```
rds-diag [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
         ↑                ↑
         First            Second
```

## Files Modified

1. `cli/main.py` - Fixed all docstring examples
2. `EXAMPLES.md` - Fixed direct rds-diag command example

## Files Created

1. `CLI-SYNTAX-GUIDE.md` - Comprehensive syntax guide
2. `CLI-FIX-SUMMARY.md` - This summary document

## Related Documentation

- Run `rds-diag --help` to see the correct syntax in the help text
- Run `rds-diag COMMAND --help` for command-specific help
- See `CLI-SYNTAX-GUIDE.md` for detailed examples and explanations
