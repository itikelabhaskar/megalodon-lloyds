"""
Automatic GCP Environment Discovery
Detects project, buckets, datasets, tables without any hardcoding
"""

import os
import json
import subprocess
from typing import Dict, List, Optional
from google.cloud import storage, bigquery
from pathlib import Path


class EnvironmentDiscovery:
    """Automatically discover GCP environment configuration"""
    
    def __init__(self):
        self.config = {}
        self.project_id = None
        self.storage_client = None
        self.bq_client = None
    
    def discover_all(self) -> Dict:
        """Run complete environment discovery"""
        print("🔍 Starting environment auto-discovery...")
        
        # Step 1: Detect GCP Project
        self.project_id = self._detect_project_id()
        self.config['project_id'] = self.project_id
        print(f"✅ Detected Project: {self.project_id}")
        
        # Step 2: Detect environment type
        env_type = self._detect_environment_type()
        self.config['environment_type'] = env_type
        print(f"✅ Environment Type: {env_type}")
        
        # Step 3: Initialize clients
        self.storage_client = storage.Client(project=self.project_id)
        self.bq_client = bigquery.Client(project=self.project_id)
        
        # Step 4: Discover GCS bucket & data
        gcs_config = self._discover_gcs_data()
        self.config['gcs'] = gcs_config
        print(f"✅ Found Bucket: {gcs_config.get('bucket')}")
        print(f"✅ Found Data Folder: {gcs_config.get('data_folder')}")
        print(f"✅ Found {len(gcs_config.get('csv_files', []))} CSV files")
        
        # Step 5: Discover or create BigQuery dataset
        bq_config = self._discover_bigquery_resources()
        self.config['bigquery'] = bq_config
        print(f"✅ BigQuery Dataset: {bq_config.get('dataset_id')}")
        
        # Step 6: Save configuration
        self._save_config()
        print(f"✅ Configuration saved to environment_config.json")
        
        return self.config
    
    def _detect_project_id(self) -> str:
        """Detect active GCP project ID"""
        # Method 1: Try environment variable
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if project_id:
            return project_id
        
        # Method 2: Try gcloud config
        try:
            result = subprocess.run(
                ['gcloud', 'config', 'get-value', 'project'],
                capture_output=True,
                text=True,
                timeout=5
            )
            project_id = result.stdout.strip()
            if project_id and project_id != '(unset)':
                return project_id
        except Exception as e:
            print(f"⚠️ Could not get project from gcloud: {e}")
        
        # Method 3: Try default credentials
        try:
            from google.auth import default
            credentials, project_id = default()
            if project_id:
                return project_id
        except Exception as e:
            print(f"⚠️ Could not get project from credentials: {e}")
        
        raise RuntimeError(
            "❌ Could not detect GCP project ID. Please set GOOGLE_CLOUD_PROJECT "
            "environment variable or run 'gcloud config set project PROJECT_ID'"
        )
    
    def _detect_environment_type(self) -> str:
        """Detect which type of environment we're in"""
        project_id = self.project_id.lower()
        
        if 'prod-' in project_id and 'hackathon' in project_id:
            return 'nayone_hackathon'
        elif 'hackathon-practice' in project_id:
            return 'personal_development'
        elif 'prod-' in project_id:
            return 'production'
        else:
            return 'unknown'
    
    def _discover_gcs_data(self) -> Dict:
        """Discover GCS bucket and data files"""
        gcs_config = {}
        
        # Step 1: Find relevant bucket
        bucket = self._find_data_bucket()
        if not bucket:
            raise RuntimeError("❌ Could not find data bucket")
        
        gcs_config['bucket'] = bucket.name
        
        # Step 2: Find data folder
        data_folder = self._find_data_folder(bucket)
        gcs_config['data_folder'] = data_folder
        
        # Step 3: Find CSV files
        csv_files = self._find_week_csv_files(bucket, data_folder)
        gcs_config['csv_files'] = csv_files
        
        return gcs_config
    
    def _find_data_bucket(self) -> Optional[storage.Bucket]:
        """Find bucket containing hackathon data"""
        buckets = list(self.storage_client.list_buckets())
        
        # Priority 1: Buckets with "hackathon" in name
        for bucket in buckets:
            if 'hackathon' in bucket.name.lower():
                return bucket
        
        # Priority 2: Buckets with "data" or "dq" in name
        for bucket in buckets:
            name_lower = bucket.name.lower()
            if 'data' in name_lower or 'dq' in name_lower:
                return bucket
        
        # Priority 3: Buckets matching "prod-*-*" pattern
        for bucket in buckets:
            if bucket.name.startswith('prod-'):
                return bucket
        
        # Fallback: Return first bucket
        if buckets:
            print("⚠️ No specific bucket found, using first available bucket")
            return buckets[0]
        
        return None
    
    def _find_data_folder(self, bucket: storage.Bucket) -> str:
        """Find folder containing data quality files"""
        blobs = bucket.list_blobs(max_results=1000)
        
        # Collect all folder prefixes
        folders = set()
        for blob in blobs:
            if '/' in blob.name:
                folder = blob.name.split('/')[0] + '/'
                folders.add(folder)
        
        # Look for data quality related folders
        dq_patterns = [
            'improving ip& data quality',
            'data quality',
            'dq',
            'bancs',
            'policies'
        ]
        
        for folder in folders:
            folder_lower = folder.lower()
            for pattern in dq_patterns:
                if pattern in folder_lower:
                    return folder
        
        # Return root if no specific folder found
        return ''
    
    def _find_week_csv_files(self, bucket: storage.Bucket, folder: str) -> List[str]:
        """Find CSV files containing weekly data"""
        prefix = folder if folder else ''
        blobs = bucket.list_blobs(prefix=prefix)
        
        csv_files = []
        week_patterns = ['week1', 'week2', 'week3', 'week4', 'week']
        
        for blob in blobs:
            filename = blob.name.split('/')[-1]
            filename_lower = filename.lower()
            
            # Must be CSV
            if not filename_lower.endswith('.csv'):
                continue
            
            # Must contain "week"
            if any(pattern in filename_lower for pattern in week_patterns):
                csv_files.append(filename)
        
        # Sort to ensure consistent ordering
        csv_files.sort()
        
        return csv_files
    
    def _discover_bigquery_resources(self) -> Dict:
        """Discover or create BigQuery dataset and tables"""
        bq_config = {}
        
        # Step 1: Find or create dataset
        dataset_id = self._find_or_create_dataset()
        bq_config['dataset_id'] = dataset_id
        
        # Step 2: List existing tables
        tables = self._list_dataset_tables(dataset_id)
        bq_config['tables'] = tables
        
        # Step 3: If tables exist, introspect schema
        if tables:
            schema = self._introspect_schema(dataset_id, tables[0])
            bq_config['schema'] = schema
        else:
            bq_config['schema'] = {'columns': [], 'key_columns': {}}
        
        return bq_config
    
    def _find_or_create_dataset(self) -> str:
        """Find existing DQ dataset or create new one"""
        datasets = list(self.bq_client.list_datasets())
        
        # Look for existing DQ dataset
        dq_patterns = ['dq', 'data_quality', 'quality', 'bancs']
        
        for dataset in datasets:
            dataset_id = dataset.dataset_id.lower()
            for pattern in dq_patterns:
                if pattern in dataset_id:
                    print(f"📊 Found existing dataset: {dataset.dataset_id}")
                    return dataset.dataset_id
        
        # Create new dataset
        dataset_id = 'dq_management_system'
        dataset = bigquery.Dataset(f"{self.project_id}.{dataset_id}")
        dataset.location = "US"
        
        try:
            dataset = self.bq_client.create_dataset(dataset, exists_ok=True)
            print(f"📊 Created new dataset: {dataset_id}")
            return dataset_id
        except Exception as e:
            print(f"⚠️ Could not create dataset: {e}")
            # Use default dataset name anyway
            return dataset_id
    
    def _list_dataset_tables(self, dataset_id: str) -> List[str]:
        """List all tables in dataset"""
        try:
            tables = self.bq_client.list_tables(f"{self.project_id}.{dataset_id}")
            return [table.table_id for table in tables]
        except Exception as e:
            print(f"⚠️ Could not list tables: {e}")
            return []
    
    def _introspect_schema(self, dataset_id: str, table_id: str) -> Dict:
        """Introspect table schema to understand structure"""
        try:
            table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
            table = self.bq_client.get_table(table_ref)
            
            schema_info = {
                'columns': [],
                'key_columns': {
                    'customer_id': None,
                    'date_fields': [],
                    'amount_fields': [],
                    'status_fields': []
                }
            }
            
            for field in table.schema:
                schema_info['columns'].append({
                    'name': field.name,
                    'type': field.field_type
                })
                
                # Detect key column types
                name_lower = field.name.lower()
                
                # Customer ID detection
                if 'cus_id' in name_lower or 'customer_id' in name_lower:
                    schema_info['key_columns']['customer_id'] = field.name
                
                # Date field detection
                if 'date' in name_lower or 'dob' in name_lower:
                    schema_info['key_columns']['date_fields'].append(field.name)
                
                # Amount field detection
                if 'pmt' in name_lower or 'amount' in name_lower or 'premium' in name_lower:
                    schema_info['key_columns']['amount_fields'].append(field.name)
                
                # Status field detection
                if 'status' in name_lower or 'state' in name_lower:
                    schema_info['key_columns']['status_fields'].append(field.name)
            
            return schema_info
            
        except Exception as e:
            print(f"⚠️ Could not introspect schema: {e}")
            return {'columns': [], 'key_columns': {}}
    
    def _save_config(self):
        """Save discovered configuration to file"""
        config_path = Path('environment_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)


def load_environment_config() -> Dict:
    """Load previously discovered environment configuration"""
    config_path = Path('environment_config.json')
    
    if not config_path.exists():
        print("⚠️ No environment configuration found. Running auto-discovery...")
        discovery = EnvironmentDiscovery()
        return discovery.discover_all()
    
    with open(config_path, 'r') as f:
        return json.load(f)


if __name__ == '__main__':
    # Run discovery when script is executed directly
    discovery = EnvironmentDiscovery()
    config = discovery.discover_all()
    
    print("\n" + "="*60)
    print("🎉 ENVIRONMENT DISCOVERY COMPLETE!")
    print("="*60)
    print(json.dumps(config, indent=2))
