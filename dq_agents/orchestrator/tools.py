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

"""Tools for DQ Orchestrator Agent."""

import logging
from typing import Any, Dict

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

logger = logging.getLogger(__name__)


async def call_identifier_agent(
    request: str,
    tool_context: ToolContext,
) -> str:
    """Call the Identifier Agent to detect DQ issues and generate rules.
    
    Args:
        request: Natural language request for the identifier agent
        tool_context: Tool execution context with state
        
    Returns:
        Response from identifier agent
    """
    logger.info("🔍 Calling Identifier Agent: %s", request)
    
    try:
        from dq_agents.identifier.agent import get_identifier_agent
        identifier_agent = get_identifier_agent()
        
        agent_tool = AgentTool(agent=identifier_agent)
        response = await agent_tool.run_async(
            args={"request": request}, 
            tool_context=tool_context
        )
        
        # Store in state for other agents
        tool_context.state["identifier_output"] = response
        logger.info("✅ Identifier Agent completed")
        
        return str(response)
    except Exception as e:
        logger.error(f"❌ Identifier Agent error: {str(e)}")
        return f"Error calling Identifier Agent: {str(e)}"


async def call_treatment_agent(
    request: str,
    tool_context: ToolContext,
) -> str:
    """Call the Treatment Agent to analyze issues and suggest fixes.
    
    Args:
        request: Natural language request for the treatment agent
        tool_context: Tool execution context with state
        
    Returns:
        Response from treatment agent with fix suggestions
    """
    logger.info("💊 Calling Treatment Agent: %s", request)
    
    try:
        from dq_agents.treatment.agent import treatment_agent
        
        agent_tool = AgentTool(agent=treatment_agent)
        response = await agent_tool.run_async(
            args={"request": request}, 
            tool_context=tool_context
        )
        
        # Store in state
        tool_context.state["treatment_output"] = response
        logger.info("✅ Treatment Agent completed")
        
        return str(response)
    except Exception as e:
        logger.error(f"❌ Treatment Agent error: {str(e)}")
        return f"Error calling Treatment Agent: {str(e)}"


async def call_remediator_agent(
    request: str,
    tool_context: ToolContext,
) -> str:
    """Call the Remediator Agent to execute approved fixes.
    
    Args:
        request: Natural language request for the remediator agent
        tool_context: Tool execution context with state
        
    Returns:
        Response from remediator agent with execution results
    """
    logger.info("🔧 Calling Remediator Agent: %s", request)
    
    try:
        from dq_agents.remediator.agent import remediator_agent
        
        agent_tool = AgentTool(agent=remediator_agent)
        response = await agent_tool.run_async(
            args={"request": request}, 
            tool_context=tool_context
        )
        
        # Store in state
        tool_context.state["remediator_output"] = response
        logger.info("✅ Remediator Agent completed")
        
        return str(response)
    except Exception as e:
        logger.error(f"❌ Remediator Agent error: {str(e)}")
        return f"Error calling Remediator Agent: {str(e)}"


async def call_metrics_agent(
    request: str,
    tool_context: ToolContext,
) -> str:
    """Call the Metrics Agent for analytics and Cost of Inaction.
    
    Args:
        request: Natural language request for the metrics agent
        tool_context: Tool execution context with state
        
    Returns:
        Response from metrics agent with analytics
    """
    logger.info("📊 Calling Metrics Agent: %s", request)
    
    try:
        from dq_agents.metrics.agent import metrics_agent
        
        agent_tool = AgentTool(agent=metrics_agent)
        response = await agent_tool.run_async(
            args={"request": request}, 
            tool_context=tool_context
        )
        
        # Store in state
        tool_context.state["metrics_output"] = response
        logger.info("✅ Metrics Agent completed")
        
        return str(response)
    except Exception as e:
        logger.error(f"❌ Metrics Agent error: {str(e)}")
        return f"Error calling Metrics Agent: {str(e)}"


def get_workflow_state(
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Get the current workflow state with outputs from all agents.
    
    Args:
        tool_context: Tool execution context with state
        
    Returns:
        Dictionary containing all agent outputs
    """
    logger.info("📋 Retrieving workflow state")
    
    state = {
        "identifier_output": tool_context.state.get("identifier_output"),
        "treatment_output": tool_context.state.get("treatment_output"),
        "remediator_output": tool_context.state.get("remediator_output"),
        "metrics_output": tool_context.state.get("metrics_output"),
    }
    
    return state


def request_human_approval(
    action: str,
    details: str,
    tool_context: ToolContext,
) -> str:
    """Request human approval for a critical action (HITL checkpoint).
    
    Args:
        action: The action requiring approval
        details: Details about the action
        tool_context: Tool execution context
        
    Returns:
        Approval request message
    """
    logger.info(f"🤚 HITL Checkpoint: Requesting approval for {action}")
    
    approval_request = f"""
🤚 **HUMAN-IN-THE-LOOP CHECKPOINT**

Action requiring approval: {action}

Details:
{details}

Please review the above information and provide approval to proceed.

Options:
1. Approve - Execute the action
2. Reject - Cancel this action
3. Modify - Request changes before execution
"""
    
    # Store approval request in state
    tool_context.state["pending_approval"] = {
        "action": action,
        "details": details,
        "status": "pending"
    }
    
    return approval_request
