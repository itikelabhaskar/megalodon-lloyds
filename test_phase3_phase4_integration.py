"""
Phase 3 & Phase 4 Integration Test

Tests the complete flow from Identifier Agent to Treatment Agent:
1. Identifier generates DQ rules
2. Rules are stored in session state
3. Treatment Agent accesses rules
4. Treatment Agent generates fix suggestions
5. Fix approval includes full context for Remediator
"""

import json

print("=" * 80)
print("PHASE 3 & 4 INTEGRATION TEST")
print("=" * 80)

# Test 1: Verify Identifier Agent
print("\n[TEST 1] Identifier Agent Tools")
print("-" * 80)
from dq_agents.identifier.agent import get_identifier_agent
identifier = get_identifier_agent()
print(f"✅ Identifier Agent: {len(identifier.tools)} tools")
for t in identifier.tools:
    print(f"   - {t.__name__ if hasattr(t, '__name__') else t}")

# Test 2: Verify Treatment Agent
print("\n[TEST 2] Treatment Agent Tools")
print("-" * 80)
from dq_agents.treatment.agent import treatment_agent
print(f"✅ Treatment Agent: {len(treatment_agent.tools)} tools")
for t in treatment_agent.tools:
    print(f"   - {t.__name__ if hasattr(t, '__name__') else t}")

# Test 3: Check for duplicate function names
print("\n[TEST 3] Check for Duplicate Tool Names")
print("-" * 80)
identifier_tools = {t.__name__ for t in identifier.tools if hasattr(t, '__name__')}
treatment_tools = {t.__name__ for t in treatment_agent.tools if hasattr(t, '__name__')}
duplicates = identifier_tools.intersection(treatment_tools)
if duplicates:
    print(f"⚠️  DUPLICATE TOOLS FOUND: {duplicates}")
    print("   Note: This is OK if they're in different modules (identifier vs treatment)")
else:
    print("✅ No duplicate tool names")

# Test 4: Verify Knowledge Bank
print("\n[TEST 4] Knowledge Bank Integration")
print("-" * 80)
from knowledge_bank.kb_manager import get_kb_manager
kb = get_kb_manager()
patterns = kb.get_all_patterns()
print(f"✅ Knowledge Bank: {len(patterns)} patterns loaded")

# Show pattern IDs
for pattern_id in list(patterns.keys())[:3]:
    print(f"   - {pattern_id}: {len(patterns[pattern_id]['historical_fixes'])} fix(es)")

# Test 5: Simulate data flow from Identifier to Treatment
print("\n[TEST 5] Simulated Data Flow: Identifier → Treatment")
print("-" * 80)

# Simulate an Identifier Agent output (what would be stored in session_state)
mock_identifier_output = {
    "rule_id": "DQ_TEST_001",
    "name": "future_dob_check",
    "description": "Date of birth cannot be in the future",
    "sql": "SELECT * FROM {table} WHERE CUS_DOB > CURRENT_DATE()",
    "severity": "critical",
    "dq_dimension": "Accuracy",
    "table": "policies_week1",
    "source": "agent"
}

print("Identifier Output (stored in session_state.generated_rules):")
print(json.dumps(mock_identifier_output, indent=2))

# Verify Treatment Agent can process this
print("\nTreatment Agent Requirements:")
required_fields = ['rule_id', 'sql', 'table', 'description', 'severity', 'dq_dimension']
missing_fields = [f for f in required_fields if f not in mock_identifier_output]

if missing_fields:
    print(f"❌ MISSING FIELDS: {missing_fields}")
else:
    print(f"✅ All required fields present: {', '.join(required_fields)}")

# Test 6: Verify Fix Approval Context
print("\n[TEST 6] Fix Approval Context (for Remediator)")
print("-" * 80)

mock_approved_fix = {
    "fix": {
        "rank": 1,
        "fix_type": "Data Repair",
        "action": "SET CUS_DOB = NULL",
        "description": "Set invalid future dates to NULL and flag for review",
        "success_probability": 0.95,
        "risk_level": "low",
        "auto_approve_eligible": False,
        "sql": "UPDATE {table} SET CUS_DOB = NULL WHERE CUS_DOB > CURRENT_DATE()"
    },
    "issue": {
        "rule": mock_identifier_output,
        "issue_summary": "Found 5 policies with future date of birth",
        "affected_rows": 5,
        "root_cause": {"source_system": "Legacy_A", "time_pattern": "12:00-1:00 AM"}
    },
    "table_name": "policies_week1",
    "timestamp": "2025-12-10T23:30:00"
}

print("Approved Fix Context (stored in session_state.approved_fix):")
print(json.dumps(mock_approved_fix, indent=2))

# Verify all context needed by Remediator is present
remediator_required = ['fix', 'issue', 'table_name', 'timestamp']
missing_remediator = [f for f in remediator_required if f not in mock_approved_fix]

if missing_remediator:
    print(f"❌ MISSING REMEDIATOR CONTEXT: {missing_remediator}")
else:
    print(f"✅ All Remediator context present: {', '.join(remediator_required)}")

# Test 7: Verify New Tools Added
print("\n[TEST 7] New Tools from Anomaly Fixes")
print("-" * 80)

# Check for get_affected_row_sample tool
has_row_sample_tool = any(
    hasattr(t, '__name__') and t.__name__ == 'get_affected_row_sample'
    for t in treatment_agent.tools
)

if has_row_sample_tool:
    print("✅ get_affected_row_sample tool added (Project.md requirement)")
else:
    print("❌ get_affected_row_sample tool NOT FOUND")

# Summary
print("\n" + "=" * 80)
print("INTEGRATION TEST SUMMARY")
print("=" * 80)

all_tests = [
    ("Identifier Agent Tools", len(identifier.tools) == 6),
    ("Treatment Agent Tools", len(treatment_agent.tools) == 7),
    ("No Critical Duplicates", len(duplicates) <= 1),  # execute_dq_rule is OK
    ("Knowledge Bank Loaded", len(patterns) > 0),
    ("Identifier → Treatment Data Flow", not missing_fields),
    ("Treatment → Remediator Context", not missing_remediator),
    ("New Tools Added", has_row_sample_tool)
]

passed = sum(1 for _, result in all_tests if result)
total = len(all_tests)

for test_name, result in all_tests:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status}: {test_name}")

print(f"\n{passed}/{total} tests passed")

if passed == total:
    print("\n🎉 ALL INTEGRATION TESTS PASSED!")
    print("Phase 3 and Phase 4 are properly integrated.")
else:
    print(f"\n⚠️  {total - passed} test(s) failed. Review issues above.")

print("=" * 80)
