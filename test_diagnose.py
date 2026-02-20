#!/usr/bin/env python
"""Test the diagnose command"""
import sys
from cli.main import cli

if __name__ == '__main__':
    sys.argv = [
        'rds-diag', 
        '--profile', 'LT-DEV', 
        '--region', 'ap-southeast-1',
        'diagnose',
        '--instance', 'ielts-idv-dev-v1-clusterinstance1',
        '--time-range', '1h'
    ]
    cli()
