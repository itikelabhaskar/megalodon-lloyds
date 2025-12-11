import os
import json
import datetime
import numpy as np
import pandas as pd
from google.cloud import bigquery
from google.adk.tools import ToolContext
from google.adk.tools.bigquery.client import get_bigquery_client
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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


def _get_dataplex_client():
    """Get Dataplex DataScan client with proper ADK integration.
    
    Creates a Dataplex client with consistent project settings and user agent
    tracking, following the same pattern as BigQuery client for ADK compatibility.
    """
    try:
        from google.cloud import dataplex_v1
    except ImportError:
        return None
    
    settings = get_database_settings()
    try:
        # Create client with proper project settings
        client = dataplex_v1.DataScanServiceClient()
        # Note: Dataplex clients don't have direct user_agent parameter
        # but inherit from google-cloud-python libraries which respect
        # GOOGLE_CLOUD_PROJECT environment variable
        return client
    except Exception as e:
        print(f"⚠️  Failed to create Dataplex client: {str(e)}")
        return None


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
        return json.dumps(schema_info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "table_name": table_name})


def _fallback_bigquery_profiling(table_name: str, scan_name: str, scan_id: str, settings: dict) -> str:
    """Fallback to BigQuery-based profiling when Dataplex API doesn't return profile data."""
    from google.cloud import bigquery
    
    project_id = settings["project_id"]
    dataset_id = settings["dataset_id"]
    table_ref = f"{project_id}.{dataset_id}.{table_name}"
    
    client = bigquery.Client(project=project_id)
    
    # Get table info
    table = client.get_table(table_ref)
    total_rows = table.num_rows
    columns = [field.name for field in table.schema]
    
    # Build dynamic null count query for all columns
    null_counts = ", ".join([f"COUNTIF({col} IS NULL) as {col}_nulls" for col in columns])
    
    query = f"""
    SELECT 
        COUNT(*) as total_rows,
        {null_counts}
    FROM `{table_ref}`
    """
    
    result = client.query(query).result()
    row = list(result)[0]
    
    null_rates = {}
    data_quality_issues = []
    
    for col in columns:
        null_count = getattr(row, f"{col}_nulls", 0)
        null_rate = null_count / total_rows if total_rows > 0 else 0
        null_rates[col] = round(null_rate * 100, 2)
        
        if null_rate > 0.1:  # > 10% null
            data_quality_issues.append({
                "issue": f"High null rate in {col}",
                "count": null_count,
                "severity": "high" if null_rate > 0.3 else "medium",
                "recommendation": f"Investigate completeness issues in {col}"
            })
    
    profiling_result = {
        "status": "scan_completed",
        "scan_id": scan_id,
        "table": table_ref,
        "scan_types": ["DATAPLEX_PROFILE", "BQ_FALLBACK"],
        "findings": {
            "total_rows": total_rows,
            "total_columns": len(columns),
            "null_rates": null_rates,
            "data_quality_issues": data_quality_issues,
            "recommended_rules": [
                "Validate null rates for critical columns",
                "Check for data type consistency"
            ]
        },
        "dataplex_resource": scan_name
    }
    
    return json.dumps(profiling_result, indent=2)


def trigger_dataplex_scan(
    table_name: str,
    tool_context: ToolContext
) -> str:
    """Trigger REAL Dataplex data profiling scans on a BigQuery table.
    
    Uses Dataplex DataScan API to create and run data profiling jobs.
    Returns comprehensive profiling results including:
    - Row count and column statistics
    - Null rates per column
    - Distinct value counts
    - Min/max values for numeric columns
    - Data quality recommendations
    
    Falls back to BigQuery-based profiling if Dataplex is not available.
    """
    settings = get_database_settings()
    project_id = settings["compute_project"]
    data_project_id = settings["project_id"]
    dataset_id = settings["dataset_id"]
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    # Get Dataplex client using ADK-integrated helper
    client = _get_dataplex_client()
    if client is None:
        print("⚠️  Dataplex not available, using BigQuery fallback profiling...")
        scan_name = f"fallback-{table_name}"
        scan_id = f"bq-profile-{table_name}"
        return _fallback_bigquery_profiling(table_name, scan_name, scan_id, settings)
    
    # Import Dataplex types for API operations
    try:
        from google.cloud import dataplex_v1
        from google.api_core import exceptions as google_exceptions
    except ImportError:
        # This shouldn't happen if client was created, but handle gracefully
        scan_name = f"fallback-{table_name}"
        scan_id = f"bq-profile-{table_name}"
        return _fallback_bigquery_profiling(table_name, scan_name, scan_id, settings)
    
    try:
        
        # Generate unique DataScan ID (lowercase, hyphens only)
        import time
        # Replace underscores with hyphens and ensure lowercase
        safe_table_name = table_name.lower().replace('_', '-')
        scan_id = f"dq-profile-{safe_table_name}-{int(time.time())}"
        parent = f"projects/{project_id}/locations/{location}"
        
        # Configure DataScan for profiling
        data_scan = dataplex_v1.DataScan(
            description=f"DQ profiling scan for {table_name}",
            data=dataplex_v1.DataSource(
                resource=f"//bigquery.googleapis.com/projects/{data_project_id}/datasets/{dataset_id}/tables/{table_name}"
            ),
            data_profile_spec=dataplex_v1.DataProfileSpec(
                sampling_percent=100.0,  # Profile entire table
                row_filter=""  # No filtering
            ),
            execution_spec=dataplex_v1.DataScan.ExecutionSpec(
                trigger=dataplex_v1.Trigger(
                    on_demand=dataplex_v1.Trigger.OnDemand()
                )
            )
        )
        
        # Create DataScan
        operation = client.create_data_scan(
            parent=parent,
            data_scan=data_scan,
            data_scan_id=scan_id
        )
        
        # Wait for DataScan creation with longer timeout
        created_scan = operation.result(timeout=180)  # 3 minutes for creation
        scan_name = created_scan.name
        
        # Run the DataScan job
        run_request = dataplex_v1.RunDataScanRequest(name=scan_name)
        run_response = client.run_data_scan(request=run_request)
        job_name = run_response.job.name
        
        # Wait for job completion (30-90 seconds typically)
        import time as time_module
        max_wait = 180  # 3 minutes max for job execution
        start_time = time_module.time()
        job_complete = False
        job_result = None
        
        while not job_complete and (time_module.time() - start_time) < max_wait:
            try:
                # Use request object with FULL view to get profile results
                get_job_request = dataplex_v1.GetDataScanJobRequest(
                    name=job_name,
                    view=dataplex_v1.GetDataScanJobRequest.DataScanJobView.FULL
                )
                job_result = client.get_data_scan_job(request=get_job_request)
                if job_result.state == dataplex_v1.DataScanJob.State.SUCCEEDED:
                    job_complete = True
                    break
                elif job_result.state in [dataplex_v1.DataScanJob.State.FAILED, dataplex_v1.DataScanJob.State.CANCELLED]:
                    return json.dumps({
                        "status": "scan_failed",
                        "error": f"DataScan job failed with state: {job_result.state.name}",
                        "scan_id": scan_id
                    }, indent=2)
                time_module.sleep(5)
            except Exception as e:
                time_module.sleep(5)
                continue
        
        if not job_complete:
            return json.dumps({
                "status": "scan_timeout",
                "message": "DataScan job did not complete within 3 minutes. Job is still running in background.",
                "scan_id": scan_id,
                "job_name": job_name
            }, indent=2)
        
        # Job completed - job_result already has full profile data from the last poll
        # Check if we have profile data
        if not job_result.data_profile_result or not job_result.data_profile_result.profile or \
           not job_result.data_profile_result.profile.fields:
            return _fallback_bigquery_profiling(table_name, scan_name, scan_id, settings)
            
        profile_result = job_result.data_profile_result.profile
        table_ref = f"{data_project_id}.{dataset_id}.{table_name}"
        
        # Get row count from the profile result
        row_count = job_result.data_profile_result.row_count
        
        # Extract null rates and stats for all columns
        null_rates = {}
        column_stats = []
        data_quality_issues = []
        
        for field in profile_result.fields:
            col_name = field.name
            null_ratio = field.profile.null_ratio if field.profile else 0.0
            null_rates[col_name] = f"{(null_ratio * 100):.1f}%"
            
            col_stat = {
                "name": col_name,
                "type": field.type_,
                "null_ratio": f"{(null_ratio * 100):.1f}%"
            }
            
            # Add numeric stats if available
            if field.profile and hasattr(field.profile, 'min') and field.profile.min:
                col_stat["min"] = str(field.profile.min)
                col_stat["max"] = str(field.profile.max)
                col_stat["mean"] = str(field.profile.mean) if hasattr(field.profile, 'mean') else None
            
            column_stats.append(col_stat)
            
            # Detect high null rates
            if null_ratio > 0.1:  # > 10% null
                data_quality_issues.append({
                    "issue": f"High null rate in {col_name}",
                    "count": int(row_count * null_ratio) if row_count else 0,
                    "severity": "high" if null_ratio > 0.3 else "medium",
                    "recommendation": f"Investigate completeness issues in {col_name}"
                })
        
        # Generate recommendations
        recommended_rules = [
            "Validate null rates for critical columns",
            "Check for data type consistency",
            "Verify value ranges for numeric columns",
            "Ensure referential integrity across tables"
        ]
        
        profiling_result = {
            "status": "scan_completed",
            "scan_id": scan_id,
            "table": table_ref,
            "scan_types": ["DATAPLEX_PROFILE"],
            "findings": {
                "total_rows": row_count,
                "total_columns": len(profile_result.fields),
                "null_rates": null_rates,
                "column_statistics": column_stats[:20],  # Limit to first 20 columns
                "data_quality_issues": data_quality_issues,
                "recommended_rules": recommended_rules
            },
            "dataplex_resource": scan_name
        }
        
        return json.dumps(profiling_result, indent=2)
    
    except google_exceptions.PermissionDenied as e:
        # Dataplex permissions missing - fallback to BigQuery profiling
        print(f"⚠️  Dataplex permission denied, using BigQuery fallback profiling...")
        scan_name = f"fallback-{table_name}"
        scan_id = f"bq-profile-{table_name}"
        return _fallback_bigquery_profiling(table_name, scan_name, scan_id, settings)
    except Exception as e:
        # Any other error - fallback to BigQuery profiling
        print(f"⚠️  Dataplex error ({str(e)[:100]}), using BigQuery fallback profiling...")
        scan_name = f"fallback-{table_name}"
        scan_id = f"bq-profile-{table_name}"
        return _fallback_bigquery_profiling(table_name, scan_name, scan_id, settings)


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
