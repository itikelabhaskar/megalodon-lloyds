# 🔍 Data Quality Management System - README

## Overview

An **AI-powered, multi-agent system** for autonomous detection, treatment, and remediation of data quality issues in Lloyd's Banking Group's BaNCS legacy data. Built with Google's ADK (Agent Development Kit) and deployed on Google Cloud Platform.

## 🌟 Key Features

### Core Capabilities
- **🔍 Autonomous DQ Detection**: AI-generated rules covering all DQ dimensions (Completeness, Accuracy, Timeliness, Conformity, Uniqueness)
- **💊 Intelligent Treatment**: Smart fix suggestions with Knowledge Bank historical precedents
- **🔧 Safe Remediation**: Dry-run validation and Shadow Table testing before production changes
- **📊 Advanced Analytics**: Cost of Inaction analysis, anomaly detection, and executive reporting

### Bonus Features
- **⏱️ Time Travel Diff View**: Side-by-side before/after comparison with confidence scores
- **🤖 Agent Debate Mode**: Live logs showing agent reasoning and collaboration
- **🎯 Root Cause Clustering**: Group similar issues by metadata to fix processes, not just data
- **🛡️ Shadow Validation**: Test fixes in temporary tables before production deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Google Cloud Project with BigQuery and Dataplex APIs enabled
- Service account with appropriate permissions
- `uv` package manager (recommended) or `pip`

### Installation

```powershell
# Clone repository
git clone <repository-url>
cd python-agents_data-science

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install uv
uv sync
```

### Configuration

Create `.env` file:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
BQ_DATA_PROJECT_ID=your-project-id
BQ_DATASET_ID=bancs_data
ROOT_AGENT_MODEL=gemini-2.0-flash
DATASET_CONFIG_FILE=bancs_dataset_config.json
```

### Running the Application

```powershell
.venv\Scripts\Activate.ps1
$env:GOOGLE_CLOUD_PROJECT="your-project-id"
streamlit run streamlit_app/app.py
```

Access at `http://localhost:8501`

## 📖 User Guide

### 1. Identifier Agent - Detect Issues
1. Select tables to analyze
2. Generate DQ rules (AI + pre-existing)
3. Execute rules and view violations
4. Save issues for treatment

### 2. Treatment Agent - Analyze & Fix
1. Select detected issues
2. Review top 3 fix suggestions
3. Check Knowledge Bank precedents
4. Approve fixes for execution

### 3. Remediator Agent - Execute Fixes
1. Review approved fixes
2. Run dry-run preview
3. View Time Travel Diff
4. Execute and validate

### 4. Metrics Agent - Analytics
- Dashboard with charts
- Anomaly detection (IsolationForest)
- Cost of Inaction calculator
- Executive reports (Markdown/HTML)

## 🏗️ Architecture

```
ORCHESTRATOR AGENT
├── Identifier Agent (DQ Detection)
├── Treatment Agent (Fix Suggestions)
├── Remediator Agent (Execution)
└── Metrics Agent (Analytics)
```

## 📊 Key Metrics

| Metric | Target |
|--------|--------|
| Auto-Fix Rate | >80% |
| Remediation Velocity | <24 hours |
| False Positive Rate | <10% |
| Knowledge Bank Hit Rate | >60% |

## 🧪 Testing

```powershell
python test_identifier_agent.py
python test_treatment_agent.py
python test_metrics_agent.py
python test_phase3_phase4_integration.py
```

## 🏢 Cloud Run Deployment

```powershell
gcloud builds submit --tag gcr.io/YOUR_PROJECT/dq-system
gcloud run deploy dq-system --image gcr.io/YOUR_PROJECT/dq-system --region us-central1
```

## 📄 License

Copyright 2025 Google LLC - Apache License 2.0

## 🙏 Acknowledgments

Built for Lloyd's Banking Group Hackathon 2025 with Google Cloud Platform and ADK.

---

**For detailed documentation, see [QUICK_START.md](QUICK_START.md) and [Project.md](Project.md)**
