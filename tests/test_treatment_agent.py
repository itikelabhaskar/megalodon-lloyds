"""
Test Treatment Agent

This script tests the Treatment Agent's functionality including:
- DQ rule execution
- Knowledge Bank search
- Fix suggestion generation
- Root cause analysis
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from dq_agents.treatment.agent import treatment_agent
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner


async def test_treatment_agent():
    print("🧪 Testing Treatment Agent\n")
    print("=" * 80)
    
    # Set up ADK components
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    
    session = await session_service.create_session(
        app_name="DQTreatmentAgent",
        user_id="test_user"
    )
    
    runner = Runner(
        app_name="DQTreatmentAgent",
        agent=treatment_agent,
        artifact_service=artifact_service,
        session_service=session_service,
    )
    
    # Test 1: Knowledge Bank Search
    print("\n📚 TEST 1: Knowledge Bank Search")
    print("-" * 80)
    
    prompt1 = """
    Search the Knowledge Bank for issues related to:
    "Date of birth is in the future"
    
    Use the search_knowledge_bank tool.
    """
    
    response1 = await runner.run_async(
        message=prompt1,
        session_id=session.session_id
    )
    
    print(f"Response: {response1.response[:500]}...")
    
    # Test 2: Execute DQ Rule
    print("\n\n🔍 TEST 2: Execute DQ Rule")
    print("-" * 80)
    
    prompt2 = """
    Execute this DQ rule to find violations:
    
    SQL: SELECT * FROM `{table}` WHERE POLI_GROSS_PMT < 0
    Table: policies_week1
    
    Use the execute_dq_rule tool.
    """
    
    response2 = await runner.run_async(
        message=prompt2,
        session_id=session.session_id
    )
    
    print(f"Response: {response2.response[:800]}...")
    
    # Test 3: Generate Fix Suggestions
    print("\n\n💡 TEST 3: Generate Fix Suggestions")
    print("-" * 80)
    
    prompt3 = """
    **DQ ISSUE ANALYSIS**
    
    Issue: "Premium amount is negative"
    Rule SQL: SELECT * FROM `{table}` WHERE POLI_GROSS_PMT < 0
    Table: policies_week1
    Severity: high
    DQ Dimension: Accuracy
    
    **YOUR TASKS:**
    1. Execute the DQ rule using execute_dq_rule() to find violations
    2. Search Knowledge Bank using search_knowledge_bank() for similar issues
    3. Analyze the violations
    4. Generate TOP 3 fix suggestions
    
    Return a JSON object with:
    - issue_summary
    - affected_rows
    - knowledge_bank_match
    - fix_suggestions (array of 3 fixes with rank, fix_type, action, description, success_probability, risk_level, auto_approve_eligible, sql)
    """
    
    response3 = await runner.run_async(
        message=prompt3,
        session_id=session.session_id
    )
    
    print(f"Response:\n{response3.response}")
    
    # Test 4: Query Related Data
    print("\n\n🔗 TEST 4: Query Related Data (Cross-Week)")
    print("-" * 80)
    
    prompt4 = """
    Query customer data across all weeks for customer_id = 'CUS_001'
    
    Use the query_related_data tool with all_weeks=True.
    """
    
    response4 = await runner.run_async(
        message=prompt4,
        session_id=session.session_id
    )
    
    print(f"Response: {response4.response[:500]}...")
    
    print("\n\n" + "=" * 80)
    print("✅ All Treatment Agent tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_treatment_agent())
