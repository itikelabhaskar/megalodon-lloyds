import os
from google.adk.agents import LlmAgent
from google.genai import types
from .prompts import return_instructions_remediator
from .tools import (
    dry_run_fix, 
    execute_fix, 
    validate_fix, 
    create_jira_ticket,
    get_before_after_comparison
)

remediator_agent = LlmAgent(
    model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-flash"),
    name="remediator_agent",
    instruction=return_instructions_remediator(),
    tools=[
        dry_run_fix,
        execute_fix,
        validate_fix,
        create_jira_ticket,
        get_before_after_comparison
    ],
    generate_content_config=types.GenerateContentConfig(temperature=0.0)  # Low temp for safety
)
