# 🚀 Quick Start Guide - Dynamic Environment Setup

## Overview

This system now **automatically detects** your GCP environment - no manual configuration needed!

Works with:
- ✅ Personal GCP accounts
- ✅ NayaOne hackathon environment  
- ✅ Production environments
- ✅ Any GCP project with data in GCS

---

## Prerequisites

1. **Python 3.12+** installed
2. **GCP Authentication** configured
3. **BigQuery & Cloud Storage APIs** enabled in your project

---

## Setup Instructions

### Step 1: Authenticate with GCP

```powershell
# Login to GCP
gcloud auth login

# Set your project (or system will auto-detect)
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config get-value project
```

### Step 2: Install Dependencies

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### Step 3: Run Environment Auto-Discovery

```powershell
# This will automatically detect:
# - GCP project ID
# - GCS buckets with data
# - CSV files (Week1-4)
# - BigQuery datasets
# - Table schemas

python init_environment.py
```

**Output:**
```
🔍 Starting environment auto-discovery...
✅ Detected Project: prod-45-hackathon-bucket-megalodon
✅ Environment Type: nayone_hackathon
✅ Found Bucket: prod-45-hackathon-bucket_megalodon
✅ Found Data Folder: 1.1 Improving IP& Data Quality/
✅ Found 4 CSV files
✅ BigQuery Dataset: dq_management_system
✅ Configuration saved to environment_config.json

Do you want to load these files to BigQuery? (y/n): y

📊 Loading 4 CSV files to BigQuery...
📥 Loading sbox-Week1.csv → policies_week1...
✅ Loaded 10000 rows to policies_week1
📥 Loading sbox-Week2.csv → policies_week2...
✅ Loaded 10000 rows to policies_week2
📥 Loading sbox-Week3.csv → policies_week3...
✅ Loaded 10000 rows to policies_week3
📥 Loading sbox-Week4.csv → policies_week4...
✅ Loaded 10000 rows to policies_week4

✅ INITIALIZATION COMPLETE!
```

### Step 4: Verify Configuration

```powershell
# Check generated config
cat environment_config.json
```

**Example output:**
```json
{
  "project_id": "prod-45-hackathon-bucket-megalodon",
  "environment_type": "nayone_hackathon",
  "gcs": {
    "bucket": "prod-45-hackathon-bucket_megalodon",
    "data_folder": "1.1 Improving IP& Data Quality/",
    "csv_files": [
      "sbox-Week1.csv",
      "sbox-Week2.csv",
      "sbox-Week3.csv",
      "sbox-Week4.csv"
    ]
  },
  "bigquery": {
    "dataset_id": "dq_management_system",
    "tables": [
      "policies_week1",
      "policies_week2",
      "policies_week3",
      "policies_week4"
    ],
    "schema": {
      "columns": [...],
      "key_columns": {
        "customer_id": "CUS_ID",
        "date_fields": ["CUS_DOB", "CUS_DEATH_DATE"],
        "amount_fields": ["POLI_GROSS_PMT"],
        "status_fields": ["CUS_LIFE_STATUS"]
      }
    }
  }
}
```

### Step 5: Run the Application

```powershell
# Option 1: Streamlit UI (Recommended)
streamlit run streamlit_app/app.py

# Option 2: Cloud Run (Production)
python main.py
```

---

## Environment-Specific Instructions

### 🏠 Personal GCP Account

```powershell
# Already done? Great! The system detected your setup automatically.
# Project detected: hackathon-practice-480508

# Run the app
streamlit run streamlit_app/app.py
```

### 🏢 NayaOne Hackathon Environment

```powershell
# In NayaOne IDE terminal:

# 1. Install gcloud SDK (if not installed)
# See nayone.md for detailed instructions

# 2. Authenticate
gcloud auth login
# Follow the link and use NayaOne GCP credentials

# 3. Set project
gcloud config set project prod-45-hackathon-bucket-megalodon

# 4. Run auto-discovery
python init_environment.py
# System will find:
#   Bucket: prod-45-hackathon-bucket_megalodon
#   Folder: 1.1 Improving IP& Data Quality/
#   Files: sbox-Week1.csv, sbox-Week2.csv, etc.

# 5. Launch app
streamlit run streamlit_app/app.py
```

### 🏭 Production Environment

```powershell
# Set production project
gcloud config set project your-prod-project-id

# Run auto-discovery
python init_environment.py

# Deploy to Cloud Run
gcloud run deploy dq-management-system \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

---

## What Gets Auto-Detected?

### ✅ GCP Project
- Checks `GOOGLE_CLOUD_PROJECT` env var
- Falls back to `gcloud config get-value project`
- Uses default credentials as last resort

### ✅ Environment Type
- `nayone_hackathon`: Project contains "prod-*-*hackathon*"
- `personal_development`: Project contains "hackathon-practice"
- `production`: Project contains "prod-*"
- `unknown`: Other projects

### ✅ GCS Bucket
Priority order:
1. Buckets with "hackathon" in name
2. Buckets with "data" or "dq" in name
3. Buckets matching "prod-*-*" pattern
4. First available bucket

### ✅ Data Folder
Searches for folders containing:
- "improving ip& data quality"
- "data quality"
- "dq"
- "bancs"
- "policies"

### ✅ CSV Files
Finds files matching:
- `*Week1*.csv`, `*Week2*.csv`, etc.
- `*week*.csv` (case-insensitive)
- Sorted alphabetically

### ✅ BigQuery Dataset
- Searches for existing datasets with "dq", "data_quality", "quality", "bancs"
- Creates `dq_management_system` if none found

### ✅ Table Schema
Automatically detects:
- Customer ID columns (CUS_ID, customer_id, etc.)
- Date fields (*DATE*, *DOB*)
- Amount fields (*PMT*, *AMOUNT*, *PREMIUM*)
- Status fields (*STATUS*, *STATE*)

---

## Manual Configuration (Optional)

If auto-detection doesn't work, manually create `environment_config.json`:

```json
{
  "project_id": "your-project-id",
  "environment_type": "production",
  "gcs": {
    "bucket": "your-bucket-name",
    "data_folder": "path/to/data/",
    "csv_files": ["file1.csv", "file2.csv"]
  },
  "bigquery": {
    "dataset_id": "your_dataset",
    "tables": ["table1", "table2"],
    "schema": {
      "columns": [],
      "key_columns": {}
    }
  }
}
```

Or set environment variables:

```powershell
$env:GOOGLE_CLOUD_PROJECT="your-project-id"
$env:BQ_DATASET_ID="your_dataset"
```

---

## Troubleshooting

### "Could not detect GCP project ID"

```powershell
# Solution 1: Set environment variable
$env:GOOGLE_CLOUD_PROJECT="your-project-id"

# Solution 2: Configure gcloud
gcloud config set project your-project-id

# Solution 3: Check authentication
gcloud auth list
gcloud auth login
```

### "Could not find data bucket"

```powershell
# List all buckets
gsutil ls

# Verify bucket access
gsutil ls gs://your-bucket-name/

# Check permissions
gcloud projects get-iam-policy your-project-id
```

### "No CSV files found"

```powershell
# List bucket contents
gsutil ls gs://your-bucket-name/**/*.csv

# Check folder structure
gsutil ls -r gs://your-bucket-name/
```

### "Could not create dataset"

```powershell
# Check BigQuery permissions
gcloud projects get-iam-policy your-project-id --flatten="bindings[].members" --filter="bindings.role:bigquery"

# Enable BigQuery API
gcloud services enable bigquery.googleapis.com
```

---

## Re-running Discovery

If your environment changes (new files, different project):

```powershell
# Delete old config
Remove-Item environment_config.json

# Run discovery again
python init_environment.py
```

---

## Next Steps

1. ✅ Environment configured automatically
2. ✅ Data loaded to BigQuery
3. 🎯 **Use the system!**
   - Open Streamlit: `streamlit run streamlit_app/app.py`
   - Identifier Agent: Detect data quality issues
   - Treatment Agent: Generate remediation SQL
   - Metrics Agent: Calculate business impact
   - Orchestrator: Run end-to-end workflows

---

## Support

- 📖 See `DYNAMIC_ENVIRONMENT_PLAN.md` for architecture details
- 📖 See `nayone.md` for NayaOne-specific instructions
- 📖 See `CODEBASE_AUDIT_REPORT.md` for production readiness checklist
- 🐛 Issues? Check `environment_config.json` for detected values
- 💬 Questions? Review logs from `python init_environment.py`

---

**No hardcoding. No manual setup. Just run and go! 🚀**
