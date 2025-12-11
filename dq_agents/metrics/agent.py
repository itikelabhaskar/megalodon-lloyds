import os
from google.adk.agents import LlmAgent
from google.genai import types
from .prompts import return_instructions_metrics
from .tools import (
    calculate_remediation_metrics,
    calculate_cost_of_inaction,
    detect_anomalies_in_data,
    generate_metrics_narrative,
    get_dq_rule_accuracy
)

metrics_agent = LlmAgent(
    model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-flash"),
    name="metrics_agent",
    instruction=return_instructions_metrics(),
    tools=[
        calculate_remediation_metrics,
        calculate_cost_of_inaction,
        detect_anomalies_in_data,
        generate_metrics_narrative,
        get_dq_rule_accuracy
    ],
    generate_content_config=types.GenerateContentConfig(temperature=0.3)
)
