"""
Test script for the Identifier Agent using ADK Runner
"""

import os
import sys
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from google.genai import types
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from dq_agents.identifier.agent import get_identifier_agent

load_dotenv()

def test_identifier():
    """Test the Identifier Agent with sample queries"""
    print("🔍 Testing Identifier Agent\n")
    print("="*70)
    
    # Set up session and runner
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    
    # Create session synchronously
    session = asyncio.run(session_service.create_session(
        app_name="DQIdentifierAgent",
        user_id="test_user"
    ))
    
    identifier_agent = get_identifier_agent()
    
    runner = Runner(
        app_name="DQIdentifierAgent",
        agent=identifier_agent,
        artifact_service=artifact_service,
        session_service=session_service,
    )
    
    # Test 1: Get schema
    print("\nTest 1: Get table schema for policies_week1")
    print("-"*70)
    try:
        prompt1 = "Get the schema for table 'policies_week1' and list the first 10 columns with their types"
        content1 = types.Content(role="user", parts=[types.Part(text=prompt1)])
        events1 = list(runner.run(
            user_id="test_user",
            session_id=session.id,
            new_message=content1
        ))
        
        last_event1 = events1[-1]
        response1 = "".join([part.text for part in last_event1.content.parts if part.text])
        print(f"✅ Response received:\n{response1[:800]}...\n")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
    
    print("="*70)
    
    # Test 2: Generate DQ rule
    print("\nTest 2: Generate DQ rule for invalid DOB")
    print("-"*70)
    try:
        prompt2 = """Based on the BaNCS data schema, generate a DQ rule that checks for 
        invalid date of birth values (CUS_DOB field). The rule should catch:
        - Future dates
        - NULL values
        - Empty strings
        
        Return it in JSON format with fields: rule_id, name, description, sql, severity, dq_dimension."""
        content2 = types.Content(role="user", parts=[types.Part(text=prompt2)])
        events2 = list(runner.run(
            user_id="test_user",
            session_id=session.id,
            new_message=content2
        ))
        
        last_event2 = events2[-1]
        response2 = "".join([part.text for part in last_event2.content.parts if part.text])
        print(f"✅ Response received:\n{response2}\n")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
    
    print("="*70)
    print("\n✅ Identifier agent tests complete")

if __name__ == "__main__":
    try:
        test_identifier()
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
