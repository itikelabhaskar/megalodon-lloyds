from dq_agents.identifier.tools import get_database_settings
settings = get_database_settings()
print('Database Settings:')
for key, value in settings.items():
    print(f'  {key}: {value}')
