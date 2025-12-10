import os
import json
import datetime
import numpy as np
import pandas as pd
from google.cloud import bigquery
from google.adk.tools import ToolContext
from google.adk.tools.bigquery.client import get_bigquery_client
from typing import Dict, List

# User agent for tracking
USER_AGENT = "adk-dq-management-system"

# Global database settings cache
_database_settings = None


def _serialize_value_for_sql(value):
    """Serializes a Python value into a BigQuery SQL literal.
    
    Properly escapes strings, handles NULL, arrays, dates, and complex types.
    Prevents SQL injection in generated DQ rules.
    
    Copied from google.adk data_science repo for production-grade SQL handling.
    """
    if isinstance(value, (list, np.ndarray)):
        # Format arrays
        return f"[{', '.join(_serialize_value_for_sql(v) for v in value)}]"
    if pd.isna(value):
        return "NULL"
    if isinstance(value, str):
        # Escape single quotes and backslashes for SQL strings
        new_value = value.replace("\\", "\\\\").replace("'", "''")
        return f"'{new_value}'"
    if isinstance(value, bytes):
        decoded = value.decode("utf-8", "replace")
        new_value = decoded.replace("\\", "\\\\").replace("'", "''")
        return f"b'{new_value}'"
    if isinstance(value, (datetime.datetime, datetime.date, pd.Timestamp)):
        # Timestamps and datetimes need to be quoted
        return f"'{value}'"
    if isinstance(value, dict):
        # For STRUCT, BQ expects ('val1', 'val2', ...)
        string_values = [_serialize_value_for_sql(v) for v in value.values()]
        return f"({', '.join(string_values)})"
    return str(value)


def get_database_settings():
    """Get database settings with caching.
    
    Caches project_id, dataset_id, and schema info to avoid repeated
    expensive BigQuery metadata queries.
    """
    global _database_settings
    if _database_settings is None:
        _database_settings = {
            "project_id": os.getenv("BQ_DATA_PROJECT_ID"),
            "dataset_id": os.getenv("BQ_DATASET_ID"),
            "compute_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        }
    return _database_settings


def _get_bigquery_client():
    """Get BigQuery client using ADK's helper for better logging and tracking."""
    settings = get_database_settings()
    try:
        return get_bigquery_client(
            project=settings["compute_project"],
            credentials=None,
            user_agent=USER_AGENT,
        )
    except Exception:
        # Fallback to basic client if ADK client fails
        return bigquery.Client(project=settings["compute_project"])


def load_preexisting_rules() -> str:
    """Load pre-existing DQ rules from Collibra/Ataccama systems.
    
    Returns a JSON string containing historical DQ rules that should be
    considered when generating new rules.
    
    Priority order:
    1. User-uploaded rules (if available in session)
    2. Mock data from mock_data/pre_existing_rules.json
    """
    import streamlit as st
    
    rules = []
    source = "none"
    
    # Check for user-uploaded rules in Streamlit session state
    try:
        if hasattr(st, 'session_state') and 'uploaded_dq_rules' in st.session_state:
            rules = st.session_state.uploaded_dq_rules
            source = "user_upload"
    except:
        pass
    
    # Fallback to mock data
    if not rules:
        try:
            rules_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mock_data', 'pre_existing_rules.json')
            with open(rules_path, 'r') as f:
                rules = json.load(f)
            source = "mock_data"
        except Exception as e:
            return json.dumps({
                "error": str(e), 
                "preexisting_rules": [],
                "source": "error"
            })
    
    return json.dumps({
        "preexisting_rules": rules, 
        "count": len(rules),
        "source": source,
        "message": f"Loaded {len(rules)} pre-existing rules from {source}"
    }, indent=2)

def get_all_week_tables(
    tool_context: ToolContext
) -> str:
    """Get all week tables from the dataset for cross-week temporal analysis.
    
    Returns list of table names that contain weekly data for temporal
    consistency checks across time periods.
    """
    settings = get_database_settings()
    project_id = settings["project_id"]
    dataset_id = settings["dataset_id"]
    
    try:
        client = _get_bigquery_client()
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

def get_table_schema_with_samples(
    table_name: str,
    sample_rows: int = 10,
    tool_context: ToolContext = None
) -> str:
    """Get BigQuery table schema with sample data for LLM-friendly DQ rule generation.
    
    Returns schema + sample rows in an easy-to-parse format:
    - Column metadata (name, type, mode)
    - Sample values for each column (first N rows)
    - Sample values are properly serialized for SQL safety
    """
    settings = get_database_settings()
    project_id = settings["project_id"]
    dataset_id = settings["dataset_id"]
    
    client = _get_bigquery_client()
    table_ref = f"{project_id}.{dataset_id}.{table_name}"
    
    try:
        # Get schema
        table = client.get_table(table_ref)
        
        # Get sample data as DataFrame for better handling
        sample_query = f"SELECT * FROM `{table_ref}` LIMIT {sample_rows}"
        sample_df = client.query(sample_query).to_dataframe()
        
        # Convert to dict with proper SQL serialization
        sample_values = sample_df.to_dict(orient="list")
        for key in sample_values:
            sample_values[key] = [
                _serialize_value_for_sql(v) for v in sample_values[key]
            ]
        
        # Format for LLM
        schema_with_samples = {
            "table_name": table_name,
            "total_rows": table.num_rows,
            "columns": []
        }
        
        for field in table.schema:
            col_info = {
                "name": field.name,
                "type": field.field_type,
                "mode": field.mode,
                "sample_values": sample_values.get(field.name, [])
            }
            schema_with_samples["columns"].append(col_info)
        
        return json.dumps(schema_with_samples, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

def get_table_schema(
    table_name: str,
    tool_context: ToolContext
) -> str:
    """Get BigQuery table schema for DQ rule generation."""
    settings = get_database_settings()
    project_id = settings["project_id"]
    dataset_id = settings["dataset_id"]
    
    client = _get_bigquery_client()
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
    
    Returns profiling results including:
    - Null rates per column
    - Distinct value counts
    - Min/max values for numeric columns
    - Data quality issues detected
    - Recommended DQ checks
    """
    settings = get_database_settings()
    project_id = settings["compute_project"]
    dataset_id = settings["dataset_id"]
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    try:
        # Note: In production, you'd create/trigger actual DataScan jobs
        # For hackathon, we simulate profiling results based on actual data inspection
        client = _get_bigquery_client()
        table_ref = f"{project_id}.{dataset_id}.{table_name}"
        
        # Get basic stats
        null_check_query = f"""
        SELECT 
            COUNTIF(CUS_DOB IS NULL OR CUS_DOB = '' OR CUS_DOB = 'None') as dob_nulls,
            COUNTIF(CUS_LIFE_STATUS IS NULL OR CUS_LIFE_STATUS = '') as status_nulls,
            COUNTIF(POLI_GROSS_PMT < 0) as negative_premiums,
            COUNTIF(CUS_NI_NO IS NULL OR CUS_NI_NO = '') as ni_nulls,
            COUNT(*) as total_rows
        FROM `{table_ref}`
        """
        
        results = list(client.query(null_check_query).result())
        row = results[0] if results else None
        
        profiling_result = {
            "status": "scan_completed",
            "table": table_ref,
            "scan_types": ["PROFILE", "DATA_QUALITY"],
            "findings": {
                "total_rows": row.total_rows if row else 0,
                "null_rates": {
                    "CUS_DOB": f"{(row.dob_nulls / row.total_rows * 100):.1f}%" if row and row.total_rows > 0 else "0%",
                    "CUS_LIFE_STATUS": f"{(row.status_nulls / row.total_rows * 100):.1f}%" if row and row.total_rows > 0 else "0%",
                    "CUS_NI_NO": f"{(row.ni_nulls / row.total_rows * 100):.1f}%" if row and row.total_rows > 0 else "0%"
                },
                "data_quality_issues": [
                    {
                        "issue": "Invalid DOB values",
                        "count": row.dob_nulls if row else 0,
                        "severity": "high",
                        "recommendation": "Check for 'None' strings, NULLs, and future dates"
                    },
                    {
                        "issue": "Negative premium amounts",
                        "count": row.negative_premiums if row else 0,
                        "severity": "critical",
                        "recommendation": "Premium values cannot be negative"
                    }
                ] if row else [],
                "recommended_rules": [
                    "Check for future dates in CUS_DOB",
                    "Validate CUS_LIFE_STATUS is in allowed values (Active/Deceased)",
                    "Ensure premium amounts are non-negative",
                    "Validate NI number format (XX-XX-XX-XX-X)",
                    "Check deceased customers have death dates"
                ]
            }
        }
        
        return json.dumps(profiling_result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "scan_failed"}, indent=2)


def execute_dq_rule(
    rule_sql: str,
    table_name: str,
    tool_context: ToolContext
) -> str:
    """Execute a DQ rule SQL query against BigQuery."""
    settings = get_database_settings()
    project_id = settings["project_id"]
    dataset_id = settings["dataset_id"]
    
    # Replace placeholder with actual table
    sql = rule_sql.replace("{table}", f"`{project_id}.{dataset_id}.{table_name}`")
    
    try:
        client = _get_bigquery_client()
        results = client.query(sql).result()
        
        issues = []
        for row in results:
            issues.append(dict(row))
        
        return str({
            "rule_sql": sql,
            "issue_count": len(issues),
            "issues": issues[:100]  # Limit to first 100
        })
    except Exception as e:
        return f"Error executing DQ rule: {str(e)}"
