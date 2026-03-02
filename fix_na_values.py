#!/usr/bin/env python3
"""Fix N/A values in report formatter."""

with open('reporting/formatters.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace the section
in_execution_metrics = False
in_resource_metrics = False
in_row_metrics = False
in_io_metrics = False
new_lines = []
skip_until_blank = False

for i, line in enumerate(lines):
    # Skip N/A lines
    if 'N/A' in line and ('CPU Time' in line or 'Lock Time' in line or 
                          'Rows Examined' in line or 'Rows Returned' in line or
                          'Efficiency Ratio' in line or 'Read I/O:' in line or
                          'Write I/O:' in line or 'Read I/O Time' in line or
                          'Write I/O Time' in line or 'Executions/sec' in line):
        continue
    
    # Skip "Note: Execution count not available" line
    if 'Note: Execution count not available from PI API for PostgreSQL' in line:
        continue
    
    # Skip section headers if all values would be N/A
    if line.strip() == 'lines.append("Resource Metrics:")':
        # Check if next lines have actual values
        has_values = False
        for j in range(i+1, min(i+10, len(lines))):
            if 'is not None' in lines[j]:
                has_values = True
                break
        if not has_values:
            skip_until_blank = True
            continue
    
    if skip_until_blank and line.strip() == 'lines.append("")':
        skip_until_blank = False
        continue
    
    if not skip_until_blank:
        new_lines.append(line)

# Write back
with open('reporting/formatters.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed N/A values in report formatter")
