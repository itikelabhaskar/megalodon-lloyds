
# EXTREMENLY IMPORTANT DECK, FOCUSES ON THIS HACKATHON, MUST GO THROUGH
# Data Quality Mgt AI Use Case

### Title

- **Creation of a Central Data Quality Management (DQM) Agentic AI solution**
    

### Content

- Create a multi agent system that automates DQ identification, treatment strategy generation and remediation fix.
    
- Synthetic data has been provided with various DQ issues and anomalies planted within it.
    

### The Ask

- We would like you to:
    
    - build the 3 key agents (identifier, treatment and remediator agents) that meet the key requirements in this briefing.
        
    - design a set of relevant metrics that give the consumers a quick view of the materiality of DQ issues identified and build a 4th Metric Agent that can build Power BI views.
        
    - identify as many of the DQ issues and anomalies in the data provided as possible via the AI agents you have built, with proposed treatment strategies to fix and if possible, attempts made to clean the data.
        

### Data Limitations

- The synthetic data is in the format of IP&I BaNCS Life & Pensions data (modelled on the BaNCS Valuations Foundation Data Product design) and we have planted various DQ issues and anomalies within it.
    

---

# The Key Agents

**System Overview:** An intelligent, automated multi-agent system with multiple agents working together.

### 1. The 'Identifier' Agent

**Function:** To scan a data source, create and refine relevant DQ rules, identify DQ issues and anomalies, and automate manual process steps and trigger the Treatment Agent if issue is found.

- **Mini agents/workflows:** This agent includes sub-processes:
    
    - `Dataplex profile` $\rightarrow$ `AI generated data quality rules` $\rightarrow$ `HITL (Human In The Loop)` $\rightarrow$ `DQ rules`
        

**$\downarrow$ (Next Step)**

### 2. The 'Treatment' Agent

**Function:** To enrich an issue, determine its root cause, priority and treatment strategy options and assign it to an owner.

**$\downarrow$ (Next Step)**

### 3. The 'Remediator' Agent

**Function:** To fix directly in the source system or manage the human-in-the-loop process of fixing the issue.

- **Exception Handling:** Automated JIRA tickets to Operational teams if system fix is not possible.
    

**$\downarrow$ (Next Step)**

### 4. The 'Metric' Agent

**Function:** To create a clear suite of metrics that help inform the business of customer impact, materiality and cost of inaction.

> **Note on Process Flow:** While the main flow is linear (Identifier $\rightarrow$ Treatment $\rightarrow$ Remediator $\rightarrow$ Metric), there is also a direct feed from the **Treatment Agent** to the **Metric Agent**, bypassing the Remediator for reporting purposes.

---

# Multi-Agent System Potential Flow

**Overview:** This process map details the end-to-end lifecycle of a Data Quality issue, distinguishing between automated AI steps and "Human in the loop" interventions.

### Step 1: Identification & Rule Generation

The **Identifier Agent** ingests data from two sources:

1. **BigQuery** $\rightarrow$ **Dataplex Profile Scan** $\rightarrow$ **Automatically harvested Metadata**
    
2. **Existing Data Rules** (e.g., Collibra/Ataccama)
    

- **Action:** The Identifier Agent generates DQ rules with reasoning.
    
- **Human in the loop:** A human user reviews the AI output to **Edit, remove, or add rules**.
    
- **Output:** This results in a `.yaml file`.
    

### Step 2: Knowledge Bank

- The system stores the `.yaml file` and a `.csv file (whole rule)` into the **Knowledge Bank**.
    
- **Trigger:** A **DQ Issue** is identified from this bank and sent to the Treatment Agent.
    

### Step 3: Strategy Formulation

- **Treatment Agent:** Receives the DQ Issue and **generates treatment strategies** to fix it.
    
- **Human in the loop:** A human reviews the proposed strategies and provides approval (represented by thumbs up/down).
    
- **Output:** **Approved treatment** is sent forward.
    

### Step 4: Remediation

- **Remediator Agent:** Receives the Approved treatment.
    
- **Human in the loop:** A human executes the final validation or fix:
    
    - _Validate_ (for Simple DQ Treatments)
        
    - _Manual Intervention_ (for Complex DQ Treatments)
        

### Step 5: Resolution Loop

- **Outcome:** **DQ Issue Fixed**.
    
- **Feedback:** The process loops back from "DQ Issue Fixed" to the **Identifier Agent**, closing the cycle for continuous learning.




# DQM Hack Challenge & Focus Areas

### Your Challenge:

- build the 3 key agents (identifier, treatment and remediator agents) that meet the key requirements in this briefing.
    
- design a set of relevant metrics that give the consumers a quick view of the materiality of DQ issues identified and build a 4th Metric Agent that can build Power BI views.
    
- identify as many of the DQ issues and anomalies in the data provided as possible via the AI agents you have built, with proposed treatment strategies to fix and if possible, attempts made to clean the data.
    

**Judges will be looking at whether you have fulfilled the following requirements in the build of the Agents:**
# DQM AI Agent Design

### DQM AI Agent Design

**Purpose:** Create a multi agent framework that automates as much of the e2e DQ process as possible with a route to live plan.

1. How well automated is the design? How well does this the design integrate with LBG infrastructure?
    
2. Is the design enduring, coherent and compliant?
    
3. Do the teams help judges understand the problem and the value of the solution?
    
4. Do you have a feasible route to live plan? Does it include resource, requirements and timescales?
    

---

### DQ Identifier Agent

**Purpose:** Identify the issues planted in the anonymised data, show them in a user friendly report and fulfil the below goals.

1. Agent can recommend an initial set of valid rules
    
2. Agent can reference, use and refine previous rules as it learns
    
3. Agent is allowing generation of rules from natural language
    
4. Anomaly detection - Agent can call an API to create anomaly detection using natural language – based on thresholds, frequency of comparison, etc.
    
5. Agent can load outputs into user friendly reports.
    

---

### DQ Treatment Agent

**Purpose:** Create value add treatment strategy options for the user to consider for each DQ issue.

1. Analyse and articulate the root cause of the issue.
    
2. Refer to previously defined DQ treatment strategies from Collibra to understand if there is treatment precedent for the particular issue identified.
    
3. If no previous treatment is available, the Agent should create a relevant set of treatment strategy options for the DQ issue for the user to consider.
    
4. A Knowledge Bank should be created which stores all of the previously approved treatment strategies.
    

---

### DQ Remediator Agent

**Purpose:** Create an agent that can automate the fix in the source system or if not possible, generate a workflow ticket for relevant team.

1. Understand what would need to be built to be able to fix DQ issues in source systems.
    
2. Build the agent and attempt to clean the DQ issues, where possible.
    
3. If not possible, introduce capability to create a ticket in JIRA with the proposed treatment strategy that is sent through to the relevant team to fix.
    

---

### DQ Metrics Agent

**Purpose:** Create an agent and design a set of metrics that provide a clear view of the materiality of the DQ issues raised.

1. Are the metrics clear in how they are calculated and their value?
    
2. Do they inform a neutral reader quickly whether there is an issue or not? And do they inform the business of impact, materiality and cost of inaction.
    
3. Do they help provoke action in the right area?
    
4. Can the agent collate the information into a self serve dashboard of data quality.



## Hand written notes
# NOTES

### Core Objective

- Build **3 key agents** in particular: Identifier, Treatment, and Remediator.
    
- **Prototype:** A prototype for these agents is required.
    

### 1. Identifier Agent

- **Function:** Apply DQ (Data Quality) rules and present findings in a user-friendly report.
    
- **Capabilities:**
    
    - it should learn from previous rules.
        
    - Generate rules from **natural language** (bridging the gap between technical and business users).
        
    - Output to user-friendly reports.
        
- **Anomaly Detection:** Identify issues that escape standard DQ rules (e.g., large data changes day-to-day or month-to-month).
    
- **Integration with Dataplex:**
    
    - Dataplex handles data profiling and standard DQ issues.
        
    - The Identifier Agent sits on top of Dataplex to allow business users (without coding experience) to create new rules via natural language and push them into Dataplex.
        
    - It addresses the gap where Dataplex does not provide user-friendly reports for business users.
        

### 2. Treatment Agent

- **Workflow Example:** If the Identifier Agent finds an incorrect DOB (Date of Birth), it passes it to the Treatment Agent.
    
- **Fixing Strategies:**
    
    - Check if the owner has other data sources containing the correct DOB.
        
    - Perform a 3rd party search (e.g., Experian) to retrieve correct details.
        
    - Contact the customer directly.
        
- **Goal:** Suggest strategies to business users, making it easy for them to query via natural language and assist in treatment.
    
- **Knowledge Bank:** The agent builds knowledge over time, storing learned strategies and solutions in a Knowledge Bank for future reuse.
    

### 3. Remediator Agent

- **Status:** This is the toughest agent to build.
    
- **Function:** Perform the actual fixing of data.
    
- **Fallback:** If a fix isn't possible, it must raise a ticket.
    
- **Validation:** The output **must be validated by a human** because it involves changing actual data.
    
- **Hackathon Context:** For this challenge, the agent can update the Excel sheet to demonstrate the fix (no need to mask data).
    

### 4. Metric Agent

- **Function:** Understand the impact of issues and the value of fixing them.
    
- **Output:** Provide complete statistics (e.g., total issues, breakdown of issue types, materiality/size of issues).
    

### Process & Human Intervention

- **Human-in-the-Loop:** Human intervention is required at each stage between agents (e.g., between Identifier and Treatment).
    
    - Humans must validate the relevance of the output at each stage.
        
    - If the agent proposes 3 solutions, the human picks the one to proceed with.
        
- **Agent Output:** The final report should state:
    
    - "We identified these issues."
        
    - "These strategies were generated."
        
    - "These fixes were made in the Excel sheet."
        

### Data & Challenge Details

- **Data Source:** Synthetic data is provided (4 weeks of data, 100 policies, 20 fields).
    
- **Planted Issues:** Issues and anomalies have been deliberately planted in the data.
    
- **Root Cause Analysis:** Scanning and understanding the data well should reveal the root causes behind the issues.
    
- **Success Metrics:**
    
    - How well can you identify the planted issues?
        
    - How far can you automate the process? (Aim for **60-70% automation**).