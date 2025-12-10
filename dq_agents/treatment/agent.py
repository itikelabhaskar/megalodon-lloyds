"""
Treatment Agent

Analyzes DQ issues and suggests remediation strategies with Knowledge Bank integration.
"""

import os
from google.adk.agents import LlmAgent
from google.genai import types
from .prompts import return_instructions_treatment
from .tools import (
    execute_dq_rule,
    query_related_data,
    search_knowledge_bank,
    save_to_knowledge_bank,
    calculate_fix_impact,
    get_column_statistics,
    get_affected_row_sample
)

treatment_agent = LlmAgent(
    model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-flash"),
    name="treatment_agent",
    instruction=return_instructions_treatment(),
    tools=[
        execute_dq_rule,
        query_related_data,
        search_knowledge_bank,
        save_to_knowledge_bank,
        calculate_fix_impact,
        get_column_statistics,
        get_affected_row_sample
    ],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2  # Slightly higher than identifier for creative fix suggestions
    )
)
