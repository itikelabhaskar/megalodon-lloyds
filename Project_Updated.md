# Data Quality Management System - Complete Specification

## Project Overview

* Automating the clean-up of legacy BaNCS data from Lloyd's Banking Group - Used for life insurance predictions   
* The given data is not the actual data, it is an example dataset with synthetic issues.  
* **No hardcoding** - solution must be generic and adaptable

**Core Objective:** Build an agentic solution that detects, categorizes, and remediates data quality issues autonomously; focus on large-scale anomaly detection and remediation.

---

## System Architecture

**Framework:** ADK (Agent Development Kit) multi-agent framework
- Use `agent.py` and `tools.py` patterns from ADK data science sample
- Multi-agent orchestration with shared state
- Cloud Run deployment for scalability

**UI:** Streamlit with Agent Tabs (Parallel Access)
```
Tab 1: 🔍 Identifier Agent
Tab 2: 💊 Treatment Agent
Tab 3: 🔧 Remediator Agent
Tab 4: 📊 Metrics Agent
Tab 5: ⚙️ Settings (GCP auth, Model config, Knowledge Bank)
```

---

## Agent 1: Identifier Agent

### Core Functionality
* **Good UI for Streamlit**
* **GCP Authentication:** 
  - Authenticate into GCP
  - Select project and table(s)
  - Support regex pattern matching for week-wise tables (e.g., `policies_week1`, `policies_week2`, `policies_week3`, `policies_week4`)

### Dataplex Integration
* **Trigger Dataplex scans via API:**
  - Profile scanning
  - Quality scanning
* Run analysis and execute recommended queries by default
* Fetch and display Dataplex results

### Rule Management

#### 1. Pre-existing Rules (Collibra/Ataccama)
* **Format:** JSON (no actual rules - create mock format)
* **Implementation:** Create a sub-agent to convert old rule formats to standard JSON
* **Mock JSON Rule Structure:**
```json
{
  "rule_id": "COL_001",
  "source": "collibra",
  "name": "DOB_future_check",
  "description": "Date of birth cannot be in the future",
  "sql": "SELECT * FROM {table} WHERE date_of_birth > CURRENT_DATE()",
  "severity": "critical",
  "category": "Accuracy",
  "dq_dimension": "Accuracy"
}
```

#### 2. AI-Generated Rules
* **Temporal Rules:** 
  - Date of death shouldn't be after current week
  - Alive/deceased status shouldn't change down the line
  - Policy start date < end date
* **Sensible Rules:**
  - Underage individuals in location restrictions
  - Premium amounts within expected ranges
  - Required fields not null

#### 3. Dataplex Rules
* Auto-extracted from Dataplex quality scans
* Profiling-based anomaly detection

### Rule Display & Selection
* **UI Requirements:**
  - Separate rules by source (Pre-existing, Dataplex, AI-generated)
  - Check for duplicates or similar rules (priority order)
  - Allow user to select which DQ rules to run
  - Show rule details: SQL, severity, category

### Operating Modes

**Mode 1 - Full Scan:**
* Run ALL rules on entire dataset
* Complete validation of all data
* Use case: Initial data quality assessment

**Mode 2 - Incremental Scan:**
* Only run rules on new/changed rows since last check
* **Implementation Options:**
  - Users manually select which tables are already DQ-assured
  - Week-wise data handling (Week 1 is assured, only scan Week 2-4)
  - Alternative: Track `last_checked_timestamp` in BigQuery metadata table

### Tools & Architecture
* Web search (for context)
* Dataplex API (trigger + fetch)
* BigQuery metadata inspection
* ADK multi-agent framework (agent.py, tools.py)

---

## Agent 2: Treatment Agent

### Core Functionality
* Runs the selected DQ rules
* Loops to check and find issues
* Identifies specific issue patterns
* Suggests ranked solutions

### Fix Strategy Options
1. Queries different profiles of the person across datasets (Self-heal)
2. Replace with empty string
3. Replace with NULL
4. Delete row
5. Replace with statistical mean/median
6. Mark with warnings (flag but keep data)
7. Raise JIRA ticket / email notification

### Human-in-the-Loop (HITL)

**UI Requirements:**
* Display top 3 ranked fixes for each issue
* **Selection Method:** Drag-and-reorder interface (preferred)
  - Gemini orders fixes by optimality before presentation
  - User can reorder priorities
* **Future Work:** Allow user to edit/customize suggested fixes before approval
  - Example: Change "Replace with NULL" to "Replace with median"

**Additional Features:**
* Button to view the problematic row
* Link to view data directly in GCP BigQuery console

### Knowledge Bank

**Implementation:** JSON-based storage (FAISS for future enhancements)

**Structure:**
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
          "approval_count": 5,
          "auto_approve": true,
          "created_at": "2025-12-01",
          "context": "Legacy data migration errors"
        }
      ],
      "similarity_threshold": 0.85
    }
  }
}
```

**Pre-population:**
* 3 "Historical Fixes" examples
  - "If DOB > 2025, set to NULL and Flag"
  - "If Premium < 0, replace with policy average"
  - "If NI number missing, flag for manual review"

**Behavior:**
* When similar issue detected: 
  - "I found a precedent in the Knowledge Bank (85% similarity)"
  - "Recommended Action: Set to Null (5 previous approvals)"
* **Auto-approval:** User can enable auto-fix for known issue patterns
* Store all approved fixes for future reference

**Future Enhancement:** Add FAISS vector store for semantic similarity matching

---

## Agent 3: Remediator Agent

### Core Functionality
* Attempts to apply approved fixes
* Self-healing loop (limit to 1 iteration for testing)
* Validation and error handling

### Execution Process
1. Apply fix to data
2. Validate fix success
3. If validation fails → Generate JIRA ticket/email

### JIRA/Email Integration

**Implementation:** Mock system (display JSON + append to file)

**Mock JIRA Ticket Format:**
```json
{
  "ticket_id": "DQ-12345",
  "title": "Data Quality Issue: Invalid DOB in 15 policies",
  "description": "15 records have date_of_birth > 2025. Automated fix failed validation.",
  "severity": "High",
  "assigned_to": "data_operations_team",
  "grouped_issues": [
    {"policy_id": "POL123", "issue": "DOB = 2026-05-12", "table": "policies_week2"},
    {"policy_id": "POL456", "issue": "DOB = 2027-08-30", "table": "policies_week3"}
  ],
  "recommended_fix": "SET date_of_birth = NULL WHERE policy_id IN ('POL123', 'POL456')",
  "failure_reason": "Shadow validation detected 2 downstream dependency errors",
  "created_at": "2025-12-10T10:30:00Z",
  "status": "open"
}
```

**File Storage:**
* Append to `jira_tickets.json`
* Display ticket status (open/addressed/resolved)
* Group similar issues in single ticket

### Validation & Safety

**Core Feature: Dry Run Button**
* Preview what would change without applying
* Show before/after comparison
* Estimate impact and confidence score

**Future Work: Shadow Validation Sandbox**
* Create temporary shadow table
* Apply fix to shadow table
* Run regression tests
* Only commit to production if tests pass
* Rollback mechanism if issues detected

---

## Agent 4: Metrics Agent

### Core Functionality
* **Good UI with Power BI-style interactive graphs**
* **Markdown Reports:** Downloadable comprehensive reports
* **Dynamic Storytelling:** AI-generated insights, not just charts
* Can run independently to some extent

### Anomaly Detection

**Implementation:**
* Use `IsolationForest` (sklearn) for outlier detection
* **Automatic Execution:** Runs automatically on numerical columns
* **Dynamic Column Selection:** 
  - Identify numerical columns from BigQuery metadata
  - Run appropriate inference based on column types
  - Columns: policy_value, premium, age, tenure, etc.

**Display:**
* Downloadable Markdown report
* Power BI-style visualizations
* Anomaly scores and explanations

**User Actions:**
* Flag anomalies for review
* Option to create DQ rules from detected anomalies
* Not automatic rule creation

### Key Metrics

#### 1. Remediation Velocity
* Average time to resolve an issue
* Trend over time (improving/degrading)

#### 2. Materiality Index
* Financial/Regulatory impact score (High/Med/Low)
* Based on affected policy values and row counts

#### 3. Auto-Fix Rate
* % of issues resolved without human intervention
* **Target: >80% automation**
* Compare human-approved vs auto-approved fixes

#### 4. Cost of Inaction
* **Critical Metric - Judges specifically requested**
* **Calculation:**
  ```python
  affected_rows = len(issues_df)
  avg_policy_value = df['policy_value'].mean()  # Extract relevant column
  regulatory_risk_rate = 0.001  # 0.1% monthly risk (assume)
  
  total_exposure = affected_rows * avg_policy_value
  monthly_coi = total_exposure * regulatory_risk_rate
  annual_coi = monthly_coi * 12
  ```
* **Dynamic Storytelling Example:**
  - "This DQ issue affects £14M of policy value."
  - "The projected Cost of Inaction is £50k/month."
  - "If left unaddressed for 6 months, estimated loss: £300k."

#### 5. Accuracy Metrics
* False Positive Rate of Identifier Agent
* Precision and Recall of rule matching
* User override frequency

### Dynamic Storytelling

**Implementation:**
* Use Gemini to generate narrative summaries
* Contextual insights based on data patterns
* Example prompt:
```python
prompt = f"""
Analyze these DQ metrics and create a compelling narrative summary:
- Issues Found: {issue_count}
- Auto-Fixed: {auto_fix_count}
- Manual Review: {manual_count}
- Total Exposure: £{total_exposure:,}
- Cost of Inaction: £{monthly_coi:,}/month

Write a 3-paragraph executive summary highlighting:
1. Current DQ health status
2. Financial impact and risk exposure
3. Remediation progress and recommendations
"""
```

---

## System-Wide Features

### Cost Management

**Model Switcher:**
* **Global Setting:** Configure default model for all agents (in Settings tab)
* **Per-Agent Override:** Each agent can use different model if needed
* **Supported Models:** Query Google API to find current latest models
  - Offer 3-4 multimodal options
  - Flash models (fast, cost-effective)
  - Pro models (advanced reasoning)
  - Example: gemini-2.0-flash, gemini-2.0-pro, gemini-1.5-pro

**Rate Limiting:**
* Configurable requests per minute per agent
* Cost tracking dashboard (estimate and actual)
* Alert when approaching quota limits

### Usability

**Documentation:**
* Comprehensive README with setup instructions
* In-app tooltips for all features
* Example workflows and demos

**UI/UX:**
* Intuitive navigation
* Clear status indicators
* Progress bars for long-running operations
* Error messages with remediation suggestions

### Explainability

**System Prompts:**
* Well-crafted, unbiased prompts
* Parametrized prompts (no hardcoding)
* Clear reasoning chains

**RAG for Context:**
* User can upload relevant documentation
* Higher priority than web search
* Context-aware rule generation and fix suggestions

**Guardrails:**
* Validation checks before data modification
* Confidence thresholds for auto-fixes
* Human approval for high-risk changes
* Audit logging for all actions

### Interpretability

**ADK Web Integration:**
* Visualize agents and their tools
* Trace agent decision-making
* Debug agent interactions

**Agent Reasoning Display:**
* Show agent "thought process" in UI
* Chain-of-thought explanations
* Tool call history and results

### Scalability

**Data Scale:**
* Handle hundreds to thousands of rows
* Efficient BigQuery query optimization
* Batch processing for large datasets

**Cloud Run Deployment:**
* All queries and fixes run in GCP (not local)
* Serverless scaling
* Concurrent agent execution

### Verifiability

**Audit Trail:**
* Log all DQ rule executions
* Record all fixes applied
* Track human approvals and overrides
* Timestamp and user attribution

**Validation:**
* Pre-fix validation (dry run)
* Post-fix validation (shadow table)
* Regression testing before commit

---

## Bonus Implementations

### 1. Agent Debate Mode (Transparency)

**Goal:** Visualize multi-agent collaboration

**Implementation:**
* Live Logs window (using `st.expander`)
* Show agents "arguing" or collaborating
* Display raw Chain-of-Thought from LLM responses

**Example:**
```
Identifier Agent: "I found a policy value of £200,000. This looks like an anomaly (> £100k rule)."
Treatment Agent: "Checking Knowledge Bank... Wait. This is a 'Jumbo Policy' type. Value is valid. Marking as False Positive."
Identifier Agent: "Understood. Learning this exception. Updating rule to exclude Jumbo Policies."
```

### 2. Root Cause Cluster Analysis (Treatment Agent)

**Goal:** Group errors by root cause, not just symptoms

**Implementation:**
* Feed metadata of bad rows into LLM
* Analyze common attributes: Creation Date, Source System, User ID, Branch ID
* Generate root cause hypothesis

**Example Output:**
```
"I detected 50 'Invalid Date of Birth' errors.
Analysis: 100% of these records were created by 'User_System_Legacy_A' 
between 12:00 AM and 1:00 AM.
Root Cause: Likely a batch import job with incorrect date parsing.
Recommendation: Fix import job logic, not just data."
```

**Why it wins:** Moves from "fixing data" to "fixing the process"

### 3. Time Travel Diff View (Remediator Agent)

**Goal:** Show before/after comparison for transparency

**Implementation:**
* Side-by-side dataframe comparison
* Highlight changed cells (red → green)
* Show confidence scores
* Use `pandas` comparison + `st.dataframe` with column highlighting

**Example:**
```
┌─────────────┬──────────────────────┬──────────────────────┬────────────────┐
│ Policy ID   │ Before               │ After                │ Confidence     │
├─────────────┼──────────────────────┼──────────────────────┼────────────────┤
│ POL123      │ 19-09-22023 (RED)    │ 19-09-2023 (GREEN)   │ 98% (Pattern)  │
│ POL456      │ NULL (RED)           │ £45,000 (GREEN)      │ 85% (Median)   │
└─────────────┴──────────────────────┴──────────────────────┴────────────────┘
```

---

## Testing Strategy

### Data Environment
* **Existing Data:** Already on GCP BigQuery
* **Structure:** Multiple week-wise tables
  - `policies_week1`, `policies_week2`, `policies_week3`, `policies_week4`
  - Or similar naming patterns
* **Handling:** Use regex pattern matching to detect and process week-wise tables
* **System Requirement:** Must handle multi-table scenarios gracefully

### Test Scenarios
1. Full scan on all 4 weeks
2. Incremental scan (Week 1-2 assured, scan Week 3-4)
3. Single week validation
4. Cross-week consistency checks (e.g., status shouldn't change)

---

## Future Enhancements

### Phase 2 Features (Post-Hackathon)
1. **FAISS Vector Store:** Replace JSON with semantic similarity search for Knowledge Bank
2. **Custom Fix Editor:** Allow users to edit suggested fixes in UI before approval
3. **Shadow Validation:** Full implementation with regression testing
4. **Real JIRA Integration:** Actual API calls instead of mock JSON
5. **Advanced Anomaly Detection:** BQML-based models for pattern learning
6. **Multi-dataset Support:** Handle relationships across different datasets
7. **Scheduled Scans:** Cron-based automatic DQ validation
8. **Email Notifications:** Alert stakeholders of critical issues
9. **Role-based Access:** Different permissions for viewers/approvers/admins
10. **Performance Optimization:** Caching, query optimization, parallel processing

---

## Success Criteria (Judging Rubric Alignment)

### Value & Proposition (20%)
* ✅ Addresses real BaNCS data quality problem
* ✅ Measurable impact (Cost of Inaction metric)
* ✅ Clear ROI demonstration

### Agentic Feasibility (20%)
* ✅ True multi-agent collaboration (not if-else)
* ✅ ADK framework usage
* ✅ Autonomous decision-making with human oversight

### Innovation & Originality (20%)
* ✅ Agent Debate Mode (transparency)
* ✅ Root Cause Clustering (process improvement)
* ✅ Knowledge Bank with learning
* ✅ Dynamic storytelling in metrics

### Technical Execution (20%)
* ✅ Working MVP with all 4 agents
* ✅ Stable, well-documented
* ✅ Cloud Run backend
* ✅ Minimal bugs

### Usability & Accessibility (10%)
* ✅ Intuitive Streamlit UI
* ✅ Tooltips and README
* ✅ Bridges technical-business gap

### Presentation & Communication (10%)
* ✅ Clear architecture diagram
* ✅ Live demo prepared
* ✅ Compelling Cost of Inaction narrative

**Target Automation Level:** 60-70% of end-to-end DQ process
