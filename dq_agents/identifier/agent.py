import os
from google.adk.agents import LlmAgent
from google.genai import types
from .prompts import return_instructions_identifier
from .tools import (
    get_table_schema,
    get_table_schema_with_samples,
    execute_dq_rule, 
    trigger_dataplex_scan,
    load_preexisting_rules,
    get_all_week_tables
)

def get_identifier_agent():
    """Create and return the Identifier Agent instance."""
    return LlmAgent(
        model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-flash"),
        name="identifier_agent",
        instruction=return_instructions_identifier(),
        tools=[
            load_preexisting_rules,
            get_all_week_tables,
            get_table_schema,
            get_table_schema_with_samples,
            trigger_dataplex_scan,
            execute_dq_rule
        ],
        generate_content_config=types.GenerateContentConfig(temperature=0.1)
    )

# Create singleton instance
identifier_agent = get_identifier_agent()
