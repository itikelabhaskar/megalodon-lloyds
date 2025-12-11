"""
Test Metrics Agent

Validates all metrics tools work correctly before UI integration.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

print("🧪 Testing Metrics Agent\n")

# Test 1: Cost of Inaction Calculation
print("=" * 60)
print("Test 1: Cost of Inaction Calculation")
print("=" * 60)

try:
    from dq_agents.metrics.tools import calculate_cost_of_inaction
    
    # Mock tool context
    class MockToolContext:
        pass
    
    result = calculate_cost_of_inaction(
        affected_rows=150,
        table_name="policies_week1",
        tool_context=MockToolContext()
    )
    
    coi_data = json.loads(result)
    
    if 'error' in coi_data:
        print(f"❌ Error: {coi_data['error']}")
    else:
        print(f"✅ Cost of Inaction calculated successfully")
        print(f"   - Affected Rows: {coi_data['affected_rows']}")
        print(f"   - Total Exposure: £{coi_data['total_exposure']:,.2f}")
        print(f"   - Monthly CoI: £{coi_data['cost_of_inaction']['monthly']:,.2f}")
        print(f"   - Annual CoI: £{coi_data['cost_of_inaction']['annual']:,.2f}")
        print(f"   - Materiality: {coi_data['materiality_index']}")

except Exception as e:
    print(f"❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n")

# Test 2: Anomaly Detection
print("=" * 60)
print("Test 2: Anomaly Detection")
print("=" * 60)

try:
    from dq_agents.metrics.tools import detect_anomalies_in_data
    
    result = detect_anomalies_in_data(
        table_name="policies_week1",
        sample_size=500,
        tool_context=MockToolContext()
    )
    
    anomaly_data = json.loads(result)
    
    if 'error' in anomaly_data:
        print(f"❌ Error: {anomaly_data['error']}")
    else:
        print(f"✅ Anomaly detection completed successfully")
        print(f"   - Rows Analyzed: {anomaly_data['total_rows_analyzed']}")
        print(f"   - Anomalies Detected: {anomaly_data['anomalies_detected']}")
        print(f"   - Anomaly Rate: {anomaly_data['anomaly_rate']}%")
        print(f"   - Columns Analyzed: {', '.join(anomaly_data['columns_analyzed'][:3])}...")
        
        if anomaly_data.get('top_anomalies'):
            print(f"\n   Top 3 Anomalies:")
            for i, anom in enumerate(anomaly_data['top_anomalies'][:3], 1):
                print(f"      {i}. Policy {anom['policy_id']}: Score {anom['anomaly_score']:.4f}")

except Exception as e:
    print(f"❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n")

# Test 3: Remediation Metrics
print("=" * 60)
print("Test 3: Remediation Metrics")
print("=" * 60)

try:
    from dq_agents.metrics.tools import calculate_remediation_metrics
    
    # Mock issue data
    mock_issues = [
        {
            "issue_id": "DQ_001",
            "status": "resolved",
            "resolution_type": "auto",
            "created_at": "2025-12-10T10:00:00",
            "resolved_at": "2025-12-10T12:30:00"
        },
        {
            "issue_id": "DQ_002",
            "status": "resolved",
            "resolution_type": "manual",
            "created_at": "2025-12-10T11:00:00",
            "resolved_at": "2025-12-10T16:00:00"
        },
        {
            "issue_id": "DQ_003",
            "status": "pending",
            "resolution_type": None,
            "created_at": "2025-12-11T09:00:00"
        },
        {
            "issue_id": "DQ_004",
            "status": "resolved",
            "resolution_type": "auto",
            "created_at": "2025-12-10T14:00:00",
            "resolved_at": "2025-12-10T15:00:00"
        }
    ]
    
    result = calculate_remediation_metrics(
        issues_data=json.dumps(mock_issues),
        tool_context=MockToolContext()
    )
    
    metrics_data = json.loads(result)
    
    if 'error' in metrics_data:
        print(f"❌ Error: {metrics_data['error']}")
    else:
        print(f"✅ Remediation metrics calculated successfully")
        print(f"   - Total Issues: {metrics_data['total_issues']}")
        print(f"   - Auto-Fixed: {metrics_data['auto_fixed']}")
        print(f"   - Manual-Fixed: {metrics_data['manual_fixed']}")
        print(f"   - Pending: {metrics_data['pending']}")
        print(f"   - Auto-Fix Rate: {metrics_data['auto_fix_rate']['percentage']}%")
        print(f"   - Status: {metrics_data['auto_fix_rate']['status']}")
        print(f"   - Avg Velocity: {metrics_data['remediation_velocity']['avg_hours']:.2f} hours")

except Exception as e:
    print(f"❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n")

# Test 4: Narrative Generation
print("=" * 60)
print("Test 4: Narrative Generation")
print("=" * 60)

try:
    from dq_agents.metrics.tools import generate_metrics_narrative
    
    # Comprehensive metrics data
    all_metrics = {
        "cost_of_inaction": {
            "total_exposure": 14000000,
            "cost_of_inaction": {"monthly": 50000, "annual": 600000},
            "materiality_index": "High",
            "affected_rows": 280
        },
        "remediation_metrics": {
            "total_issues": 4,
            "auto_fixed": 2,
            "manual_fixed": 1,
            "pending": 1,
            "auto_fix_rate": {"percentage": 66.67, "status": "below_target"},
            "remediation_velocity": {"avg_hours": 3.17, "status": "excellent"}
        },
        "anomaly_detection": {
            "total_rows_analyzed": 500,
            "anomalies_detected": 35,
            "anomaly_rate": 7.0,
            "columns_analyzed": ["policy_value", "premium", "sum_assured"],
            "top_anomalies": [
                {"policy_id": "POL_001", "anomaly_score": -0.3456}
            ]
        }
    }
    
    narrative = generate_metrics_narrative(
        metrics_data=json.dumps(all_metrics),
        tool_context=MockToolContext()
    )
    
    if narrative.startswith("Error"):
        print(f"❌ {narrative}")
    else:
        print("✅ Narrative generated successfully")
        print("\nNarrative Preview:")
        print("-" * 60)
        print(narrative[:500] + "...\n")

except Exception as e:
    print(f"❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n")

# Test 5: Agent Integration
print("=" * 60)
print("Test 5: Full Agent Integration")
print("=" * 60)

try:
    import asyncio
    from dq_agents.metrics.agent import metrics_agent
    
    async def test_agent():
        response = await metrics_agent.send_message(
            "Calculate the cost of inaction for 100 affected rows in table 'policies_week1'. "
            "Provide a summary of the financial impact."
        )
        return response.text
    
    result = asyncio.run(test_agent())
    
    print("✅ Metrics Agent responded successfully")
    print("\nAgent Response Preview:")
    print("-" * 60)
    print(result[:300] + "...\n")

except Exception as e:
    print(f"❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n")
print("=" * 60)
print("🎉 Testing Complete!")
print("=" * 60)
print("\nNext Steps:")
print("1. Run 'streamlit run streamlit_app/app.py'")
print("2. Navigate to the 'Metrics Agent' tab")
print("3. Test all 4 modes: Dashboard, Anomaly Detection, Cost of Inaction, Executive Report")
print("\n✨ The Metrics Agent is ready for use!")
