# Metrics Agent - Data Quality Analytics

## Overview

The Metrics Agent provides comprehensive analytics for the Data Quality Management System, including:
- **Dashboard Overview**: Real-time metrics on DQ issues, remediation status, and severity distribution
- **Anomaly Detection**: ML-powered outlier detection using IsolationForest
- **Cost of Inaction**: Financial impact analysis with regulatory, churn, and operational risk calculations
- **Executive Reports**: AI-generated markdown reports with dynamic storytelling

## Key Features

### 1. Dashboard Overview
- **Total Violations**: Aggregate count of all DQ issues detected
- **Auto-Fix Rate**: Percentage of issues resolved automatically (Target: >80%)
- **Average Severity**: Weighted severity score across all issues
- **Exposure**: Total policy value affected by DQ issues

**Interactive Visualizations:**
- Issues by DQ Dimension (Bar chart)
- Issues by Severity (Pie chart)
- Remediation Status (Pie chart)

### 2. Anomaly Detection
Uses scikit-learn's **IsolationForest** algorithm to detect outliers in numerical columns:
- Analyzes policy values, premiums, and other numerical fields
- Returns anomaly scores (lower = more anomalous)
- Configurable sample size (100-5000 rows)
- Statistical summaries for all analyzed columns

**Use Cases:**
- Detect fraudulent policy values
- Identify data entry errors
- Find outlier premiums or claims

### 3. Cost of Inaction (CoI)
Calculates financial risk of leaving DQ issues unresolved:

**Formula:**
```
Total Exposure = Affected Rows × Average Policy Value
Monthly CoI = (Regulatory Risk + Churn Risk + Operational Cost)
Annual CoI = Monthly CoI × 12
```

**Risk Components:**
- **Regulatory Risk**: 0.1% of exposure (FCA fines)
- **Customer Churn Risk**: 2% of affected premiums
- **Operational Cost**: 0.5% of exposure

**Materiality Index:**
- **High**: Exposure > £10M
- **Medium**: Exposure > £1M
- **Low**: Exposure < £1M

### 4. Executive Reports
AI-generated markdown reports include:
- Executive Summary (2-3 paragraphs)
- Key Findings (bullet points)
- Financial Impact
- Remediation Status
- Recommendations
- Next Steps

Reports use **dynamic storytelling** powered by Gemini to create actionable insights.

## Tools Available

### `calculate_remediation_metrics(issues_data: str) -> str`
Calculates:
- Auto-fix rate
- Remediation velocity (avg hours to resolve)
- Resolution rate
- Issue breakdown by status

### `calculate_cost_of_inaction(affected_rows: int, table_name: str) -> str`
Computes financial impact with risk breakdown

### `detect_anomalies_in_data(table_name: str, sample_size: int) -> str`
Runs IsolationForest ML algorithm on numerical columns

### `generate_metrics_narrative(metrics_data: str) -> str`
Creates markdown-formatted executive summary

### `get_dq_rule_accuracy(rule_results: str) -> str`
Calculates false positive rate and accuracy of DQ rules

## Integration with Other Agents

### From Identifier Agent
- Receives detected DQ issues (`filtered_issues`)
- Analyzes severity distribution
- Calculates total violations

### From Treatment Agent
- Tracks approved fixes
- Monitors auto-fix rate
- Measures remediation velocity

### From Remediator Agent
- Validates fix execution
- Tracks success/failure rates
- Updates Cost of Inaction based on resolved issues

## Usage Examples

### 1. Run Dashboard Overview
```python
# Navigate to Metrics tab
# Select "📈 Dashboard Overview"
# View real-time metrics from session state
```

### 2. Detect Anomalies
```python
# Select "🔍 Anomaly Detection"
# Choose table: policies_week1
# Set sample size: 1000
# Click "Run Anomaly Detection"
# View top 10 anomalous records
```

### 3. Calculate Cost of Inaction
```python
# Select "💰 Cost of Inaction"
# Uses detected issues from Identifier
# Or enter manual values
# Click "Calculate Cost"
# View financial breakdown
```

### 4. Generate Executive Report
```python
# Select "📝 Executive Report"
# Click "Generate Report"
# AI creates comprehensive markdown report
# Download as .md file
```

## Performance Considerations

- **Anomaly Detection**: Sample size affects speed (1000 rows ~2-3 seconds)
- **Cost Calculations**: Requires BigQuery query (~1 second)
- **Dashboard**: Real-time updates from session state (instant)
- **Report Generation**: AI storytelling (~3-5 seconds)

## Project.md Requirements Met

✅ **Good UI**: Multi-tab interface with mode selection
✅ **Anomaly Detection**: IsolationForest implementation
✅ **Interactive Graphs**: Plotly bar, pie charts
✅ **Markdown Reports**: Downloadable executive reports
✅ **User Perspective**: Executive summaries with actionable insights
✅ **Independent Operation**: Can run without other agents
✅ **Remediation Velocity**: Average hours to resolution
✅ **Materiality Index**: High/Medium/Low scoring
✅ **Auto-Fix Rate**: % of automated resolutions (Target >80%)
✅ **Cost of Inaction**: Monthly/annual £ projections
✅ **Accuracy**: False positive rate tracking
✅ **Dynamic Storytelling**: AI-generated narratives with financial context

## Future Enhancements

- [ ] Historical trend analysis (week-over-week comparisons)
- [ ] Predictive analytics (forecast future DQ issues)
- [ ] Custom risk rate configuration
- [ ] Multi-table aggregation
- [ ] Real-time alerting for high-materiality issues
- [ ] Integration with Power BI/Tableau
- [ ] PDF export for executive reports
