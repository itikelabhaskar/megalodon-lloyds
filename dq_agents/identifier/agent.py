import os
from google.adk.agents import LlmAgent
from google.genai import types
from .prompts import return_instructions_identifier
from .tools import (
    get_table_schema, 
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
            trigger_dataplex_scan,
 