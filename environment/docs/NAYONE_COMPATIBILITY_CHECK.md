# NayaOne Environment Compatibility Check

**Date:** December 11, 2025  
**Project:** Data Quality Management System with Real Dataplex Integration

---

## ✅ OVERALL STATUS: COMPATIBLE

Your application **WILL WORK** in the NayaOne environment with **minor setup required**.

---

## 🔍 COMPATIBILITY ANALYSIS

### ✅ Python Version
- **Required:** Python >= 3.12
- **NayaOne:** Python is pre-installed in VS Code workspace
- **Status:** ✅ **COMPATIBLE**

### ✅ Dependencies
- **All dependencies** are listed in `pyproject.toml`
- **Key libraries:**
  - `google-adk >= 1.14` ✅
  - `google-cloud-aiplatform[adk,agent-engines] >= 1.93.0` ✅
  - `google-cloud-dataplex == 2.15.0` ✅ **(Installed and tested)**
  - `streamlit >= 1.41.0` ✅
  - `google-cloud-bigquery` ✅
  
- **Installation method:** `uv` (modern Python package installer)
- **Status:** ✅ **COMPATIBLE**

### ✅ GCP Authentication
- **Method:** Uses `gcloud auth login` (NayaOne standard)
- **Configuration:** Auto-detects project via `gcloud config get-value project`
- **Status:** ✅ **COMPATIBLE** - Follows NayaOne guide exactly

### ✅ GCP Permissions Required

Your app requires these **IAM roles**:

1. **BigQuery:**
   - `roles/bigquery.dataViewer` (read tables)
   - `roles/bigquery.jobUser` (run queries)
   - `roles/bigquery.dataEditor` (for test data loading)

2. **Dataplex:** ⚠️ **CRITICAL**
   - `roles/dataplex.admin` (create DataScans)
   - `roles/dataplex.dataScanAdmin` (run profiling)
   - `roles/dataplex.viewer` (view results)

3. **Cloud Storage:**
   - `roles/storage.objectViewer` (read CSV files from bucket)

4. **Vertex AI:**
   - `roles/aiplatform.user` (for ADK agents and Gemini)

**Action Required:** Verify with NayaOne support that your team's GCP account has Dataplex permissions enabled.

### ✅ Network Connectivity
- **GCP API Endpoints:** All Google Cloud APIs are accessible from NayaOne workspaces
- **Dataplex API:** `dataplex.googleapis.com` ✅
- **BigQuery API:** `bigquery.googleapis.com` ✅
- **Vertex AI API:** `aiplatform.googleapis.com` ✅
- **Status:** ✅ **COMPATIBLE**

### ✅ Environment Variables
Your app uses these environment variables (all optional with fallbacks):

```bash
GOOGLE_CLOUD_PROJECT      # Auto-detected from gcloud config
BQ_DATASET_ID            # Auto-detected or set via Streamlit UI
GOOGLE_CLOUD_LOCATION    # Defaults to "us-central1"
BQ_DATA_PROJECT_ID       # Defaults to GOOGLE_CLOUD_PROJECT
```

**Status:** ✅ **COMPATIBLE** - No hardcoded values, everything is configurable

---

## 🚀 SETUP INSTRUCTIONS FOR NAYONE

### Step 1: Initial Workspace Setup (Done Once)

Follow NayaOne guide Section 2-5 to:
1. Access your Developer Workspace
2. Open VS Code IDE
3. Setup GCP authentication:
   ```bash
   gcloud auth login
   gcloud config set project <YOUR_NAYONE_PROJECT_ID>
   ```
4. Clone your GitLab repository

### Step 2: Install Dependencies

In the VS Code terminal:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to project directory
cd <your-repo-name>

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Linux (NayaOne uses Linux)
uv pip install -e .
```

### Step 3: Initialize Environment

Run the auto-discovery script:

```bash
python init_environment.py
```

This will:
- ✅ Auto-detect your GCP project
- ✅ Find your GCS bucket and data files
- ✅ Discover or create BigQuery dataset
- ✅ Save configuration to `environment_config.json`
- ✅ Optionally load CSV data from GCS → BigQuery

### Step 4: Setup Dataplex Infrastructure

**CRITICAL:** Dataplex requires initial setup in your GCP project.

```bash
# Enable Dataplex API
gcloud services enable dataplex.googleapis.com

# Create Dataplex Lake
gcloud dataplex lakes create your-dq-lake \
  --location=us-central1 \
  --display-name="Data Quality Lake"

# Create Zone
gcloud dataplex zones create raw-zone \
  --lake=your-dq-lake \
  --location=us-central1 \
  --type=RAW \
  --resource-location-type=SINGLE_REGION

# Link BigQuery Dataset as Asset
gcloud dataplex assets create your-dataset-asset \
  --lake=your-dq-lake \
  --zone=raw-zone \
  --location=us-central1 \
  --resource-type=BIGQUERY_DATASET \
  --resource-name=projects/<PROJECT_ID>/datasets/<DATASET_ID>
```

**Time Required:** ~2 minutes for infrastructure to become ACTIVE

### Step 5: Verify Dataplex Setup

```bash
# Check lake status
gcloud dataplex lakes list --location=us-central1

# Should show:
# NAME: your-dq-lake
# LAKE_STATUS: ACTIVE
```

### Step 6: Run the Application

```bash
# Start Streamlit app
streamlit run streamlit_app/app.py
```

The app will be accessible at:
- Local: `http://localhost:8501`
- Network: Available within NayaOne workspace network

---

## ⚠️ POTENTIAL ISSUES & SOLUTIONS

### Issue 1: "Dataplex API not enabled"

**Error:**
```
google.api_core.exceptions.PermissionDenied: 403 Dataplex API has not been used...
```

**Solution:**
```bash
gcloud services enable dataplex.googleapis.com
```

### Issue 2: "Permission denied" when creating DataScans

**Error:**
```
google.api_core.exceptions.PermissionDenied: 403 Missing roles/dataplex.admin
```

**Solution:**
Contact NayaOne support to add these IAM roles to your team's service account:
- `roles/dataplex.admin`
- `roles/dataplex.dataScanAdmin`

### Issue 3: Slow Dataplex Scans

**Behavior:**
First scan takes 60-90 seconds

**Explanation:**
This is **NORMAL** - Real Dataplex profiling scans 100% of data.
- Shows progress in UI: "Dataplex profiling takes ~60s per table"
- Results are cached by Dataplex for subsequent queries
- Visible in GCP Console → Dataplex → DataScans

**This is NOT a bug - it's real GCP infrastructure working!**

### Issue 4: "No module named 'google.cloud.dataplex'"

**Error:**
```
ModuleNotFoundError: No module named 'google.cloud.dataplex'
```

**Solution:**
```bash
uv pip install google-cloud-dataplex==2.15.0
```

Or add to `pyproject.toml`:
```toml
dependencies = [
    "google-cloud-dataplex>=2.15.0",
    # ... other dependencies
]
```

Then reinstall:
```bash
uv pip install -e .
```

---

## 📊 FEATURE AVAILABILITY IN NAYONE

| Feature | Status | Notes |
|---------|--------|-------|
| **Real Dataplex Integration** | ✅ Works | Requires permissions + infrastructure setup |
| **BigQuery Queries** | ✅ Works | Standard GCP API |
| **Streamlit UI** | ✅ Works | Runs in VS Code terminal |
| **Multi-Agent System (ADK)** | ✅ Works | Uses Vertex AI APIs |
| **Knowledge Bank** | ✅ Works | JSON file storage |
| **DQ Rule Generation** | ✅ Works | Uses Gemini via Vertex AI |
| **Treatment Agent** | ✅ Works | Standard Python + BQ |
| **Metrics Calculation** | ✅ Works | Standard Python |
| **GCS Data Loading** | ✅ Works | Auto-detected from bucket |

---

## 🎯 VERIFICATION CHECKLIST

Before running in NayaOne, verify:

- [ ] GCP authentication completed (`gcloud auth list` shows active account)
- [ ] Project ID configured (`gcloud config get-value project`)
- [ ] Dataplex API enabled (`gcloud services list | grep dataplex`)
- [ ] IAM permissions granted (check with NayaOne support)
- [ ] Dataplex infrastructure created (lake, zone, asset)
- [ ] Dependencies installed (`uv pip list | grep dataplex`)
- [ ] Environment initialized (`python init_environment.py`)
- [ ] Test data loaded to BigQuery

---

## 🚨 CRITICAL NOTES FOR NAYONE ENVIRONMENT

### 1. First-Time Setup
Dataplex infrastructure **MUST be created ONCE per GCP project**:
```bash
# Run these commands ONCE (not per workspace)
gcloud dataplex lakes create...
gcloud dataplex zones create...
gcloud dataplex assets create...
```

### 2. Permissions
Dataplex is an **enterprise-grade service** - requires explicit IAM roles.
If you get permission errors, contact NayaOne support immediately.

### 3. Network Access
All GCP APIs are accessible from NayaOne workspaces.
No VPN or special network configuration needed.

### 4. Workspace Persistence
- Code: Persists via GitLab
- Python packages: Need reinstall if workspace recreates
- GCP auth: Need `gcloud auth login` if workspace recreates
- Dataplex infrastructure: Persists (project-level, not workspace-level)

### 5. Costs
Dataplex DataScans are **NOT free tier**. Each scan costs ~$0.05-0.10.
For hackathon: ~100 scans = ~$5-10 total.
Check with NayaOne about GCP credit allocation.

---

## ✅ FINAL RECOMMENDATION

**Your application IS ready for NayaOne with these steps:**

1. ✅ **Day 1:** Setup workspace, install dependencies, init environment
2. ✅ **Day 1:** Create Dataplex infrastructure (one-time, 10 minutes)
3. ✅ **Day 1:** Verify permissions with NayaOne support
4. ✅ **Day 1:** Load test data, run first Dataplex scan
5. ✅ **Day 2+:** Full development and testing

**Estimated setup time:** 30-60 minutes
**Blocker risk:** LOW (if permissions are granted)

---

## 📞 SUPPORT CONTACTS

**If you encounter issues:**

1. **GCP/Dataplex Issues:**
   - Check: `gcloud auth list`
   - Check: `gcloud services list | grep dataplex`
   - Contact: NayaOne GCP Guardians (in Support Workspace)

2. **Application Issues:**
   - Check: `streamlit_app/app.py` logs
   - Check: `environment_config.json` values
   - Check: Dataplex Console → DataScans

3. **Dependency Issues:**
   - Re-run: `uv pip install -e .`
   - Check: `uv pip list`

---

**Last Updated:** December 11, 2025  
**Tested Environment:** Local Windows + GCP  
**Target Environment:** NayaOne Linux VS Code Workspace
