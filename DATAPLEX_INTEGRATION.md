# Dataplex Integration Guide

## Overview
This system integrates **Google Cloud Dataplex** for advanced data profiling and quality scanning, with intelligent fallback to BigQuery-based profiling when Dataplex is unavailable.

## Architecture

### ADK Integration Pattern
The Dataplex client follows the same ADK integration pattern as BigQuery:

```python
def _get_dataplex_client():
    """Get Dataplex DataScan client with proper ADK integration."""
    # Respects GOOGLE_CLOUD_PROJECT environment variable
    # Consistent with ADK's BigQuery client pattern
    return dataplex_v1.DataScanServiceClient()
```

### Graceful Fallback
- **Primary**: Dataplex DataScan API (full profiling with statistics)
- **Fallback**: BigQuery INFORMATION_SCHEMA queries (null counts, basic stats)

## Installation

### Step 1: Install Dependencies
```powershell
# From project root
pip install -e .
```

This installs `google-cloud-dataplex>=1.18.0` from `pyproject.toml`.

### Step 2: Enable Dataplex API
```powershell
gcloud services enable dataplex.googleapis.com
```

### Step 3: Verify Installation
```powershell
python -c "from google.cloud import dataplex_v1; print('Dataplex OK ✅')"
```

## Usage in Agents

### Identifier Agent Tool
```python
# In dq_agents/identifier/agent.py
tools = [
    trigger_dataplex_scan,  # Automatically uses ADK-integrated client
    # ... other tools
]
```

### How It Works
1. **Dataplex Available**: Creates DataScan → Runs profiling → Returns detailed stats
2. **Dataplex Unavailable**: Falls back to BigQuery profiling automatically
3. **No User Intervention Required**: System handles the decision transparently

## Profiling Results

### Dataplex Profile (Full)
```json
{
  "status": "scan_completed",
  "scan_types": ["DATAPLEX_PROFILE"],
  "findings": {
    "total_rows": 100000,
    "total_columns": 25,
    "null_rates": {"column_name": "5.2%"},
    "column_statistics": [
      {"name": "age", "type": "INT64", "min": "18", "max": "99", "mean": "45.2"}
    ],
    "data_quality_issues": [
      {"issue": "High null rate in email", "severity": "high"}
    ]
  }
}
```

### BigQuery Fallback (Basic)
```json
{
  "status": "scan_completed",
  "scan_types": ["DATAPLEX_PROFILE", "BQ_FALLBACK"],
  "findings": {
    "total_rows": 100000,
    "null_rates": {"column_name": "5.2%"},
    "data_quality_issues": [
      {"issue": "High null rate in email", "severity": "high"}
    ]
  }
}
```

## Troubleshooting

### Error: Cannot import dataplex_v1
**Cause**: Package not installed  
**Fix**: Run `pip install -e .` from project root

### Error: Permission denied
**Cause**: Missing Dataplex permissions  
**Fix**: System automatically falls back to BigQuery profiling (no action needed)

### Error: Dataplex API not enabled
**Cause**: API not enabled in GCP project  
**Fix**: `gcloud services enable dataplex.googleapis.com`

## Performance Notes

- **Dataplex scans**: 30-90 seconds (comprehensive stats)
- **BigQuery fallback**: 5-15 seconds (null counts only)
- **Recommendation**: Enable Dataplex for production systems

## Environment Variables

```bash
GOOGLE_CLOUD_PROJECT=your-project-id      # Required
GOOGLE_CLOUD_LOCATION=us-central1         # Optional (default: us-central1)
BQ_COMPUTE_PROJECT_ID=your-project-id     # Required
BQ_DATA_PROJECT_ID=your-data-project-id   # Required
BQ_DATASET_ID=your-dataset-id             # Required
```

## Best Practices

1. **Enable Dataplex in production** for comprehensive profiling
2. **Use BigQuery fallback in dev/test** for faster iteration
3. **Monitor scan costs** - Dataplex scans have per-scan costs
4. **Cache profiling results** - Store in `dq_rules_cache.json`

## Integration with ADK

The Dataplex integration follows ADK's recommended patterns:

- ✅ Uses `ToolContext` for agent coordination
- ✅ Returns structured JSON for LLM parsing
- ✅ Graceful error handling with fallbacks
- ✅ Proper logging with user agent tracking
- ✅ Respects ADK environment configuration

## Example: Running Profiling

### From Streamlit UI
1. Navigate to **Identifier Agent**
2. Select table to profile
3. Click **Run Identifier Agent**
4. System automatically uses Dataplex or falls back to BigQuery

### From Python
```python
from dq_agents.identifier.tools import trigger_dataplex_scan

result = trigger_dataplex_scan(
    table_name="policies_week1",
    tool_context=None
)
# Returns JSON with profiling results
```

## Next Steps

1. Install dependencies: `pip install -e .`
2. Enable Dataplex API: `gcloud services enable dataplex.googleapis.com`
3. Run profiling test: `python test_dataplex_profiling.py`
4. Check logs for confirmation: Look for "Dataplex OK ✅" or "using BigQuery fallback"

---

**Status**: ✅ Fully integrated with ADK  
**Fallback**: ✅ BigQuery profiling (no manual intervention)  
**Dependencies**: `google-cloud-dataplex>=1.18.0` (in pyproject.toml)
