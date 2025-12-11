# 🧪 Complete End-to-End Testing Guide

**Project:** Data Quality Management System with Real Dataplex Integration  
**Test Date:** December 11, 2025  
**Tester:** _____________  
**Environment:** Local Development

---

## 📋 PRE-FLIGHT CHECKLIST

Before starting tests, verify:

- [ ] Python 3.12+ installed (`python --version`)
- [ ] Virtual environment activated (`.venv`)
- [ ] All dependencies installed (`uv pip list | Select-String "google-cloud"`)
- [ ] GCP authentication completed (`gcloud auth list`)
- [ ] Project ID configured (`gcloud config get-value project`)
- [ ] Environment config exists (`environment_config.json`)

---

## 🚀 TEST EXECUTION PLAN

### PHASE 0: Environment Setup & Verification
### PHASE 1: Streamlit App Launch
### PHASE 2: Sidebar Configuration Tests
### PHASE 3: Orchestrator Agent Tests
### PHASE 4: Identifier Agent Tests
### PHASE 5: Treatment Agent Tests
### PHASE 6: Remediator Agent Tests
### PHASE 7: Metrics Agent Tests
### PHASE 8: Advanced Settings Tests
### PHASE 9: End-to-End Workflow Tests

---

## PHASE 0: Environment Setup & Verification

### TEST 0.1: Check Python Environment
**Command:**
```powershell
python --version
```

**Expected Output:**
```
Python 3.12.x
```

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 0.2: Check Virtual Environment
**Command:**
```powershell
Get-Command python | Select-Object Source
```

**Expected Output:**
```
Source
------
C:\Users\mylil\Desktop\...\python-agents_data-science\.venv\Scripts\python.exe
```

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 0.3: Verify GCP Authentication
**Command:**
```powershell
gcloud auth list
```

**Expected Output:**
```
Credentialed Accounts
ACTIVE  ACCOUNT
*       your-email@gmail.com
```

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 0.4: Check Environment Config
**Command:**
```powershell
Get-Content environment_config.json | Select-String "project_id"
```

**Expected Output:**
```json
  "project_id": "hackathon-practice-480508",
```

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 0.5: Verify BigQuery Access
**Command:**
```powershell
python -c "from google.cloud import bigquery; client = bigquery.Client(); print('✅ BigQuery client initialized')"
```

**Expected Output:**
```
✅ BigQuery client initialized
```

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 0.6: Verify Dataplex Library Installed
**Command:**
```powershell
python -c "from google.cloud import dataplex_v1; print('✅ Dataplex library available')"
```

**Expected Output:**
```
✅ Dataplex library available
```

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

## PHASE 1: Streamlit App Launch

### TEST 1.1: Start Streamlit App
**Command:**
```powershell
streamlit run streamlit_app/app.py
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 1.2: Verify App Loads in Browser
**Action:** Open browser to `http://localhost:8501`

**Expected Output:**
- Page title: "DQ Management System"
- Header: "🔍 Data Quality Management System"
- 6 tabs visible: Orchestrator, Identifier, Treatment, Remediator, Metrics, Advanced Settings
- Sidebar visible with "⚙️ Settings"

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 1.3: Check for Console Errors
**Action:** Open browser DevTools (F12), check Console tab

**Expected Output:**
- No red error messages
- No warnings about missing dependencies

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

## PHASE 2: Sidebar Configuration Tests

### TEST 2.1: Verify GCP Configuration Pre-loaded
**Action:**
1. Look at sidebar "☁️ GCP Configuration" section
2. Check if Project ID and Dataset ID are pre-filled

**Expected Output:**
- Project ID: `hackathon-practice-480508` (or your project ID)
- Dataset ID: `bancs_dataset` (or your dataset ID)

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 2.2: Test Connection Button
**Action:**
1. Click "🔌 Test Connection" button in sidebar

**Expected Output:**
- Spinner shows "Connecting..."
- Success message: "Connected! Found X tables."
- Green success box appears

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 2.3: Test Invalid Connection
**Action:**
1. Change Dataset ID to "nonexistent_dataset"
2. Click "🔌 Test Connection"

**Expected Output:**
- Red error message: "Connection failed: 404 Not found..."

**Action to Restore:**
3. Change Dataset ID back to "bancs_dataset"
4. Click "🔌 Test Connection" again to verify it works

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 2.4: Model Settings Dropdown
**Action:**
1. Expand "🤖 Model Settings" in sidebar
2. Check dropdown options

**Expected Output:**
- Dropdown shows: "gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro"
- Default selected: "gemini-2.0-flash"

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 2.5: Environment Info Display
**Action:**
1. Scroll to bottom of sidebar
2. Check "Environment" section

**Expected Output:**
```
Environment
Type: personal_development
Tables: 4
```

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

## PHASE 3: Orchestrator Agent Tests

### TEST 3.1: Navigate to Orchestrator Tab
**Action:**
1. Click "🤖 Orchestrator" tab

**Expected Output:**
- Tab content loads
- Header: "🤖 Orchestrator Agent"
- Subheader: "Master coordinator for the complete DQ workflow"
- "ℹ️ About the Orchestrator" expander visible

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 3.2: Expand About Section
**Action:**
1. Click "ℹ️ About the Orchestrator" expander

**Expected Output:**
- Info box displays description of all 4 agents
- Mentions Human-in-the-Loop (HITL)

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 3.3: Full Automated Workflow - Table Selection
**Action:**
1. Select "🚀 Full Automated Workflow" from dropdown
2. Check table dropdown

**Expected Output:**
- Dropdown shows: policies_week1, policies_week2, policies_week3, policies_week4
- Default selected: policies_week1

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 3.4: Full Automated Workflow - Auto-approve Checkbox
**Action:**
1. Check the "Auto-approve high-confidence fixes" checkbox
2. Uncheck it

**Expected Output:**
- Checkbox toggles on/off
- Help text: "Automatically approve fixes with >90% confidence"

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 3.5: Full Automated Workflow - Start Workflow (SKIP FOR NOW)
**Action:**
⚠️ **SKIP THIS TEST** - This starts a full workflow that takes 5-10 minutes

**Reason:** We'll test the full workflow at the end (PHASE 9)

**Status:** [ ] SKIPPED  
**Notes:** Will test in PHASE 9

---

### TEST 3.6: Natural Language Request - UI Check
**Action:**
1. Select "💬 Natural Language Request" from workflow dropdown
2. Check text area

**Expected Output:**
- Text area visible with placeholder: "Example: Find all data quality issues..."
- "🎯 Execute Request" button visible

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 3.7: Natural Language Request - Empty Input
**Action:**
1. Leave text area empty
2. Click "🎯 Execute Request"

**Expected Output:**
- Warning message: "Please enter a request"

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

## PHASE 4: Identifier Agent Tests

### TEST 4.1: Navigate to Identifier Tab
**Action:**
1. Click "🔍 Identifier" tab

**Expected Output:**
- Header: "🔍 Identifier Agent"
- Section "0. Upload Pre-existing DQ Rules (Optional)" visible
- Section "0.5. Generation Mode" visible
- Section "1. Select Tables" visible

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.2: Download DQ Rules Template
**Action:**
1. Click "📥 Download Template" button

**Expected Output:**
- File `dq_rules_template.json` downloads
- File contains example JSON structure

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.3: Generation Mode - Check Radio Buttons
**Action:**
1. Check both radio button options

**Expected Output:**
- Option 1: "🤖 Automated (Schema + Profiling)"
- Option 2: "💬 Natural Language (with Sample Data)"
- Default selected: Automated

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.4: Natural Language Mode - Text Area
**Action:**
1. Select "💬 Natural Language (with Sample Data)"
2. Check if text area appears

**Expected Output:**
- Text area appears with placeholder about UK postcodes, premiums, etc.

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.5: Table Selection - Load Tables
**Action:**
1. Scroll to "1. Select Tables" section
2. Check multiselect dropdown

**Expected Output:**
- Multiselect shows: policies_week1, policies_week2, policies_week3, policies_week4
- Default: policies_week1 (first table selected)

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.6: Table Selection - Select Multiple Tables
**Action:**
1. Select all 4 tables from multiselect

**Expected Output:**
- All 4 tables show as selected chips
- Can remove by clicking X on chip

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.7: Dataplex Profiling Checkbox
**Action:**
1. Scroll down to find "🔍 Run Dataplex Data Profiling" checkbox
2. Check it

**Expected Output:**
- Checkbox has label "🔍 Run Dataplex Data Profiling (GCP Integration)"
- Help text mentions ~60s per table
- Badge says "REAL GCP DATAPLEX"

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.8: Cache Management - Check Cache Status
**Action:**
1. Look for "2. Cache Management" section
2. Check if any cached rules exist

**Expected Output:**
- If cache exists: Shows list of tables with cached rules
- If no cache: Shows "No cached rules found"

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.9: Cache Management - Clear All Cache
**Action:**
1. If cache exists, click "🗑️ Clear All Cache"
2. Confirm action

**Expected Output:**
- Success message: "Cleared all cached rules"
- Cache status updates to "No cached rules found"

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.10: Generate DQ Rules - Button Disabled Check
**Action:**
1. Deselect all tables
2. Check "🚀 Generate DQ Rules" button

**Expected Output:**
- Button is disabled (greyed out)
- Cannot click it

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.11: Generate DQ Rules - Run Generation (1 Table, No Dataplex)
**Action:**
1. Select ONLY "policies_week1"
2. Uncheck "🔍 Run Dataplex Data Profiling"
3. Keep "🤖 Automated" mode
4. Click "🚀 Generate DQ Rules"

**Expected Output:**
- Status box appears: "🔍 Analyzing tables..."
- Progress messages:
  - "Analyzing schema for policies_week1..."
  - "Generating DQ rules..."
- After 10-30 seconds: "✅ Successfully generated X rules for 1 table!"
- Rules display below in JSON format

**Status:** [ ] PASS [ ] FAIL  
**Execution Time:** _______ seconds  
**Rules Generated:** _______ rules  
**Notes:** _______________

---

### TEST 4.12: Verify Generated Rules Format
**Action:**
1. Scroll to see generated rules
2. Check JSON structure

**Expected Output:**
- Rules displayed in expandable sections (one per table)
- Each rule has:
  - `rule_id`
  - `name`
  - `description`
  - `sql` (SELECT query)
  - `severity` (critical/high/medium/low)
  - `dq_dimension`
  - `category`

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.13: Generate DQ Rules - WITH Dataplex Profiling
**Action:**
1. Select "policies_week1"
2. CHECK "🔍 Run Dataplex Data Profiling"
3. Click "🚀 Generate DQ Rules"

**Expected Output:**
- Status messages include:
  - "Running Dataplex profiling for policies_week1..."
  - "⏱️ Profiling takes ~60s per table..."
- Wait 60-90 seconds
- Success message: "✅ Successfully generated X rules"
- Rules include profiling statistics (null rates, etc.)
- Link to GCP Console appears

**Status:** [ ] PASS [ ] FAIL  
**Execution Time:** _______ seconds  
**Dataplex Scan Time:** _______ seconds  
**Rules Generated:** _______ rules  
**Notes:** _______________

---

### TEST 4.14: GCP Console Link - Click Link
**Action:**
1. After Dataplex profiling completes, find "View in GCP Console" link
2. Click it

**Expected Output:**
- Opens new browser tab
- URL: `https://console.cloud.google.com/dataplex/...`
- Shows DataScan in GCP Console (if logged in)

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.15: Manual Rule Entry - Add Custom Rule
**Action:**
1. Scroll to "Manual Rule Entry" section
2. Fill in fields:
   - Rule Name: "test_rule_manual"
   - Description: "Test manual rule entry"
   - SQL Query: `SELECT * FROM \`hackathon-practice-480508.bancs_dataset.policies_week1\` WHERE CUS_FORNAME IS NULL LIMIT 10`
   - Severity: "high"
   - DQ Dimension: "Completeness"
3. Click "➕ Add Rule"

**Expected Output:**
- Success message: "✅ Rule added successfully"
- Rule appears in "Current Rules" section below

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.16: Manual Rule - Delete Rule
**Action:**
1. Find the manually added rule in "Current Rules"
2. Click "🗑️" delete button

**Expected Output:**
- Rule disappears from list
- Success message (optional)

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 4.17: Natural Language Rule Generation
**Action:**
1. Scroll to "🤖 Generate Rule from Description"
2. Enter description: "Check if premium amounts are negative"
3. Click "🤖 Generate Rule from Description"

**Expected Output:**
- Spinner shows "Generating rule..."
- After 5-15 seconds, rule appears in "Raw AI-Generated Rules"
- Rule has SQL query checking for negative premiums

**Status:** [ ] PASS [ ] FAIL  
**Execution Time:** _______ seconds  
**Notes:** _______________

---

### TEST 4.18: Go to Treatment Agent Button
**Action:**
1. Scroll to bottom of Identifier tab
2. Click "▶️ Go to Treatment Agent"

**Expected Output:**
- App navigates to Treatment Agent tab
- Treatment tab becomes active

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

## PHASE 5: Treatment Agent Tests

### TEST 5.1: Navigate to Treatment Tab
**Action:**
1. Click "💊 Treatment" tab

**Expected Output:**
- Header: "💊 Treatment Agent"
- Subheader: "Analyze DQ issues and suggest remediation strategies"
- Section "1. Input DQ Issues" visible

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 5.2: Run Rules - Check Prerequisites
**Action:**
1. Check if "Select Rules to Execute" dropdown is populated
2. If empty, go back to Identifier tab and generate rules first

**Expected Output:**
- If rules exist: Dropdown shows generated rules
- If no rules: Warning message appears

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 5.3: Run Rules - Select Rules and Execute
**Action:**
1. Select 2-3 rules from dropdown
2. Click "▶️ Run Selected Rules" button

**Expected Output:**
- Status: "Executing DQ rules..."
- Progress bar appears
- After 10-30 seconds: "✅ Rules execution completed"
- Results table shows:
  - Rule Name
  - Issues Found (number)
  - Sample Violations
  - Status

**Status:** [ ] PASS [ ] FAIL  
**Execution Time:** _______ seconds  
**Issues Found:** _______ issues  
**Notes:** _______________

---

### TEST 5.4: Clear Results Button
**Action:**
1. Click "🗑️ Clear Results" button

**Expected Output:**
- Results disappear
- Status resets to ready

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 5.5: Manual Issue Input - JSON Format
**Action:**
1. Scroll to "Manual Issue Input" section
2. Enter JSON:
```json
[
  {
    "issue_id": "TEST_001",
    "description": "Missing customer names",
    "affected_records": 150,
    "severity": "high"
  }
]
```
3. Click "📥 Load Issues"

**Expected Output:**
- Success message: "✅ Loaded 1 issues"
- Issues appear in session state

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 5.6: Group Issues and Generate Strategies
**Action:**
1. After running rules (TEST 5.3), click "🔬 Group Issues & Generate Remediation Strategies"

**Expected Output:**
- Status: "🔬 Analyzing issues and generating remediation strategies..."
- Progress messages:
  - "Grouping similar issues..."
  - "Generating fixes for group X..."
- After 30-60 seconds: "✅ Remediation strategies generated"
- Shows grouped issues with fix strategies

**Status:** [ ] PASS [ ] FAIL  
**Execution Time:** _______ seconds  
**Groups Created:** _______ groups  
**Strategies Generated:** _______ strategies  
**Notes:** _______________

---

### TEST 5.7: View Grouped Issues
**Action:**
1. After grouping, check "Grouped Issues & Remediation Strategies" section
2. Expand each group

**Expected Output:**
- Each group shows:
  - Group title (e.g., "Group 1: Completeness Issues")
  - Number of issues in group
  - List of issues
  - Top 3 remediation strategies ranked by confidence

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 5.8: Approve Fix Strategy
**Action:**
1. Find a fix strategy with high confidence (>80%)
2. Click "✅ Approve Fix X for Group Y"

**Expected Output:**
- Success message: "Approved fix strategy X"
- Strategy marked as approved (green checkmark)
- "Send to Remediator" button appears

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 5.9: Reject Fix Strategy
**Action:**
1. Find another fix strategy
2. Click "❌ Reject Fix X"

**Expected Output:**
- Strategy marked as rejected (red X)
- Reason field appears (optional)

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 5.10: Send to Remediator Button
**Action:**
1. After approving at least one fix, click "🚀 Send Approved Fixes to Remediator"

**Expected Output:**
- Success message: "✅ Sent X approved fixes to Remediator"
- App navigates to Remediator tab

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

## PHASE 6: Remediator Agent Tests

### TEST 6.1: Navigate to Remediator Tab
**Action:**
1. Click "🔧 Remediator" tab

**Expected Output:**
- Header: "🔧 Remediator Agent"
- Subheader: "Execute approved remediation strategies safely"
- Warning box about Human-in-the-Loop

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 6.2: Check Approved Fixes Loaded
**Action:**
1. Check if approved fixes from Treatment agent are loaded
2. Look for "Approved Remediation Strategies" section

**Expected Output:**
- Shows list of approved fixes
- Each fix has:
  - Group name
  - Fix description
  - Confidence score
  - Affected records

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 6.3: Dry Run Mode - Enable
**Action:**
1. Find "Dry Run Mode" checkbox
2. Check it

**Expected Output:**
- Checkbox checked
- Info message: "Dry run will simulate changes without modifying data"

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 6.4: Select Fix to Execute
**Action:**
1. Select first approved fix from dropdown
2. Review fix details

**Expected Output:**
- Fix details displayed:
  - SQL query
  - Estimated affected records
  - Rollback query

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 6.5: Run Dry Run
**Action:**
1. With dry run enabled and fix selected
2. Click "🔍 Run Dry Run"

**Expected Output:**
- Status: "Running dry run..."
- After 5-15 seconds: "✅ Dry run completed"
- Shows:
  - Records that would be affected
  - Sample changes (before/after)
  - No actual changes made to database

**Status:** [ ] PASS [ ] FAIL  
**Execution Time:** _______ seconds  
**Notes:** _______________

---

### TEST 6.6: Cancel Fix
**Action:**
1. Click "❌ Cancel Fix" button

**Expected Output:**
- Fix selection cleared
- Returns to initial state

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 6.7: Execute Fix (WITH CAUTION - Modifies Data)
**Action:**
⚠️ **CAUTION:** This will modify your BigQuery data!

1. Select a safe fix (e.g., one that adds default values to nulls)
2. Disable dry run mode
3. Check "I understand this will modify production data"
4. Click "⚡ Execute Fix"

**Expected Output:**
- Confirmation dialog appears
- After confirming:
  - Status: "Executing fix..."
  - Progress messages
  - After 10-30 seconds: "✅ Fix executed successfully"
  - Shows:
    - Records modified
    - Rollback script saved
    - Execution log

**Status:** [ ] PASS [ ] FAIL [ ] SKIPPED  
**Execution Time:** _______ seconds  
**Records Modified:** _______ records  
**Notes:** _______________

---

### TEST 6.8: Verify Rollback Script Generated
**Action:**
1. After executing a fix, check if rollback script was saved
2. Look for "Rollback Script" section

**Expected Output:**
- Rollback SQL query displayed
- "📥 Download Rollback Script" button available
- Can click to download .sql file

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 6.9: Execute Another Fix Button
**Action:**
1. Click "🔄 Execute Another Fix"

**Expected Output:**
- Resets to initial state
- Can select another fix to execute

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

## PHASE 7: Metrics Agent Tests

### TEST 7.1: Navigate to Metrics Tab
**Action:**
1. Click "📊 Metrics" tab

**Expected Output:**
- Header: "📊 Metrics Agent"
- Subheader: "Calculate Cost of Inaction (COI) for DQ issues"
- Two modes: Individual Issue Analysis, Bulk Analysis

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 7.2: Individual Issue Analysis - Enter Issue
**Action:**
1. Select "Individual Issue Analysis" mode
2. Fill in form:
   - Issue Description: "Missing customer phone numbers"
   - Affected Records: 500
   - Severity: "high"
   - DQ Dimension: "Completeness"

**Expected Output:**
- All fields accept input
- Help text appears for each field

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 7.3: Generate Metrics Dashboard
**Action:**
1. Click "📊 Generate Metrics Dashboard"

**Expected Output:**
- Status: "🔬 Calculating Cost of Inaction..."
- After 10-30 seconds: "✅ Metrics calculated"
- Dashboard displays:
  - COI value (e.g., "£25,000/year")
  - Risk score
  - Business impact description
  - Compliance impact
  - Recommended action

**Status:** [ ] PASS [ ] FAIL  
**Execution Time:** _______ seconds  
**COI Calculated:** £_______ / year  
**Notes:** _______________

---

### TEST 7.4: Metrics Dashboard - Visualizations
**Action:**
1. After metrics generated, scroll through dashboard
2. Check for charts

**Expected Output:**
- COI breakdown chart (Plotly)
- Risk level gauge
- Timeline projection
- All interactive (hover for details)

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 7.5: Export Metrics Report
**Action:**
1. Look for "📥 Export Report" button
2. Click it

**Expected Output:**
- Downloads `metrics_report_YYYYMMDD_HHMMSS.json`
- File contains all metrics data

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 7.6: Bulk Analysis - Upload CSV
**Action:**
1. Select "Bulk Analysis" mode
2. Click "Browse files" to upload CSV
3. Upload a CSV with columns: issue_description, affected_records, severity

**Expected Output:**
- File uploads successfully
- Shows preview of data (first 5 rows)
- "Run Bulk Analysis" button appears

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 7.7: Run Bulk Analysis
**Action:**
1. Click "🚀 Run Bulk Analysis"

**Expected Output:**
- Progress bar: "Analyzing issue 1/X..."
- After 30-60 seconds: "✅ Bulk analysis completed"
- Summary table shows COI for each issue
- Total COI across all issues
- Priority ranking

**Status:** [ ] PASS [ ] FAIL  
**Execution Time:** _______ seconds  
**Issues Analyzed:** _______ issues  
**Total COI:** £_______ / year  
**Notes:** _______________

---

### TEST 7.8: Bulk Analysis - Download Results
**Action:**
1. Click "📥 Download Results" button

**Expected Output:**
- Downloads `bulk_metrics_YYYYMMDD.csv`
- CSV contains all issues with COI calculations

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

## PHASE 8: Advanced Settings Tests

### TEST 8.1: Navigate to Advanced Settings Tab
**Action:**
1. Click "⚙️ Advanced Settings" tab

**Expected Output:**
- Header: "⚙️ Advanced Settings"
- Multiple configuration sections

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 8.2: Per-Agent Model Configuration
**Action:**
1. Find "Per-Agent Model Configuration" section
2. Change Identifier Agent model to "gemini-2.0-pro"

**Expected Output:**
- Dropdown changes
- Info message about model selection

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 8.3: Debug Mode Toggle
**Action:**
1. Find "Debug Mode" toggle
2. Enable it

**Expected Output:**
- Toggle switches on
- Info: "Debug logs will be displayed in agent outputs"

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 8.4: Knowledge Bank Settings
**Action:**
1. Scroll to "Knowledge Bank" section
2. Check current status

**Expected Output:**
- Shows path to knowledge_bank.json
- Number of entries
- Last updated timestamp

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 8.5: Add Knowledge Bank Entry
**Action:**
1. Fill in:
   - Key: "test_entry"
   - Value: "This is a test entry"
2. Click "➕ Add Entry"

**Expected Output:**
- Success message: "✅ Entry added"
- Entry appears in knowledge bank list

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 8.6: Delete Knowledge Bank Entry
**Action:**
1. Find the test entry added above
2. Click "🗑️" delete button

**Expected Output:**
- Entry removed from list
- Success message (optional)

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 8.7: System Information Display
**Action:**
1. Scroll to "System Information" section
2. Review displayed info

**Expected Output:**
- Shows:
  - Python version
  - Streamlit version
  - Google ADK version
  - GCP project ID
  - BigQuery dataset
  - Environment type

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 8.8: Clear All Session Data
**Action:**
1. Find "🗑️ Clear All Session Data" button
2. Click it

**Expected Output:**
- Confirmation dialog
- After confirming: "All session data cleared"
- App resets to initial state

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

## PHASE 9: End-to-End Workflow Tests

### TEST 9.1: Complete Full Workflow (1 Table)
**Action:**
1. Go to Orchestrator tab
2. Select "🚀 Full Automated Workflow"
3. Select table: "policies_week1"
4. Disable auto-approve
5. Click "🚀 Start Full Workflow"

**Expected Output:**
- Workflow executes through all phases:
  1. Identifier: Generates rules (30-60s)
  2. Identifier: Executes rules (10-20s)
  3. Treatment: Analyzes issues and suggests fixes (30-60s)
  4. Treatment: Requests human approval (WAIT)
  5. (After approval) Remediator: Executes fixes (10-30s)
  6. Metrics: Calculates COI (10-20s)
  7. Shows executive summary

**Total Expected Time:** 2-4 minutes (excluding human approval time)

**Status:** [ ] PASS [ ] FAIL  
**Total Time:** _______ minutes  
**Notes:** _______________

---

### TEST 9.2: Complete Workflow - Verify Each Phase Output
**Action:**
1. After workflow completes, review "📋 Workflow Results" section
2. Check Agent Debate logs

**Expected Output:**
- Shows output from each agent
- Agent Debate Mode shows:
  - Orchestrator thoughts
  - Identifier reasoning
  - Treatment analysis
  - Remediator execution log
  - Metrics calculations

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 9.3: Manual Workflow - Identifier → Treatment
**Action:**
1. Go to Identifier tab
2. Generate rules for "policies_week2"
3. Click "▶️ Go to Treatment Agent"
4. Run generated rules
5. Group issues and generate strategies

**Expected Output:**
- Seamless navigation between tabs
- Data persists across tabs
- Treatment successfully receives rules from Identifier

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 9.4: Manual Workflow - Treatment → Remediator
**Action:**
1. Continue from TEST 9.3
2. Approve at least one fix strategy
3. Click "🚀 Send to Remediator"
4. In Remediator tab, execute fix (dry run)

**Expected Output:**
- Approved fixes successfully transferred
- Remediator can execute/dry-run the fix
- Rollback script generated

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 9.5: Manual Workflow - Generate Metrics After Fix
**Action:**
1. Go to Metrics tab
2. Select "Individual Issue Analysis"
3. Enter issue from previous workflow
4. Generate metrics

**Expected Output:**
- Metrics calculated showing cost savings after fix
- COI reflects remediation status

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 9.6: Cache Persistence Test
**Action:**
1. Go to Identifier tab
2. Generate rules for "policies_week3" with Dataplex
3. Wait for completion
4. Close Streamlit app (Ctrl+C in terminal)
5. Restart app: `streamlit run streamlit_app/app.py`
6. Go to Identifier tab
7. Check cache status

**Expected Output:**
- After restart, cache shows rules for "policies_week3"
- Can load cached rules instead of regenerating

**Status:** [ ] PASS [ ] FAIL  
**Notes:** _______________

---

### TEST 9.7: Error Handling - Network Failure Simulation
**Action:**
⚠️ **OPTIONAL:** Only if you want to test error handling

1. Disconnect internet/wifi
2. Try to generate DQ rules
3. Reconnect internet

**Expected Output:**
- Error message displayed: "Connection error..."
- Does NOT crash the app
- After reconnection, can retry successfully

**Status:** [ ] PASS [ ] FAIL [ ] SKIPPED  
**Notes:** _______________

---

### TEST 9.8: Large Dataset Test (4 Tables, Dataplex)
**Action:**
⚠️ **CAUTION:** This takes 4-6 minutes!

1. Go to Identifier tab
2. Select ALL 4 tables
3. Enable Dataplex profiling
4. Click "🚀 Generate DQ Rules"

**Expected Output:**
- Progress messages for each table
- Dataplex runs 4 times (60s each = 4 minutes)
- Total time: 4-6 minutes
- Successfully generates rules for all 4 tables
- No timeouts or crashes

**Status:** [ ] PASS [ ] FAIL [ ] SKIPPED  
**Total Time:** _______ minutes  
**Rules Generated:** _______ rules  
**Notes:** _______________

---

## 📊 TEST SUMMARY

### Overall Statistics
- **Total Tests:** 98
- **Tests Passed:** _______
- **Tests Failed:** _______
- **Tests Skipped:** _______
- **Pass Rate:** _______%

### Critical Issues Found
1. _______________________________________
2. _______________________________________
3. _______________________________________

### Minor Issues Found
1. _______________________________________
2. _______________________________________
3. _______________________________________

### Performance Notes
- **Fastest operation:** _____________ (____s)
- **Slowest operation:** _____________ (____s)
- **Average Dataplex scan time:** _______s
- **Average rule generation time:** _______s

### Browser Compatibility (if tested)
- [ ] Chrome: PASS / FAIL
- [ ] Firefox: PASS / FAIL
- [ ] Edge: PASS / FAIL
- [ ] Safari: PASS / FAIL

---

## 🎯 CONCLUSION

**Application Status:** [ ] PRODUCTION READY [ ] NEEDS FIXES [ ] MAJOR ISSUES

**Tester Comments:**
_____________________________________________
_____________________________________________
_____________________________________________

**Sign-off:**
- Tester: ________________
- Date: ________________
- Environment: ________________

---

## 📝 NOTES FOR NAYONE DEPLOYMENT

After completing local tests, these features MUST be retested in NayaOne:
- [ ] GCP authentication (gcloud auth login)
- [ ] Dataplex API access (may need permissions)
- [ ] BigQuery connectivity
- [ ] Streamlit app launch
- [ ] All agent workflows

**Expected differences in NayaOne:**
1. Linux environment (vs Windows)
2. Shared GCP project
3. Browser-based VSCode
4. Network restrictions

**Refer to:** `NAYONE_COMPATIBILITY_CHECK.md` for NayaOne-specific setup.

---

**End of Test Document**
