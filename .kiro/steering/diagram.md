# RDS Diagnostics Tool - Architecture Diagram

## System Architecture Overview

The RDS Diagnostics Tool is a **local Python CLI application** that runs on your machine and makes read-only API calls to existing AWS services. 

**Important:** This tool does NOT create or require any AWS resources (no Lambda functions, S3 buckets, EC2 instances, etc.). It only uses boto3 to make API calls to existing AWS services to gather information about your RDS instances.

## Architecture Components

### Local Machine (Client Side)

#### User Interface Layer
- CLI interface built with Click framework
- Batch scripts for Windows users (rds-list.bat, rds-diagnose.bat, etc.)
- Command-line arguments and configuration file support

#### Application Core (Python Application)
- **RDSDiagnosticsApp**: Main orchestrator coordinating all operations
- **Configuration Management**: YAML-based config with validation
- **Data Models**: Pydantic v2 models for type-safe data handling

#### AWS SDK Layer (boto3)
- **RDS Client**: Makes API calls to retrieve instance metadata and parameters
- **CloudWatch Client**: Makes API calls to retrieve metrics (CPU, memory, connections, IOPS, storage)
- **Performance Insights Client**: Makes API calls to retrieve SQL queries, wait events, top databases/users

#### Data Processing Layer (Local)
- **Instance Info Collector**: Processes RDS instance metadata locally
- **Metrics Collector**: Processes CloudWatch metrics locally
- **Performance Insights Collector**: Processes advanced database performance data locally

#### Analysis & Reporting Layer (Local)
- **Diagnostic Analyzer**: Threshold-based analysis and severity assessment (runs locally)
- **Report Generator**: Technical and management report formatting (runs locally)
- **Formatters**: Text and JSON output formats (runs locally)

### AWS Cloud (API Services Only)

**No AWS resources are created or required.** The tool only makes read-only API calls to:

- **AWS IAM**: Authentication and authorization
- **Amazon RDS API**: Database instance information and configuration
- **Amazon CloudWatch API**: Performance metrics and monitoring data
- **AWS Performance Insights API**: SQL-level performance analysis

## Data Flow

1. User invokes CLI command (list, diagnose, report, check-permissions) on their local machine
2. Application initializes boto3 AWS clients with profile/region configuration
3. boto3 clients make read-only API calls to AWS services (IAM, RDS, CloudWatch, Performance Insights)
4. Data is retrieved from AWS APIs and processed locally
5. Local collectors organize the retrieved data
6. Local analyzer evaluates metrics against configurable thresholds
7. Local report generator formats findings for technical or management audiences
8. Output delivered to console or file on local machine (text/JSON format)

**Key Point:** All data processing, analysis, and reporting happens locally on your machine. The tool only makes read-only API calls to AWS to retrieve information.

## AWS Services Integration

**Read-Only API Calls Only - No Resources Created**

- **AWS IAM**: Authentication and authorization for API access
- **Amazon RDS API**: Database instance information and configuration (read-only)
- **Amazon CloudWatch API**: Performance metrics and monitoring data (read-only)
- **AWS Performance Insights API**: SQL-level performance analysis (read-only)

The tool uses boto3 (AWS SDK for Python) to make API calls. No Lambda functions, S3 buckets, EC2 instances, or any other AWS resources are created or required.

## Key Features

- Multi-account support via AWS profiles
- Configurable alert thresholds
- Graceful degradation (works without Performance Insights)
- Comprehensive error handling with retry logic
- Dual reporting modes (technical/management)

## Visual Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RDS Diagnostics Tool Architecture                         │
│                                                                               │
│  LOCAL MACHINE (Client Side) - All Processing Happens Here                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Database   │
│Administrator │
│    (User)    │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLI Layer (Local)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Click CLI (main.py)                                                 │   │
│  │  Commands: list | diagnose | report | check-permissions             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Python Application (Local)                                │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │
│  │ RDSDiagnosticsApp    │  │  Configuration   │  │   Data Models    │     │
│  │   (Orchestrator)     │◄─┤   Management     │  │   (Pydantic)     │     │
│  └──────────┬───────────┘  └──────────────────┘  └──────────────────┘     │
└─────────────┼───────────────────────────────────────────────────────────────┘
              │
              ├──────────────────┬──────────────────┬──────────────────┐
              ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    boto3 SDK - AWS API Clients (Local)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  IAM Client  │  │  RDS Client  │  │  CloudWatch  │  │ Performance  │   │
│  │              │  │              │  │    Client    │  │   Insights   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
└─────────┼──────────────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │                  │
          │ READ-ONLY API CALLS (HTTPS)        │                  │
          ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AWS CLOUD - API SERVICES ONLY                             │
│                    (No Resources Created or Required)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   AWS IAM    │  │  Amazon RDS  │  │   Amazon     │  │     AWS      │   │
│  │     API      │  │     API      │  │  CloudWatch  │  │ Performance  │   │
│  │ (Auth Only)  │  │ (Read Info)  │  │     API      │  │ Insights API │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │                  │                  │
                    Data Retrieved via API       │                  │
                              ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Data Collectors (Local Processing)                        │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐ │
│  │  Instance Info       │  │  Metrics Collector   │  │  Performance     │ │
│  │    Collector         │  │  (CloudWatch)        │  │    Insights      │ │
│  │                      │  │                      │  │   Collector      │ │
│  └──────────┬───────────┘  └──────────┬───────────┘  └──────┬───────────┘ │
└─────────────┼──────────────────────────┼──────────────────────┼─────────────┘
              │                          │                      │
              └──────────────┬───────────┴──────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                Analysis & Reporting Layer (Local Processing)                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Diagnostic Analyzer                               │   │
│  │  • Threshold-based analysis                                          │   │
│  │  • Severity assessment (Critical, Warning, Info)                     │   │
│  │  • Recommendation generation                                         │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                             │
│                                ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Report Generator                                  │   │
│  │  • Technical reports (detailed metrics & analysis)                   │   │
│  │  • Management reports (executive summary)                            │   │
│  │  • Text & JSON formatters                                            │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  Output (Console │
                        │    or File)      │
                        │   LOCAL MACHINE  │
                        └──────────────────┘
```

## Component Interactions

1. **User → CLI**: DBA invokes commands (list, diagnose, report, check-permissions)
2. **CLI → App Core**: Parses arguments, loads configuration, initializes RDSDiagnosticsApp
3. **App → AWS Clients**: Authenticates via IAM, creates service clients
4. **Clients → AWS Services**: Makes API calls to RDS, CloudWatch, Performance Insights
5. **Collectors → Data**: Gathers instance info, metrics, and PI data
6. **Analyzer → Insights**: Evaluates metrics against thresholds, assigns severity
7. **Reporter → Output**: Formats findings as technical or management reports
8. **Output → User**: Displays results in console or saves to file

## Professional Diagram Generation ✓

A professional architecture diagram has been successfully generated using the Python `diagrams` library with Graphviz!

**Output File:** `architecture_diagram.png`

The diagram includes:
- Color-coded layers (User, CLI, Core, AWS Clients, AWS Services, Collectors, Analysis)
- Clear data flow with labeled edges
- Professional AWS service icons
- Proper clustering and organization
- High-quality PNG output

### Viewing the Diagram

The diagram has been generated and saved as `architecture_diagram.png` in the project root directory. You can open it with any image viewer.

### Regenerating the Diagram

If you need to regenerate the diagram (e.g., after making changes):

#### Option 1: Windows Batch Script (Recommended)
```bash
generate-diagram.bat
```
This will automatically open the diagram after generation.

#### Option 2: Direct Python Execution
```bash
python generate_architecture_diagram.py
```

### Configuration

The scripts are configured to use your local Graphviz installation at:
```
C:\Users\thiagarajan.b\OneDrive - IDP Education Ltd\Management\KiroImmersionDay\Graphviz-14.1.2-win64\bin
```

### Files Created

1. **architecture_diagram.png** ✓ - Generated architecture diagram
2. **generate_architecture_diagram.py** - Python script using diagrams library
3. **generate-diagram.bat** - Windows batch script to run the Python script
4. **architecture-diagram.dot** - Alternative Graphviz DOT source file
5. **README-DIAGRAM.md** - Detailed installation and usage guide

### Diagram Features

- **Local Machine Cluster**: Shows all components run locally (CLI, Python app, boto3 clients, data processing)
- **AWS Cloud Cluster**: Shows only API services (no resources created)
- **Python Icons**: Used for local Python components to clarify this is a local application
- **Read-Only API Calls**: Clearly labeled to show the tool only reads data from AWS
- **Color-Coded Edges**: Different colors for different data flows (blue=local flow, orange=AWS API calls, purple=data processing, red=reporting)
- **Clear Separation**: Visual distinction between local processing and AWS API services
