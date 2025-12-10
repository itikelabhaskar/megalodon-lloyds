"""
Treatment Agent Tools

Tools for analyzing DQ issues and suggesting remediation strategies.
"""

import os
import json
from typing import Dict, List, Any
from google.cloud import bigquery
from google.adk.tools import ToolContext
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from knowledge_bank.kb_manager import get_kb_manager


def execute_dq_rule(
    rule_sql: str,
    table_name: str,
    tool_context: ToolContext
) -> str:
    """
    Execute a DQ rule SQL query against BigQuery to find violations.
    
    Args:
        rule_sql: SQL query to execute (may contain {table} placeholder)
        table_name: Name of the table to query (e.g., 'policies_week1')
        tool_context: ADK tool context
    
    Returns:
        JSON string with issue count and sample violations
    """
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    # Replace placeholder with actual table reference
    full_table = f"`{project_id}.{dataset_id}.{table_name}`"
    sql = rule_sql.replace("{table}", full_table).replace("TABLE_NAME", full_table)
    
    client = bigquery.Client(project=project_id)
    
    try:
        results = client.query(sql).result()
        
        issues = []
        for row in results:
            issues.append(dict(row))
            if len(issues) >= 100:  # Limit to first 100
                break
        
        return json.dumps({
            "status": "success",
            "issue_count": len(issues),
            "sample_issues": issues[:10],  # Show first 10
            "note": f"Showing up to 10 sample violations out of {len(issues)} total"
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "sql": sql
        }, indent=2)


def query_related_data(
    customer_id: str,
    all_weeks: bool = True,
    tool_context: ToolContext = None
) -> str:
    """
    Query data for a specific customer across all weeks to find patterns or correct values.
    
    Args:
        customer_id: Customer ID to query
        all_weeks: If True, query all week tables; if False, query only week1
        tool_context: ADK tool context
    
    Returns:
        JSON string with customer data across weeks
    """
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    client = bigquery.Client(project=project_id)
    
    if all_weeks:
        # Query all weeks with UNION ALL
        sql = f"""
        SELECT 'week1' as week, * FROM `{project_id}.{dataset_id}.policies_week1` WHERE CUS_ID = '{customer_id}'
        UNION ALL
        SELECT 'week2' as week, * FROM `{project_id}.{dataset_id}.policies_week2` WHERE CUS_ID = '{customer_id}'
        UNION ALL
        SELECT 'week3' as week, * FROM `{project_id}.{dataset_id}.policies_week3` WHERE CUS_ID = '{customer_id}'
        UNION ALL
        SELECT 'week4' as week, * FROM `{project_id}.{dataset_id}.policies_week4` WHERE CUS_ID = '{customer_id}'
        ORDER BY week
        """
    else:
        sql = f"""
        SELECT * FROM `{project_id}.{dataset_id}.policies_week1` 
        WHERE CUS_ID = '{customer_id}'
        """
    
    try:
        results = client.query(sql).result()
        
        data = []
        for row in results:
            data.append(dict(row))
        
        return json.dumps({
            "status": "success",
            "customer_id": customer_id,
            "records_found": len(data),
            "data": data
        }, indent=2, default=str)  # default=str handles datetime serialization
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


def search_knowledge_bank(
    issue_description: str,
    issue_pattern: str = "",
    tool_context: ToolContext = None
) -> str:
    """
    Search Knowledge Bank for similar historical issues and their successful fixes.
    
    Args:
        issue_description: Natural language description of the issue
        issue_pattern: Optional SQL pattern or regex describing the issue
        tool_context: ADK tool context
    
    Returns:
        JSON string with matching pattern and historical fix suggestions
    """
    kb_manager = get_kb_manager()
    
    match = kb_manager.search_similar_issue(issue_pattern, issue_description)
    
    if match:
        return json.dumps({
            "status": "match_found",
            "similarity": match['similarity'],
            "pattern_id": match['pattern_id'],
            "pattern_description": match['description'],
            "historical_fixes": match['historical_fixes'],
            "recommendation": "Consider using one of the historical fixes with high success rate"
        }, indent=2)
    else:
        return json.dumps({
            "status": "no_match",
            "message": "No similar historical issue found in Knowledge Bank",
            "recommendation": "Generate new fix suggestions based on data analysis"
        }, indent=2)


def save_to_knowledge_bank(
    pattern_id: str,
    fix_data: Dict,
    tool_context: ToolContext = None
) -> str:
    """
    Save a new fix pattern to the Knowledge Bank for future reference.
    
    Args:
        pattern_id: Unique identifier for the pattern (e.g., "DOB_FUTURE")
        fix_data: Dictionary containing fix details (fix_id, fix_type, action, etc.)
        tool_context: ADK tool context
    
    Returns:
        Confirmation message
    """
    kb_manager = get_kb_manager()
    
    try:
        kb_manager.add_new_fix(pattern_id, fix_data)
        return json.dumps({
            "status": "success",
            "message": f"Fix pattern '{pattern_id}' saved to Knowledge Bank",
            "fix_id": fix_data.get('fix_id')
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


def calculate_fix_impact(
    fix_sql: str,
    table_name: str,
    dry_run: bool = True,
    tool_context: ToolContext = None
) -> str:
    """
    Estimate impact of a proposed fix by running it in dry-run mode.
    
    Args:
        fix_sql: SQL UPDATE/DELETE statement to analyze
        table_name: Name of the table to apply fix to
        dry_run: If True, only estimate impact; if False, show what would be affected
        tool_context: ADK tool context
    
    Returns:
        JSON string with impact estimate (rows affected, columns changed, etc.)
    """
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    # Replace placeholder with actual table reference
    full_table = f"`{project_id}.{dataset_id}.{table_name}`"
    sql = fix_sql.replace("{table}", full_table).replace("TABLE_NAME", full_table)
    
    # Convert UPDATE to SELECT to see what would be affected
    if "UPDATE" in sql.upper():
        # Extract WHERE clause
        where_clause = ""
        if "WHERE" in sql.upper():
            where_idx = sql.upper().index("WHERE")
            where_clause = sql[where_idx:]
        
        # Create SELECT query to count affected rows
        count_sql = f"""
        SELECT COUNT(*) as affected_rows
        FROM {full_table}
        {where_clause}
        """
    elif "DELETE" in sql.upper():
        # Extract WHERE clause
        where_clause = ""
        if "WHERE" in sql.upper():
            where_idx = sql.upper().index("WHERE")
            where_clause = sql[where_idx:]
        
        count_sql = f"""
        SELECT COUNT(*) as affected_rows
        FROM {full_table}
        {where_clause}
        """
    else:
        return json.dumps({
            "status": "error",
            "error": "Only UPDATE and DELETE statements supported for impact analysis"
        }, indent=2)
    
    client = bigquery.Client(project=project_id)
    
    try:
        results = client.query(count_sql).result()
        
        for row in results:
            affected_rows = row['affected_rows']
        
        # Get total rows in table
        total_sql = f"SELECT COUNT(*) as total_rows FROM {full_table}"
        total_results = client.query(total_sql).result()
        for row in total_results:
            total_rows = row['total_rows']
        
        impact_percentage = (affected_rows / total_rows * 100) if total_rows > 0 else 0
        
        # Determine risk level
        if impact_percentage > 50:
            risk_level = "HIGH - affects majority of table"
        elif impact_percentage > 20:
            risk_level = "MEDIUM - affects significant portion"
        elif impact_percentage > 5:
            risk_level = "LOW-MEDIUM - affects moderate amount"
        else:
            risk_level = "LOW - affects small subset"
        
        return json.dumps({
            "status": "success",
            "affected_rows": affected_rows,
            "total_rows": total_rows,
            "impact_percentage": round(impact_percentage, 2),
            "risk_level": risk_level,
            "recommendation": "Review before execution" if impact_percentage > 20 else "Safe to proceed"
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


def get_column_statistics(
    table_name: str,
    column_name: str,
    tool_context: ToolContext = None
) -> str:
    """
    Get statistical summary of a column for imputation strategies.
    
    Args:
        table_name: Name of the table
        column_name: Name of the column to analyze
        tool_context: ADK tool context
    
    Returns:
        JSON string with statistics (mean, median, mode, null count, etc.)
    """
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    full_table = f"`{project_id}.{dataset_id}.{table_name}`"
    
    # Get column type first
    client = bigquery.Client(project=project_id)
    table_ref = client.get_table(f"{project_id}.{dataset_id}.{table_name}")
    
    column_type = None
    for field in table_ref.schema:
        if field.name == column_name:
            column_type = field.field_type
            break
    
    if not column_type:
        return json.dumps({
            "status": "error",
            "error": f"Column '{column_name}' not found in table '{table_name}'"
        }, indent=2)
    
    # Build appropriate statistics query based on type
    if column_type in ["INTEGER", "FLOAT", "NUMERIC", "BIGNUMERIC"]:
        # Numerical statistics
        sql = f"""
        SELECT
            COUNT(*) as total_count,
            COUNT({column_name}) as non_null_count,
            COUNTIF({column_name} IS NULL) as null_count,
            AVG({column_name}) as mean,
            MIN({column_name}) as min_value,
            MAX({column_name}) as max_value,
            STDDEV({column_name}) as std_dev,
            APPROX_QUANTILES({column_name}, 100)[OFFSET(50)] as median
        FROM {full_table}
        """
    else:
        # Categorical statistics
        sql = f"""
        SELECT
            COUNT(*) as total_count,
            COUNT({column_name}) as non_null_count,
            COUNTIF({column_name} IS NULL) as null_count,
            COUNT(DISTINCT {column_name}) as distinct_count,
            APPROX_TOP_COUNT({column_name}, 5) as top_values
        FROM {full_table}
        """
    
    try:
        results = client.query(sql).result()
        
        stats = {}
        for row in results:
            stats = dict(row)
        
        return json.dumps({
            "status": "success",
            "column_name": column_name,
            "column_type": column_type,
            "statistics": stats
        }, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


def get_affected_row_sample(
    rule_sql: str,
    table_name: str,
    limit: int = 10,
    tool_context: ToolContext = None
) -> str:
    """
    Get sample rows that violate a DQ rule for inspection.
    
    This helps users see actual problematic data before approving fixes.
    Returns sample rows with all columns for context.
    
    Args:
        rule_sql: SQL query that identifies violations
        table_name: Name of the table
        limit: Number of sample rows to return (default 10)
        tool_context: ADK tool context
    
    Returns:
        JSON string with sample rows and BigQuery console link
    """
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    compute_project = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    # Replace placeholder with actual table reference
    full_table = f"`{project_id}.{dataset_id}.{table_name}`"
    sql = rule_sql.replace("{table}", full_table).replace("TABLE_NAME", full_table)
    
    # Add LIMIT if not already present
    if "LIMIT" not in sql.upper():
        sql = f"{sql} LIMIT {limit}"
    
    client = bigquery.Client(project=project_id)
    
    try:
        results = client.query(sql).result()
        
        sample_rows = []
        for row in results:
            sample_rows.append(dict(row))
        
        # Generate BigQuery console link
        bq_console_url = f"https://console.cloud.google.com/bigquery?project={compute_project}&ws=!1m5!1m4!4m3!1s{project_id}!2s{dataset_id}!3s{table_name}"
        
        return json.dumps({
            "status": "success",
            "sample_count": len(sample_rows),
            "sample_rows": sample_rows,
            "bigquery_console_url": bq_console_url,
            "note": "Click the URL to view full table in BigQuery console"
        }, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

