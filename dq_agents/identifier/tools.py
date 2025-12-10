import os
import json
from google.cloud import bigquery
from google.adk.tools import ToolContext
from typing import Dict, List

def load_preexisting_rules() -> str:
    """Load pre-existing DQ rules from Collibra/Ataccama systems.
    
    Returns a JSON string containing historical DQ rules that should be
    considered when generating new rules.
    """
    try:
        rules_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mock_data', 'pre_existing_rules.json')
        with open(rules_path, 'r') as f:
            rules = json.load(f)
        return json.dumps({"preexisting_rules": rules, "count": len(rules)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "preexisting_rules": []})

def get_all_week_tables(
    tool_context: ToolContext
) -> str:
    """Get all week tables from the dataset for cross-week temporal analysis.
    
    Returns list of table names that contain weekly data for temporal
    consistency checks across time periods.
    """
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    try:
        client = bigquery.Client(project=project_id)
        dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
        
        tables = [table.table_id for table in client.list_tables(dataset_ref)]
        week_tables = sorted([t for t in tables if 'week' in t.lower()])
        
        return json.dumps({
            "week_tables": week_tables,
            "count": len(week_tables),
            "message": "Use these tables to generate cross-week temporal consistency rules"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "week_tables": []})

def get_table_schema(
    table_name: str,
    tool_context: ToolContext
) -> str:
    """Get BigQuery table schema for DQ rule generation."""
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_name}"
    
    try:
        table = client.get_table(table_ref)
        schema_info = {
            "table_name": table_name,
            "num_rows": table.num_rows,
            "columns": [
                {
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode
                }
                for field in table.schema
            ]
        }
        return str(schema_info)
    except Exception as e:
        return f"Error getting schema: {str(e)}"


def trigger_dataplex_scan(
    table_name: str,
    tool_context: ToolContext
) -> str:
    """Trigger Dataplex data quality and profiling scans on a BigQuery table.
    
    Re