# Data Quality Management System - Implementation Plan

## 🎯 **OVERVIEW**

This is a step-by-step implementation plan for building the DQ Management System using the existing ADK data science sample as foundation. Each phase has clear deliverables and verification steps.

**Timeline:** ~20-24 hours of development (2 days)
**Approach:** Incremental development with verification at each step
**Architecture Base:** Google ADK multi-agent framework (existing codebase)

---

## 📋 **PREREQUISITES CHECKLIST**

Before starting, verify you have:
- [ ] Python 3.12+ installed
- [ ] Google Cloud account with billing enabled
- [ ] Git installed
- [ ] PowerShell terminal access
- [ ] Text editor (VS Code recommended)

**Note:** We'll use Python venv (built-in) instead of `uv` for better cross-laptop compatibility.

---

# PHASE 0: Environment Setup & Verification (2-3 hours)

## Step 0.1: GCP Authentication & Project Setup

**Goal:** Connect local environment to Google Cloud Platform

**Actions:**
```powershell
# Install Google Cloud SDK (if not already installed)
# Download from: https://cloud.google.com/sdk/docs/install

# Authenticate to GCP
gcloud auth login

# Set your project (replace with your project ID)
gcloud config set project YOUR_PROJECT_ID

# Verify authentication
gcloud auth list

# Set up application default credentials (for ADK)
gcloud auth application-default login

# Verify project
gcloud config get-value project
```

**Verification:**
- ✅ `gcloud auth list` shows your account with asterisk (*)
- ✅ `gcloud config get-value project` returns your project ID
- ✅ Application default credentials stored in `~/.config/gcloud/`

**Deliverable:** Authenticated GCP connection

---

## Step 0.2: Enable Required GCP APIs

**Goal:** Activate all necessary Google Cloud services

**Actions:**
```powershell
# Enable required APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable dataplex.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

# Verify enabled services
gcloud services list --enabled | Select-String -Pattern "bigquery|aiplatform|dataplex"
```

**Verification:**
- ✅ All 5 APIs show as "ENABLED"
- ✅ No error messages during enable commands

**Deliverable:** All required APIs enabled

---

## Step 0.3: Verify Existing BaNCS Data in BigQuery

**Goal:** Confirm synthetic data is accessible and understand structure

**Actions:**
```powershell
# List datasets in your project
gcloud bigquery ls --project=YOUR_PROJECT_ID

# List tables in your dataset (replace DATASET_ID)
gcloud bigquery ls YOUR_DATASET_ID

# Get table schema for one table
bq show --schema --format=prettyjson YOUR_DATASET_ID.policies_week1

# Query sample data
bq query --use_legacy_sql=false "SELECT * FROM \`YOUR_PROJECT_ID.YOUR_DATASET_ID.policies_week1\` LIMIT 5"
```

**Verification:**
- ✅ Can list datasets and tables
- ✅ Week-wise tables visible (week1, week2, week3, week4)
- ✅ Schema shows expected columns (policy_id, customer_name, date_of_birth, etc.)
- ✅ Sample data returns rows with planted issues

**Deliverable:** Document table structure in notes:
```
Dataset: [DATASET_ID]
Tables:
- policies_week1: [X] rows
- policies_week2: [X] rows
- policies_week3: [X] rows
- policies_week4: [X] rows

Key columns: policy_id, customer_name, date_of_birth, status, premium, policy_value, ...
```

---

## Step 0.4: Test Dataplex API Access

**Goal:** Verify Dataplex is accessible and understand API structure

**Actions:**
```powershell
# List Dataplex lakes (if any exist)
gcloud dataplex lakes list --project=YOUR_PROJECT_ID --location=YOUR_REGION

# Check if Dataplex data scans exist
gcloud dataplex datascans list --project=YOUR_PROJECT_ID --location=YOUR_REGION

# If no scans exist, note that you'll need to create them
```

**Verification:**
- ✅ Commands execute without authentication errors
- ✅ Document existing Dataplex setup (or note: "Need to create from scratch")

**Deliverable:** Dataplex access confirmed + inventory of existing resources

---

## Step 0.5: Create Virtual Environment & Install Dependencies

**Goal:** Set up Python virtual environment with all dependencies (for cross-laptop compatibility)

**Actions:**
```powershell
# Navigate to project directory
cd "c:\Users\mylil\Desktop\google adk-samples main python-agents_data-science"

# Create virtual environment (if not exists)
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install core dependencies
pip install google-adk>=1.14
pip install google-cloud-aiplatform[adk,agent-engines]>=1.93.0
pip install google-cloud-bigquery
pip install google-cloud-dataplex
pip install streamlit
pip install plotly
pip install altair
pip install pandas
pip install numpy
pip install scikit-learn
pip install python-dotenv

# Verify ADK installation
python -c "import google.adk; print(google.adk.__version__)"

# Verify key packages
python -c "import google.cloud.bigquery; import google.cloud.aiplatform; import google.cloud.dataplex; print('Packages OK')"
```

**IMPORTANT:** Always activate venv before running commands:
```powershell
.venv\Scripts\Activate.ps1
```

**Verification:**
- ✅ Virtual environment activates (prompt shows `(.venv)`)
- ✅ All packages install without errors
- ✅ ADK version prints (e.g., `1.14` or higher)
- ✅ Import statements succeed

**Deliverable:** Working Python environment with ADK in venv

---

## Step 0.6: Configure .env File

**Goal:** Set up environment variables for the project

**Actions:**
```powershell
# Copy example .env file
Copy-Item .env.example .env

# Edit .env file with your values
# Use notepad or VS Code
notepad .env
```

**Configuration (update these values):**
```dotenv
# Model backend
GOOGLE_GENAI_USE_VERTEXAI=1

# GCP settings
GOOGLE_CLOUD_PROJECT=your-actual-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# BigQuery settings
BQ_COMPUTE_PROJECT_ID=your-actual-project-id
BQ_DATA_PROJECT_ID=your-actual-project-id
BQ_DATASET_ID=your-actual-dataset-id

# NL2SQL method
BQ_NL2SQL_METHOD=BASELINE

# Models (use latest available)
ROOT_AGENT_MODEL=gemini-2.0-flash
ANALYTICS_AGENT_MODEL=gemini-2.0-flash
BIGQUERY_AGENT_MODEL=gemini-2.0-flash
BASELINE_NL2SQL_MODEL=gemini-2.0-flash

# Dataset config (we'll create this)
DATASET_CONFIG_FILE=bancs_dataset_config.json

# Leave these empty for now (will set up later)
BQML_RAG_CORPUS_NAME=
CODE_INTERPRETER_EXTENSION_NAME=
```

**Verification:**
- ✅ `.env` file exists in project root
- ✅ All `YOUR_VALUE_HERE` placeholders replaced with actual values
- ✅ No syntax errors in file

**Deliverable:** Configured `.env` file

---

## Step 0.7: Test Basic ADK Functionality

**Goal:** Verify ADK can connect to GCP and run simple agent

**Actions:**
```powershell
# Create test script
New-Item -Path "test_setup.py" -ItemType File
```

**test_setup.py:**
```python
import os
from dotenv import load_dotenv
from google.cloud import bigquery
from google.genai import Client

# Load environment
load_dotenv()

# Test 1: BigQuery connection
print("Test 1: BigQuery Connection")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
client = bigquery.Client(project=project_id)
print(f"✅ Connected to BigQuery project: {project_id}")

# Test 2: List datasets
print("\nTest 2: List Datasets")
datasets = list(client.list_datasets())
if datasets:
    for dataset in datasets:
        print(f"  - {dataset.dataset_id}")
else:
    print("  No datasets found")

# Test 3: Vertex AI connection
print("\nTest 3: Vertex AI / Gemini Connection")
location = os.getenv("GOOGLE_CLOUD_LOCATION")
genai_client = Client(
    vertexai=True,
    project=project_id,
    location=location
)
print(f"✅ Gemini client initialized for {location}")

# Test 4: Simple Gemini call
print("\nTest 4: Test Gemini API")
response = genai_client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say 'Setup test successful!' in one sentence."
)
print(f"✅ Gemini Response: {response.text}")

print("\n🎉 All setup tests passed!")
```

**Run test:**
```powershell
# Activate venv first!
.venv\Scripts\Activate.ps1

# Run test
python test_setup.py
```

**Verification:**
- ✅ All 4 tests print success messages
- ✅ BigQuery connection works
- ✅ Datasets list correctly
- ✅ Gemini API responds

**Deliverable:** Verified working connection to all GCP services

---

# PHASE 1: Data Foundation (2-3 hours)

## Step 1.1: Create Dataset Configuration

**Goal:** Configure how agents access BaNCS data (following ADK pattern)

**Actions:**
```powershell
New-Item -Path "bancs_dataset_config.json" -ItemType File
```

**bancs_dataset_config.json:**
```json
{
  "datasets": [
    {
      "type": "bigquery",
      "name": "bancs_dq_dataset",
      "description": "BaNCS Life & Pensions synthetic data for DQ validation. Contains 4 weeks of policy data with planted data quality issues across dimensions: Completeness, Accuracy, Timeliness, Conformity, Uniqueness.",
      "tables": [
        "policies_week1",
        "policies_week2",
        "policies_week3",
        "policies_week4"
      ]
    }
  ]
}
```

**Update .env:**
```dotenv
DATASET_CONFIG_FILE=bancs_dataset_config.json
```

**Verification:**
- ✅ JSON file is valid (no syntax errors)
- ✅ Table names match actual BigQuery tables
- ✅ `.env` points to this config file

**Deliverable:** Dataset configuration file

---

## Step 1.2: Test BigQuery Schema Introspection

**Goal:** Verify we can programmatically inspect BaNCS table structure

**Actions:**
```powershell
New-Item -Path "test_schema.py" -ItemType File
```

**test_schema.py:**
```python
import os
import json
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

project_id = os.getenv("BQ_DATA_PROJECT_ID")
dataset_id = os.getenv("BQ_DATASET_ID")

client = bigquery.Client(project=project_id)
dataset_ref = bigquery.DatasetReference(project_id, dataset_id)

print(f"📊 Inspecting schema for dataset: {dataset_id}\n")

# Load config
with open("bancs_dataset_config.json") as f:
    config = json.load(f)

tables_to_check = config["datasets"][0]["tables"]

for table_name in tables_to_check:
    print(f"Table: {table_name}")
    table_ref = dataset_ref.table(table_name)
    
    try:
        table = client.get_table(table_ref)
        print(f"  Rows: {table.num_rows}")
        print(f"  Columns: {len(table.schema)}")
        print(f"  Schema:")
        for field in table.schema[:10]:  # First 10 columns
            print(f"    - {field.name}: {field.field_type}")
        print()
    except Exception as e:
        print(f"  ❌ Error: {e}\n")

print("✅ Schema introspection test complete")
```

**Run:**
```powershell
# Activate venv first!
.venv\Scripts\Activate.ps1

# Run test
python test_schema.py
```

**Verification:**
- ✅ All 4 week tables found
- ✅ Row counts displayed
- ✅ Schema fields printed correctly

**Deliverable:** Confirmed ability to programmatically access table metadata

---

## Step 1.3: Create Sample DQ Rule (Test Data Quality Detection)

**Goal:** Verify we can run SQL-based DQ rules on BaNCS data

**Actions:**
```powershell
New-Item -Path "test_dq_rule.py" -ItemType File
```

**test_dq_rule.py:**
```python
import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

project_id = os.getenv("BQ_DATA_PROJECT_ID")
dataset_id = os.getenv("BQ_DATASET_ID")

client = bigquery.Client(project=project_id)

# Test DQ Rule: Find future dates of birth
test_rule = f"""
SELECT 
    policy_id,
    customer_name,
    date_of_birth,
    'Future DOB' as issue_type,
    'Accuracy' as dq_dimension
FROM `{project_id}.{dataset_id}.policies_week1`
WHERE date_of_birth > CURRENT_DATE()
LIMIT 10
"""

print("🔍 Testing DQ Rule: Future Date of Birth\n")
print(f"SQL:\n{test_rule}\n")

results = client.query(test_rule).result()
issue_count = 0

print("Issues Found:")
for row in results:
    issue_count += 1
    print(f"  - Policy {row.policy_id}: DOB = {row.date_of_birth}")

if issue_count > 0:
    print(f"\n✅ Test passed: Found {issue_count} DQ issues (as expected in synthetic data)")
else:
    print("\n⚠️  No issues found (check if data has planted errors)")
```

**Run:**
```powershell
# Activate venv first!
.venv\Scripts\Activate.ps1

# Run test
python test_dq_rule.py
```

**Verification:**
- ✅ Query executes successfully
- ✅ At least some DQ issues found (proving data has problems)
- ✅ Results formatted correctly

**Deliverable:** Proof that SQL-based DQ rules work on BaNCS data

---

# PHASE 2: Streamlit Foundation (2-3 hours)

## Step 2.1: Create Basic Streamlit App Structure

**Goal:** Set up multi-page Streamlit app with agent tabs

**Actions:**
```powershell
# Activate venv first!
.venv\Scripts\Activate.ps1

# Streamlit already installed in Phase 0.5
# Create Streamlit app directory
New-Item -Path "streamlit_app" -ItemType Directory
New-Item -Path "streamlit_app\pages" -ItemType Directory

# Create main app file
New-Item -Path "streamlit_app\app.py" -ItemType File
```

**streamlit_app/app.py:**
```python
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="DQ Management System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for settings
with st.sidebar:
    st.title("⚙️ Settings")
    
    # GCP Configuration
    st.subheader("GCP Configuration")
    project_id = st.text_input(
        "Project ID", 
        value=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
        help="Your Google Cloud Project ID"
    )
    
    dataset_id = st.text_input(
        "Dataset ID",
        value=os.getenv("BQ_DATASET_ID", ""),
        help="BigQuery dataset containing BaNCS data"
    )
    
    # Model Selection
    st.subheader("Model Configuration")
    global_model = st.selectbox(
        "Global Model",
        ["gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro"],
        help="Default model for all agents"
    )
    
    st.divider()
    st.info("💡 Configure per-agent models in Settings tab")

# Main app header
st.title("🔍 Data Quality Management System")
st.markdown("**Autonomous DQ Detection, Treatment & Remediation for BaNCS Data**")

# Create tabs for agents
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Identifier", 
    "💊 Treatment", 
    "🔧 Remediator", 
    "📊 Metrics",
    "⚙️ Advanced Settings"
])

with tab1:
    st.header("Identifier Agent")
    st.info("🚧 Coming soon: DQ rule detection and identification")
    
with tab2:
    st.header("Treatment Agent")
    st.info("🚧 Coming soon: Issue analysis and treatment suggestions")
    
with tab3:
    st.header("Remediator Agent")
    st.info("🚧 Coming soon: Fix execution and validation")
    
with tab4:
    st.header("Metrics Agent")
    st.info("🚧 Coming soon: Dashboards and Cost of Inaction analysis")
    
with tab5:
    st.header("Advanced Settings")
    st.info("🚧 Coming soon: Knowledge Bank, per-agent models, rate limits")

# Footer
st.divider()
st.caption("Built with ADK Multi-Agent Framework | Lloyd's Banking Group Hackathon 2025")
```

**Run Streamlit:**
```powershell
# Activate venv first!
.venv\Scripts\Activate.ps1

# Run Streamlit
streamlit run streamlit_app\app.py
```

**Verification:**
- ✅ Streamlit opens in browser (http://localhost:8501)
- ✅ 5 tabs visible
- ✅ Sidebar shows settings with model options: gemini-2.0-flash, gemini-2.0-pro, gemini-1.5-pro
- ✅ GCP project/dataset values pre-filled from .env

**Deliverable:** Working Streamlit app skeleton

---

## Step 2.2: Add GCP Connection Test to Streamlit

**Goal:** Allow users to test GCP connection from UI

**Actions:**
Update `streamlit_app/app.py` - add to sidebar:

```python
# Add after Model Configuration in sidebar
st.divider()
st.subheader("Connection Test")

if st.button("🔌 Test GCP Connection"):
    with st.spinner("Testing connections..."):
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=project_id)
            datasets = list(client.list_datasets())
            
            st.success(f"✅ Connected to project: {project_id}")
            st.success(f"✅ Found {len(datasets)} datasets")
            
            # Try to access specific dataset
            dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
            tables = list(client.list_tables(dataset_ref))
            st.success(f"✅ Dataset '{dataset_id}' has {len(tables)} tables")
            
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)}")
```

**Verification:**
- ✅ Button appears in sidebar
- ✅ Clicking button shows success messages
- ✅ Table count matches expected (4 week tables)

**Deliverable:** UI-based GCP connection verification

---

# PHASE 3: Identifier Agent - Core (4-5 hours)

## Step 3.1: Create Identifier Agent Backend (ADK Pattern)

**Goal:** Build identifier agent following ADK multi-agent structure

**Actions:**
```powershell
# Create identifier agent directory structure
New-Item -Path "dq_agents" -ItemType Directory
New-Item -Path "dq_agents\identifier" -ItemType Directory
New-Item -Path "dq_agents\identifier\__init__.py" -ItemType File
New-Item -Path "dq_agents\identifier\agent.py" -ItemType File
New-Item -Path "dq_agents\identifier\tools.py" -ItemType File
New-Item -Path "dq_agents\identifier\prompts.py" -ItemType File
```

**dq_agents/identifier/prompts.py:**
```python
def return_instructions_identifier() -> str:
    return """
You are a Data Quality Identifier Agent specialized in detecting data quality issues.

Your responsibilities:
1. Analyze BigQuery table schemas and data
2. Generate SQL-based data quality rules
3. Categorize issues by DQ dimension: Completeness, Accuracy, Timeliness, Conformity, Uniqueness
4. Identify temporal inconsistencies (e.g., future dates, status changes)
5. Detect sensible rule violations (e.g., underage workers, negative values)

When generating DQ rules:
- Always use parameterized SQL with {table} placeholder
- Include clear descriptions of what the rule checks
- Assign appropriate severity: critical, high, medium, low
- Categorize by DQ dimension
- Return rules in JSON format

Example rule format:
{
  "rule_id": "DQ_001",
  "name": "future_dob_check",
  "description": "Date of birth cannot be in the future",
  "sql": "SELECT * FROM {table} WHERE date_of_birth > CURRENT_DATE()",
  "severity": "critical",
  "category": "Accuracy"
}
"""
```

**dq_agents/identifier/tools.py:**
```python
import os
from google.cloud import bigquery
from google.cloud import dataplex_v1
from google.adk.tools import ToolContext

def get_table_schema(
    table_name: str,
    tool_context: ToolContext
) -> str:
    """Get BigQuery table schema for DQ rule generation."""
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_name}"
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
    
    return str(schema_info)


def trigger_dataplex_scan(
    table_name: str,
    tool_context: ToolContext
) -> str:
    """Trigger Dataplex data quality and profiling scans on a BigQuery table."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    try:
        # Initialize Dataplex client
        # Note: In production, you'd create/trigger actual DataScan jobs
        # For hackathon, we'll return a simulated response
        result = {
            "status": "scan_triggered",
            "table": f"{project_id}.{dataset_id}.{table_name}",
            "scan_types": ["PROFILE", "DATA_QUALITY"],
            "message": "Dataplex scans initiated. Results will be available in 2-5 minutes.",
            "note": "Mock implementation - integrate real Dataplex DataScanServiceClient for production"
        }
        return str(result)
    except Exception as e:
        return f"Error triggering Dataplex scan: {str(e)}"


def execute_dq_rule(
    rule_sql: str,
    table_name: str,
    tool_context: ToolContext
) -> str:
    """Execute a DQ rule SQL query against BigQuery."""
    project_id = os.getenv("BQ_DATA_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    # Replace placeholder with actual table
    sql = rule_sql.replace("{table}", f"`{project_id}.{dataset_id}.{table_name}`")
    
    client = bigquery.Client(project=project_id)
    results = client.query(sql).result()
    
    issues = []
    for row in results:
        issues.append(dict(row))
    
    return {
        "issue_count": len(issues),
        "issues": issues[:100]  # Limit to first 100
    }
```

**dq_agents/identifier/agent.py:**
```python
import os
from google.adk.agents import LlmAgent
from google.genai import types
from .prompts import return_instructions_identifier
from .tools import get_table_schema, execute_dq_rule, trigger_dataplex_scan

identifier_agent = LlmAgent(
    model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-flash"),
    name="identifier_agent",
    instruction=return_instructions_identifier(),
    tools=[get_table_schema, execute_dq_rule, trigger_dataplex_scan],
    generate_content_config=types.GenerateContentConfig(temperature=0.1)
)
```

**Verification:**
- ✅ Directory structure created
- ✅ Files have valid Python syntax
- ✅ Agent follows ADK pattern (similar to bigquery_agent in sample)

**Deliverable:** Identifier agent backend structure

---

## Step 3.2: Create Pre-existing Rules Mock Data

**Goal:** Create mock JSON file with sample DQ rules from Collibra/Ataccama systems

**Actions:**
```powershell
# Create pre-existing rules directory
New-Item -Path "mock_data" -ItemType Directory
New-Item -Path "mock_data\pre_existing_rules.json" -ItemType File
```

**mock_data/pre_existing_rules.json:**
```json
[
  {
    "rule_id": "COL_001",
    "source": "collibra",
    "name": "DOB_future_check",
    "description": "Date of birth cannot be in the future",
    "sql": "SELECT * FROM {table} WHERE date_of_birth > CURRENT_DATE()",
    "severity": "critical",
    "category": "Accuracy",
    "dq_dimension": "Accuracy"
  },
  {
    "rule_id": "COL_002",
    "source": "collibra",
    "name": "premium_negative_check",
    "description": "Premium amount must be positive",
    "sql": "SELECT * FROM {table} WHERE premium < 0",
    "severity": "high",
    "category": "Validity",
    "dq_dimension": "Accuracy"
  },
  {
    "rule_id": "ATA_001",
    "source": "ataccama",
    "name": "policy_id_null_check",
    "description": "Policy ID must not be null",
    "sql": "SELECT * FROM {table} WHERE policy_id IS NULL",
    "severity": "critical",
    "category": "Completeness",
    "dq_dimension": "Completeness"
  },
  {
    "rule_id": "ATA_002",
    "source": "ataccama",
    "name": "policy_dates_consistency",
    "description": "Policy start date must be before end date",
    "sql": "SELECT * FROM {table} WHERE policy_start_date >= policy_end_date",
    "severity": "high",
    "category": "Consistency",
    "dq_dimension": "Conformity"
  },
  {
    "rule_id": "ATA_003",
    "source": "ataccama",
    "name": "ni_number_format_check",
    "description": "NI number must follow UK format",
    "sql": "SELECT * FROM {table} WHERE ni_number IS NOT NULL AND NOT REGEXP_CONTAINS(ni_number, r'^[A-Z]{2}[0-9]{6}[A-D]$')",
    "severity": "medium",
    "category": "Format",
    "dq_dimension": "Conformity"
  }
]
```

**Verification:**
- ✅ JSON file created with 5 mock rules
- ✅ Rules from 2 sources: Collibra (2) and Ataccama (3)
- ✅ Covers multiple DQ dimensions: Accuracy, Completeness, Conformity

**Deliverable:** Pre-existing rules mock data

---

## Step 3.3: Test Identifier Agent (Command Line)

**Goal:** Verify agent works before integrating with Streamlit

**Actions:**
```powershell
New-Item -Path "test_identifier_agent.py" -ItemType File
```

**test_identifier_agent.py:**
```python
import asyncio
from dotenv import load_dotenv
from dq_agents.identifier.agent import identifier_agent

load_dotenv()

async def test_identifier():
    print("🔍 Testing Identifier Agent\n")
    
    # Test 1: Get schema
    print("Test 1: Get table schema")
    response1 = await identifier_agent.send_message(
        "Get the schema for table 'policies_week1' and summarize the columns"
    )
    print(f"Response: {response1.text[:500]}...\n")
    
    # Test 2: Generate DQ rule
    print("Test 2: Generate DQ rule for future dates")
    response2 = await identifier_agent.send_message(
        """Based on the schema, generate a DQ rule that checks for 
        date_of_birth values in the future. Return it in JSON format."""
    )
    print(f"Response: {response2.text}\n")
    
    print("✅ Identifier agent tests complete")

if __name__ == "__main__":
    asyncio.run(test_identifier())
```

**Run:**
```powershell
# Activate venv first!
.venv\Scripts\Activate.ps1

# Run test
python test_identifier_agent.py
```

**Verification:**
- ✅ Agent responds to schema request
- ✅ Agent generates DQ rule in JSON format
- ✅ No errors in tool execution

**Deliverable:** Working identifier agent (command line)

---

## Step 3.4: Integrate Identifier Agent with Streamlit

**Goal:** Connect agent to UI for user interaction

**Actions:**
Update `streamlit_app/app.py` - replace "Identifier" tab content:

```python
with tab1:
    st.header("🔍 Identifier Agent")
    st.markdown("Detect data quality issues using AI-generated rules + Dataplex")
    
    # Table selection
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_tables = st.multiselect(
            "Select tables to analyze",
            ["policies_week1", "policies_week2", "policies_week3", "policies_week4"],
            default=["policies_week1"]
        )
    
    with col2:
        scan_mode = st.radio(
            "Scan Mode",
            ["Full Scan", "Incremental"]
        )
    
    # Generate rules button
    if st.button("🎯 Generate DQ Rules", key="gen_rules"):
        if not selected_tables:
            st.warning("Please select at least one table")
        else:
            with st.spinner("🤖 AI is analyzing schema and generating rules..."):
                # Import agent
                import asyncio
                from dq_agents.identifier.agent import identifier_agent
                
                # Get schema
                prompt = f"Analyze the schema for table '{selected_tables[0]}' and generate 5 data quality rules covering different DQ dimensions (Completeness, Accuracy, Timeliness, Conformity, Uniqueness). Return as JSON array."
                
                async def run_agent():
                    response = await identifier_agent.send_message(prompt)
                    return response.text
                
                result = asyncio.run(run_agent())
                
                st.success("✅ Rules generated!")
                st.code(result, language="json")
    
    # Placeholder for rule display
    st.divider()
    st.subheader("Generated Rules")
    st.info("Click 'Generate DQ Rules' to see AI-generated rules")
```

**Verification:**
- ✅ Button appears in UI
- ✅ Clicking button shows spinner
- ✅ Agent generates rules (JSON displayed)
- ✅ No crashes or errors

**Deliverable:** Identifier agent integrated with Streamlit

---

# PHASE 4: Treatment Agent (3-4 hours)

## Step 4.1: Create Treatment Agent Backend

**Goal:** Build agent that suggests fixes for DQ issues

**Actions:**
```powershell
New-Item -Path "dq_agents\treatment" -ItemType Directory
New-Item -Path "dq_agents\treatment\__init__.py" -ItemType File
New-Item -Path "dq_agents\treatment\agent.py" -ItemType File
New-Item -Path "dq_agents\treatment\tools.py" -ItemType File
New-Item -Path "dq_agents\treatment\prompts.py" -ItemType File
```

**Follow same pattern as Identifier Agent**

**Key additions:**
- Knowledge Bank JSON file operations
- Fix suggestion ranking logic
- Root cause analysis prompts

**Deliverable:** Treatment agent backend

---

## Step 4.2: Create Knowledge Bank System

**Goal:** Implement JSON-based storage for historical fixes

**Actions:**
```powershell
New-Item -Path "knowledge_bank" -ItemType Directory
New-Item -Path "knowledge_bank\knowledge_bank.json" -ItemType File
New-Item -Path "knowledge_bank\kb_manager.py" -ItemType File
```

**knowledge_bank/knowledge_bank.json:**
```json
{
  "issue_patterns": {
    "DOB_future": {
      "pattern": "date_of_birth > CURRENT_DATE",
      "historical_fixes": [
        {
          "fix_id": "FIX_001",
          "action": "SET date_of_birth = NULL",
          "success_rate": 0.95,
          "approval_count": 3,
          "auto_approve": false
        }
      ]
    }
  }
}
```

**Deliverable:** Knowledge Bank storage system

---

## Step 4.3: Integrate Treatment Agent with Streamlit

**Goal:** UI for reviewing and approving fixes with drag-and-reorder interface

**Actions:**
```powershell
# Activate venv first!
.venv\Scripts\Activate.ps1

# Install streamlit-sortables for drag-and-reorder
pip install streamlit-sortables
```

Update Streamlit Treatment tab with:
- Issue display
- Top 3 fix suggestions
- **Drag-and-reorder interface using `streamlit-sortables`**
  - If library issues occur, fallback to manual priority input (1, 2, 3)
- Approval buttons

**Example drag-and-reorder code:**
```python
from streamlit_sortables import sort_items

# Display fix suggestions
fix_options = [
    "Fix 1: Replace with NULL",
    "Fix 2: Replace with median",
    "Fix 3: Delete row"
]

# Drag-and-reorder
sorted_fixes = sort_items(fix_options)
st.write("Your prioritized fixes:", sorted_fixes)
```

**Fallback (if streamlit-sortables fails):**
```python
# Manual priority selection
for i, fix in enumerate(fix_options):
    priority = st.number_input(f"Priority for {fix}", min_value=1, max_value=3, value=i+1, key=f"priority_{i}")
```

**Verification:**
- ✅ streamlit-sortables installed (or fallback ready)
- ✅ User can reorder fix priorities
- ✅ Approval buttons functional

**Deliverable:** Treatment agent UI with drag-and-reorder

---

# PHASE 5: Remediator Agent (2-3 hours)

## Step 5.1: Create Remediator Agent Backend

**Goal:** Execute approved fixes with validation

**Actions:**
```powershell
New-Item -Path "dq_agents\remediator" -ItemType Directory
# Follow ADK pattern
```

**Key features:**
- Dry run mode (preview changes)
- BigQuery UPDATE/DELETE execution
- Validation checks
- JIRA ticket generation (mock)

**Deliverable:** Remediator agent backend

---

## Step 5.2: Mock JIRA System

**Goal:** Simulate ticket creation for failed fixes

**Actions:**
```powershell
New-Item -Path "jira_mock" -ItemType Directory
New-Item -Path "jira_mock\jira_tickets.json" -ItemType File
New-Item -Path "jira_mock\ticket_manager.py" -ItemType File
```

**Deliverable:** JIRA mock system

---

## Step 5.3: Integrate Remediator with Streamlit

**Goal:** UI for executing fixes and viewing results

**Actions:**
Update Streamlit Remediator tab with:
- Dry run button
- Execute button
- Before/after comparison
- JIRA ticket display

**Deliverable:** Remediator UI

---

# PHASE 6: Metrics Agent (3-4 hours)

## Step 6.1: Implement Anomaly Detection

**Goal:** IsolationForest for outlier detection

**Actions:**
```python
# In metrics agent tools
from sklearn.ensemble import IsolationForest
import pandas as pd

def detect_anomalies(table_name: str) -> dict:
    # Load data from BigQuery
    # Identify numerical columns
    # Run IsolationForest
    # Return anomalies with scores
```

**Deliverable:** Anomaly detection function

---

## Step 6.2: Create Metrics Dashboard

**Goal:** Power BI-style visualizations

**Actions:**
```python
# Use Plotly/Altair for interactive charts
import plotly.express as px
import altair as alt

# Charts needed:
# - Issues by DQ dimension (bar chart)
# - Auto-fix rate (gauge)
# - Cost of Inaction (metric cards)
# - Remediation velocity (line chart)
# - Anomaly scores (scatter plot)
```

**Deliverable:** Interactive dashboard

---

## Step 6.3: Cost of Inaction Calculator

**Goal:** Financial impact analysis

**Actions:**
```python
def calculate_cost_of_inaction(issues_df, policy_values):
    affected_rows = len(issues_df)
    avg_policy_value = policy_values.mean()
    regulatory_risk_rate = 0.001  # 0.1%
    
    total_exposure = affected_rows * avg_policy_value
    monthly_coi = total_exposure * regulatory_risk_rate
    
    return {
        "total_exposure": total_exposure,
        "monthly_coi": monthly_coi,
        "annual_coi": monthly_coi * 12
    }
```

**Deliverable:** Cost calculator + display

---

## Step 6.4: Dynamic Storytelling

**Goal:** AI-generated narrative summaries

**Actions:**
```python
# Use Gemini to generate insights
def generate_narrative_summary(metrics):
    prompt = f"""
    Create an executive summary of this DQ analysis:
    - Issues Found: {metrics['issues']}
    - Auto-Fixed: {metrics['auto_fixed']}
    - Total Exposure: £{metrics['exposure']:,}
    
    Write 3 paragraphs...
    """
    # Call Gemini
    # Display in Streamlit
```

**Deliverable:** AI-powered insights

---

# PHASE 7: Integration & Polish (2-3 hours)

## Step 7.1: Agent Orchestration

**Goal:** Connect all 4 agents in workflow

**Actions:**
- Create root orchestrator agent (like data_science/agent.py)
- Handle state passing between agents
- Implement HITL checkpoints

**Deliverable:** End-to-end workflow

---

## Step 7.2: Bonus Features

**Goal:** Implement high-impact bonuses

**Priority order:**
1. Time Travel Diff View (critical for demo)
2. Agent Debate Mode (shows multi-agent collaboration)
3. Root Cause Clustering (if time permits)

**Deliverable:** At least 2 bonus features

---

## Step 7.3: Documentation

**Goal:** README and in-app tooltips

**Actions:**
- Update README.md with setup instructions
- Add st.help() tooltips throughout UI
- Create demo script/walkthrough

**Deliverable:** Complete documentation

---

# PHASE 8: Cloud Run Deployment (2-3 hours)

## Step 8.1: Update Dockerfile

**Goal:** Containerize Streamlit app for Cloud Run

**Actions:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

COPY . .

EXPOSE 8080
CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

**Deliverable:** Updated Dockerfile

---

## Step 8.2: Deploy to Cloud Run

**Goal:** Live deployed demo

**Actions:**
```powershell
# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT/dq-system

# Deploy to Cloud Run
gcloud run deploy dq-system `
  --image gcr.io/YOUR_PROJECT/dq-system `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated
```

**Verification:**
- ✅ Cloud Run URL works
- ✅ All features functional
- ✅ GCP authentication works

**Deliverable:** Deployed application

---

# PHASE 9: Testing & Demo Prep (2 hours)

## Step 9.1: End-to-End Testing

**Goal:** Verify complete workflow with real data

**Test scenarios:**
1. Full scan of Week 1 data
2. Generate 10 DQ rules
3. Approve 3 fixes
4. Execute with dry run
5. View metrics dashboard
6. Export markdown report

**Deliverable:** Test results documentation

---

## Step 9.2: Demo Script

**Goal:** 5-minute live demo script

**Script outline:**
```
1. [30s] Show GCP connection + data tables
2. [60s] Identifier: Generate rules, show categorization
3. [60s] Treatment: Select issue, show 3 fix options, Knowledge Bank precedent
4. [45s] Remediator: Dry run, before/after diff
5. [45s] Metrics: Cost of Inaction dashboard, anomaly detection
6. [30s] Bonus: Agent Debate Mode logs
```

**Deliverable:** Rehearsed demo

---

## 📊 VERIFICATION CHECKLIST

At the end of implementation, verify:

### Infrastructure
- [ ] GCP authentication working
- [ ] BigQuery access confirmed
- [ ] Dataplex API accessible
- [ ] All APIs enabled

### Agents
- [ ] Identifier generates rules
- [ ] Treatment suggests fixes
- [ ] Remediator executes safely
- [ ] Metrics calculates Cost of Inaction

### UI
- [ ] All 5 tabs functional
- [ ] GCP connection test works
- [ ] Settings properly configured
- [ ] No crashes or errors

### Bonus Features
- [ ] At least 2 bonus features working
- [ ] Agent Debate Mode visible
- [ ] Time Travel Diff implemented

### Documentation
- [ ] README updated
- [ ] Tooltips added
- [ ] Demo script prepared

### Deployment
- [ ] Cloud Run deployment successful
- [ ] Live URL accessible
- [ ] All features work in production

---

## 🚀 TIMELINE ESTIMATE

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 0: Environment Setup | 2-3 hours | 3h |
| Phase 1: Data Foundation | 2-3 hours | 6h |
| Phase 2: Streamlit Foundation | 2-3 hours | 9h |
| Phase 3: Identifier Agent | 4-5 hours | 14h |
| Phase 4: Treatment Agent | 3-4 hours | 18h |
| Phase 5: Remediator Agent | 2-3 hours | 21h |
| Phase 6: Metrics Agent | 3-4 hours | 25h |
| Phase 7: Integration & Polish | 2-3 hours | 28h |
| Phase 8: Cloud Run Deployment | 2-3 hours | 31h |
| Phase 9: Testing & Demo Prep | 2 hours | 33h |

**Target: Complete in 24-30 hours** (2 days of hackathon)

---

## 💡 RISK MITIGATION

### If behind schedule:
1. Skip BQML agent (not core to DQ system)
2. Simplify Dataplex integration (manual rule upload)
3. Defer Cloud Run deployment (run locally)
4. Limit to 1 bonus feature
5. Use fallback priority input instead of drag-and-reorder

### If ahead of schedule:
1. Add FAISS vector store for Knowledge Bank
2. Implement Shadow Validation
3. Add custom fix editor
4. Build admin panel for settings

---

## 📝 NOTES

- **Verify at each step** - Don't proceed until current step works
- **Use existing ADK patterns** - Don't reinvent, adapt
- **Test frequently** - Catch issues early
- **Document as you go** - Comments, tooltips, README
- **Save often** - Git commits after each phase

**This plan is your roadmap. Follow it step-by-step, verify each milestone, and you'll have a working system!** 🎯
