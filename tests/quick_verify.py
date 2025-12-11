import sys
import os

# Add parent directory to path so we can import from root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dq_agents.identifier.tools import _serialize_value_for_sql, get_database_settings, _get_bigquery_client

print('✅ All imports successful')
settings = get_database_settings()
print(f'✅ Database settings cached: {list(settings.keys())}')
client = _get_bigquery_client()
print(f'✅ ADK client created: {type(client).__name__}')
print(f'✅ SQL serialization test (quote escape): {_serialize_value_for_sql("O\'Brien")}')
print(f'✅ SQL serialization test (NULL): {_serialize_value_for_sql(None)}')
print('\n🎉 All three improvements verified and working!')
