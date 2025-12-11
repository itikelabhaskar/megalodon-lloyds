"""
Metrics Agent Tools

Provides analytics and metrics calculation for DQ management system.
"""

import os
import json
from datetime import datetime
from google.cloud import bigquery
from google.adk.tools import ToolContext
import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from environment.config_utils import (
    get_project_id, 
    get_dataset_id, 
    get_risk_rate, 
    get_materiality_threshold,
    get_anomaly_contamination_rate
)


def calculate_remediation_metrics(
    issues_data: str,
    tool_context: ToolContext
) -> str:
    """
    Calculate key remediation metrics including velocity, auto-fix rate, and efficiency.
    
    Args:
        issues_data: JSON string containing issue history with timestamps
    
    Returns:
        JSON string with remediation metrics
    """
    try:
        issues = json.loads(issues_data)
        
        total_issues = len(issues)
        auto_fixed = sum(1 for issue in issues if issue.get('resolution_type') == 'auto')
        manual_fixed = sum(1 for issue in issues if issue.get('resolution_type') == 'manual')
        pending = sum(1 for issue in issues if issue.get('status') == 'pending')
        
        # Calculate auto-fix rate
        resolved = auto_fixed + manual_fixed
        auto_fix_rate = (auto_fixed / resolved * 100) if resolved > 0 else 0
        
        # Calculate remediation velocity (average hours to resolve)
        resolution_times = []
        for issue in issues:
            if 'created_at' in issue and 'resolved_at' in issue and issue.get('status') == 'resolved':
                created = datetime.fromisoformat(issue['created_at'])
                resolved = datetime.fromisoformat(issue['resolved_at'])
                hours = (resolved - created).total_seconds() / 3600
                resolution_times.append(hours)
        
        avg_velocity = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        metrics = {
            "total_issues": total_issues,
            "auto_fixed": auto_fixed,
            "manual_fixed": manual_fixed,
            "pending": pending,
            "auto_fix_rate": {
                "percentage": round(auto_fix_rate, 2),
                "target": 80,
                "status": "above_target" if auto_fix_rate >= 80 else "below_target"
            },
            "remediation_velocity": {
                "avg_hours": round(avg_velocity, 2),
                "status": "excellent" if avg_velocity < 24 else "good" if avg_velocity < 72 else "needs_improvement"
            },
            "resolution_rate": round((resolved / total_issues * 100), 2) if total_issues > 0 else 0
        }
        
        return json.dumps(metrics, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to calculate metrics: {str(e)}"})


def calculate_cost_of_inaction(
    affected_rows: int,
    table_name: str,
    tool_context: ToolContext
) -> str:
    """
    Calculate financial impact of unresolved DQ issues (Cost of Inaction).
    
    Args:
        affected_rows: Number of rows with DQ issues
        table_name: Name of the affected table
    
    Returns:
        JSON string with cost analysis
    """
    try:
        project_id = os.getenv("BQ_DATA_PROJECT_ID")
        dataset_id = os.getenv("BQ_DATASET_ID")
        
        client = bigquery.Client(project=project_id)
        
        # Get average policy value from the table
        query = f"""
        SELECT 
            AVG(CAST(policy_value AS FLOAT64)) as avg_policy_value,
            AVG(CAST(premium AS FLOAT64)) as avg_premium,
            COUNT(*) as total_policies
        FROM `{project_id}.{dataset_id}.{table_name}`
        WHERE policy_value IS NOT NULL
        """
        
        results = client.query(query).result()
        row = next(results, None)
        
        if row:
            avg_policy_value = float(row.avg_policy_value or 50000)  # Default £50k
            avg_premium = float(row.avg_premium or 1000)  # Default £1k
        else:
            avg_policy_value = 50000
            avg_premium = 1000
        
        # Calculate financial exposure
        total_exposure = affected_rows * avg_policy_value
        
        # Get risk rates from configuration (configurable via environment variables)
        regulatory_risk_rate = get_risk_rate('regulatory')  # Default 0.001 (0.1%)
        customer_churn_rate = get_risk_rate('customer_churn')  # Default 0.02 (2%)
        operational_rate = get_risk_rate('operational')  # Default 0.005 (0.5%)
        
        # Calculate costs
        regulatory_risk = total_exposure * regulatory_risk_rate
        churn_risk = affected_rows * avg_premium * customer_churn_rate
        operational_cost = total_exposure * operational_rate
        
        monthly_coi = regulatory_risk + churn_risk + operational_cost
        annual_coi = monthly_coi * 12
        
        # Determine materiality using configurable thresholds
        high_threshold = get_materiality_threshold('high')  # Default £10M
        medium_threshold = get_materiality_threshold('medium')  # Default £1M
        
        if total_exposure > high_threshold:
            materiality = "High"
        elif total_exposure > medium_threshold:
            materiality = "Medium"
        else:
            materiality = "Low"
        
        cost_analysis = {
            "affected_rows": affected_rows,
            "avg_policy_value": round(avg_policy_value, 2),
            "total_exposure": round(total_exposure, 2),
            "cost_breakdown": {
                "regulatory_risk": round(regulatory_risk, 2),
                "customer_churn_risk": round(churn_risk, 2),
                "operational_cost": round(operational_cost, 2)
            },
            "cost_of_inaction": {
                "monthly": round(monthly_coi, 2),
                "annual": round(annual_coi, 2),
                "currency": "GBP"
            },
            "materiality_index": materiality,
            "risk_assessment": {
                "regulatory_risk_rate": f"{regulatory_risk_rate * 100}%",
                "customer_churn_rate": f"{customer_churn_rate * 100}%",
                "operational_risk_rate": f"{operational_rate * 100}%"
            }
        }
        
        return json.dumps(cost_analysis, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to calculate Cost of Inaction: {str(e)}"})


def detect_anomalies_in_data(
    table_name: str,
    sample_size: int = 1000,
    tool_context: ToolContext = None
) -> str:
    """
    Detect anomalies in numerical columns using IsolationForest.
    
    Args:
        table_name: BigQuery table to analyze
        sample_size: Number of rows to sample
    
    Returns:
        JSON string with anomaly detection results
    """
    try:
        project_id = os.getenv("BQ_DATA_PROJECT_ID")
        dataset_id = os.getenv("BQ_DATASET_ID")
        
        client = bigquery.Client(project=project_id)
        
        # Get table schema to identify numerical columns
        table_ref = f"{project_id}.{dataset_id}.{table_name}"
        table = client.get_table(table_ref)
        
        numerical_columns = [
            field.name for field in table.schema 
            if field.field_type in ['INTEGER', 'FLOAT', 'NUMERIC', 'BIGNUMERIC', 'INT64', 'FLOAT64']
        ]
        
        if not numerical_columns:
            return json.dumps({"error": "No numerical columns found for anomaly detection"})
        
        # Sample data
        columns_str = ", ".join([f"CAST({col} AS FLOAT64) as {col}" for col in numerical_columns[:5]])  # Limit to 5 columns
        query = f"""
        SELECT 
            policy_id,
            {columns_str}
        FROM `{table_ref}`
        WHERE {" AND ".join([f"{col} IS NOT NULL" for col in numerical_columns[:5]])}
        LIMIT {sample_size}
        """
        
        df = client.query(query).to_dataframe()
        
        if len(df) < 10:
            return json.dumps({"error": "Insufficient data for anomaly detection (minimum 10 rows required)"})
        
        # Prepare features for IsolationForest
        feature_cols = [col for col in df.columns if col != 'policy_id']
        X = df[feature_cols].fillna(0).values
        
        # Run IsolationForest with configurable contamination rate
        contamination_rate = get_anomaly_contamination_rate()  # Default 0.1 (10%)
        iso_forest = IsolationForest(contamination=contamination_rate, random_state=42)
        predictions = iso_forest.fit_predict(X)
        anomaly_scores = iso_forest.score_samples(X)
        
        # Identify anomalies
        df['is_anomaly'] = predictions == -1
        df['anomaly_score'] = anomaly_scores
        
        anomalies = df[df['is_anomaly'] == True]
        
        anomaly_results = {
            "total_rows_analyzed": len(df),
            "anomalies_detected": len(anomalies),
            "anomaly_rate": round(len(anomalies) / len(df) * 100, 2),
            "columns_analyzed": feature_cols,
            "top_anomalies": [
                {
                    "policy_id": str(row['policy_id']),
                    "anomaly_score": round(float(row['anomaly_score']), 4),
                    "values": {col: float(row[col]) for col in feature_cols}
                }
                for _, row in anomalies.nsmallest(10, 'anomaly_score').iterrows()
            ],
            "statistics": {
                col: {
                    "mean": round(float(df[col].mean()), 2),
                    "std": round(float(df[col].std()), 2),
                    "min": round(float(df[col].min()), 2),
                    "max": round(float(df[col].max()), 2)
                }
                for col in feature_cols
            }
        }
        
        return json.dumps(anomaly_results, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Anomaly detection failed: {str(e)}"})


def generate_metrics_narrative(
    metrics_data: str,
    tool_context: ToolContext
) -> str:
    """
    Generate a narrative summary of DQ metrics for executive reporting.
    
    Args:
        metrics_data: JSON string with all metrics data
    
    Returns:
        Markdown-formatted narrative report
    """
    try:
        metrics = json.loads(metrics_data)
        
        # Build narrative
        narrative = "# Data Quality Metrics Report\n\n"
        narrative += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Executive Summary
        narrative += "## Executive Summary\n\n"
        
        if 'cost_of_inaction' in metrics:
            coi = metrics['cost_of_inaction']
            exposure = coi.get('total_exposure', 0)
            monthly = coi.get('cost_of_inaction', {}).get('monthly', 0)
            materiality = coi.get('materiality_index', 'Unknown')
            
            narrative += f"This data quality analysis reveals **{materiality}** materiality issues affecting "
            narrative += f"**£{exposure:,.0f}** in policy value. "
            narrative += f"The projected Cost of Inaction is **£{monthly:,.0f}/month** "
            narrative += f"(£{monthly * 12:,.0f} annually) if these issues remain unresolved.\n\n"
        
        # Remediation Performance
        if 'remediation_metrics' in metrics:
            rem = metrics['remediation_metrics']
            auto_rate = rem.get('auto_fix_rate', {}).get('percentage', 0)
            velocity = rem.get('remediation_velocity', {}).get('avg_hours', 0)
            
            narrative += "## Remediation Performance\n\n"
            narrative += f"- **Auto-Fix Rate:** {auto_rate}% "
            
            if auto_rate >= 80:
                narrative += "(✅ Above 80% target)\n"
            else:
                narrative += f"(⚠️ Below 80% target, need {80 - auto_rate}% improvement)\n"
            
            narrative += f"- **Remediation Velocity:** {velocity:.1f} hours average\n"
            narrative += f"- **Total Issues:** {rem.get('total_issues', 0)} detected\n"
            narrative += f"- **Resolved:** {rem.get('auto_fixed', 0) + rem.get('manual_fixed', 0)}\n"
            narrative += f"- **Pending:** {rem.get('pending', 0)}\n\n"
        
        # Anomaly Detection
        if 'anomaly_detection' in metrics:
            anom = metrics['anomaly_detection']
            narrative += "## Anomaly Detection\n\n"
            narrative += f"Analyzed **{anom.get('total_rows_analyzed', 0)}** records across "
            narrative += f"**{len(anom.get('columns_analyzed', []))}** numerical columns. "
            narrative += f"Detected **{anom.get('anomalies_detected', 0)}** anomalies "
            narrative += f"({anom.get('anomaly_rate', 0)}% of data).\n\n"
            
            if anom.get('top_anomalies'):
                narrative += "Top anomalous records require investigation for potential data quality issues.\n\n"
        
        # Recommendations
        narrative += "## Recommendations\n\n"
        
        if 'cost_of_inaction' in metrics and metrics['cost_of_inaction'].get('materiality_index') == 'High':
            narrative += "1. **Immediate Action Required:** High materiality issues pose significant financial risk\n"
        
        if 'remediation_metrics' in metrics and metrics['remediation_metrics'].get('auto_fix_rate', {}).get('percentage', 0) < 80:
            narrative += "2. **Increase Automation:** Current auto-fix rate is below target; review Knowledge Bank patterns\n"
        
        if 'anomaly_detection' in metrics and metrics['anomaly_detection'].get('anomaly_rate', 0) > 5:
            narrative += "3. **Investigate Anomalies:** High anomaly rate suggests systematic data quality issues\n"
        
        narrative += "\n---\n"
        narrative += "*This report was generated automatically by the DQ Metrics Agent.*\n"
        
        return narrative
        
    except Exception as e:
        return f"Error generating narrative: {str(e)}"


def get_dq_rule_accuracy(
    rule_results: str,
    tool_context: ToolContext
) -> str:
    """
    Calculate accuracy metrics for DQ rules including false positive rate.
    
    Args:
        rule_results: JSON string with rule execution history and validation results
    
    Returns:
        JSON string with accuracy metrics
    """
    try:
        results = json.loads(rule_results)
        
        total_detections = 0
        false_positives = 0
        true_positives = 0
        
        for rule in results:
            detected = rule.get('issues_detected', 0)
            validated = rule.get('issues_validated', 0)
            
            total_detections += detected
            true_positives += validated
            false_positives += (detected - validated)
        
        false_positive_rate = (false_positives / total_detections * 100) if total_detections > 0 else 0
        accuracy = (true_positives / total_detections * 100) if total_detections > 0 else 0
        
        accuracy_metrics = {
            "total_detections": total_detections,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_positive_rate": round(false_positive_rate, 2),
            "accuracy": round(accuracy, 2),
            "status": "excellent" if false_positive_rate < 5 else "good" if false_positive_rate < 10 else "needs_improvement"
        }
        
        return json.dumps(accuracy_metrics, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to calculate accuracy: {str(e)}"})
