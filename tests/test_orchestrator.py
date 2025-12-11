"""Test script for DQ Orchestrator Agent."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_orchestrator_full_workflow():
    """Test complete DQ workflow orchestration."""
    print("🤖 Testing Orchestrator Agent - Full Workflow\n")
    print("=" * 60)
    
    try:
        from dq_agents.orchestrator.agent import orchestrator_agent
        from google.genai import types
        
        # Test 1: Full Automated Workflow
        print("\n📋 Test 1: Full Automated Workflow")
        print("-" * 60)
        
        prompt = """
        Execute the complete DQ workflow for table 'policies_week1':
        
        1. Call identifier agent to detect DQ issues and generate rules
        2. Execute the generated rules and identify violations
        3. Call treatment agent to analyze issues and suggest top 3 fixes
        4. Call metrics agent to calculate Cost of Inaction
        5. Generate executive summary report
        
        Provide detailed status updates at each phase.
        """
        
        response = await orchestrator_agent.send_message(prompt)
        print(f"✅ Response:\n{response.text}\n")
        
        # Test 2: Natural Language Request
        print("\n📋 Test 2: Natural Language Request")
        print("-" * 60)
        
        nl_prompt = "Show me the top 5 most critical data quality issues in policies_week1 and tell me how much they're costing us per month"
        
        response2 = await orchestrator_agent.send_message(nl_prompt)
        print(f"✅ Response:\n{response2.text}\n")
        
        # Test 3: Custom Workflow (Identifier + Metrics only)
        print("\n📋 Test 3: Custom Workflow (Detection + Analytics)")
        print("-" * 60)
        
        custom_prompt = """
        For policies_week1:
        1. Call identifier agent to detect issues
        2. Skip treatment and remediation
        3. Call metrics agent to calculate Cost of Inaction
        4. Return analytics summary only
        """
        
        response3 = await orchestrator_agent.send_message(custom_prompt)
        print(f"✅ Response:\n{response3.text}\n")
        
        print("=" * 60)
        print("✅ All orchestrator tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_orchestrator_hitl():
    """Test Human-in-the-Loop checkpoint functionality."""
    print("\n🤖 Testing Orchestrator Agent - HITL Checkpoints\n")
    print("=" * 60)
    
    try:
        from dq_agents.orchestrator.agent import orchestrator_agent
        
        prompt = """
        Demonstrate HITL checkpoint workflow:
        
        1. Detect issues in policies_week1
        2. Request human approval before proceeding to treatment
        3. Show what information would be presented to the user
        4. Explain the approval options available
        """
        
        response = await orchestrator_agent.send_message(prompt)
        print(f"✅ HITL Demonstration:\n{response.text}\n")
        
        print("=" * 60)
        print("✅ HITL test completed!")
        
    except Exception as e:
        print(f"❌ Error during HITL testing: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_agent_coordination():
    """Test how orchestrator coordinates multiple agents."""
    print("\n🤖 Testing Agent Coordination\n")
    print("=" * 60)
    
    try:
        from dq_agents.orchestrator.agent import orchestrator_agent
        
        prompt = """
        Show how you coordinate multiple agents for this scenario:
        
        User wants to:
        - Find all date-related issues in policies_week1
        - Get fix suggestions for future dates
        - Calculate the financial impact
        
        Explain which agents you would call, in what order, and how you would pass information between them.
        """
        
        response = await orchestrator_agent.send_message(prompt)
        print(f"✅ Agent Coordination Plan:\n{response.text}\n")
        
        print("=" * 60)
        print("✅ Coordination test completed!")
        
    except Exception as e:
        print(f"❌ Error during coordination testing: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_bonus_features():
    """Test bonus features integration."""
    print("\n🎁 Testing Bonus Features\n")
    print("=" * 60)
    
    try:
        # Test Agent Debate Logger
        print("\n📋 Test: Agent Debate Logger")
        print("-" * 60)
        
        from dq_agents.bonus_features import AgentDebateLogger
        
        logger = AgentDebateLogger()
        
        # Log some agent thoughts
        logger.log_agent_thought(
            "Identifier",
            "Found 127 violations in policies_week1",
            "Passing violations to Treatment Agent",
            "127 issues identified"
        )
        
        logger.log_agent_thought(
            "Treatment",
            "Analyzing 127 issues. Checking Knowledge Bank...",
            "Found historical precedent with 95% confidence",
            "Recommended fix: SET to NULL"
        )
        
        # Log an agent debate
        logger.log_agent_debate(
            "Treatment",
            "This policy value of £200,000 appears to be an anomaly",
            "Metrics",
            "Actually, this is a valid 'Jumbo Policy' type. Not an error.",
            "Metrics Agent correct. Added 'Jumbo Policy' exception to rules."
        )
        
        formatted_logs = logger.get_formatted_logs()
        print(formatted_logs)
        print("✅ Agent Debate Logger working correctly\n")
        
        # Test Time Travel Diff
        print("\n📋 Test: Time Travel Diff View")
        print("-" * 60)
        
        from dq_agents.bonus_features import TimeTravelDiff
        import pandas as pd
        
        # Create sample data
        original_df = pd.DataFrame({
            'policy_id': [1, 2, 3],
            'date_of_birth': ['2099-01-01', '1985-05-15', '2025-12-31'],
            'premium': [-500, 1000, 300]
        })
        
        fixed_df = pd.DataFrame({
            'policy_id': [1, 2, 3],
            'date_of_birth': [None, '1985-05-15', None],
            'premium': [500, 1000, 300]
        })
        
        confidence_scores = {
            '0_date_of_birth': 0.98,
            '0_premium': 0.92,
            '2_date_of_birth': 0.85
        }
        
        diff = TimeTravelDiff.generate_diff(original_df, fixed_df, confidence_scores)
        print(diff)
        print("✅ Time Travel Diff working correctly\n")
        
        # Test Root Cause Clustering
        print("\n📋 Test: Root Cause Clustering")
        print("-" * 60)
        
        from dq_agents.bonus_features import RootCauseClusterer
        
        # Create sample issues data
        issues_df = pd.DataFrame({
            'policy_id': range(1, 128),
            'error_type': ['future_dob'] * 95 + ['negative_premium'] * 32,
            'source_system': ['Legacy_A'] * 95 + ['System_B'] * 32,
            'created_time': ['00:30'] * 103 + ['14:00'] * 24
        })
        
        clusterer = RootCauseClusterer()
        analysis = clusterer.analyze_metadata(
            issues_df,
            metadata_columns=['source_system', 'created_time']
        )
        
        narrative = clusterer.generate_root_cause_narrative(analysis)
        print(narrative)
        print("✅ Root Cause Clustering working correctly\n")
        
        print("=" * 60)
        print("✅ All bonus features tests completed!")
        
    except Exception as e:
        print(f"❌ Error during bonus features testing: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all orchestrator tests."""
    print("\n")
    print("=" * 60)
    print("  DQ ORCHESTRATOR AGENT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("\n")
    
    # Run all tests
    await test_orchestrator_full_workflow()
    await test_orchestrator_hitl()
    await test_agent_coordination()
    await test_bonus_features()
    
    print("\n")
    print("=" * 60)
    print("  ALL TESTS COMPLETED")
    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
