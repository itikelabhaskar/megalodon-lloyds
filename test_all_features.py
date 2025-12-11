#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite for DQ Management System
Tests all features that can be verified programmatically
"""

import os
import sys
import json
import time
from datetime import datetime

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []
        
    def test(self, name, test_func):
        """Run a single test"""
        print(f"\n{BLUE}TEST: {name}{RESET}")
        try:
            result = test_func()
            if result is True:
                print(f"{GREEN}✅ PASS{RESET}")
                self.passed += 1
                self.results.append({"name": name, "status": "PASS"})
                return True
            elif result is False:
                print(f"{RED}❌ FAIL{RESET}")
                self.failed += 1
                self.results.append({"name": name, "status": "FAIL"})
                return False
            else:
                print(f"{YELLOW}⚠️  WARNING: {result}{RESET}")
                self.warnings += 1
                self.results.append({"name": name, "status": "WARNING", "message": result})
                return True
        except Exception as e:
            print(f"{RED}❌ FAIL - Exception: {str(e)[:150]}{RESET}")
            self.failed += 1
            self.results.append({"name": name, "status": "FAIL", "error": str(e)[:150]})
            return False
    
    def summary(self):
        """Print test summary"""
        total = self.passed + self.failed + self.warnings
        print(f"\n{'='*80}")
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print(f"{'='*80}")
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        print(f"Pass Rate: {(self.passed/total*100):.1f}%")
        print(f"{'='*80}\n")
        
        return self.failed == 0

# Initialize test runner
runner = TestRunner()

print(f"{BLUE}{'='*80}")
print(f"DQ MANAGEMENT SYSTEM - AUTOMATED TEST SUITE")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}{RESET}\n")

# ============================================================================
# PHASE 1: ENVIRONMENT TESTS
# ============================================================================
print(f"\n{BLUE}{'='*80}")
print("PHASE 1: ENVIRONMENT TESTS")
print(f"{'='*80}{RESET}")

def test_python_version():
    import sys
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    return version.major == 3 and version.minor >= 12

def test_venv_active():
    venv_path = os.environ.get('VIRTUAL_ENV', '')
    print(f"   Virtual env: {venv_path}")
    return '.venv' in venv_path or 'venv' in venv_path

def test_gcp_auth():
    import subprocess
    result = subprocess.run(['gcloud', 'auth', 'list', '--format=value(account)'], 
                          capture_output=True, text=True)
    account = result.stdout.strip()
    print(f"   Account: {account}")
    return '@' in account

def test_gcp_project():
    import subprocess
    result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                          capture_output=True, text=True)
    project = result.stdout.strip()
    print(f"   Project: {project}")
    return len(project) > 0

runner.test("Python Version (>=3.12)", test_python_version)
runner.test("Virtual Environment Active", test_venv_active)
runner.test("GCP Authentication", test_gcp_auth)
runner.test("GCP Project Configured", test_gcp_project)

# ============================================================================
# PHASE 2: DEPENDENCY TESTS
# ============================================================================
print(f"\n{BLUE}{'='*80}")
print("PHASE 2: DEPENDENCY TESTS")
print(f"{'='*80}{RESET}")

def test_google_adk():
    import google.adk
    print(f"   Version: {google.adk.__version__ if hasattr(google.adk, '__version__') else 'unknown'}")
    return True

def test_bigquery():
    from google.cloud import bigquery
    client = bigquery.Client()
    print(f"   Client initialized for project: {client.project}")
    return True

def test_dataplex():
    from google.cloud import dataplex_v1
    client = dataplex_v1.DataScanServiceClient()
    print(f"   DataScan client initialized")
    return True

def test_streamlit():
    import streamlit
    print(f"   Version: {streamlit.__version__}")
    return True

def test_pandas():
    import pandas as pd
    print(f"   Version: {pd.__version__}")
    return True

runner.test("Google ADK", test_google_adk)
runner.test("BigQuery Client", test_bigquery)
runner.test("Dataplex Client", test_dataplex)
runner.test("Streamlit", test_streamlit)
runner.test("Pandas", test_pandas)

# ============================================================================
# PHASE 3: CONFIGURATION TESTS
# ============================================================================
print(f"\n{BLUE}{'='*80}")
print("PHASE 3: CONFIGURATION TESTS")
print(f"{'='*80}{RESET}")

def test_env_config_exists():
    exists = os.path.exists('environment_config.json')
    if exists:
        with open('environment_config.json', 'r') as f:
            config = json.load(f)
        print(f"   Project: {config.get('project_id')}")
        print(f"   Dataset: {config.get('bigquery', {}).get('dataset_id')}")
    return exists

def test_cache_file():
    exists = os.path.exists('dq_rules_cache.json')
    if exists:
        with open('dq_rules_cache.json', 'r') as f:
            cache = json.load(f)
        tables_cached = len(cache.get('tables', {}))
        print(f"   Cached tables: {tables_cached}")
    else:
        print(f"   Cache will be created on first use")
    return True  # Not required

def test_knowledge_bank():
    exists = os.path.exists('knowledge_bank/knowledge_bank.json')
    if exists:
        with open('knowledge_bank/knowledge_bank.json', 'r') as f:
            kb = json.load(f)
        print(f"   Entries: {len(kb)}")
    return exists

runner.test("Environment Config File", test_env_config_exists)
runner.test("DQ Rules Cache", test_cache_file)
runner.test("Knowledge Bank", test_knowledge_bank)

# ============================================================================
# PHASE 4: BIGQUERY ACCESS TESTS
# ============================================================================
print(f"\n{BLUE}{'='*80}")
print("PHASE 4: BIGQUERY ACCESS TESTS")
print(f"{'='*80}{RESET}")

def test_list_tables():
    from google.cloud import bigquery
    client = bigquery.Client(project='hackathon-practice-480508')
    dataset_ref = bigquery.DatasetReference('hackathon-practice-480508', 'bancs_dataset')
    tables = list(client.list_tables(dataset_ref))
    print(f"   Found {len(tables)} tables:")
    for table in tables:
        print(f"      - {table.table_id}")
    return len(tables) >= 4

def test_query_table():
    from google.cloud import bigquery
    client = bigquery.Client(project='hackathon-practice-480508')
    query = 'SELECT COUNT(*) as row_count FROM `hackathon-practice-480508.bancs_dataset.policies_week1`'
    result = client.query(query).result()
    for row in result:
        print(f"   Row count: {row.row_count}")
        return row.row_count > 0
    return False

def test_table_schema():
    from google.cloud import bigquery
    client = bigquery.Client(project='hackathon-practice-480508')
    table = client.get_table('hackathon-practice-480508.bancs_dataset.policies_week1')
    print(f"   Columns: {len(table.schema)}")
    print(f"   Sample columns: {[f.name for f in table.schema[:5]]}")
    return len(table.schema) > 0

runner.test("List BigQuery Tables", test_list_tables)
runner.test("Query BigQuery Data", test_query_table)
runner.test("Get Table Schema", test_table_schema)

# ============================================================================
# PHASE 5: AGENT MODULE TESTS
# ============================================================================
print(f"\n{BLUE}{'='*80}")
print("PHASE 5: AGENT MODULE TESTS")
print(f"{'='*80}{RESET}")

def test_identifier_agent():
    from dq_agents.identifier.agent import get_identifier_agent
    agent = get_identifier_agent()
    print(f"   Agent name: {agent.name}")
    return True

def test_treatment_agent():
    from dq_agents.treatment.agent import treatment_agent
    print(f"   Agent name: {treatment_agent.name}")
    return True

def test_remediator_agent():
    from dq_agents.remediator.agent import remediator_agent
    print(f"   Agent name: {remediator_agent.name}")
    return True

def test_metrics_agent():
    from dq_agents.metrics.agent import metrics_agent
    print(f"   Agent name: {metrics_agent.name}")
    return True

runner.test("Import Identifier Agent", test_identifier_agent)
runner.test("Import Treatment Agent", test_treatment_agent)
runner.test("Import Remediator Agent", test_remediator_agent)
runner.test("Import Metrics Agent", test_metrics_agent)

# ============================================================================
# PHASE 6: TOOL AVAILABILITY TESTS
# ============================================================================
print(f"\n{BLUE}{'='*80}")
print("PHASE 6: TOOL AVAILABILITY TESTS")
print(f"{'='*80}{RESET}")

def test_identifier_tools():
    from dq_agents.identifier.tools import (
        get_table_schema,
        trigger_dataplex_scan,
        execute_dq_rule
    )
    print(f"   ✓ get_table_schema")
    print(f"   ✓ trigger_dataplex_scan")
    print(f"   ✓ execute_dq_rule")
    return True

def test_treatment_tools():
    from dq_agents.treatment.tools import (
        execute_dq_rule,
        calculate_fix_impact
    )
    print(f"   ✓ execute_dq_rule")
    print(f"   ✓ calculate_fix_impact")
    return True

runner.test("Identifier Tools Available", test_identifier_tools)
runner.test("Treatment Tools Available", test_treatment_tools)

# ============================================================================
# PHASE 7: ADK FUNCTIONALITY TESTS
# ============================================================================
print(f"\n{BLUE}{'='*80}")
print("PHASE 7: ADK FUNCTIONALITY TESTS")
print(f"{'='*80}{RESET}")

def test_session_creation():
    import asyncio
    from google.adk.sessions import InMemorySessionService
    
    session_service = InMemorySessionService()
    session = asyncio.run(session_service.create_session(
        app_name='TestApp',
        user_id='test_user'
    ))
    print(f"   Session ID: {session.id[:16]}...")
    return len(session.id) > 0

def test_artifact_service():
    from google.adk.artifacts import InMemoryArtifactService
    artifact_service = InMemoryArtifactService()
    print(f"   Artifact service initialized")
    return True

runner.test("ADK Session Creation", test_session_creation)
runner.test("ADK Artifact Service", test_artifact_service)

# ============================================================================
# PHASE 8: FUNCTIONAL TESTS (Schema Retrieval)
# ============================================================================
print(f"\n{BLUE}{'='*80}")
print("PHASE 8: FUNCTIONAL TESTS")
print(f"{'='*80}{RESET}")

def test_get_schema_tool():
    from dq_agents.identifier.tools import get_table_schema
    
    class MockContext:
        pass
    
    context = MockContext()
    result = get_table_schema('policies_week1', context)
    
    # Check if result is valid JSON string
    if isinstance(result, str):
        schema_data = json.loads(result)
        columns = schema_data.get('columns', [])
        print(f"   Columns retrieved: {len(columns)}")
        return len(columns) > 0
    return False

runner.test("Get Table Schema Tool", test_get_schema_tool)

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print(f"\n{BLUE}{'='*80}")
print(f"TEST EXECUTION COMPLETED")
print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}{RESET}")

success = runner.summary()

# Save results to file
results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(results_file, 'w') as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": runner.passed + runner.failed + runner.warnings,
            "passed": runner.passed,
            "failed": runner.failed,
            "warnings": runner.warnings,
            "pass_rate": f"{(runner.passed/(runner.passed+runner.failed+runner.warnings)*100):.1f}%"
        },
        "results": runner.results
    }, f, indent=2)

print(f"\n{GREEN}✅ Test results saved to: {results_file}{RESET}\n")

# Exit with appropriate code
sys.exit(0 if success else 1)
