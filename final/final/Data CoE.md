Summary of Call with platform SMEs and data

# **Key points from** SME call Dec 5 2025

- **Matthew explained the goal is to automate the end-to-end data quality (DQ) management process using a multi-agent system: identifier agent (finds DQ issues), treatment agent (suggests fixes), and remediator agent (implements fixes or creates JIRA tickets if direct remediation isn't possible).**
- **The identifier agent should allow business users to create DQ rules from natural language, generate user-friendly reports, and perform anomaly detection.**
- **Synthetic data modeled on a life and pension system will be provided, with planted DQ issues for teams to discover.**
- **Teams are expected to build agents that can identify DQ issues, generate treatment strategies, and demonstrate remediation, even if only for a few issues.**
- **The approach aims to create consistency, pace, and knowledge banks of DQ rules and treatment strategies for future use.**

**Technical and Practical Considerations:**

- **Mukul asked about the benefits of an agentic approach versus traditional models; Matthew highlighted consistency, support for less experienced teams, and faster issue resolution.**
- **Terri emphasized the identifier agent's ability to ingest multiple sources and generate rules without manual effort.**
- **Umesh asked if DQ rules would be provided; Matthew clarified only synthetic data will be shared, and teams must create their own rules.**
- **Terri noted flexibility in rule definition is more important than exact format, as requirements may change.**

# Summary of the data

## Data Quality Agentic AI Use Case Briefing Pack (PPT)

This presentation sets the stage for a **CIO Hackathon challenge** focused on building an **Agentic AI solution for Data Quality Management (DQM)**. It explains:

- **Objective:** Create a multi-agent system to automate the end-to-end data quality process—identification, treatment, remediation, and metrics.
- **Agents Defined:**

- **Identifier Agent:** Detects anomalies and applies data quality rules.
- **Treatment Agent:** Analyses root causes and suggests strategies.
- **Remediator Agent:** Fixes issues or triggers workflows for human intervention.
- **Metric Agent:** Provides dashboards and KPIs like accuracy, completeness, and cost of inaction.

- **Hackathon Goals:** Build prototypes, design metrics, and demonstrate automation feasibility.
- **Evaluation Criteria:** Automation level, integration with infrastructure, clarity of metrics, and actionable insights.
- **Visuals:** Flow diagrams showing how agents interact, and examples of treatment strategies for common issues (e.g., invalid dates, inconsistent policy details).

## BaNCs Synthetic Data – DQM AI Use Case (Excel)

This file contains **synthetic life and pensions data** modeled on BaNCS systems, deliberately seeded with data quality issues for testing AI agents. Key points:

- **Structure:** Multiple sheets (Week1–Week4) representing snapshots of customer and policy data over time.
- **Fields:** Customer details (name, DOB, NI number, postcode), policy info (policy number, scheme type, renewal date), and financials (gross payment, tax, income, units).

This dataset is meant to **stress-test AI agents** for anomaly detection, rule generation, and remediation strategies.

## BaNCs Synthetic Data (Excel)

This is a **larger, detailed dataset** similar in structure to the previous file but with more extensive records. It serves as the **primary input for building and validating AI-driven data quality solutions**. It includes:

- Rich customer and policy attributes.
- Multiple transaction and payment details.
- Embedded inconsistencies for real-world complexity simulation.