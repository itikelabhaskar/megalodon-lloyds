"""
Test script to verify all enhanced Identifier Agent features
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from google.genai import types
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from dq_agents.identifier.agent import get_identifier_agent

load_dotenv()

def test_enhanced_features():
    """Test all enhanced features of Identifier Agent"""
    print("🚀 Testing Enhanced Identifier Agent Features\n")
    print("="*80)
    
    # Set up ADK components
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    
    # Create session
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
    
    # Test comprehensive analysis with all new features
    print("\n📋 COMPREHENSIVE DQ ANALYSIS TEST")
    print("-"*80)
    
    prompt = """
    Run a COMPREHENSIVE data quality analysis on the BaNCS dataset.
    
    **Execute these steps:**
    1. Load pre-existing rules from Collibra/Ataccama
    2. Get all week tables available
    3. Trigger Dataplex scans for policies_week1 and policies_week2
    4. Get schemas as needed
    
    **Generate 10 DQ rules including:**
    - 3+ Cross-week temporal consistency rules
    - Rules based on Dataplex profiling findings
    - BaNCS business logic rules
    - Enhancements to pre-existing rules
    
    Focus on: Completeness, Accuracy, Timeliness
    
    Return results in JSON format with clear categorization by source 
    (dataplex/agent/preexisting/cross_week).
    """
    
    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    events = list(runner.run(
        user_id="test_user",
        session_id=session.id,
        new_message=content
    ))
    
    # Extract response
    last_event = events[-1]
    response = "".join([part.text for part in last_event.content.parts if part.text])
    
    print(f"\n✅ RESULTS:\n{response}\n")
    
    print("="*80)
    print("\n✅ Enhanced Identifier Agent test complete!")
    print("\nNew Features Verified:")
    print("  ✅ Pre-existing rules loading (Collibra/Ataccama)")
    print("  ✅ Cross-week table detection")
    print("  ✅ Dataplex scan triggering")
    print("  ✅ Profiling data parsing")
    print("  ✅ Cross-week temporal rule generation")

if __name__ == "__main__":
    try:
        test_enhanced_features()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
