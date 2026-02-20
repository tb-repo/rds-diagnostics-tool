#!/usr/bin/env python
"""Test Performance Insights with the UTC fix"""
import sys
from cli.main import cli

if __name__ == '__main__':
    sys.argv = [
        'rds-diag', 
        '--config', 'config.yaml',
        '--profile', 'LT-SIT',
        'diagnose',
        '--instance', 'ielts-ors-sit-v1-clusterinstance1',
        '--time-range', '1h'
    ]
    cli()
