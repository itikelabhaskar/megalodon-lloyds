"""
Environment Initialization Script
Run this first in any new environment to auto-detect configuration
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from environment.auto_discovery import EnvironmentDiscovery
from environment.data_loader import load_all_week_data


def main():
    print("=" * 70)
    print("🚀 DATA QUALITY MANAGEMENT SYSTEM - ENVIRONMENT INITIALIZATION")
    print("=" * 70)
    print()
    
    # Step 1: Auto-discover environment
    print("STEP 1: Discovering GCP Environment...")
    print("-" * 70)
    try:
        discovery = EnvironmentDiscovery()
        config = discovery.discover_all()
        print()
    except Exception as e:
        print(f"\n❌ Environment discovery failed: {e}")
        print("\nPlease ensure:")
        print("  1. You are authenticated with GCP (run: gcloud auth login)")
        print("  2. Project is set (run: gcloud config set project YOUR_PROJECT_ID)")
        print("  3. You have necessary permissions to access GCS and BigQuery")
        return 1
    
    # Step 2: Ask user if they want to load data
    print("\nSTEP 2: Data Loading")
    print("-" * 70)
    
    csv_files = config.get('gcs', {}).get('csv_files', [])
    
    if not csv_files:
        print("⚠️  No CSV files found in GCS bucket.")
        print("   You'll need to upload data files manually.")
        print()
        response = 'n'
    else:
        print(f"Found {len(csv_files)} CSV files:")
        for csv_file in csv_files:
            print(f"  - {csv_file}")
        print()
        
        response = input("Do you want to load these files to BigQuery? (y/n): ").strip().lower()
    
    if response == 'y':
        try:
            loaded_tables = load_all_week_data(config)
            
            # Update config with loaded tables
            config['bigquery']['tables'] = loaded_tables
            
            # Save updated config
            import json
            with open('environment_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
        except Exception as e:
            print(f"\n❌ Data loading failed: {e}")
            print("   You can try loading data manually later.")
    else:
        print("⏭️  Skipping data load. You can run it later with:")
        print("   python environment/data_loader.py")
    
    print()
    print("=" * 70)
    print("✅ INITIALIZATION COMPLETE!")
    print("=" * 70)
    print()
    print("Configuration saved to: environment_config.json")
    print()
    print("Next steps:")
    print("  1. Review environment_config.json")
    print("  2. Run Streamlit app: streamlit run streamlit_app/app.py")
    print("  3. Or run main.py for Cloud Run deployment")
    print()
    print(f"Environment Type: {config.get('environment_type', 'unknown')}")
    print(f"Project ID: {config.get('project_id')}")
    print(f"Dataset: {config.get('bigquery', {}).get('dataset_id')}")
    print(f"Tables: {len(config.get('bigquery', {}).get('tables', []))}")
    print()
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
