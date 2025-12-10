# Team Megalodon: IP&I Data Quality Agentic AI Challenge (1.1)

## 📌 1. Strategic Context & Problem Statement

**Context:** IP&I (Insurance, Pensions & Investments) aims to migrate 80% of its data to GCP by 2025.

**The Problem:**
- Manual data quality (DQ) checks are slow, inconsistent, and error-prone.
- Data inaccuracies cause risks in: Regulatory reporting, Customer communication, Underwriting, and Operational decisions.

**The Goal:**
- Build an **Agentic AI solution** that detects, categorizes, and remediates data quality issues autonomously.
- Focus on **large-scale anomaly detection** and **remediation** with human oversight.
    

---

## 🛠️ 2. Technology Stack & Platform

### Required GCP Services:
- **BigQuery:** Primary data warehouse and data source for the synthetic BaNCS dataset.
- **Dataplex:** Automated data profiling and standard DQ rule generation.
  - The Identifier Agent **sits on top of Dataplex** to enable business users to create custom rules via natural language.
  - Dataplex provides automated data quality checks, profiling, and cataloging.
- **Cloud Run:** Serverless deployment platform for hosting the agent backend.
- **Vertex AI Agent Builder:** Platform for building and deploying AI agents.

### Recommended Framework:
- **Agent Development Kit (ADK):** Google's open-source framework for building, testing, and deploying multi-agent systems.
  - Easy-to-use interface for agent development
  - Modular and flexible architecture
  - Native multimodal support
  - Built-in tools: Google Search, Code Execution, Vertex AI Search
  - Support for MCP (Model Context Protocol) and A2A (Agent-to-Agent) protocols

### Data Quality Dimensions:
The system must assess data quality across five key dimensions:
1. **Completeness:** Are all required fields populated?
2. **Accuracy:** Are values correct and truthful?
3. **Timeliness:** Is data current and up-to-date?
4. **Conformity:** Does data follow expected formats and standards?
5. **Uniqueness:** Are there duplicate records?
    

---

## 📅 3. Hackathon Timeline

**Date:** December 10-11, 2025

**Day 1 (Dec 10):**
- 08:00-09:00: Arrival & Registration
- 09:00-10:15: Kick-off, Overview, Agentic AI Introduction
- 10:15-11:30: IT Setup (Sandbox access, Wi-Fi)
- 11:30-13:30: Ideation Phase
- 13:30-14:30: Lunch
- 14:30-17:30: Build & Test (with breaks)

**Day 2 (Dec 11):**
- 08:00-11:45: Build & Test continues
- 11:45-12:15: Wrap-up & Presentation Prep
- 12:15-13:15: **Pitches to Coaches** (5 min per team)
- 13:45-14:15: Shortlist announced
- 14:15-16:45: **Pitches to Judges** (8 min + 2 min Q&A)
- 17:00-17:30: Winners announced
    

---

## 🎯 4. The Core Challenge

You must design and prototype **4 cooperating agents** that work together to improve data quality at scale using a provided synthetic dataset (Life & Pensions data modeled on BaNCS).

### Key Objectives:
1. **Identify:** Detect issues using rules & anomaly detection.
2. **Categorize:** Group issues by DQ dimension (Completeness, Accuracy, etc.).
3. **Suggest:** Propose root causes and treatment strategies.
4. **Remediate:** Fix data or raise tickets (with human oversight).
5. **Report:** Visualize impact and "Cost of Inaction."
    

---

## 🤖 3. Agent Specifications

### 🟦 Agent 1: The Identifier
**Role:** The Bridge between Business Users & Technical Rules  
**Input:** Synthetic Data (Excel/BQ), Natural Language Instructions

**Integration with Dataplex:**
- Leverages **Dataplex Profile Scans** to automatically harvest metadata from BigQuery.
- Ingests existing data rules (e.g., from Collibra/Ataccama) as baseline.
- Sits **on top of Dataplex** to enable non-technical business users to create custom DQ rules via natural language.
- Addresses the gap where Dataplex lacks user-friendly report generation for business stakeholders.

**Key Responsibilities:**
- **Rule Generation:** Allow business users to create DQ rules using **Natural Language** (e.g., "Dates must be in the past," "Premiums cannot be negative").
  - Generate rules with reasoning and output to `.yaml` format.
  - Allow Human-in-the-Loop (HITL) to **edit, remove, or add rules** before finalization.
- **Execution:** Apply these rules to the dataset to find missing values, format errors, and mismatches.
- **Anomaly Detection:** Detect issues _not_ caught by rules (e.g., sudden large weekly jumps, pattern breaks across the 4-week snapshot).
  - Use thresholds, frequency comparisons, and statistical methods.
  - Call APIs for advanced anomaly detection using natural language descriptions.
- **Reporting:** Output a **user-friendly report** grouping issues by DQ dimension: **Completeness, Accuracy, Timeliness, Conformity, Uniqueness**
- **Learning:** Reference and refine previous rules as it learns.
  - Store approved rules in the **Knowledge Bank** for future reuse.
    

### 🟪 Agent 2: The Treatment
**Role:** The Strategist & Root Cause Analyst  
**Input:** Identified Issues from Agent 1

**Key Responsibilities:**
- **Root Cause Analysis:** Analyze _why_ the issue happened (e.g., "System migration error," "User entry error").
  - Scan and understand data patterns across the 4-week snapshot to identify root causes.
- **Strategy Generation:** Suggest **3 distinct treatment options** for the user.
  - _Example for incorrect DOB:_
    1. "Check owner's other data sources for correct DOB"
    2. "Perform 3rd party search (e.g., Experian) to retrieve correct details"
    3. "Contact customer directly for verification"
- **Knowledge Bank Integration:**
  - **Query:** Check the Knowledge Bank for previously approved treatment strategies.
  - **Storage Format:** `.yaml file` (DQ rules with metadata), `.csv file` (complete rule definitions), Treatment strategy records (issue type, root cause, approved solutions)
  - **Learning:** If no previous treatment exists, generate new strategy options and store approved ones in the Knowledge Bank for future reuse.
  - **Precedent Reference:** Refer to Collibra or other governance tools for treatment precedents.
- **Human-in-the-Loop:** Present options to the human user for approval (Thumbs up/down).
  - User selects which strategy to proceed with before passing to Remediator Agent.
    

### 🟧 Agent 3: The Remediator
**Role:** The Fixer  
**Input:** Approved Treatment Strategy from Agent 2  
**Note:** This is the most technically challenging agent to build.

**Key Responsibilities:**
- **Execution:**
  - **Simple Fix:** Directly update the data source (Excel/BigQuery) if the fix is deterministic and approved.
    - For hackathon demo: Update the Excel sheet to demonstrate the fix.
  - **Complex Fix:** If a system fix is not possible/safe, generate a **JIRA ticket** with: Issue description and root cause, Proposed treatment strategy, Data location and affected records, Assigned to relevant operational team
- **Validation:** **CRITICAL - Human Validation is REQUIRED** before committing any changes to actual data.
  - Changes involve modifying source data, so human oversight is mandatory.
  - Present proposed changes for review and explicit approval.
- **Audit:** Produce a "Before vs. After" comparison.
  - Show original values vs. corrected values
  - Timestamp and log all changes
  - Track which treatment strategy was applied
    

### 🟩 Agent 4: The Metric
**Role:** The Value Demonstrator & Impact Analyst  
**Input:** Logs from all previous agents

**Key Responsibilities:**
- **Complete Statistics:** Total issues identified (by DQ dimension), Breakdown of issue types (format errors, missing values, anomalies, etc.), Materiality/size of each issue, Issues resolved vs. pending, Time to resolution metrics
- **Impact Analysis:** Calculate the **"Cost of Inaction"** (financial or risk impact if left unfixed).
  - Customer impact assessment
  - Regulatory risk scoring
  - Operational cost estimation
- **Dashboards:** Create Power BI-style views showing: Total issues found vs. fixed, Severity ranking (Critical, Major, Minor), Trends across the 4 weeks of data, Issues by DQ dimension (Completeness, Accuracy, etc.), Treatment strategy effectiveness
- **Success Stats:** E.g., "30% improvement after remediation."
- **Clarity Requirements:** Metrics must be clear in how they're calculated, Inform neutral readers quickly whether there's an issue, Provoke action in the right areas
    

---

## 🔄 5. System Workflow (The "Megalodon" Flow)

1. **Ingest:** Load 4 weeks of synthetic BaNCS data.
2. **Identify:** Identifier Agent scans data + takes NL input → Outputs **Issue List**.
3. **HITL 1:** Human validates/edits rules.
4. **Treat:** Treatment Agent analyzes issues → Outputs **3 Strategy Options**.
5. **HITL 2:** Human selects/approves a strategy.
6. **Remediate:** Remediator Agent executes fix → Updates Data OR Raises Ticket.
7. **HITL 3:** Human validates the data change.
8. **Measure:** Metric Agent calculates ROI/Health → Updates Dashboard.
9. **Loop:** Resolved issues feed back into the **Identifier** to improve future detection.
    

---

## 🧪 6. Data & Evaluation Criteria

### The Dataset
- **Content:** Synthetic Life & Pensions policies (~100 policies, 20+ fields).
- **Structure:** 4 weekly snapshots (Week 1–4).
- **Planted Issues:** Wrong DOB formats, Negative premiums, Missing NI numbers, Policy mismatches, Date inconsistencies
- **Anomalies:** Root-cause patterns hidden inside 4-week trends.
        

### Judging Criteria (Official Hackathon Scoring)
**Target Automation Level:** Aim for **60-70% automation** of the end-to-end DQ process.

**Scoring Breakdown:**
1. **Value & Proposition (20%)** - Does the solution address a real problem with measurable impact? Clear understanding of the problem landscape and solution adoption potential.
2. **Agentic Feasibility (20%)** - Leverages true agentic AI principles (autonomy, decision-making, multi-agent collaboration). Can be realistically implemented and scaled within LBG's tech stack. Must demonstrate real agentic decision-making capabilities (not just if-else code).
3. **Innovation & Originality (20%)** - Novel approach or fresh take on existing challenges. Strong embodiment of Agentic AI principles.
4. **Technical Execution (20%)** - Working prototype/MVP demonstrating core agentic capabilities. Stable, well-documented, minimal bugs. Working demo with Cloud Run backend.
5. **Usability & Accessibility (10%)** - Intuitive, easy to use, quick to understand. Bridge the technical gap for business users.
6. **Presentation & Communication (10%)** - Clear articulation of idea, value, and agentic AI application. Convincing and well-structured presentation.
    

---

## 📦 7. Deliverables Checklist

### Core Deliverables:
1. [ ] **Agentic System Prototype:** 4 Agents (or 3 + Metric capability) built using **ADK** or equivalent framework. Demonstrates true multi-agent collaboration (not sequential scripts). Implements MCP/A2A protocols where applicable.
2. [ ] **UI/Screenshots:** User-friendly interface for business users, Dashboard visualizations, Before/After comparisons
3. [ ] **Cloud Run Backend:** Deployed and accessible, Integrated with BigQuery and Dataplex
4. [ ] **Knowledge Bank Implementation:** Storage for DQ rules (`.yaml` format), Treatment strategy repository, Learning/feedback loop mechanism
5. [ ] **Final Report:** Issues Found (detailed list of planted DQ issues identified), Rules Created (generated DQ rules with natural language inputs used), Treatments Proposed (strategy options generated for each issue), Fixes Applied (data corrections made with before/after evidence), Metrics & Impact Analysis (complete statistics and Cost of Inaction calculations)

### Demonstration Requirements:
- **Pitch to Coaches:** 5 minutes on Day 2 (12:15 PM)
- **Pitch to Judges:** 8 minutes + 2 minutes Q&A (if shortlisted)
- **Format:** Slides, live demo, or any creative presentation format

### Success Metrics:
- **Issue Detection Rate:** What % of planted issues did you find?
- **Automation Level:** How much of the process is automated? (Target: 60-70%)
- **Treatment Success:** How many issues did you successfully remediate?
- **Business Value:** Clear ROI and impact demonstration