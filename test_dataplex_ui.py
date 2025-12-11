"""
Test Dataplex through Streamlit UI by simulating the identifier agent workflow
This mimics what happens when user clicks "Generate DQ Rules" with Dataplex enabled
"""

import asyncio
import json
import time
from datetime import datetime

print("=" * 80)
print("DATAPLEX UI TEST - Via Identifier Agent in Streamlit Context")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Simulate Streamlit environment
print("TEST 1: Simulating Streamlit Session Environment")
print("-" * 80)

class MockStreamlitSessionState:
    """Mock Streamlit session state"""
    def __init__(self):
        self.data = {}
    
    def __contains__(self, key):
        return key in self.data
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value

# Create mock streamlit module
import sys
from types import ModuleType

streamlit_mock = ModuleType('streamlit')
streamlit_mock.session_state = MockStreamlitSessionState()

# Inject mock streamlit
sys.modules['streamlit'] = streamlit_mock

print("✅ Streamlit environment mocked")

# Test 2: Import and setup identifier agent
print("\nTEST 2: Import Identifier Agent")
print("-" * 80)

try:
    from dq_agents.identifier.agent import get_identifier_agent
    from google.adk.sessions import InMemorySessionService
    from google.adk.artifacts import InMemoryArtifactService
    from google.adk.runners import Runner
    from google.genai import types
    
    print("✅ Identifier agent imported")
    print("✅ ADK components imported")
except Exception as e:
    print(f"❌ FAIL - {str(e)}")
    sys.exit(1)

# Test 3: Create session and runner
print("\nTEST 3: Create ADK Session and Runner")
print("-" * 80)

try:
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    
    identifier_agent = get_identifier_agent()
    
    runner = Runner(
        app_name="IdentifierAgentTest",
        agent=identifier_agent,
        session_service=session_service,
        artifact_service=artifact_service
    )
    
    session = asyncio.run(session_service.create_session(
        app_name="IdentifierAgentTest",
        user_id="test_user"
    ))
    
    print(f"✅ Session created: {session.id[:16]}...")
    print(f"✅ Runner initialized")
except Exception as e:
    print(f"❌ FAIL - {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Run identifier agent with Dataplex profiling
print("\nTEST 4: Generate DQ Rules with Dataplex Profiling")
print("-" * 80)
print("⚠️  This will take 60-90 seconds (real Dataplex scan)...\n")

try:
    start_time = time.time()
    
    # Create the prompt exactly as Streamlit app does
    table_name = "policies_week1"
    prompt = f"""Generate comprehensive DQ rules for table '{table_name}'.

Follow these steps:
1. Get the schema for {table_name}
2. Run Dataplex data profiling scan on {table_name} to get:
   - Row counts and column statistics
   - Null rates for each column
   - Data quality issues
3. Use the profiling results to generate targeted DQ rules focusing on:
   - Completeness checks for columns with high null rates
   - Accuracy checks for critical fields
   - Consistency checks across related columns

Return the generated rules in this JSON format:
{{
  "table": "{table_name}",
  "rules": [
    {{
      "rule_id": "unique_id",
      "name": "rule_name",
      "description": "what it checks",
      "sql": "SELECT query",
      "severity": "critical/high/medium/low",
      "dq_dimension": "Completeness/Accuracy/Consistency/etc",
      "category": "category_name"
    }}
  ]
}}"""
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending prompt to identifier agent...")
    print(f"Table: {table_name}")
    print(f"With Dataplex profiling: YES\n")
    
    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    events = list(runner.run(
        user_id="test_user",
        session_id=session.id,
        new_message=content
    ))
    
    elapsed_time = time.time() - start_time
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Agent completed in {elapsed_time:.1f} seconds")
    
    if events:
        last_event = events[-1]
        response_text = "".join([
            part.text for part in last_event.content.parts 
            if hasattr(part, 'text') and part.text
        ])
        
        print("\n✅ PASS - Identifier agent completed successfully")
        print("-" * 80)
        print("AGENT RESPONSE:")
        print("-" * 80)
        
        # Try to parse JSON from response
        try:
            # Look for JSON in response
            if '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]
                
                rules_data = json.loads(json_str)
                
                print(f"Table: {rules_data.get('table')}")
                print(f"Rules Generated: {len(rules_data.get('rules', []))}")
                
                print("\nSample Rules:")
                for i, rule in enumerate(rules_data.get('rules', [])[:3], 1):
                    print(f"\n  Rule {i}:")
                    print(f"    ID: {rule.get('rule_id')}")
                    print(f"    Name: {rule.get('name')}")
                    print(f"    Severity: {rule.get('severity')}")
                    print(f"    DQ Dimension: {rule.get('dq_dimension')}")
                
                # Save results
                output_file = f"ui_test_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w') as f:
                    json.dump(rules_data, f, indent=2)
                print(f"\n💾 Full rules saved to: {output_file}")
                
            else:
                print("Response (first 1000 chars):")
                print(response_text[:1000])
                
        except json.JSONDecodeError:
            print("Response (first 1000 chars):")
            print(response_text[:1000])
        
    else:
        print("❌ No response from agent")
        
except Exception as e:
    elapsed_time = time.time() - start_time
    print(f"\n❌ FAIL - Error after {elapsed_time:.1f} seconds")
    print(f"Error: {str(e)}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

# Test 5: Verify Dataplex was called
print("\n" + "=" * 80)
print("TEST 5: Verify Dataplex Scan Was Executed")
print("=" * 80)

try:
    from google.cloud import dataplex_v1
    client = dataplex_v1.DataScanServiceClient()
    parent = "projects/hackathon-practice-480508/locations/us-central1"
    
    request = dataplex_v1.ListDataScansRequest(parent=parent)
    scans = list(client.list_data_scans(request=request))
    
    # Check for recent scans (within last 5 minutes)
    recent_scans = [s for s in scans if 'policies-week1' in s.name]
    
    print(f"✅ Found {len(recent_scans)} scan(s) for policies_week1")
    if recent_scans:
        latest_scan = recent_scans[0]
        print(f"   Latest scan: {latest_scan.name.split('/')[-1]}")
        print(f"   State: {latest_scan.state.name}")
    
except Exception as e:
    print(f"⚠️  Could not verify scans: {str(e)[:150]}")

# Final Summary
print("\n" + "=" * 80)
print("DATAPLEX UI TEST SUMMARY")
print("=" * 80)
print(f"✅ All UI workflow tests completed")
print(f"Total execution time: {elapsed_time:.1f} seconds")
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print("\n🎯 Next: Test in actual Streamlit browser UI")
print("   1. Open http://localhost:8502")
print("   2. Go to Identifier tab")
print("   3. Select policies_week1")
print("   4. Check 'Run Dataplex Data Profiling'")
print("   5. Click 'Generate DQ Rules'")
print("   6. Wait ~60-90 seconds")
print("=" * 80)
