"""
Environment Auto-Discovery Module
Automatically detects GCP configuration without hardcoding
"""

from .auto_discovery import EnvironmentDiscovery, load_environment_config
from .data_loader import load_csv_to_bigquery, load_all_week_data

__all__ = [
    'EnvironmentDiscovery',
    'load_environment_config',
    'load_csv_to_bigquery',
    'load_all_week_data'
]
