"""
Test Dataplex Profiling via Identifier Agent
This simulates what happens when you click "Generate DQ Rules" with Dataplex enabled
"""

import os
import sys
import json
import time
from datetime import datetime

print("=" * 80)
print("DATAPLEX PROFILING TEST - Via Identifier Agent")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Test 1: Import Dataplex tools
print("TEST 1: Import Dataplex Tools")
print("-" * 80)
try:
    from dq_agents.identifier.tools import trigger_dataplex_scan
    print("✅ PASS - trigger_dataplex_scan imported")
except Exception as e:
    print(f"❌ FAIL - {str(e)}")
    sys.exit(1)

# Test 2: Check Dataplex client
print("\nTEST 2: Initialize Dataplex Client")
print("-" * 80)
try:
    from google.cloud import dataplex_v1
    client = dataplex_v1.DataScanServiceClient()
    print("✅ PASS - Dataplex client initialized")
except Exception as e:
    print(f"❌ FAIL - {str(e)}")
    sys.exit(1)

# Test 3: Trigger actual Dataplex scan
print("\nTEST 3: Trigger Real Dataplex Scan for policies_week1")
print("-" * 80)
print("⚠️  WARNING: This will take 60-90 seconds!")
print("Creating DataScan job on GCP...\n")

class MockToolContext:
    """Mock ToolContext for standalone testing"""
    pass

try:
    context = MockToolContext()
    table_name = "policies_week1"
    
    start_time = time.time()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Dataplex scan for {table_name}...")
    
    result = trigger_dataplex_scan(table_name, context)
    
    elapsed_time = time.time() - start_time
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scan completed in {elapsed_time:.1f} seconds")
    
    # Parse result
    if isinstance(result, str):
        try:
            result_data = json.loads(result)
            print("\n✅ PASS - Dataplex scan completed successfully")
            print("-" * 80)
            print("PROFILING RESULTS:")
            print("-" * 80)
            
            # Display key metrics
            if "row_count" in result_data:
                print(f"📊 Total Rows: {result_data['row_count']}")
            
            if "column_count" in result_data:
                print(f"📊 Total Columns: {result_data['column_count']}")
            
            if "scan_name" in result_data:
                print(f"🔍 DataScan Name: {result_data['scan_name']}")
            
            if "columns" in result_data:
                print(f"\n📋 Column Profiling:")
                for col in result_data['columns'][:5]:  # Show first 5
                    col_name = col.get('name', 'unknown')
                    null_ratio = col.get('null_ratio', 0)
                    distinct_count = col.get('distinct_count', 'N/A')
                    print(f"   • {col_name}:")
                    print(f"     - Null ratio: {null_ratio:.2%}")
                    print(f"     - Distinct values: {distinct_count}")
                
                if len(result_data['columns']) > 5:
                    print(f"   ... and {len(result_data['columns']) - 5} more columns")
            
            if "dq_issues_detected" in result_data:
                issues = result_data['dq_issues_detected']
                print(f"\n🚨 DQ Issues Detected: {len(issues)}")
                for issue in issues[:3]:  # Show first 3
                    print(f"   • {issue}")
            
            # GCP Console link
            if "console_url" in result_data:
                print(f"\n🌐 View in GCP Console:")
                print(f"   {result_data['console_url']}")
            
            # Save full results
            output_file = f"dataplex_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            print(f"\n💾 Full results saved to: {output_file}")
            
        except json.JSONDecodeError:
            print("⚠️  WARNING - Result is not JSON, showing raw output:")
            print(result[:500])
    else:
        print(f"✅ Scan completed, result type: {type(result)}")
        print(str(result)[:500])
    
except Exception as e:
    elapsed_time = time.time() - start_time
    print(f"\n❌ FAIL - Error after {elapsed_time:.1f} seconds")
    print(f"Error: {str(e)}")
    import traceback
    print("\nFull traceback:")
    print(traceback.format_exc())
    sys.exit(1)

# Test 4: Verify DataScan exists in GCP
print("\n" + "=" * 80)
print("TEST 4: Verify DataScan in GCP")
print("=" * 80)
try:
    from google.cloud import dataplex_v1
    client = dataplex_v1.DataScanServiceClient()
    parent = "projects/hackathon-practice-480508/locations/us-central1"
    
    print(f"Listing DataScans in {parent}...")
    
    request = dataplex_v1.ListDataScansRequest(parent=parent)
    scans = list(client.list_data_scans(request=request))
    
    print(f"\n✅ Found {len(scans)} DataScan(s) in GCP:")
    for scan in scans[:5]:  # Show first 5
        scan_name = scan.name.split('/')[-1]
        state = scan.state.name
        print(f"   • {scan_name} - State: {state}")
    
    if len(scans) > 5:
        print(f"   ... and {len(scans) - 5} more scans")
    
except Exception as e:
    print(f"⚠️  Could not list DataScans: {str(e)[:200]}")

# Final Summary
print("\n" + "=" * 80)
print("DATAPLEX TEST SUMMARY")
print("=" * 80)
print(f"✅ All Dataplex tests completed")
print(f"Total execution time: {elapsed_time:.1f} seconds")
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
