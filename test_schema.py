import os
import json
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

project_id = os.getenv("BQ_DATA_PROJECT_ID")
dataset_id = os.getenv("BQ_DATASET_ID")

client = bigquery.Client(project=project_id)
dataset_ref = bigquery.DatasetReference(project_id, dataset_id)

print(f"📊 Inspecting schema for dataset: {dataset_id}\n")

# Load config
with open("bancs_dataset_config.json") as f:
    config = json.load(f)

tables_to_check = config["datasets"][0]["tables"]

for table_name in tables_to_check:
    print(f"Table: {table_name}")
    table_ref = dataset_ref.table(table_name)
    
    try:
        table = client.get_table(table_ref)
        print(f"  Rows: {table.num_rows:,}")
        print(f"  Columns: {len(table.schema)}")
        print(f"  Schema (first 10 fields):")
        for field in table.schema[:10]:
            print(f"    - {field.name} ({field.field_type})")
        print()
    except Exception as e:
        print(f"  ❌ Error: {e}\n")

print("✅ Schema introspection test complete")
