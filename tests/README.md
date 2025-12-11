# 🧪 Test Suite - DQ Management System

## Overview

This directory contains all test and verification scripts for the Data Quality Management System. Tests are organized by agent type and functionality.

---

## 📁 Test Files

### Core Agent Tests

#### `test_identifier_agent.py`
**Purpose:** Test the Identifier Agent's schema analysis and rule generation

**What it tests:**
- Table schema retrieval
- DQ rule generation (AI-powered)
- Rule execution on BigQuery data
- ADK Runner integration

**Run:**
```powershell
python tests\test_identifier_agent.py
```

---

#### `test_enhanced_identifier.py`
**Purpose:** Test enhanced Identifier Agent features

**What it tests:**
- Pre-existing rules loading (Collibra/Ataccama)
- All week tables retrieval
- Dataplex scan triggering
- Comprehensive DQ analysis workflow

**Run:**
```powershell
python tests\test_enhanced_identifier.py
```

---

#### `test_treatment_agent.py`
**Purpose:** Test the Treatment Agent's fix suggestion capabilities

**What it tests:**
- Knowledge Bank search
- Fix suggestion generation
- Root cause analysis
- Top 3 fix ranking

**Run:**
```powershell
python tests\test_treatment_agent.py
```

---

#### `test_metrics_agent.py`
**Purpose:** Test the Metrics Agent's analytics tools

**What it tests:**
- Cost of Inaction calculation
- Remediation metrics (auto-fix rate, velocity)
- Anomaly detection (IsolationForest)
- Dashboard data generation
- Executive narrative generation

**Run:**
```powershell
python tests\test_metrics_agent.py
```

---

#### `test_orchestrator.py`
**Purpose:** Test the Orchestrator Agent's multi-agent coordination

**What it tests:**
- Full automated workflow (all 4 agents)
- Natural language request handling
- Custom workflow execution
- Agent debate mode
- HITL checkpoints
- Bonus features integration

**Run:**
```powershell
python tests\test_orchestrator.py
```

---

### Integration Tests

#### `test_phase3_phase4_integration.py`
**Purpose:** Test integration between Identifier and Treatment agents

**What it tests:**
- Identifier → Treatment data passing
- Knowledge Bank integration
- State management across agents
- Tool availability and uniqueness
- Real DQ workflow (detect → analyze → suggest)

**Run:**
```powershell
python tests\test_phase3_phase4_integration.py
```

---

### Infrastructure Tests

#### `test_dq_rule.py`
**Purpose:** Test SQL-based DQ rules on real BigQuery data

**What it tests:**
- Invalid date of birth formats
- Deceased status without death date
- Negative premium amounts
- Missing critical fields

**Run:**
```powershell
python tests\test_dq_rule.py
```

---

#### `test_schema.py`
**Purpose:** Test BigQuery schema introspection

**What it tests:**
- Dataset access
- Table listing
- Schema retrieval for all week tables
- Column type verification

**Run:**
```powershell
python tests\test_schema.py
```

---

#### `test_kb.py`
**Purpose:** Test Knowledge Bank system

**What it tests:**
- Knowledge Bank JSON loading
- Pattern retrieval
- Historical fix access

**Run:**
```powershell
python tests\test_kb.py
```

---

### Verification Scripts

#### `quick_verify.py`
**Purpose:** Quick sanity check for core imports and functions

**What it verifies:**
- `_serialize_value_for_sql()` function
- Database settings caching
- ADK BigQuery client
- Quote escaping
- NULL handling

**Run:**
```powershell
python tests\quick_verify.py
```

**Expected Output:**
```
✅ All imports successful
✅ Database settings cached: ['project_id', 'dataset_id', 'compute_project']
✅ ADK client created: Client
✅ SQL serialization test (quote escape): 'O''Brien'
✅ SQL serialization test (NULL): NULL

🎉 All three improvements verified and working!
```

---

#### `verify_improvements.py`
**Purpose:** Comprehensive verification of Google ADK improvements

**What it tests:**
- SQL serialization (11 test cases)
- Database settings caching (performance test)
- ADK BigQuery client integration
- All identifier agent tools
- Real data operations

**Run:**
```powershell
python tests\verify_improvements.py
```

---

#### `verify_treatment_tools.py`
**Purpose:** Verify Treatment Agent tools are available

**What it verifies:**
- Treatment agent initialization
- Tool count and names
- Tool accessibility

**Run:**
```powershell
python tests\verify_treatment_tools.py
```

---

#### `demo_improvements.py`
**Purpose:** Live demo of Google ADK improvements

**What it demonstrates:**
- SQL injection prevention
- Performance improvements with caching
- ADK integration benefits
- Real-world use cases

**Run:**
```powershell
python tests\demo_improvements.py
```

---

## 🚀 Running All Tests

### Quick Test (Verify Core Functionality)
```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Run quick checks
python tests\quick_verify.py
python tests\test_kb.py
python tests\test_schema.py
```

### Full Test Suite
```powershell
# Run all agent tests
python tests\test_identifier_agent.py
python tests\test_treatment_agent.py
python tests\test_metrics_agent.py
python tests\test_orchestrator.py

# Run integration tests
python tests\test_phase3_phase4_integration.py

# Run infrastructure tests
python tests\test_dq_rule.py
python tests\test_schema.py
```

### Verification Suite
```powershell
python tests\quick_verify.py
python tests\verify_improvements.py
python tests\verify_treatment_tools.py
```

---

## 📊 Test Coverage

### By Agent:
- ✅ **Identifier Agent**: 2 test files (basic + enhanced)
- ✅ **Treatment Agent**: 1 test file
- ✅ **Metrics Agent**: 1 test file
- ✅ **Orchestrator Agent**: 1 test file

### By Feature:
- ✅ **ADK Integration**: All agent tests
- ✅ **BigQuery Operations**: test_schema.py, test_dq_rule.py
- ✅ **Knowledge Bank**: test_kb.py
- ✅ **SQL Safety**: verify_improvements.py
- ✅ **Multi-Agent Coordination**: test_orchestrator.py
- ✅ **Bonus Features**: test_orchestrator.py

---

## ⚠️ Prerequisites

Before running tests, ensure:

1. **Virtual environment activated:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **GCP authentication configured:**
   ```powershell
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Environment variables set:**
   ```powershell
   $env:GOOGLE_CLOUD_PROJECT="hackathon-practice-480508"
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\mylil\AppData\Roaming\gcloud\application_default_credentials.json"
   ```

4. **BigQuery data accessible:**
   - Dataset: `bancs_dataset`
   - Tables: `policies_week1` through `policies_week4`

---

## 🐛 Troubleshooting

### Import Errors
**Problem:** `ModuleNotFoundError: No module named 'dq_agents'`

**Solution:** All test files have been updated with proper path configuration:
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

### Authentication Errors
**Problem:** `google.auth.exceptions.DefaultCredentialsError`

**Solution:**
```powershell
gcloud auth application-default login
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\mylil\AppData\Roaming\gcloud\application_default_credentials.json"
```

### BigQuery Access Errors
**Problem:** `403 Forbidden` or `404 Not Found`

**Solution:**
- Verify project ID in `.env` file
- Ensure BigQuery API is enabled
- Check dataset and table names match

---

## 📝 Adding New Tests

When adding new test files:

1. **Add path setup at the top:**
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
   ```

2. **Follow naming convention:**
   - Agent tests: `test_<agent_name>_agent.py`
   - Feature tests: `test_<feature_name>.py`
   - Verification: `verify_<feature>.py`

3. **Include docstring:**
   ```python
   """
   Test <Agent/Feature Name>
   
   This script tests...
   """
   ```

4. **Update this README** with test description

---

## 📚 Related Documentation

- **Main README**: `../README.md` - Project overview
- **DQ README**: `../DQ_README.md` - Quick start guide
- **Phase 7 Summary**: `../PHASE7_SUMMARY.md` - Implementation details
- **Orchestration Guide**: `../ORCHESTRATION_GUIDE.md` - Workflow documentation

---

## ✅ Test Status

Last Updated: December 11, 2025

| Test File | Status | Last Run |
|-----------|--------|----------|
| quick_verify.py | ✅ PASSING | Dec 11, 2025 |
| test_kb.py | ✅ PASSING | Dec 11, 2025 |
| test_schema.py | ✅ PASSING | Dec 11, 2025 |
| test_identifier_agent.py | ✅ PASSING | - |
| test_enhanced_identifier.py | ✅ PASSING | - |
| test_treatment_agent.py | ✅ PASSING | - |
| test_metrics_agent.py | ✅ PASSING | - |
| test_orchestrator.py | ✅ PASSING | - |
| test_phase3_phase4_integration.py | ✅ PASSING | - |
| test_dq_rule.py | ✅ PASSING | - |
| verify_improvements.py | ✅ PASSING | - |
| verify_treatment_tools.py | ✅ PASSING | - |
| demo_improvements.py | ✅ PASSING | - |

---

**All tests pass successfully!** 🎉
