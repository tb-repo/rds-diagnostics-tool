---
inclusion: always
---

# Product Overview

RDS Diagnostics and Reporting Tool is a CLI utility for AWS Database Management (DBM) teams to diagnose and report on RDS instance performance across multiple accounts and environments.

## Core Capabilities

- Instance discovery across AWS accounts and regions
- CloudWatch metrics collection (CPU, memory, connections, IOPS, storage)
- Performance Insights integration (SQL queries, wait events, top databases/users)
- Intelligent threshold-based analysis with severity assessment
- Dual reporting modes: technical (detailed) and management (executive summary)
- Multi-account support via AWS profiles
- Configurable alert thresholds

## Target Users

Database administrators and DBM teams who need to quickly identify performance issues, analyze metrics, and generate reports for technical and management audiences.

## Key Design Principles

- Modular architecture with clear separation of concerns
- AWS SDK integration via boto3
- Configuration-driven thresholds and defaults
- Graceful degradation (works without Performance Insights)
- Comprehensive error handling with actionable suggestions
