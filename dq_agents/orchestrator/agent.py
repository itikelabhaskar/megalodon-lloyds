# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""DQ Orchestrator Agent."""

import os
from google.adk.agents import LlmAgent
from google.genai import types

from .prompts import return_instructions_orchestrator
from .tools import (
    call_identifier_agent,
    call_treatment_agent,
    call_remediator_agent,
    call_metrics_agent,
    get_workflow_state,
    request_human_approval,
)

orchestrator_agent = LlmAgent(
    model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-flash"),
    name="orchestrator_agent",
    instruction=return_instructions_orchestrator(),
    tools=[
        call_identifier_agent,
        call_treatment_agent,
        call_remediator_agent,
        call_metrics_agent,
        get_workflow_state,
        request_human_approval,
    ],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=8192,
    )
)
