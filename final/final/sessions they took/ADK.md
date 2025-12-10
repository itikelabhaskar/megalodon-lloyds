# Build, scale, and govern agents

Satender Qazi
November 2025
Google Cloud

**Proprietary & Confidential**

---

## Contents

|**Section**|**Title**|
|---|---|
|**01**|Vertex AI Agent Builder Overview|
|**02**|Build agents|
|**03**|Agent Development Kit (ADK)|
|**04**|Agent tools|
|**05**|Agentic Protocols|
|**06**|Pre-built agents|
|**07**|Scale with Agent Engine|
|**08**|Demo|

---

## 01 Vertex AI Agent Builder Overview

**Build, scale, and govern agents**

> [Image Note: AI Agent Runtime Architecture]
>
> A diagram illustrating how AI Agents function.
>
> * User Interaction: A user provides a Query, and the system provides a Response.
>
> - **Agent Runtime:** The core box containing the following components:
>   - **Orchestration (e.g., Agent Brain):** Handles Profile, goals & instructions. Includes **Memory** (Short-term & Long-term) and **Model-based reasoning/planning** (Question decomposition & reflection).
>   - **Generative AI Models:** Used to reason over goals, determine plans, and generate responses. An Agent can use multiple models.
>   - **Tools:** Used to fetch data, perform actions or transactions. Includes APIs, Functions, Databases, and other Agents.
>
> - Definitions:
>   * Model(s): Used to reason over goals, determine the plan and generate a response.
>   * Tools: Fetch data, perform actions or transactions by calling other APIs or services.
>   * Orchestration: Maintain memory and state (including the approach used to plan), tools, data provided/fetched, etc.
>   * Runtime: Execute the system when invoked.

---

### The Google Cloud AI Agent Builder Stack

> [Image Note: Technology Stack Pyramid]
>
> A hierarchical view of the Agent Builder stack, from bottom to top:
>
> 1. Vertex AI w/Gemini: Google Cloud's unified and open technology stack to meet the needs of enterprise customers.
> 2. Agent2Agent (A2A) protocol: Open standard designed to enable communication and collaboration between AI agents.
> 3. Model Context Protocol (MCP): Open protocol that standardizes how applications provide context to LLMs.
> 4. Agent Engine: Managed platform to deploy, manage, and scale AI agents in production.
> 5. Agent Developer Kit (ADK): Open-source toolkit for building, evaluating, and deploying AI agents.

---

### Vertex AI Agent Builder Architecture

> [Image Note: Detailed Architecture Diagram]
>
> A comprehensive dashboard view divided into three layers: Build, Scale, and Govern.

**Build:** Open-source toolkit for building, evaluating, and deploying AI agents (Agent Development Kit).

- **Models / Gemini API:**
  - **Gemini Models:** Optimized for agentic reasoning.
  - **Model Garden:** Hundreds of curated LLMs.
  - **Model Agnostic:** Choose the model for your needs.
  - **Multimodal:** Audio, Video Streaming.

- **Tools and Data:**
  - **Protocols:** A2A, MCP.
  - **Grounding:** Search Grounding, RAG.
  - **Ecosystem:** Ecosystem Tools, 100s of Connectors, Agent garden.
  - **Context:** Enterprise Context, Data for Agents.

- **Other Components:** Open Source Orchestration, Eval and Annotation.

**Scale:** Deploy and manage agents in production with managed services (Agent Engine).

- **Core Services:** Runtime, Sessions, Memory Bank.
- **Capabilities:** Observability, Code Execution, Computer Use.
- **Optimization:** Evaluation, Example Store.

**Govern:** Govern agent sprawl; manage risk and compliance (Agent Engine).

- **Features:** Identity, Enterprise Ready, Agent & Tool Registries, Security.

---

## 02 Build Agents

**Use ADK to define multi-agent applications for complex real-world scenarios with access to world-class models and tools.**

---

## 03 Agent Development Kit (ADK)

### What is ADK?

An open-source framework designed to build, test, & deploy agents.

- Easy to use interface
- Modular and flexible
- Instant local testing
- Native multimodal support
- Deployment ready

> [Image Note: Agent Hierarchy]
>
> A tree diagram showing a Root agent branching into Sub-Agent 1 and Sub-Agent 2. Sub-Agent 1 further branches into two more sub-agents. This illustrates the hierarchical structure supported by ADK.

### Agent Types Structure

> [Image Note: Class Inheritance Diagram]
>
> * BaseAgent: The parent class.
>
> - **Extended By:**
>   - A. LLM-Based: `LlmAgent` (Reasoning, Tools, Transfer).
>   - B. Workflow Agents: `SequentialAgent`, `ParallelAgent`, `LoopAgent`.
>   - C. Custom Logic: `CustomAgent`.

### ADK Core Concepts (Super Speed Run!)

**LlmAgent (Agent): The brain / worker**

- Uses an LLM (e.g., Claude, open models, Gemini, etc.).
- Key parameters: name, model, instruction, tools.

**Tools (FunctionTool): Agent's skill / action**

- Capabilities you give to your agent (Python functions).
- ADK handles the schema generation for the LLM.

**Runner: Executes the agent (ADK run, ADK web)**

- Executes your agent.
- Manages session (conversation state).

**Session & State**

- **Session:** Conversation.
- **State:** Dictionary for passing data within a session.

---

## 04 Agent Tools

### Today: Flexible Tool Support

Tools give agents a way to interact with the world.

> [Image Note: Tool Categories Diagram]
>
> A categorization of available tools with logos:
>
> * Functions: Python Function, Agent-as-tool.
> * Built-in: Google Search, Code Execution, Vertex AI Search.
> * Third-Party: LangChain, CrewAI.
> * Custom: MCP, OpenAPI.
> * Google Cloud: Apigee, GCP APIs (coming soon), MCP Toolbox for Databases.
> * GCP Marketplace: Crowdstrike, Wiz, HubSpot.
> * Community: Github, BrowserBase, Notion.

**Enterprise ready tool enablement (Coming soon):**

- **Tool Registry:** A trusted source of approved tools for developers in your organization.
- **Add any tool:** Tools covering 1P GCP services, support for building custom tools (Apigee) or bring 3P remote tools (standardized on MCP) as supported today.
- **Provide reuse:** Configure tools once and distribute approved tools to developers in your organization eliminating duplicate development efforts across teams.
- **Centralized Management:** Govern tool use with built-in Agent Identity support.

> [Image Note: Tool Registry Screenshot]
>
> A screenshot of the Vertex AI console showing a "Tools" list. Columns include Name, Description, Type (e.g., MCP_SERVER), Server Source (e.g., Apigee, Cloud Run), Org policy (Allowed), and MCP status (Enabled). Examples include "Acme API", "Salesforce API", "Inventory-function".

### Continuously Expanding Portfolio of Tools

- **Dec 2025:** Tool Registry: Unified tool management and discovery in GCP and ADK. New tools: Google Maps, Cloud Run, GKE, BigQuery, Firecrawl.
- **Q1 2026:** New Tools: GCP Marketplace tools, Twilio, Tavily, CloudSQL.
- **Q2 2026:** Securely manage connection to 3P providers with GCP IAM Connections. Reuse tools across Gemini Enterprise and Agent Builder.

---

## 05 Agentic Protocols

### Native support for Agentic protocols

MCP helps you build your own agents, A2A lets you and your agents use other agents.

**MCP (Model Context Protocol) for tools and resources**

- Connect agents to tools, APIs, and resources with structured inputs/outputs.
- ADK supports MCP tools, enabling wide range of MCP servers to be used with agents.

**A2A (Agent2Agent Protocol) for agent-agent collaboration**

- Dynamic, multimodal communication between different agents without sharing memory, resources, and tools.
- Open standard driven by community.
- Samples available using ADK, LangGraph, Crew.AI.

> **[Image Note: MCP vs A2A Diagram]**
>
> - **MCP Flow (Agent A):** Agent A acts as an MCP Host. It connects to MCP Clients, which connect to MCP Servers (A, B, C). These servers connect to Local Data Sources and Web APIs (Internet).
> - **A2A Flow:** Agent A (MCP Host) connects to Agent B (MCP Host) via the **A2A Protocol**. Agent B has its own set of MCP Clients and Servers (Y, Z).
>
> * **A2A Features:** Secure Collaboration, Task and State Management, UX Negotiation, Capability Discovery.

### Agent Payments Protocol (AP2) for Secure Agentic Commerce

Built on top of MCP and A2A to:

- Establish trust b/w "Shopping Agent", Merchants & Payments.
- Provide visibility into Agent Initiated Payments.
- Safely exchange sensitive identity & payments credentials.
- Establish accountability contracts among Users, Merchants & Issuers.
- Manage Txn lifecycle (Risk Check, Auth, Refunds, disputes etc.).

> **[Image Note: Protocol Stack Diagram]**
>
> - **Layer 2 (AP2 Protocol):** Deeper trust, specific functionality. Uses OAuth, API Keys, VCs.
> - Layer 1 (Underlying Protocols): Discovery, communication, baseline trust.
>   * A2A: Agent-to-Agent Interaction.
>   * MCP: Agent-Web Services Interaction.
>   * Base: HTTP/SSL/DNSSEC (Today's Internet).

---

## 06 Pre-built Agents

### The AI Agent Marketplace

Open platform for enterprise customers to find, buy and deploy 3p AI Agents.

> [Image Note: Marketplace Screenshot]
>
> A grid view of the Google Cloud Marketplace showing "AI Agents".
>
> * Listings: 1236 results.
> * Examples: Sensor Cue Detector Agent (Accenture), Deepgram Voice AI, TCS GenAI SDLC Assistant, Airline Assistant, PhishDetect Phishing Detector, Agentic CV Parser, Kyndryl Consult Helper, Marketing Campaign Planner, Damage Visual Inspector, HR Assist.
> * Partners: Palo Alto Networks, Optimizely, UiPath, Accenture, Deloitte, Wipro, HCL.

### Start building faster with agent samples: Vertex AI Agent Garden

Discover agent samples and tools specific to your use cases. Learn by example, how to use frameworks and tools.

> [Image Note: Agent Garden Screenshot]
>
> A catalog of "Samples" and blueprints.
>
> * Samples: Data Science, FOMC Research, Travel Concierge, Brand Search Optimization, Customer Service, RAG, LLM Auditor, Personalized Shopping.
> * Tools: AlloyDB, Amazon S3, BigQuery, Box, Cloud SQL, Confluence, Custom APIs, Dropbox.
>
> - **Features:** Get started with source code in GitHub, clone and customize. Components of your multi-agent system may already be available.

---

## 07 Scale with Agent Engine

**Use managed services from the Vertex AI Agent Engine to scale agents in production.**

### Vertex AI Agent Engine (AE)

**Scale agents in production with modular, managed services**

- **Runtime:** Deploy and scale agents in production without managing infrastructure.
- **Sessions:** Store and manage context of conversations between agents and users.
- **Memory Bank:** Summarize data across sessions to personalize & improve.
- **Example Store:** Improve quality by storing, managing, and retrieving few-shot examples during conversations.
- **AE Sandbox (Coming soon):** Securely execute code and control computer use.
- **Observability:** Integrated Observability (Cloud Trace, Monitoring, Logging) and Evaluation suites.

### Simplify the process of building and deploying agents

> [Image Note: Microservices vs Agents Comparison]
>
> * Microservices (Old Way): Business Logic + External Integration -> Containerized App -> Framework (Kubernetes/Cloud Run) -> Platform (Monitor, Scale, Network, Volume, Identity, Image Registry).
>
> - Agents (New Way): Agent Development Kit (ADK) -> Agent Engine.
>   * Agent Engine Handles: Tool use, Sessions & short term memory, Long term Memory Bank, Identity Management, Code execution, Evaluation, Agent Garden.
>   * Concept: User Flow + Agentic Framework = Ready to deploy Agents.

> [Image Note: Scalable Deployment Diagram]
>
> Highlights the transition from multiple frameworks (LangGraph, LangChain, AG2, CrewAI, Google ADK, LlamaIndex) to a unified Agent Engine.
>
> * Features: Serverless Runtime & Session Store, Agent Monitoring & Visualization (Vertex AI Console, Track & Trace), Vertex AI GenAI Evaluation.---

### AE Runtime

Prebuilt Templates in SDK

Easily deploy to Unified interface while retaining the framework specific customizability powered by the protocol in Agent Engine SDK. Supported frameworks: ADK, LangChain, LangGraph, LlamaIndex, AG2.

**Code Examples:**

- **ADK:** `agent = agent_engines.AdkApp(model=model, tools=[...])`
- **LangChain:** `agent = agent_engines.LangchainAgent(model=model, tools=[...])`
- **LangGraph:** `agent = agent_engines.LanggraphAgent(model=model, tools=[...])`
- **LlamaIndex:** `agent = agent_engines.LlamaIndexAgent(model=model, tools=[...])`
- **A2A:** (Coming Soon) Deploy any A2A agent to AgentEngine.

**Why choose the Agent Engine Runtime?** Spend more time building great agents, less time managing infrastructure.

- **Bundled Services:** Managed Runtime, Sessions, Memory Bank, Sandboxes.
- **Integrated Governance & Quality:** Agent Identity, Model Armor, Quality & Evaluation services, A2A.
- **Ecosystem Solutions:** Integration with Agent & Tool Registry and Gemini Enterprise.
- **A Unified Production UI:** Single console, Monitoring Dashboard, Unified Traces Tab, Integrated Playground.

---

### AE Sessions and Memory Bank

> [Image Note: Sessions & Memory Flowchart]
>
> A cycle showing how data moves:
>
> 1. ListEvents: Fetch history for current session.
> 2. Sessions (Agent Engine): Stores interaction history.
> 3. AppendEvent: User messages/agent actions logged as events.
> 4. Generate Memories: Extracts facts (Extract, merge).
> 5. Memory Bank (Agent Engine): Stores the memories.
> 6. Retrieve Memories: Agent fetches relevant memories.
> 7. Generate Memories (Merge only): Agent functions as a tool (memory-as-a-tool) to write pre-extracted info.

> [Image Note: User-Agent-Memory Swimlane]
>
> * Turn 1: User: "I have oily skin..." -> Agent creates memory 'Oily Skin'.
> * Turn 2: User: "Recommendation for cleanser?" -> Agent recalls `'Oily Skin'` -> Recommends gel-based.
> * Turn 3: User: "Skin type changed to dry..." -> Agent updates memory to `'Dry, Flaky, Sensitive Skin'`.
> * Turn 4: User: "Skincare routine?" -> Agent recalls `'Dry, Flaky...'` -> Recommends hydrating cleanser.

**How it works (Step-by-Step):**

1. **CreateSessions:** Each conversation begins with a new Session linked to a userID.
2. **AppendEvent:** User messages and agent actions are sequentially logged as Events within the session.
3. **ListEvent:** Fetch the history for the current session to maintain context.
4. **Generate Memories:** At set intervals, the system automatically analyzes session history to extract facts.
5. **Generate Memories (merge only):** The agent can function as a tool to directly write pre-extracted information to the Memory Bank.
6. **Retrieve Memories:** The agent retrieves stored memories for that user to inform its next response. Retrieved facts are inserted into the prompt.

**Why use Memory Bank?**

- **Personalize interactions:** Remember names, preferences.
- **Maintain continuity:** Pick up conversations where they left off.
- **Provide better context:** Give agent background info.
- **Improve User Experience:** Avoid repetitive questions.

---

### Sample Multi-Agent built with ADK on Google Cloud

> [Image Note: Multi-Agent Architecture]
>
> A diagram of a financial report system.
>
> * User interacts with Orchestrator Agent.
>
> - Orchestrator connects to:
>   * Report Generator Agent
>   * Broad Screening Agent (Connects to BigQuery)
>   * Deep Dive Research Agent (Connects to Knowledge Repository)
>   * Middle Layer: Relevancy Agent acts as a filter/check between Report Generator and Deep Dive.
>   * Tools: Google Search Grounding, Agentspace Deep Research.
>   * Data Pipeline: Document AI (Text extraction) -> Cloud Storage (Raw docs) -> BigQuery (Parsed reports/embeddings).

### Example: HKFinBot

> [Image Note: HKFinBot Flow 1]
>
> User -> Coordinator Agent.
>
> * Coordinator: Orchestrates tasks, delegates to sub-agents, maintains context.

> [Image Note: HKFinBot Flow 2]
>
> Coordinator Agent branches to three sub-agents:
>
> 1. Market Pulse Agent
> 2. News Impact Agent
> 3. Stock Deepdive Agent

> **[Image Note: HKFinBot Flow 3 - Tool Connections]**
>
> - **Market Pulse & News Impact Agents** connect to **HSI MCP Server (Tool)**. This provides Live HSI data and Live news.
> - **Stock Deepdive Agent** connects to **Google Search (Built-in Tool)**. This provides Public web access.

---

## 08 Demo

Data science agent

Showing the power of the ADK to build a multi-agent system that can get data, analyze it, make predictions, and improve with input from the Gemini multimodal live API.

**ADK Sample Codes:** `https://github.com/google/adk-samples`

---

## Wrapping Up

> [Image Note: Enterprise Security & Governance Stack]
>
> A summary diagram of the entire platform.
>
> * Users: Internal Chatbot, AI Applications, Customer Engagement Suite.
> * Data & Tools: Grounding & RAG, Data for Agents, Enterprise Context (Connectors, Knowledge Graph).
>
> - Vertex AI Agentic Foundation (For Developers):
>   * Build: Agent Development Kit (ADK).
>   * Runtime (Agent Engine): Orchestration, Monitor/Log, Sessions, Evaluation, Code Execution, Long term memory.
>   * Models: Gemini API, Gemini Models (Optimized for agentic reasoning).
>   * Ecosystem: Native tool use, MCP, A2A, LangChain, etc.
>   * Libraries: Agent Garden, Model Garden.

**Thank you**