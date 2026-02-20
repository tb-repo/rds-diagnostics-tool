#!/usr/bin/env python
"""Test the CLI directly"""
import sys
from cli.main import cli

if __name__ == '__main__':
    sys.argv = ['rds-diag', '--profile', 'LT-DEV', '--region', 'ap-southeast-1', 'list']
    cli()
