import os
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from .prompts import return_instructions_identifier
from .tools import (
    get_table_schema,
    get_table_schema_with_samples,
    execute_dq_rule, 
    trigger_dataplex_scan,
    load_preexisting_rules,
    get_all_week_tables,
    get_database_settings
)

def setup_identifier_agent(callback_context: CallbackContext) -> None:
    """Initialize database settings before agent runs."""
    if "database_settings" not in callback_context.state:
        callback_context.state["database_settings"] = get_database_settings()

def cache_identifier_results(tool, args, tool_context, tool_response) -> None:
    """Cache tool results for later use."""
    # Cache schema lookups
    if tool.name == "get_table_schema" and "table_schemas" not in tool_context.state:
        tool_context.state["table_schemas"] = {}
    
    if tool.name == "get_table_schema" and tool_response:
        table_name = args.get("table_name")
        if table_name:
            tool_context.state["table_schemas"][table_name] = tool_response
    
    return None

def get_identifier_agent():
    """Create and return the Identifier Agent instance with callbacks."""
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
        before_agent_callback=setup_identifier_agent,
        after_tool_callback=cache_identifier_results,
        generate_content_config=types.GenerateContentConfig(temperature=0.1)
    )

# Create singleton instance
identifier_agent = get_identifier_agent()
