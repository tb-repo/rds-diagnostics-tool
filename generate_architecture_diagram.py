#!/usr/bin/env python3
"""Generate RDS Diagnostics Tool architecture diagram using Python diagrams library."""

import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.database import RDS
from diagrams.aws.management import Cloudwatch
from diagrams.aws.security import IAM
from diagrams.onprem.client import User
from diagrams.onprem.compute import Server
from diagrams.programming.language import Python

# Set Graphviz path
GRAPHVIZ_PATH = r"C:\Users\thiagarajan.b\OneDrive - IDP Education Ltd\Management\KiroImmersionDay\Graphviz-14.1.2-win64\bin"
os.environ["PATH"] = GRAPHVIZ_PATH + os.pathsep + os.environ.get("PATH", "")


def generate_architecture_diagram():
    """Generate the RDS Diagnostics Tool architecture diagram."""
    
    graph_attr = {
        "fontsize": "14",
        "bgcolor": "white",
        "pad": "0.5",
    }
    
    node_attr = {
        "fontsize": "11",
    }
    
    edge_attr = {
        "fontsize": "10",
    }
    
    with Diagram(
        "RDS Diagnostics Tool Architecture",
        show=False,
        direction="TB",
        filename="architecture_diagram",
        outformat="png",
        graph_attr=graph_attr,
        node_attr=node_attr,
        edge_attr=edge_attr,
    ):
        # User Layer
        user = User("Database\nAdministrator")
        
        # Local Machine / Client Side
        with Cluster("Local Machine (Client Side)"):
            # CLI Layer
            with Cluster("CLI Layer"):
                cli = Server("Click CLI\n(main.py)")
                batch = Server("Batch Scripts\n(Windows)")
            
            # Application Core - Python Application
            with Cluster("Python Application"):
                app = Python("RDS Diagnostics\nApp\n(Orchestrator)")
                config = Server("Configuration\nManagement\n(YAML)")
                models = Python("Data Models\n(Pydantic)")
            
            # AWS Client Layer - boto3
            with Cluster("boto3 SDK (AWS API Clients)"):
                rds_client = Python("RDS Client")
                cw_client = Python("CloudWatch\nClient")
                pi_client = Python("Performance\nInsights Client")
            
            # Data Processing
            with Cluster("Local Data Processing"):
                inst_collector = Python("Instance Info\nCollector")
                metrics_collector = Python("Metrics\nCollector")
                pi_collector = Python("PI Collector")
                analyzer = Python("Diagnostic\nAnalyzer")
                reporter = Python("Report\nGenerator")
        
        # AWS Cloud - API Services Only
        with Cluster("AWS Cloud (API Services Only - No Resources Created)"):
            iam = IAM("IAM\nAuthentication")
            rds = RDS("Amazon RDS\nAPI")
            cloudwatch = Cloudwatch("CloudWatch\nAPI")
            pi = RDS("Performance\nInsights API")
        
        # Data Flow - User to CLI
        user >> Edge(label="invoke command", color="blue") >> cli
        user >> Edge(style="dashed", color="gray") >> batch
        batch >> Edge(style="dashed", color="gray") >> cli
        
        # CLI to Core
        cli >> Edge(label="initialize", color="blue") >> app
        app >> Edge(label="load") >> config
        app >> Edge(label="use") >> models
        
        # Core to AWS Clients
        app >> Edge(label="create clients", color="blue") >> rds_client
        app >> Edge(label="create clients", color="blue") >> cw_client
        app >> Edge(label="create clients", color="blue") >> pi_client
        
        # AWS Clients to Services (API Calls Only)
        rds_client >> Edge(label="API calls\n(read-only)", color="orange") >> iam
        rds_client >> Edge(label="API calls\n(read-only)", color="orange") >> rds
        cw_client >> Edge(label="API calls\n(read-only)", color="orange") >> cloudwatch
        pi_client >> Edge(label="API calls\n(read-only)", color="orange") >> pi
        
        # App to Collectors (Local Processing)
        app >> Edge(label="collect", color="blue") >> inst_collector
        app >> Edge(label="collect", color="blue") >> metrics_collector
        app >> Edge(label="collect", color="blue") >> pi_collector
        
        # Collectors use AWS Clients
        inst_collector >> Edge(style="dashed") >> rds_client
        metrics_collector >> Edge(style="dashed") >> cw_client
        pi_collector >> Edge(style="dashed") >> pi_client
        
        # Collectors to Analyzer (Local Processing)
        inst_collector >> Edge(label="data", color="purple") >> analyzer
        metrics_collector >> Edge(label="data", color="purple") >> analyzer
        pi_collector >> Edge(label="data", color="purple") >> analyzer
        
        # Analyzer to Reporter (Local Processing)
        analyzer >> Edge(label="analysis", color="red") >> reporter
        
        # Reporter back to CLI and User
        reporter >> Edge(label="report", color="red") >> cli
        cli >> Edge(label="display/save", color="blue") >> user
    
    print("✓ Architecture diagram generated successfully!")
    print("  Output: architecture_diagram.png")
    print("\nNote: This tool runs locally and only makes read-only API calls to AWS.")
    print("      No AWS resources (Lambda, S3, EC2) are created or required.")


if __name__ == "__main__":
    try:
        generate_architecture_diagram()
    except ImportError as e:
        print(f"Error: Missing required library - {e}")
        print("\nPlease install the diagrams library:")
        print("  pip install diagrams")
    except Exception as e:
        print(f"Error generating diagram: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        generate_architecture_diagram()
    except ImportError as e:
        print(f"Error: Missing required library - {e}")
        print("\nPlease install the diagrams library:")
        print("  pip install diagrams")
    except Exception as e:
        print(f"Error generating diagram: {e}")
        import traceback
        traceback.print_exc()
