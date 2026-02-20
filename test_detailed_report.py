#!/usr/bin/env python
"""Generate a detailed technical report"""
import sys
from cli.main import cli

if __name__ == '__main__':
    sys.argv = [
        'rds-diag', 
        '--config', 'config.yaml',
        '--profile', 'LT-SIT',
        'report',
        '--instance', 'ielts-ors-sit-v1-clusterinstance1',
        '--time-range', '15m',
        '--output', 'detailed-report.txt'
    ]
    cli()
