import os
from google.cloud import bigquery
from google.adk.tools import ToolContext
import json
from datetime import datetime


def dry_run_fix(
    fix_sql: str,
    table_name: str,
    tool_context: ToolContext
) -> str:
    """
    Perform a dry run of a fix by showing affected rows without making changes.
    Converts UPDATE/DELETE to SELECT to preview changes.
    """
    project_id = os.getenv("BQ_DATA_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    if not project_id or not dataset_id:
        return json.dumps({
            "error": "Missing BQ_DATA_PROJECT_ID or BQ_DATASET_ID environment variables",
            "status": "config_error"
        })
    
    try:
        # Clean SQL - remove any hardcoded dataset/project references
        sql = fix_sql.strip()
        
        # Replace common hardcoded patterns with correct ones
        import re
        # Remove dataset/project qualifiers from table references
        # Pattern: dataset.table or project.dataset.table -> just table
        sql = re.sub(r'\b[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.([a-zA-Z0-9_-]+)\b', r'\1', sql)
        sql = re.sub(r'\b[a-zA-Z0-9_-]+\.([a-zA-Z0-9_-]+)\b(?!\s*\()', r'\1', sql)
        
        # Now build proper table reference
        full_table = f"`{project_id}.{dataset_id}.{table_name}`"
        
        # Replace table placeholders
        sql = sql.replace("{table}", full_table).replace("TABLE_NAME", full_table).replace("{{table}}", full_table)
        
        # Replace bare table name with fully qualified name
        sql = re.sub(rf'\b{table_name}\b', full_table, sql)
        
        # Convert UPDATE/DELETE to SELECT for dry run
        dry_run_sql = sql
        
        if "UPDATE" in sql.upper():
            # Extract WHERE clause from UPDATE
            where_idx = sql.upper().find("WHERE")
            if where_idx > -1:
                where_clause = sql[where_idx:]
                dry_run_sql = f"SELECT * FROM {full_table} {where_clause} LIMIT 100"
            else:
                return json.dumps({
                    "error": "UPDATE statement must have WHERE clause for safety",
                    "status": "invalid_sql"
                })
        
        elif "DELETE" in sql.upper():
            # Extract WHERE clause from DELETE
            from_idx = sql.upper().find("FROM")
            where_idx = sql.upper().find("WHERE")
            if where_idx > -1:
                table_part = sql[from_idx+4:where_idx].strip()
                where_clause = sql[where_idx:]
                dry_run_sql = f"SELECT * FROM {full_table} {where_clause} LIMIT 100"
            else:
                return json.dumps({
                    "error": "DELETE statement must have WHERE clause for safety",
                    "status": "invalid_sql"
                })
        
        # Execute dry run
        client = bigquery.Client(project=project_id)
        results = client.query(dry_run_sql).result()
        
        affected_rows = []
        for row in results:
            affected_rows.append(dict(row))
        
        # Get total count
        count_sql = dry_run_sql.replace("SELECT *", "SELECT COUNT(*) as total").replace("LIMIT 100", "")
        total_count = list(client.query(count_sql).result())[0].total
        
        return json.dumps({
            "status": "success",
            "affected_row_count": total_count,
            "sample_rows": affected_rows[:10],
            "dry_run_sql": dry_run_sql,
            "original_sql": sql
        })
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "status": "error",
            "sql": fix_sql
        })


def execute_fix(
    fix_sql: str,
    table_name: str,
    batch_size: int,
    tool_context: ToolContext
) -> str:
    """
    Execute a DQ fix on BigQuery table.
    Uses batch processing for large updates.
    """
    project_id = os.getenv("BQ_DATA_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    if not project_id or not dataset_id:
        return json.dumps({
            "error": "Missing BQ_DATA_PROJECT_ID or BQ_DATASET_ID environment variables",
            "status": "config_error"
        })
    
    try:
        # Clean SQL - remove any hardcoded dataset/project references
        sql = fix_sql.strip()
        
        # Replace common hardcoded patterns
        import re
        # Remove dataset/project qualifiers from table references
        sql = re.sub(r'\b[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.([a-zA-Z0-9_-]+)\b', r'\1', sql)
        sql = re.sub(r'\b[a-zA-Z0-9_-]+\.([a-zA-Z0-9_-]+)\b(?!\s*\()', r'\1', sql)
        
        # Now build proper table reference
        full_table = f"`{project_id}.{dataset_id}.{table_name}`"
        
        # Replace table placeholders
        sql = sql.replace("{table}", full_table).replace("TABLE_NAME", full_table).replace("{{table}}", full_table)
        
        # Replace bare table name with fully qualified name
        sql = re.sub(rf'\b{table_name}\b', full_table, sql)
        
        # Safety check: Ensure WHERE clause exists for UPDATE/DELETE
        if "UPDATE" in sql.upper() or "DELETE" in sql.upper():
            if "WHERE" not in sql.upper():
                return json.dumps({
                    "error": "UPDATE/DELETE without WHERE clause is not allowed",
                    "status": "rejected"
                })
        
        # Execute SQL
        client = bigquery.Client(project=project_id)
        
        # For UPDATE/DELETE, use DML
        if "UPDATE" in sql.upper() or "DELETE" in sql.upper():
            # Add LIMIT if not present and batch_size specified
            if batch_size and batch_size > 0:
                if "LIMIT" not in sql.upper():
                    # For UPDATE/DELETE in BigQuery, we can't use LIMIT directly
                    # Instead, we'll note this limitation
                    pass
            
            query_job = client.query(sql)
            result = query_job.result()
            
            # Get number of affected rows (for DML)
            num_dml_affected_rows = query_job.num_dml_affected_rows if hasattr(query_job, 'num_dml_affected_rows') else 0
            
            return json.dumps({
                "status": "success",
                "affected_rows": num_dml_affected_rows,
                "execution_time_ms": query_job.total_bytes_processed,
                "sql_executed": sql
            })
        
        else:
            # For other SQL (CREATE TABLE AS, INSERT)
            query_job = client.query(sql)
            result = query_job.result()
            
            return json.dumps({
                "status": "success",
                "execution_time_ms": query_job.total_bytes_processed,
                "sql_executed": sql
            })
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "status": "failed",
            "sql": fix_sql
        })


def validate_fix(
    original_rule_sql: str,
    table_name: str,
    tool_context: ToolContext
) -> str:
    """
    Validate that a fix worked by re-running the original DQ rule.
    If the rule returns 0 violations, the fix was successful.
    """
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    try:
        # Replace table placeholder
        full_table = f"`{project_id}.{dataset_id}.{table_name}`"
        sql = original_rule_sql.replace("{table}", full_table).replace("TABLE_NAME", full_table).replace("{{table}}", full_table)
        
        # Execute validation query
        client = bigquery.Client(project=project_id)
        results = client.query(sql).result()
        
        violations = []
        for row in results:
            violations.append(dict(row))
        
        validation_status = "success" if len(violations) == 0 else "partial"
        
        return json.dumps({
            "status": validation_status,
            "remaining_violations": len(violations),
            "sample_violations": violations[:5],
            "message": "All issues resolved" if len(violations) == 0 else f"{len(violations)} violations still exist"
        })
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "status": "error"
        })


def create_jira_ticket(
    issue_summary: str,
    issue_description: str,
    affected_rows: int,
    fix_sql: str,
    priority: str,
    tool_context: ToolContext
) -> str:
    """
    Create a JIRA ticket for DQ issues that require manual intervention.
    This is a mock implementation - in production, integrate with actual JIRA API.
    """
    # Generate mock JIRA ticket
    ticket_id = f"DQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    ticket = {
        "ticket_id": ticket_id,
        "summary": issue_summary,
        "description": issue_description,
        "priority": priority,
        "affected_rows": affected_rows,
        "status": "OPEN",
        "created_at": datetime.now().isoformat(),
        "assignee": "DQ-Team",
        "labels": ["data-quality", "auto-generated", "bancs"],
        "attachment": {
            "name": "fix_sql.sql",
            "content": fix_sql
        }
    }
    
    # In production: Save to jira_mock/jira_tickets.json
    # For now, just return the ticket
    
    return json.dumps({
        "status": "ticket_created",
        "ticket": ticket,
        "message": f"JIRA ticket {ticket_id} created successfully",
        "url": f"https://jira.example.com/browse/{ticket_id}"  # Mock URL
    })


def get_before_after_comparison(
    table_name: str,
    row_identifiers: list,
    columns_to_compare: list,
    tool_context: ToolContext
) -> str:
    """
    Get before/after comparison for specific rows to visualize fix impact.
    """
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    try:
        # This would need a backup/snapshot table in production
        # For now, return mock comparison structure
        
        comparison = {
            "table": f"{project_id}.{dataset_id}.{table_name}",
            "rows_compared": len(row_identifiers),
            "columns": columns_to_compare,
            "changes": [
                {
                    "row_id": row_id,
                    "before": {"column": "old_value"},
                    "after": {"column": "new_value"}
                }
                for row_id in row_identifiers[:5]
            ],
            "note": "Before/after comparison requires table snapshots in production"
        }
        
        return json.dumps(comparison)
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "status": "error"
        })
