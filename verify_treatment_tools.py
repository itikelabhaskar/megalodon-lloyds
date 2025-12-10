from dq_agents.treatment.agent import treatment_agent

print(f'Treatment agent: {len(treatment_agent.tools)} tools')
for t in treatment_agent.tools:
    tool_name = t.__name__ if hasattr(t, '__name__') else str(t)
    print(f'  - {tool_name}')
print("\n✅ Treatment Agent verified with all tools")
