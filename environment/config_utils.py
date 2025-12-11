"""
Configuration Utility
Centralized configuration loading for all agents and UI
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional


def load_config() -> Dict:
    """
    Load configuration from environment_config.json or environment variables
    
    Returns:
        dict: Configuration dictionary with project_id, dataset_id, tables, etc.
    """
    config_path = Path('environment_config.json')
    
    # Try to load from file first
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    
    # Fallback to environment variables
    print("⚠️ environment_config.json not found. Using environment variables...")
    
    config = {
        'project_id': os.getenv('GOOGLE_CLOUD_PROJECT', os.getenv('BQ_COMPUTE_PROJECT_ID', '')),
        'environment_type': 'manual',
        'gcs': {
            'bucket': os.getenv('GCS_BUCKET', ''),
            'data_folder': os.getenv('GCS_DATA_FOLDER', ''),
            'csv_files': []
        },
        'bigquery': {
            'dataset_id': os.getenv('BQ_DATASET_ID', ''),
            'tables': [],
            'schema': {'columns': [], 'key_columns': {}}
        }
    }
    
    return config


def get_project_id() -> str:
    """Get GCP project ID from config"""
    config = load_config()
    return config.get('project_id', os.getenv('GOOGLE_CLOUD_PROJECT', ''))


def get_dataset_id() -> str:
    """Get BigQuery dataset ID from config"""
    config = load_config()
    return config.get('bigquery', {}).get('dataset_id', os.getenv('BQ_DATASET_ID', ''))


def get_tables() -> List[str]:
    """Get list of available tables from config"""
    config = load_config()
    return config.get('bigquery', {}).get('tables', [])


def get_customer_id_column() -> Optional[str]:
    """Get the customer ID column name from schema introspection"""
    config = load_config()
    schema = config.get('bigquery', {}).get('schema', {})
    return schema.get('key_columns', {}).get('customer_id')


def get_date_fields() -> List[str]:
    """Get list of date field column names from schema"""
    config = load_config()
    schema = config.get('bigquery', {}).get('schema', {})
    return schema.get('key_columns', {}).get('date_fields', [])


def get_amount_fields() -> List[str]:
    """Get list of amount field column names from schema"""
    config = load_config()
    schema = config.get('bigquery', {}).get('schema', {})
    return schema.get('key_columns', {}).get('amount_fields', [])


def get_status_fields() -> List[str]:
    """Get list of status field column names from schema"""
    config = load_config()
    schema = config.get('bigquery', {}).get('schema', {})
    return schema.get('key_columns', {}).get('status_fields', [])


def get_all_columns() -> List[Dict]:
    """Get all columns with their types"""
    config = load_config()
    schema = config.get('bigquery', {}).get('schema', {})
    return schema.get('columns', [])


def get_environment_type() -> str:
    """Get environment type (nayone_hackathon, personal_development, etc.)"""
    config = load_config()
    return config.get('environment_type', 'unknown')


def get_gcs_bucket() -> str:
    """Get GCS bucket name"""
    config = load_config()
    return config.get('gcs', {}).get('bucket', '')


def get_gcs_data_folder() -> str:
    """Get GCS data folder path"""
    config = load_config()
    return config.get('gcs', {}).get('data_folder', '')


# Configuration settings with defaults
def get_risk_rate(risk_type: str) -> float:
    """Get risk rate from environment or use default"""
    defaults = {
        'regulatory': 0.001,
        'customer_churn': 0.02,
        'operational': 0.005
    }
    
    env_vars = {
        'regulatory': 'REGULATORY_RISK_RATE',
        'customer_churn': 'CUSTOMER_CHURN_RATE',
        'operational': 'OPERATIONAL_COST_RATE'
    }
    
    env_var = env_vars.get(risk_type)
    if env_var:
        return float(os.getenv(env_var, defaults[risk_type]))
    return defaults.get(risk_type, 0.001)


def get_materiality_threshold(level: str) -> float:
    """Get materiality threshold from environment or use default"""
    defaults = {
        'high': 10000000,  # £10M
        'medium': 1000000   # £1M
    }
    
    env_vars = {
        'high': 'MATERIALITY_HIGH_THRESHOLD',
        'medium': 'MATERIALITY_MEDIUM_THRESHOLD'
    }
    
    env_var = env_vars.get(level)
    if env_var:
        return float(os.getenv(env_var, defaults[level]))
    return defaults.get(level, 1000000)


def get_anomaly_contamination_rate() -> float:
    """Get anomaly detection contamination rate"""
    return float(os.getenv('ANOMALY_CONTAMINATION_RATE', '0.1'))


def get_organization_name() -> str:
    """Get organization name for branding"""
    return os.getenv('ORGANIZATION_NAME', 'Your Organization')


def get_copyright_year() -> str:
    """Get copyright year for branding"""
    return os.getenv('COPYRIGHT_YEAR', '2025')


# Utility function for validation
def validate_config() -> bool:
    """
    Validate that required configuration exists
    
    Returns:
        bool: True if config is valid, False otherwise
    """
    try:
        config = load_config()
        
        # Check required fields
        if not config.get('project_id'):
            print("❌ Missing project_id in configuration")
            return False
        
        if not config.get('bigquery', {}).get('dataset_id'):
            print("❌ Missing dataset_id in configuration")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


if __name__ == '__main__':
    # Test configuration loading
    print("Testing configuration loading...")
    print("-" * 60)
    
    config = load_config()
    print(f"Project ID: {get_project_id()}")
    print(f"Dataset ID: {get_dataset_id()}")
    print(f"Environment Type: {get_environment_type()}")
    print(f"Tables: {get_tables()}")
    print(f"Customer ID Column: {get_customer_id_column()}")
    print(f"Date Fields: {get_date_fields()}")
    print(f"Amount Fields: {get_amount_fields()}")
    print(f"Status Fields: {get_status_fields()}")
    print()
    print("Configuration is valid!" if validate_config() else "Configuration has issues!")
