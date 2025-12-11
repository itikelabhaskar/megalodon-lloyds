# 🚨 CODEBASE AUDIT REPORT - PRODUCTION READINESS

## Date: December 11, 2025
## Status: ⚠️ CRITICAL ISSUES FOUND - REQUIRES FIXES BEFORE PRODUCTION

---

## 🔴 CRITICAL ISSUES (MUST FIX)

### 1. **HARDCODED PROJECT-SPECIFIC VALUES** ❌

#### Location: `bancs_dataset_config.json`
**Issue:** Hardcoded project ID and dataset name
```json
{
  "project_id": "hackathon-practice-480508",  // ❌ HARDCODED
  "dataset_id": "bancs_dataset",               // ❌ HARDCODED
```

**Impact:** Cannot be used by other organizations or projects
**Against Spec:** PLAN.md states "No hardcoding - solution must be generic and adaptable"

**Fix Required:**
```json
{
  "project_id": "${GOOGLE_CLOUD_PROJECT}",     // ✅ USE ENV VAR
  "dataset_id": "${BQ_DATASET_ID}",            // ✅ USE ENV VAR
```

---

### 2. **HARDCODED TABLE NAMES** ❌

#### Location: `streamlit_app/app.py` (Multiple locations)
**Lines:** 220, 297, 1132, 1391, 2096, 2097, 2195, 2299, 2308, 2309, 2573, 2625, 2844

**Issue:** Table names "policies_week1", "policies_week2", etc. are hardcoded throughout UI

**Against Spec:** PLAN.md states "Support regex pattern matching for week-wise tables" - should dynamically fetch tables

**Example Violations:**
```python
# Line 220
["policies_week1", "policies_week2", "policies_week3", "policies_week4"],  // ❌

# Line 1132
table_name = rule.get('table', 'policies_week1')  // ❌ Fallback hardcoded

# Line 2097
default=["policies_week1"],  // ❌ Default hardcoded
```

**Fix Required:**
- Fetch tables dynamically from BigQuery using `get_all_week_tables()` tool
- Store in session state
- Use dynamic table list instead of hardcoded array

**Proposed Fix:**
```python
# At app startup or in sidebar
if 'available_tables' not in st.session_state:
    # Fetch from BigQuery dynamically
    client = bigquery.Client(project=project_id)
    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    all_tables = [table.table_id for table in client.list_tables(dataset_ref)]
    st.session_state.available_tables = all_tables

# Then use throughout app
st.multiselect("Select tables", st.session_state.available_tables)
```

---

### 3. **BANCS-SPECIFIC COLUMN NAMES IN PROMPTS** ⚠️

#### Location: `dq_agents/identifier/prompts.py`
**Lines:** 79-82

**Issue:** Hardcoded BaNCS-specific column names in agent instructions
```python
Focus on BaNCS-specific columns like:
- CUS_DOB, CUS_DEATH_DATE, CUS_LIFE_STATUS    // ❌ HARDCODED
- POLI_GROSS_PMT, POLI_TAX_PMT, POLI_INCOME_PMT  // ❌ HARDCODED
- CUS_NI_NO, CUS_POSTCODE                      // ❌ HARDCODED
```

**Against Spec:** Solution should work for ANY insurance company data, not just BaNCS schema

**Impact:** Agent will fail or perform poorly on non-BaNCS datasets

**Fix Required:**
Option 1: Remove BaNCS-specific guidance
Option 2: Make it schema-agnostic:
```python
Focus on common insurance data columns like:
- Date fields (date_of_birth, death_date, policy_start_date, etc.)
- Status fields (life_status, policy_status, etc.)
- Payment fields (premium, payment_amount, tax, etc.)
- Identity fields (national_id, customer_id, policy_id, etc.)
```

---

### 4. **HARDCODED COLUMN NAMES IN TOOLS** ❌

#### Location: `dq_agents/identifier/tools.py`
**Lines:** 262-265, 280-282, 299-300

**Issue:** Query uses BaNCS-specific column names
```python
COUNTIF(CUS_DOB IS NULL OR CUS_DOB = '' OR CUS_DOB = 'None') as dob_nulls,  // ❌
COUNTIF(CUS_LIFE_STATUS IS NULL OR CUS_LIFE_STATUS = '') as status_nulls,   // ❌
COUNTIF(POLI_GROSS_PMT < 0) as negative_premiums,                           // ❌
COUNTIF(CUS_NI_NO IS NULL OR CUS_NI_NO = '') as ni_nulls,                   // ❌
```

**Fix Required:**
- Dynamically detect column names from schema
- Use generic patterns (e.g., columns with "DOB", "DATE", "PMT", "STATUS" in name)
- OR make this query fully optional/configurable

---

### 5. **HARDCODED WEEK TABLE NAMES IN TREATMENT AGENT** ❌

#### Location: `dq_agents/treatment/tools.py`
**Lines:** 90-96, 101

**Issue:** SQL hardcodes "policies_week1", "policies_week2", etc.
```python
SELECT 'week1' as week, * FROM `{project_id}.{dataset_id}.policies_week1` WHERE CUS_ID = '{customer_id}'  // ❌
UNION ALL
SELECT 'week2' as week, * FROM `{project_id}.{dataset_id}.policies_week2` WHERE CUS_ID = '{customer_id}'  // ❌
```

**Fix Required:**
```python
# Get all week tables dynamically
week_tables = get_all_week_tables()
queries = []
for table in week_tables:
    queries.append(f"SELECT '{table}' as week, * FROM `{{project_id}}.{{dataset_id}}.{table}` WHERE CUS_ID = '{{customer_id}}'")
sql = " UNION ALL ".join(queries)
```

---

### 6. **HARDCODED EXAMPLE SQL IN PROMPTS** ⚠️

#### Location: `dq_agents/identifier/prompts.py`
**Line:** 71

**Issue:** Example SQL uses hardcoded table names
```python
"sql": "SELECT w2.CUS_ID, w1.CUS_LIFE_STATUS as week1_status, w2.CUS_LIFE_STATUS as week2_status FROM `PROJECT.DATASET.policies_week1` w1 JOIN `PROJECT.DATASET.policies_week2` w2 ON w1.CUS_ID = w2.CUS_ID WHERE w1.CUS_LIFE_STATUS = 'Deceased' AND w2.CUS_LIFE_STATUS = 'Active'",
```

**Fix Required:**
Use placeholders:
```python
"sql": "SELECT w2.customer_id, w1.status as week1_status, w2.status as week2_status FROM `PROJECT.DATASET.{table_week1}` w1 JOIN `PROJECT.DATASET.{table_week2}` w2 ON w1.customer_id = w2.customer_id WHERE w1.status = 'Deceased' AND w2.status = 'Active'"
```

---

## 🟡 MEDIUM PRIORITY ISSUES

### 7. **HARDCODED RISK RATES IN METRICS AGENT** ⚠️

#### Location: `dq_agents/metrics/tools.py`
**Lines:** 121-123

**Issue:** Cost of Inaction uses hardcoded risk rates
```python
regulatory_risk_rate = 0.001  # 0.1% for regulatory fines  // ❌
customer_churn_rate = 0.02    # 2% for customer impact     // ❌
operational_rate = 0.005      # 0.5% for operational costs // ❌
```

**Impact:** May not be accurate for different industries/companies

**Fix Required:**
- Make these configurable via environment variables
- OR provide UI controls to adjust rates
- OR make them industry-specific with lookup

**Suggested Fix:**
```python
regulatory_risk_rate = float(os.getenv("REGULATORY_RISK_RATE", "0.001"))
customer_churn_rate = float(os.getenv("CUSTOMER_CHURN_RATE", "0.02"))
operational_rate = float(os.getenv("OPERATIONAL_COST_RATE", "0.005"))
```

---

### 8. **HARDCODED MATERIALITY THRESHOLDS** ⚠️

#### Location: `dq_agents/metrics/tools.py`
**Lines:** 134-136

**Issue:** Fixed thresholds for materiality assessment
```python
if total_exposure > 10000000:  # £10M+   // ❌ Hardcoded
    materiality = "High"
elif total_exposure > 1000000:  # £1M+  // ❌ Hardcoded
    materiality = "Medium"
```

**Fix Required:**
Make configurable based on organization size:
```python
high_threshold = float(os.getenv("MATERIALITY_HIGH_THRESHOLD", "10000000"))
medium_threshold = float(os.getenv("MATERIALITY_MEDIUM_THRESHOLD", "1000000"))
```

---

### 9. **HARDCODED CONTAMINATION RATE** ⚠️

#### Location: `dq_agents/metrics/tools.py`
**Line:** 223

**Issue:** IsolationForest contamination hardcoded
```python
iso_forest = IsolationForest(contamination=0.1, random_state=42)  // ❌
```

**Fix Required:**
```python
contamination_rate = float(os.getenv("ANOMALY_CONTAMINATION_RATE", "0.1"))
iso_forest = IsolationForest(contamination=contamination_rate, random_state=42)
```

---

### 10. **ORGANIZATION NAME HARDCODED IN UI** ⚠️

#### Location: `streamlit_app/app.py`
**Lines:** 3033, 3074

**Issue:** "Lloyd's Banking Group" hardcoded
```python
<p>Data Quality Management System | Lloyd's Banking Group Hackathon 2025</p>  // ❌
st.caption("Built with ADK Multi-Agent Framework | Lloyd's Banking Group Hackathon 2025")  // ❌
```

**Fix Required:**
```python
organization = os.getenv("ORGANIZATION_NAME", "Your Organization")
year = os.getenv("COPYRIGHT_YEAR", "2025")
<p>Data Quality Management System | {organization} {year}</p>
```

---

## 🟢 GOOD PRACTICES FOUND ✅

### 1. **Environment Variables Used Correctly**
- ✅ All agents use `os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-flash")`
- ✅ Project ID, dataset ID use environment variables in most places
- ✅ Fallback values provided for development

### 2. **No API Keys Hardcoded**
- ✅ Uses GCP authentication, no hardcoded API keys found

### 3. **SQL Injection Prevention**
- ✅ `_serialize_value_for_sql()` function properly escapes SQL values
- ✅ SQL parameterization used where possible

### 4. **Caching Implemented**
- ✅ Database settings cached in `_database_settings` global

---

## 📋 PRIORITY FIX LIST

### CRITICAL (Must fix before production):
1. ❗ Remove hardcoded project ID from `bancs_dataset_config.json`
2. ❗ Make table names dynamic in Streamlit app (fetch from BigQuery)
3. ❗ Remove BaNCS-specific column names from prompts
4. ❗ Remove hardcoded column names from identifier tools
5. ❗ Make treatment agent week tables dynamic

### HIGH (Should fix before demo):
6. ⚠️ Make risk rates configurable in metrics agent
7. ⚠️ Make materiality thresholds configurable
8. ⚠️ Remove Lloyd's Banking Group from footer (make generic)

### MEDIUM (Nice to have):
9. 💡 Make contamination rate configurable
10. 💡 Add configuration file for industry-specific settings

---

## ✅ VERIFICATION AGAINST PLAN.MD

### Spec Requirement: "No hardcoding - solution must be generic and adaptable"
**Status:** ❌ **VIOLATED**
- Multiple hardcoded values found
- BaNCS-specific references throughout
- Table names hardcoded

### Spec Requirement: "Support regex pattern matching for week-wise tables"
**Status:** ❌ **NOT IMPLEMENTED**
- Tables hardcoded as array
- Should use `get_all_week_tables()` dynamically

### Spec Requirement: "Solution should work with ANY insurance data"
**Status:** ❌ **VIOLATED**
- BaNCS column names in prompts
- CUS_*, POLI_* column assumptions

---

## 🎯 RECOMMENDED ACTION PLAN

### Phase 1: Critical Fixes (2-3 hours)
1. Create `make_config_dynamic.py` script to:
   - Update `bancs_dataset_config.json` to use environment variables
   - Add function to load config with env var substitution

2. Update `streamlit_app/app.py`:
   - Add dynamic table fetching at startup
   - Replace all hardcoded table arrays with dynamic lists
   - Store in `st.session_state.available_tables`

3. Update all agent prompts:
   - Remove BaNCS-specific column names
   - Use generic insurance terminology
   - Add schema introspection guidance

4. Update `identifier/tools.py`:
   - Make column queries schema-agnostic
   - Detect columns by pattern (e.g., *_DOB, *_DATE, *_PMT)

5. Update `treatment/tools.py`:
   - Use `get_all_week_tables()` to build dynamic UNION queries

### Phase 2: Configuration Enhancements (1-2 hours)
6. Add new environment variables to `.env.example`:
   ```
   REGULATORY_RISK_RATE=0.001
   CUSTOMER_CHURN_RATE=0.02
   OPERATIONAL_COST_RATE=0.005
   MATERIALITY_HIGH_THRESHOLD=10000000
   MATERIALITY_MEDIUM_THRESHOLD=1000000
   ANOMALY_CONTAMINATION_RATE=0.1
   ORGANIZATION_NAME=Your Organization
   COPYRIGHT_YEAR=2025
   ```

7. Update metrics agent to use these env vars

8. Update UI footer to use env vars

### Phase 3: Testing (1 hour)
9. Test with different project IDs
10. Test with different dataset names
11. Test with non-BaNCS schema (create sample data)

---

## 📊 SUMMARY METRICS

- **Total Issues Found:** 10
- **Critical Issues:** 6 ❌
- **Medium Priority:** 4 ⚠️
- **Good Practices:** 4 ✅

**Production Readiness Score:** 40/100 ⚠️

**Recommendation:** **DO NOT DEPLOY TO PRODUCTION** until critical issues are resolved.

---

## 🔧 QUICK FIX COMMANDS

```powershell
# 1. Backup current files
Copy-Item bancs_dataset_config.json bancs_dataset_config.json.backup
Copy-Item streamlit_app/app.py streamlit_app/app.py.backup

# 2. Run fix script (to be created)
python scripts/fix_hardcoded_values.py

# 3. Verify fixes
python scripts/verify_no_hardcoding.py

# 4. Test with different config
$env:GOOGLE_CLOUD_PROJECT="different-project-123"
$env:BQ_DATASET_ID="different_dataset"
streamlit run streamlit_app/app.py
```

---

## 📝 NEXT STEPS

1. **IMMEDIATE:** Review this audit with team
2. **TODAY:** Implement Phase 1 critical fixes
3. **TOMORROW:** Implement Phase 2 config enhancements
4. **BEFORE DEMO:** Full testing with different configurations
5. **POST-DEMO:** Refactor for multi-tenant support if needed

---

**Audited by:** GitHub Copilot AI Assistant
**Date:** December 11, 2025
**Version:** Pre-Production Audit v1.0
