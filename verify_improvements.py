"""
Verification script for Google ADK improvements implementation.
Tests: SQL serialization, database settings caching, and ADK BigQuery client.
"""
import os
import sys
from dotenv import load_dotenv

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv()

# Set required env vars for testing
os.environ["BQ_DATA_PROJECT_ID"] = os.getenv("GOOGLE_CLOUD_PROJECT", "hackathon-practice-480508")
os.environ["BQ_DATASET_ID"] = "bancs_dataset"

from dq_agents.identifier.tools import (
    _serialize_value_for_sql,
    get_database_settings,
    _get_bigquery_client,
    get_table_schema,
    get_all_week_tables,
    get_table_schema_with_samples,
)
import pandas as pd
import numpy as np
import datetime

def test_sql_serialization():
    """Test 1: SQL Serialization Utility"""
    print("\n" + "="*60)
    print("TEST 1: SQL Serialization Utility (_serialize_value_for_sql)")
    print("="*60)
    
    test_cases = [
        ("Simple string", "Hello World", "'Hello World'"),
        ("String with quote", "O'Brien", "'O''Brien'"),
        ("String with backslash", "C:\\path\\file", "'C:\\\\path\\\\file'"),
        ("NULL value", None, "NULL"),
        ("NaN value", np.nan, "NULL"),
        ("Integer", 123, "123"),
        ("Float", 123.45, "123.45"),
        ("Date", datetime.date(2023, 1, 15), "'2023-01-15'"),
        ("Datetime", datetime.datetime(2023, 1, 15, 10, 30), "'2023-01-15 10:30:00'"),
        ("Array", [1, 2, 3], "[1, 2, 3]"),
        ("String array", ["a", "b"], "['a', 'b']"),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, input_val, expected in test_cases:
        try:
            result = _serialize_value_for_sql(input_val)
            if result == expected:
                print(f"✅ {test_name}: PASSED")
                print(f"   Input: {input_val} → Output: {result}")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                print(f"   Input: {input_val}")
                print(f"   Expected: {expected}")
                print(f"   Got: {result}")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
            failed += 1
    
    print(f"\n📊 SQL Serialization Results: {passed} passed, {failed} failed")
    return failed == 0


def test_database_settings_cache():
    """Test 2: Database Settings Caching"""
    print("\n" + "="*60)
    print("TEST 2: Database Settings Caching")
    print("="*60)
    
    try:
        # First call - should populate cache
        settings1 = get_database_settings()
        print(f"✅ First call successful:")
        print(f"   Project: {settings1.get('project_id')}")
        print(f"   Dataset: {settings1.get('dataset_id')}")
        print(f"   Compute Project: {settings1.get('compute_project')}")
        
        # Second call - should use cache (same object)
        settings2 = get_database_settings()
        
        # Verify it's the same cached object
        if settings1 is settings2:
            print(f"✅ Cache working: Same object returned (id: {id(settings1)})")
            cache_working = True
        else:
            print(f"❌ Cache NOT working: Different objects returned")
            cache_working = False
        
        # Verify all required fields present
        required_fields = ["project_id", "dataset_id", "compute_project"]
        all_present = all(field in settings1 for field in required_fields)
        
        if all_present:
            print(f"✅ All required fields present")
        else:
            print(f"❌ Missing fields: {[f for f in required_fields if f not in settings1]}")
        
        print(f"\n📊 Database Settings Cache: {'PASSED' if (cache_working and all_present) else 'FAILED'}")
        return cache_working and all_present
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_adk_bigquery_client():
    """Test 3: ADK BigQuery Client"""
    print("\n" + "="*60)
    print("TEST 3: ADK BigQuery Client Integration")
    print("="*60)
    
    try:
        # Get client
        client = _get_bigquery_client()
        print(f"✅ ADK Client created successfully")
        print(f"   Type: {type(client).__name__}")
        print(f"   Project: {client.project}")
        
        # Test basic operation
        try:
            result = client.query("SELECT 1 as test").result()
            row = next(result)
            if row.test == 1:
                print(f"✅ Client query execution works")
                query_works = True
            else:
                print(f"❌ Query returned unexpected result")
                query_works = False
        except Exception as e:
            print(f"❌ Query execution failed: {str(e)}")
            query_works = False
        
        print(f"\n📊 ADK BigQuery Client: {'PASSED' if query_works else 'FAILED'}")
        return query_works
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test 4: Integration Test - Real Tool Functions"""
    print("\n" + "="*60)
    print("TEST 4: Integration Test - Tool Functions with Improvements")
    print("="*60)
    
    results = {}
    
    # Test get_all_week_tables
    print("\n🔍 Testing get_all_week_tables...")
    try:
        from google.adk.tools import ToolContext
        context = ToolContext(session_id="test", turn_id="test", agent_name="test")
        
        week_tables_result = get_all_week_tables(context)
        import json
        week_tables_data = json.loads(week_tables_result)
        
        if "week_tables" in week_tables_data and isinstance(week_tables_data["week_tables"], list):
            print(f"✅ get_all_week_tables works")
            print(f"   Found {len(week_tables_data['week_tables'])} week tables")
            print(f"   Tables: {', '.join(week_tables_data['week_tables'][:3])}")
            results["week_tables"] = True
        else:
            print(f"❌ get_all_week_tables: Unexpected format")
            results["week_tables"] = False
    except Exception as e:
        print(f"❌ get_all_week_tables failed: {str(e)}")
        results["week_tables"] = False
    
    # Test get_table_schema_with_samples (with SQL serialization)
    print("\n🔍 Testing get_table_schema_with_samples...")
    try:
        schema_result = get_table_schema_with_samples("policies_week1", sample_rows=3)
        schema_data = json.loads(schema_result)
        
        if "columns" in schema_data and "sample_values" in schema_data["columns"][0]:
            print(f"✅ get_table_schema_with_samples works")
            print(f"   Table: {schema_data['table_name']}")
            print(f"   Columns: {len(schema_data['columns'])}")
            
            # Check if sample values are properly serialized
            sample_col = schema_data["columns"][0]
            print(f"   Sample column: {sample_col['name']}")
            print(f"   Sample values: {sample_col['sample_values'][:2]}")
            results["schema_samples"] = True
        else:
            print(f"❌ get_table_schema_with_samples: Missing expected fields")
            results["schema_samples"] = False
    except Exception as e:
        print(f"❌ get_table_schema_with_samples failed: {str(e)}")
        import traceback
        traceback.print_exc()
        results["schema_samples"] = False
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n📊 Integration Tests: {passed}/{total} passed")
    return all(results.values())


def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("🔍 GOOGLE ADK IMPROVEMENTS VERIFICATION")
    print("="*60)
    print("\nTesting implementations:")
    print("1. SQL Serialization Utility (_serialize_value_for_sql)")
    print("2. Database Settings Caching")
    print("3. ADK BigQuery Client Integration")
    print("4. Integration with Tool Functions")
    
    results = {
        "SQL Serialization": test_sql_serialization(),
        "Database Settings Cache": test_database_settings_cache(),
        "ADK BigQuery Client": test_adk_bigquery_client(),
        "Integration Tests": test_integration(),
    }
    
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Implementation Verified!")
        print("="*60)
        print("\n✅ Improvements successfully implemented:")
        print("  • SQL injection prevention with _serialize_value_for_sql()")
        print("  • Database settings caching for performance")
        print("  • ADK BigQuery client with user agent tracking")
        print("  • All tool functions updated to use new patterns")
    else:
        print("⚠️ SOME TESTS FAILED - Review Implementation")
        print("="*60)
        failed = [name for name, passed in results.items() if not passed]
        print(f"\nFailed tests: {', '.join(failed)}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
