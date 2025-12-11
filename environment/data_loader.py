"""
Dynamic Data Loader
Loads data from GCS to BigQuery automatically
"""

from google.cloud import storage, bigquery
from pathlib import Path
import json


def load_csv_to_bigquery(
    project_id: str,
    bucket_name: str,
    csv_file: str,
    dataset_id: str,
    table_id: str,
    data_folder: str = ''
):
    """Load CSV from GCS to BigQuery table"""
    
    # Construct GCS URI
    blob_path = f"{data_folder}{csv_file}" if data_folder else csv_file
    gcs_uri = f"gs://{bucket_name}/{blob_path}"
    
    print(f"📥 Loading {csv_file} → {table_id}...")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=project_id)
    
    # Configure load job
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,  # Auto-detect schema
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE  # Overwrite
    )
    
    # Start load job
    load_job = client.load_table_from_uri(
        gcs_uri,
        table_ref,
        job_config=job_config
    )
    
    # Wait for completion
    load_job.result()
    
    # Get table info
    table = client.get_table(table_ref)
    print(f"✅ Loaded {table.num_rows} rows to {table_id}")
    
    return table


def load_all_week_data(config: dict):
    """Load all week CSV files to BigQuery"""
    
    project_id = config['project_id']
    bucket_name = config['gcs']['bucket']
    data_folder = config['gcs']['data_folder']
    dataset_id = config['bigquery']['dataset_id']
    csv_files = config['gcs']['csv_files']
    
    print(f"\n📊 Loading {len(csv_files)} CSV files to BigQuery...")
    
    loaded_tables = []
    
    for csv_file in csv_files:
        # Extract week number or use filename
        filename = csv_file.replace('.csv', '').lower()
        
        # Try to extract week pattern
        if 'week1' in filename:
            table_id = 'policies_week1'
        elif 'week2' in filename:
            table_id = 'policies_week2'
        elif 'week3' in filename:
            table_id = 'policies_week3'
        elif 'week4' in filename:
            table_id = 'policies_week4'
        elif 'combined' in filename:
            table_id = 'policies_combined'
        else:
            # Use sanitized filename as table name
            table_id = filename.replace('-', '_').replace(' ', '_')
        
        try:
            table = load_csv_to_bigquery(
                project_id=project_id,
                bucket_name=bucket_name,
                csv_file=csv_file,
                dataset_id=dataset_id,
                table_id=table_id,
                data_folder=data_folder
            )
            loaded_tables.append(table_id)
        except Exception as e:
            print(f"❌ Failed to load {csv_file}: {e}")
    
    print(f"\n✅ Successfully loaded {len(loaded_tables)} tables:")
    for table in loaded_tables:
        print(f"   - {table}")
    
    return loaded_tables


if __name__ == '__main__':
    # Load environment config
    with open('environment_config.json', 'r') as f:
        config = json.load(f)
    
    # Load all data
    load_all_week_data(config)
