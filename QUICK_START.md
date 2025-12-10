# 🚀 Quick Start Guide - DQ Management System

## ⚡ FIRST TIME SETUP (Run Once)

```powershell
# 1. Navigate to project
cd "c:\Users\mylil\Desktop\google adk-samples main python-agents_data-science"

# 2. Create virtual environment
python -m venv .venv

# 3. Activate venv
.venv\Scripts\Activate.ps1

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install ALL dependencies
pip install google-adk>=1.14
pip install google-cloud-aiplatform[adk,agent-engines]>=1.93.0
pip install google-cloud-bigquery
pip install google-cloud-dataplex
pip install streamlit plotly altair pandas numpy scikit-learn python-dotenv
pip install streamlit-sortables

# 6. Authenticate to GCP
gcloud auth login
gcloud auth application-default login
gcloud config set project hackathon-practice-480508
gcloud auth application-default set-quota-project hackathon-practice-480508

# 7. Enable APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable dataplex.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

---

## 🔄 EVERY SESSION (Run Every Time)

```powershell
# 1. Navigate to project
cd "c:\Users\mylil\Desktop\google adk-samples main python-agents_data-science"

# 2. Activate venv (CRITICAL!)
.venv\Scripts\Activate.ps1

# You'll see (.venv) in your prompt when active
```

---

## 📋 PHASE 0 CHECKLIST

### Step 0.1: GCP Authentication ✓
```powershell
gcloud auth login
gcloud config set project hackathon-practice-480508
gcloud auth application-default login
gcloud auth application-default set-quota-project hackathon-practice-480508
gcloud config get-value project  # Verify
```

### Step 0.2: Enable APIs ✓
```powershell
gcloud services enable bigquery.googleapis.com aiplatform.googleapis.com dataplex.googleapis.com
```

### Step 0.3: Verify BaNCS Data ✓
```powershell
bq ls hackathon-practice-480508:bancs_dataset
bq query --use_legacy_sql=false 'SELECT * FROM `hackathon-practice-480508.bancs_dataset.policies_week1` LIMIT 5'
```

### Step 0.4: Test Dataplex Access ✓
```powershell
gcloud dataplex lakes list --project=hackathon-practice-480508 --location=us-central1
```

### Step 0.5: Virtual Environment ✓
```powershell
# Already done in first time setup!
python -c "import google.adk; print('ADK OK')"
python -c "import google.cloud.bigquery; print('BigQuery OK')"
```

### Step 0.6: Configure .env ✓
```powershell
Copy-Item .env.example .env
notepad .env  # Edit with your values
```

**Already configured in .env:**
- `GOOGLE_CLOUD_PROJECT=hackathon-practice-480508` ✅
- `BQ_COMPUTE_PROJECT_ID=hackathon-practice-480508` ✅
- `BQ_DATA_PROJECT_ID=hackathon-practice-480508` ✅
- `BQ_DATASET_ID=bancs_dataset` ✅
- `GOOGLE_CLOUD_LOCATION=us-central1` ✅

### Step 0.7: Test Setup ✓
```powershell
python test_setup.py
```

---

## 🎯 WORKFLOW REMINDER

### Before Running ANY Python Command:
```powershell
.venv\Scripts\Activate.ps1
```

### Before Running Tests:
```powershell
.venv\Scripts\Activate.ps1
python test_file.py
```

### Before Running Streamlit:
```powershell
.venv\Scripts\Activate.ps1
streamlit run streamlit_app\app.py
```

---

## 📁 NEW FILES TO CREATE (As You Progress)

### Phase 1:
- `bancs_dataset_config.json`
- `test_schema.py`
- `test_dq_rule.py`

### Phase 2:
- `streamlit_app/app.py`

### Phase 3:
- `dq_agents/identifier/agent.py`
- `dq_agents/identifier/tools.py`
- `dq_agents/identifier/prompts.py`
- `mock_data/pre_existing_rules.json` ← NEW!

### Phase 4:
- `dq_agents/treatment/agent.py`
- `knowledge_bank/knowledge_bank.json`

### Phase 5:
- `dq_agents/remediator/agent.py`
- `jira_mock/jira_tickets.json`

### Phase 6:
- `dq_agents/metrics/agent.py`

---

## 🔍 TROUBLESHOOTING

### "python not found"
```powershell
python --version  # Check Python 3.12+
```

### "Module not found"
```powershell
# Check venv is active
.venv\Scripts\Activate.ps1

# Reinstall package
pip install google-adk
```

### "gcloud not found"
Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install

### "Permission denied in BigQuery"
```powershell
gcloud auth application-default login
```

---

## ✅ VERIFICATION AT EACH STEP

Don't proceed until current step's verification passes!

**Example:**
```
Step 0.1 Verification:
✅ gcloud auth list shows your account
✅ gcloud config get-value project returns correct ID

Only then → Move to Step 0.2
```

---

## 🚨 CRITICAL REMINDERS

1. **ALWAYS activate venv first**: `.venv\Scripts\Activate.ps1`
2. **Verify each step** before moving forward
3. **Use forward slashes** in paths (Python compatibility)
4. **Check .env file** has correct project/dataset IDs
5. **Git commit** after each phase (save progress!)

---

## 📞 QUICK REFERENCE

**Activate venv:**
```powershell
.venv\Scripts\Activate.ps1
```

**Deactivate venv:**
```powershell
deactivate
```

**Check Python packages:**
```powershell
pip list | Select-String "google"
```

**Test BigQuery connection:**
```powershell
python -c "from google.cloud import bigquery; print('OK')"
```

**Run Streamlit:**
```powershell
streamlit run streamlit_app\app.py
```

---

## 🎯 YOU ARE HERE

**Status:** ✅ All gaps patched, ready to start Phase 0

**Next Command:**
```powershell
gcloud auth login
```

**Follow:** PLAN.md step-by-step with verification at each checkpoint

**Time to Complete:** 24-30 hours (2 days)

**Let's go!** 🚀
