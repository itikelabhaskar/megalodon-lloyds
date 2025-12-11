import streamlit as st
import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings

# Suppress specific warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*coroutine.*was never awaited.*')
warnings.filterwarnings('ignore', message='.*missing ScriptRunContext.*')

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

# Import environment configuration utilities
from environment.config_utils import (
    load_config, 
    get_project_id, 
    get_dataset_id, 
    get_tables,
    get_environment_type,
    get_organization_name,
    get_copyright_year
)

# Import ADK components at the top
import asyncio
from google.genai import types
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from dq_agents.identifier.agent import get_identifier_agent

st.set_page_config(
    page_title="DQ Management System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional UI
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Card-like container styling */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: #262730;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        border: 1px solid #363940;
        color: #FAFAFA;
    }

    /* Metric styling */
    div[data-testid="stMetric"] {
        background-color: #262730;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        border: 1px solid #363940;
        color: #FAFAFA;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 6px;
        gap: 1px;
        padding: 0px 16px;
        font-weight: 500;
        color: #FAFAFA;
    }
    .stTabs [aria-selected="true"] {
        background-color: #363940;
        color: #4da6ff;
        font-weight: 600;
        border-bottom: none;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0E1117;
        border-right: 1px solid #363940;
    }
    
    /* Header styling */
    h1 {
        color: #FAFAFA;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    h2 {
        color: #E0E0E0;
        font-weight: 600;
        letter-spacing: -0.3px;
    }
    h3 {
        color: #E0E0E0;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    
    /* Custom Header Styling */
    .custom-header {
        display: flex;
        align-items: center;
        padding: 1.5rem 0 1rem 0;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid #363940;
    }
    
    .custom-header img {
        height: 60px;
        margin-right: 1.5rem;
    }
    
    .custom-header-text {
        flex: 1;
    }
    
    .custom-header-title {
        font-size: 2rem;
        font-weight: 700;
        color: #FAFAFA;
        margin: 0;
        line-height: 1.2;
    }
    
    .custom-header-subtitle {
        font-size: 1rem;
        color: #B0B0B0;
        margin: 0.25rem 0 0 0;
        font-weight: 400;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with dynamic configuration
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    
    # Load dynamic configuration
    try:
        config = load_config()
        st.session_state.project_id = config.get('project_id', '')
        st.session_state.dataset_id = config.get('bigquery', {}).get('dataset_id', '')
        st.session_state.available_tables = config.get('bigquery', {}).get('tables', [])
        st.session_state.environment_type = config.get('environment_type', 'unknown')
    except Exception as e:
        st.warning(f"⚠️ Could not load environment_config.json: {e}")
        st.info("💡 Run `python init_environment.py` to set up automatic environment detection")
        # Fallback to environment variables
        st.session_state.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        st.session_state.dataset_id = os.getenv("BQ_DATASET_ID", "")
        st.session_state.available_tables = []
        st.session_state.environment_type = 'manual'

# Cache management configuration
CACHE_FILE = "dq_rules_cache.json"

# Cache management functions
def load_rules_cache():
    """Load DQ rules cache from JSON file"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Failed to load cache: {e}")
            return {"cache_metadata": {"last_updated": None, "version": "1.0.0"}, "tables": {}}
    return {"cache_metadata": {"last_updated": None, "version": "1.0.0"}, "tables": {}}

def save_rules_cache(cache_data):
    """Save DQ rules cache to JSON file"""
    try:
        cache_data["cache_metadata"]["last_updated"] = datetime.now().isoformat()
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2, default=str)
        return True
    except Exception as e:
        st.error(f"Failed to save cache: {e}")
        return False

def get_cached_rules(table_name):
    """Get cached rules for a specific table"""
    cache = load_rules_cache()
    return cache.get("tables", {}).get(table_name, None)

def cache_rules_for_table(table_name, rules):
    """Cache rules for a specific table"""
    cache = load_rules_cache()
    if "tables" not in cache:
        cache["tables"] = {}
    cache["tables"][table_name] = {
        "rules": rules,
        "generated_at": datetime.now().isoformat(),
        "rule_count": len(rules)
    }
    return save_rules_cache(cache)

def clear_cache_for_table(table_name):
    """Clear cached rules for a specific table"""
    cache = load_rules_cache()
    if table_name in cache.get("tables", {}):
        del cache["tables"][table_name]
        return save_rules_cache(cache)
    return False

import base64

# Initialize active tab in session state if not exists
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "🔍 Identifier"

# Add custom header with Lloyd's logo (BEFORE sidebar)
import base64
logo_path = "lloyd's logo.png"
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <div class="custom-header">
        <img src="data:image/png;base64,{logo_base64}" alt="Lloyd's Logo">
        <div class="custom-header-text">
            <h1 class="custom-header-title">🔍 Data Quality Management System</h1>
            <p class="custom-header-subtitle">Autonomous DQ Detection, Treatment & Remediation for Lloyd's Banking</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="custom-header">
        <div class="custom-header-text">
            <h1 class="custom-header-title">🔍 Data Quality Management System</h1>
            <p class="custom-header-subtitle">Autonomous DQ Detection, Treatment & Remediation for Lloyd's Banking</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Tab names for navigation
tab_names = [
    "🤖 Orchestrator",
    "🔍 Identifier", 
    "💊 Treatment", 
    "🔧 Remediator",
    "📊 Metrics",
    "⚙️ Advanced Settings"
]

# Sidebar with Navigation FIRST, then Settings
with st.sidebar:
    # Navigation in sidebar - FIRST
    st.markdown("### 📍 Navigation")
    
    # Determine default index
    try:
        default_index = tab_names.index(st.session_state.active_tab)
    except (ValueError, AttributeError):
        default_index = 1  # Default to Identifier
    
    selected_tab = st.radio(
        "Go to:",
        options=tab_names,
        index=default_index,
        label_visibility="collapsed"
    )
    
    # Update active tab if changed
    if selected_tab != st.session_state.active_tab:
        st.session_state.active_tab = selected_tab
        st.rerun()
    
    st.divider()
    
    # Settings - SECOND
    st.title("⚙️ Settings")
    
    with st.expander("☁️ GCP Configuration", expanded=True):
        project_id = st.text_input(
            "Project ID", 
            value=st.session_state.project_id,
            key="project_id_input",
            help="Your Google Cloud Project ID"
        )
        st.session_state.project_id = project_id
        
        dataset_id = st.text_input(
            "Dataset ID",
            value=st.session_state.dataset_id,
            key="dataset_id_input",
            help="BigQuery dataset containing BaNCS data"
        )
        st.session_state.dataset_id = dataset_id
        
        if st.button("🔌 Test Connection", use_container_width=True):
            with st.spinner("Connecting..."):
                try:
                    from google.cloud import bigquery
                    client = bigquery.Client(project=project_id)
                    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
                    tables = list(client.list_tables(dataset_ref))
                    st.success(f"Connected! Found {len(tables)} tables.")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")

    with st.expander("🤖 Model Settings", expanded=False):
        global_model = st.selectbox(
            "Global Model",
            options=["gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro"],
            index=0
        )
        st.info("Configure per-agent models in Advanced Settings")

    st.divider()
    
    # Environment Info Compact
    env_type = st.session_state.get('environment_type', 'unknown')
    available_tables = st.session_state.get('available_tables', [])
    
    st.markdown("### Environment")
    st.caption(f"Type: {env_type}")
    st.caption(f"Tables: {len(available_tables)}")
    
    if env_type == 'manual' or not available_tables:
        st.warning("Run `init_environment.py` for auto-setup")
    
    # GCP Logo at the bottom - pinned
    st.divider()
    st.markdown("<br>" * 2, unsafe_allow_html=True)  # Add spacing to push logo down
    
    try:
        with open("Google_Cloud_logo.svg.png", "rb") as f:
            gcp_logo_data = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <div style="position: fixed; bottom: 20px; width: 250px; text-align: center;">
                <img src="data:image/png;base64,{gcp_logo_data}" 
                     style="width: 100%; max-width: 180px; opacity: 0.7;">
                <p style="font-size: 10px; color: #666; margin-top: 5px;">Powered by Google Cloud</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        pass  # If logo not found, skip

# Initialize Agent Debate Logger in session state
if 'agent_debate_logger' not in st.session_state:
    from dq_agents.bonus_features import AgentDebateLogger
    st.session_state.agent_debate_logger = AgentDebateLogger()

# Render content based on active tab
active_tab = st.session_state.active_tab

if active_tab == "🤖 Orchestrator":
    st.markdown("**Master coordinator for the complete DQ workflow** - from detection to remediation")
    
    with st.expander("ℹ️ About the Orchestrator", expanded=False):
        st.info("""
        The Orchestrator Agent is the "brain" that coordinates all 4 specialized agents:
        - 🔍 **Identifier**: Detects DQ issues and generates rules
        - 💊 **Treatment**: Analyzes issues and suggests fixes
        - 🔧 **Remediator**: Executes approved fixes safely
        - 📊 **Metrics**: Provides analytics and Cost of Inaction
        
        It implements Human-in-the-Loop (HITL) checkpoints for critical decisions.
        """)
    
    # Workflow mode selection
    with st.container():
        st.subheader("1. Select Workflow")
        
        workflow_mode = st.selectbox(
            "Choose a workflow",
            [
                "🚀 Full Automated Workflow",
                "🎯 Custom Workflow (Select Agents)",
                "💬 Natural Language Request"
            ],
            help="Select how you want to orchestrate the agents"
        )
        
        if workflow_mode == "🚀 Full Automated Workflow":
            st.markdown("### Full Automated Workflow")
            st.caption("Run the complete DQ pipeline: Detect → Analyze → Fix → Report")
            
            col_wf1, col_wf2 = st.columns(2)
            
            with col_wf1:
                available_tables = st.session_state.get('available_tables', [])
                if not available_tables:
                    st.error("❌ No tables found. Run `python init_environment.py` to initialize.")
                    available_tables = ["policies_week1"]  # Fallback
                
                wf_tables = st.multiselect(
                    "Select table(s)",
                    available_tables,
                    default=[available_tables[0]] if available_tables else [],
                    help="Select one or more tables to analyze"
                )
            
            with col_wf2:
                wf_auto_approve = st.checkbox(
                    "Auto-approve high-confidence fixes",
                    value=False,
                    help="Automatically approve fixes with >90% confidence"
                )
            
            if st.button("🚀 Start Full Workflow", type="primary", key="start_full_wf", use_container_width=True, disabled=len(wf_tables) == 0):
                with st.status("🤖 Orchestrator is coordinating agents...", expanded=True) as status:
                    try:
                        from dq_agents.orchestrator.agent import orchestrator_agent
                        from google.genai import types
                        
                        session_service = InMemorySessionService()
                        artifact_service = InMemoryArtifactService()
                        runner = Runner(
                            app_name="DQOrchestratorAgent",
                            agent=orchestrator_agent,
                            session_service=session_service,
                            artifact_service=artifact_service
                        )
                        
                        import asyncio
                        session = asyncio.run(session_service.create_session(
                            app_name="DQOrchestratorAgent",
                            user_id="streamlit_user"
                        ))
                        
                        # Format tables list
                        tables_str = ", ".join(wf_tables) if len(wf_tables) > 1 else wf_tables[0]
                        
                        # Log orchestrator start
                        st.session_state.agent_debate_logger.log_agent_thought(
                            "Orchestrator",
                            f"Starting full workflow for {tables_str}",
                            "Initializing all agents",
                            "Workflow started"
                        )
                        
                        auto_approve_text = " with auto-approval enabled" if wf_auto_approve else ""
                        tables_plural = "tables" if len(wf_tables) > 1 else "table"
                        prompt = (
                            f"Execute the complete DQ workflow for {tables_plural} '{tables_str}'{auto_approve_text}:\n\n"
                            "1. Call identifier agent to detect DQ issues and generate rules\n"
                            "2. Execute the generated rules and identify violations\n"
                            "3. Call treatment agent to analyze issues and suggest top 3 fixes\n"
                            "4. Request human approval for fixes (unless auto-approve is enabled)\n"
                            "5. Call remediator agent to execute approved fixes\n"
                            "6. Call metrics agent to calculate Cost of Inaction\n"
                            "7. Generate executive summary report\n\n"
                            "Provide detailed status updates at each phase showing agent reasoning."
                        )
                        
                        content = types.Content(role="user", parts=[types.Part(text=prompt)])
                        
                        # Stream events to show progress
                        progress_placeholder = st.empty()
                        event_count = 0
                        all_events = []
                        
                        status.write("🔄 Starting orchestration...")
                        
                        for event in runner.run(
                            user_id="streamlit_user",
                            session_id=session.id,
                            new_message=content
                        ):
                            all_events.append(event)
                            event_count += 1
                            
                            # Show progress updates
                            if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                                for part in event.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        # Extract phase from text
                                        text_snippet = part.text[:150]
                                        if "identifier" in text_snippet.lower():
                                            progress_placeholder.info("📋 Phase 1: Detecting issues...")
                                        elif "treatment" in text_snippet.lower():
                                            progress_placeholder.info("💊 Phase 2: Analyzing fixes...")
                                        elif "remediator" in text_snippet.lower():
                                            progress_placeholder.info("🔧 Phase 3: Applying fixes...")
                                        elif "metrics" in text_snippet.lower():
                                            progress_placeholder.info("📊 Phase 4: Calculating costs...")
                                        
                                        # Show snippet in status
                                        status.write(f"🤖 Event {event_count}: {text_snippet}...")
                        
                        if all_events:
                            last_event = all_events[-1]
                            response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                            
                            st.session_state.orchestrator_output = response_text
                            progress_placeholder.empty()
                            status.update(label="✅ Workflow completed!", state="complete", expanded=False)
                            st.rerun()
                        else:
                            status.update(label="❌ No response from Orchestrator", state="error")
                    
                    except Exception as e:
                        status.update(label="❌ Error occurred", state="error")
                        st.error(f"❌ Error: {str(e)}")
                        import traceback
                        with st.expander("🐛 Debug Info"):
                            st.code(traceback.format_exc())
        
        elif workflow_mode == "💬 Natural Language Request":
            st.markdown("### Natural Language Request")
            st.caption("Describe what you want to do in plain English")
            
            nl_request = st.text_area(
                "Your request",
                placeholder="Example: Find all data quality issues in the dataset, show me the top 5 most critical ones, and calculate how much money we're losing",
                height=100,
                help="Describe your DQ analysis request in natural language"
            )
            
            if st.button("🎯 Execute Request", key="exec_nl_req", use_container_width=True):
                if nl_request:
                    with st.status("🤖 Orchestrator is processing your request...", expanded=True) as status:
                        try:
                            from dq_agents.orchestrator.agent import orchestrator_agent
                            from google.genai import types
                            
                            session_service = InMemorySessionService()
                            artifact_service = InMemoryArtifactService()
                            runner = Runner(
                                app_name="DQOrchestratorAgent",
                                agent=orchestrator_agent,
                                session_service=session_service,
                                artifact_service=artifact_service
                            )
                            
                            import asyncio
                            session = asyncio.run(session_service.create_session(
                                app_name="DQOrchestratorAgent",
                                user_id="streamlit_user"
                            ))
                            
                            # Log to agent debate
                            st.session_state.agent_debate_logger.log_agent_thought(
                                "Orchestrator",
                                f"User request: {nl_request}",
                                "Analyzing request and planning agent coordination",
                                "Determining which agents to call"
                            )
                            
                            content = types.Content(role="user", parts=[types.Part(text=nl_request)])
                            
                            # Stream events to show progress
                            progress_placeholder = st.empty()
                            event_count = 0
                            all_events = []
                            
                            status.write("🔄 Processing your request...")
                            
                            for event in runner.run(
                                user_id="streamlit_user",
                                session_id=session.id,
                                new_message=content
                            ):
                                all_events.append(event)
                                event_count += 1
                                
                                # Show progress updates
                                if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                                    for part in event.content.parts:
                                        if hasattr(part, 'text') and part.text:
                                            text_snippet = part.text[:150]
                                            status.write(f"🤖 {text_snippet}...")
                            
                            if all_events:
                                last_event = all_events[-1]
                                response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                                
                                st.session_state.orchestrator_output = response_text
                                progress_placeholder.empty()
                                status.update(label="✅ Request completed!", state="complete", expanded=False)
                                st.rerun()
                            else:
                                status.update(label="❌ No response from Orchestrator", state="error")
                        
                        except Exception as e:
                            status.update(label="❌ Error occurred", state="error")
                            st.error(f"❌ Error: {str(e)}")
                            import traceback
                            with st.expander("🐛 Debug Info"):
                                st.code(traceback.format_exc())
                else:
                    st.warning("Please enter a request")
    
    # Display orchestrator output
    if 'orchestrator_output' in st.session_state:
        st.divider()
        with st.container():
            st.subheader("📋 Workflow Results")
            
            st.markdown(st.session_state.orchestrator_output)
            
            # Show agent debate logs
            if st.checkbox("🤖 Show Agent Debate Mode", value=True, help="View live agent reasoning and collaboration"):
                with st.expander("🗣️ Agent Thought Process & Collaboration", expanded=True):
                    debate_logs = st.session_state.agent_debate_logger.get_formatted_logs()
                    st.markdown(debate_logs)
            
            if st.button("🔄 Start New Workflow", use_container_width=True):
                del st.session_state.orchestrator_output
                st.session_state.agent_debate_logger.clear()
                st.rerun()

elif active_tab == "🔍 Identifier":
    st.markdown("Detect data quality issues and generate SQL-based DQ rules for BaNCS tables")
    
    # File uploader for pre-existing DQ rules
    with st.container():
        st.subheader("0. Upload Pre-existing DQ Rules (Optional)")
        st.caption("Upload your Collibra/Ataccama DQ rules as JSON. If not provided, system will use mock data.")
        
        col_upload, col_template = st.columns([3, 1])
        
        with col_upload:
            uploaded_file = st.file_uploader(
                "Upload DQ Rules JSON",
                type=['json'],
                help="Upload a JSON file containing your existing DQ rules from Collibra, Ataccama, or other systems"
            )
        
        with col_template:
            # Download template button
            template_json = """[
      {
        "rule_id": "YOUR_RULE_001",
        "name": "example_rule_name",
        "description": "Describe what this rule checks for",
        "sql": "SELECT * FROM `PROJECT.DATASET.TABLE` WHERE condition",
        "severity": "critical",
        "source": "Collibra",
        "dq_dimension": "Completeness",
        "category": "Completeness"
      }
    ]"""
            st.download_button(
                label="📥 Download Template",
                data=template_json,
                file_name="dq_rules_template.json",
                mime="application/json",
                help="Download a template JSON file to fill with your DQ rules",
                use_container_width=True
            )
        
        if uploaded_file is not None:
            try:
                import json
                rules_data = json.load(uploaded_file)
                
                # Validate it's a list
                if isinstance(rules_data, list):
                    st.session_state.uploaded_dq_rules = rules_data
                    st.success(f"✅ Loaded {len(rules_data)} pre-existing DQ rules from uploaded file")
                    
                    # Show preview
                    with st.expander("📄 Preview Uploaded Rules"):
                        st.json(rules_data[:3] if len(rules_data) > 3 else rules_data)
                else:
                    st.error("❌ JSON must be an array of rule objects")
            except Exception as e:
                st.error(f"❌ Error loading file: {str(e)}")
        else:
            if 'uploaded_dq_rules' in st.session_state:
                del st.session_state['uploaded_dq_rules']
            st.info("💡 No file uploaded. Using mock pre-existing rules from Collibra/Ataccama.")
    
    st.divider()
    
    # Generation Mode Selection
    with st.container():
        st.subheader("0.5. Generation Mode")
        generation_mode = st.radio(
            "How would you like to generate DQ rules?",
            options=["🤖 Automated (Schema + Profiling)", "💬 Natural Language (with Sample Data)"],
            help="Automated uses schema and Dataplex. Natural Language shows sample data to LLM for better rule generation."
        )
        
        if generation_mode == "💬 Natural Language (with Sample Data)":
            nl_description = st.text_area(
                "Describe the DQ rules you need:",
                placeholder="Example: I need rules to check for valid UK postcodes, ensure premiums are positive, and detect customers with future death dates...",
                height=100,
                help="Describe what you want to check in plain English. The agent will see table schemas + sample data."
            )
    
    st.divider()
    
    # Table selection
    with st.container():
        st.subheader("1. Select Tables")
        
        # Get available tables
        selected_tables = []
        try:
            from google.cloud import bigquery
            
            # Get project_id and dataset_id from session state
            _project_id = st.session_state.get('project_id', '')
            _dataset_id = st.session_state.get('dataset_id', '')
            
            if not _project_id or not _dataset_id:
                st.warning("⚠️ Please configure Project ID and Dataset ID in the sidebar settings.")
            else:
                client = bigquery.Client(project=_project_id)
                dataset_ref = bigquery.DatasetReference(_project_id, _dataset_id)
                tables = [table.table_id for table in client.list_tables(dataset_ref)]
                
                if tables:
                    selected_tables = st.multiselect(
                        "Choose tables to analyze:",
                        options=tables,
                        default=tables[:1] if tables else [],
                        help="Select one or more BaNCS tables"
                    )
                else:
                    st.warning("⚠️ No tables found in dataset")
        except Exception as e:
            st.error(f"❌ Failed to load tables: {str(e)}")
            st.info("💡 Check your GCP configuration in the sidebar")
    
    st.divider()
    
    # Analysis options
    st.subheader("2. Analysis Options")
    
    # GCP Integration Badge
    st.info("☁️ **Real GCP Integration Active** - Using Google Cloud Dataplex API for data profiling (~60 seconds per table)")
    
    col1, col2 = st.columns(2)
    with col1:
        include_schema = st.checkbox("Include Schema Analysis", value=True)
        include_dataplex = st.checkbox("🔍 Run Dataplex Data Profiling", value=True, help="Uses REAL Google Cloud Dataplex API for profiling - analyzes null rates, value distributions, and data patterns")
        include_preexisting = st.checkbox("Load Pre-existing Rules (Collibra/Ataccama)", value=True, help="Auto-enabled: Reviews historical DQ rules")
    
    with col2:
        include_crossweek = st.checkbox("Generate Cross-Week Temporal Rules", value=True, help="Auto-enabled: Detects status changes across time periods")
        focus_dimensions = st.multiselect(
            "Focus DQ Dimensions:",
            options=["Completeness", "Accuracy", "Timeliness", "Conformity", "Uniqueness"],
            default=["Completeness", "Accuracy", "Timeliness"],
            help="Select which data quality dimensions to prioritize"
        )
    
    num_rules = st.slider(
        "Number of rules to generate per table:",
        min_value=5,
        max_value=50,
        value=20,
        help="How many DQ rules should the agent generate? (Includes cross-week rules)"
    )
    
    st.divider()
    
    # Generate button
    st.subheader("3. Generate DQ Rules")
    
    # Check cache status
    rules_cache = load_rules_cache()
    cached_tables = list(rules_cache.get("tables", {}).keys())
    
    # Show cache status for selected tables
    if selected_tables:
        st.markdown("**📦 Cache Status:**")
        for table in selected_tables:
            if table in cached_tables:
                cache_info = rules_cache["tables"][table]
                st.success(f"✅ {table}: {cache_info['rule_count']} rules cached (generated {cache_info['generated_at'][:19]})")
            else:
                st.info(f"ℹ️ {table}: No cached rules")
    
    col_gen, col_cache = st.columns([3, 1])
    with col_gen:
        use_cache = st.checkbox("Use cached rules if available", value=True, help="Load from cache instead of regenerating")
    with col_cache:
        if cached_tables:
            if st.button("🗑️ Clear All Cache", help="Delete all cached rules"):
                for table in cached_tables:
                    clear_cache_for_table(table)
                st.success("Cache cleared!")
                st.rerun()
    
    if st.button("🚀 Generate DQ Rules", type="primary", disabled=not selected_tables):
        if not selected_tables:
            st.warning("⚠️ Please select at least one table")
        else:
            # Check cache first if enabled
            if use_cache:
                all_cached_rules = []
                uncached_tables = []
                
                for table in selected_tables:
                    cached = get_cached_rules(table)
                    if cached:
                        all_cached_rules.extend(cached['rules'])
                        st.info(f"📦 Loaded {cached['rule_count']} cached rules for `{table}`")
                    else:
                        uncached_tables.append(table)
                
                # If all tables are cached, use cache and skip generation
                if not uncached_tables:
                    st.session_state.generated_rules = all_cached_rules
                    st.success(f"✅ Loaded {len(all_cached_rules)} rules from cache!")
                    st.balloons()
                    st.rerun()
                
                # Update selected_tables to only uncached ones
                tables_to_generate = uncached_tables
                st.info(f"🔄 Generating rules for {len(tables_to_generate)} uncached table(s): {', '.join(tables_to_generate)}")
            else:
                tables_to_generate = selected_tables
                all_cached_rules = []
            
            with st.spinner("🔍 Identifier Agent is analyzing tables... (Dataplex profiling takes ~60s per table)"):
                try:
                    # Set up ADK components
                    session_service = InMemorySessionService()
                    artifact_service = InMemoryArtifactService()
                    
                    # Create session
                    session = asyncio.run(session_service.create_session(
                        app_name="DQIdentifierAgent",
                        user_id="streamlit_user"
                    ))
                    
                    # Get agent
                    identifier_agent = get_identifier_agent()
                    
                    # Create runner
                    runner = Runner(
                        app_name="DQIdentifierAgent",
                        agent=identifier_agent,
                        artifact_service=artifact_service,
                        session_service=session_service,
                    )
                    
                    # Process each table
                    all_rules = []
                    
                    for table_name in tables_to_generate:
                        st.write(f"**Analyzing: {table_name}**")
                        
                        # Check generation mode and build appropriate prompt
                        if generation_mode == "💬 Natural Language (with Sample Data)":
                            # Natural Language Mode with Sample Data
                            prompt = f"""
                            **NATURAL LANGUAGE DQ RULE GENERATION**
                            
                            Dataset: '{dataset_id}'
                            Selected Tables: {', '.join(selected_tables)}
                            Current Table: '{table_name}'
                            
                            **User's Natural Language Request:**
                            {nl_description}
                            
                            **MANDATORY STEPS:**
                            1. Load pre-existing rules using load_preexisting_rules()
                            2. Get all week tables using get_all_week_tables()
                            3. Use get_table_schema_with_samples('{table_name}', sample_rows=10) to see actual data
                            4. Analyze sample data to understand patterns, formats, and potential issues
                            
                            **GENERATE {num_rules} DQ RULES based on:**
                            - The user's natural language description above
                            - Patterns observed in the 10 sample rows
                            - BaNCS insurance domain knowledge
                            - Pre-existing rules to avoid duplicates
                            - Cross-week temporal consistency requirements
                            
                            **Focus DQ Dimensions:** {', '.join(focus_dimensions)}
                            
                            **Output Format:**
                            Return a JSON array where each rule has:
                            {{
                              "rule_id": "DQ_NL_XXX",
                              "name": "descriptive_snake_case_name",
                              "description": "Clear business-friendly description of what is checked",
                              "natural_language": "User-friendly explanation based on the original request",
                              "sql": "Complete SQL query with full table paths",
                              "severity": "critical/high/medium/low",
                              "dq_dimension": "{'/'.join(focus_dimensions)}",
                              "scope": "single_table or cross_week",
                              "source": "natural_language"
                            }}
                            
                            Make sure natural_language field explains the rule in plain English.
                            """
                        else:
                            # Automated Mode
                            prompt = f"""
                            **COMPREHENSIVE DQ ANALYSIS REQUEST**
                            
                            Dataset: '{dataset_id}'
                            Selected Tables: {', '.join(selected_tables)}
                            Current Table: '{table_name}'
                            
                            **MANDATORY STEPS:**
                            1. Load pre-existing rules from Collibra/Ataccama using load_preexisting_rules()
                            2. Get all week tables using get_all_week_tables()
                            3. Run data profiling scan for '{table_name}' to get null rates and value patterns
                            4. Get schema for '{table_name}' if needed
                            
                            **GENERATE {num_rules} DQ RULES with these requirements:**
                            
                            A) Dataplex-Based Rules (from profiling findings):
                               - Rules for high null rate columns
                               - Rules for value range anomalies
                               - Rules based on recommended checks
                            
                            B) Cross-Week Temporal Rules (MINIMUM 3):
                               - Status consistency across weeks (e.g., deceased → alive)
                               - Date logic across weeks (death dates, DOB changes)
                               - Premium/value fluctuations across weeks
                               - Customer attribute changes that shouldn't occur
                            
                            C) BaNCS Business Logic Rules:
                               - Future date checks (DOB, death dates)
                               - Negative value checks (premiums, payments)
                               - Format validation (NI numbers, postcodes)
                               - Deceased customers must have death dates
                            
                            D) Pre-existing Rule Enhancements:
                               - Review pre-existing rules
                               - Avoid duplicates
                               - Enhance or extend existing rules
                            
                            **Focus DQ Dimensions:** {', '.join(focus_dimensions)}
                            
                            **Output Format:**
                            Return a JSON array where each rule has:
                            {{
                              "rule_id": "DQ_XXX or DQ_TEMPORAL_XXX",
                              "name": "descriptive_snake_case_name",
                              "description": "Clear description of what is checked",
                              "natural_language": "User-friendly explanation of the rule",
                              "sql": "Complete SQL query with full table paths",
                              "severity": "critical/high/medium/low",
                              "dq_dimension": "{'/'.join(focus_dimensions)}",
                              "scope": "single_table or cross_week",
                              "source": "dataplex/agent/preexisting"
                            }}
                            
                            Prioritize CROSS-WEEK rules as they detect temporal data quality issues.
                            """
                        
                        # Run agent
                        content = types.Content(role="user", parts=[types.Part(text=prompt)])
                        events = list(runner.run(
                            user_id="streamlit_user",
                            session_id=session.id,
                            new_message=content
                        ))
                        
                        # Extract response
                        last_event = events[-1]
                        response = "".join([part.text for part in last_event.content.parts if part.text])
                        
                        # Parse JSON from response
                        import json
                        import re
                        
                        # Try to extract JSON array from response (handle markdown code blocks)
                        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
                        if json_match:
                            json_str = json_match.group(1)
                        else:
                            # Try to find JSON array directly
                            json_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', response)
                            json_str = json_match.group(0) if json_match else response
                        
                        try:
                            rules = json.loads(json_str)
                            if isinstance(rules, list):
                                for rule in rules:
                                    rule['table'] = table_name
                                all_rules.extend(rules)
                            else:
                                st.warning(f"⚠️ Could not parse rules for {table_name} - not a list")
                                all_rules.append({
                                    "table": table_name,
                                    "raw_response": response
                                })
                        except json.JSONDecodeError:
                            st.warning(f"⚠️ Could not parse JSON for {table_name} - storing raw response")
                            all_rules.append({
                                "table": table_name,
                                "raw_response": response
                            })
                    
                    # Store in session state and cache
                    if 'generated_rules' not in st.session_state:
                        st.session_state.generated_rules = []
                    
                    # Merge with cached rules if any
                    all_rules.extend(all_cached_rules)
                    st.session_state.generated_rules = all_rules
                    
                    # Cache the newly generated rules per table
                    rules_by_table = {}
                    for rule in all_rules:
                        if rule not in all_cached_rules:  # Only cache newly generated
                            table = rule.get('table', 'unknown')
                            if table not in rules_by_table:
                                rules_by_table[table] = []
                            rules_by_table[table].append(rule)
                    
                    for table, rules in rules_by_table.items():
                        if cache_rules_for_table(table, rules):
                            st.info(f"💾 Cached {len(rules)} rules for `{table}`")
                    
                    st.success(f"✅ Generated {len(all_rules)} total rules ({len(all_cached_rules)} from cache, {len(all_rules) - len(all_cached_rules)} newly generated)")
                    
                    # Show Dataplex Console link
                    dataplex_url = f"https://console.cloud.google.com/dataplex/dataScans?project={_project_id}"
                    st.info(f"☁️ View Dataplex scans in GCP Console: [Open Dataplex]({dataplex_url})")
                    
                    st.balloons()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Display Generated Rules
    st.divider()
    st.subheader("4. Generated DQ Rules")
    
    # Add Natural Language Rule Appender
    with st.expander("➕ Add Natural Language Rule (No Scan Required)", expanded=False):
        st.markdown("**Describe the DQ rule you want to create in plain English:**")
        
        nl_rule_desc = st.text_area(
            "Natural Language Description",
            placeholder="Example: Check if all UK postcodes follow the pattern AA9A 9AA or A9A 9AA",
            key="nl_rule_desc",
            height=100
        )
        
        # Get available tables for selection
        try:
            from google.cloud import bigquery
            _project_id = st.session_state.get('project_id', '')
            _dataset_id = st.session_state.get('dataset_id', '')
            if _project_id and _dataset_id:
                client = bigquery.Client(project=_project_id)
                dataset_ref = bigquery.DatasetReference(_project_id, _dataset_id)
                available_tables = [table.table_id for table in client.list_tables(dataset_ref)]
            else:
                available_tables = []
        except:
            available_tables = []
        
        nl_table = st.selectbox(
            "Target Table",
            options=[""] + [f"{st.session_state.get('dataset_id', 'dataset')}.{table}" for table in available_tables],
            key="nl_rule_table"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            nl_severity = st.selectbox("Severity", ["critical", "high", "medium", "low"], index=1, key="nl_severity")
        with col2:
            nl_dimension = st.selectbox("DQ Dimension", ["Completeness", "Accuracy", "Timeliness", "Conformity", "Uniqueness"], key="nl_dimension")
        
        if st.button("🤖 Generate Rule from Description", type="secondary"):
            if not nl_rule_desc or not nl_table:
                st.warning("Please provide both a description and select a table")
            else:
                with st.spinner("🔍 Generating rule..."):
                    try:
                        # Use already imported ADK components
                        session_service = InMemorySessionService()
                        artifact_service = InMemoryArtifactService()
                        session = asyncio.run(session_service.create_session(app_name="DQIdentifierAgent", user_id="streamlit_user"))
                        
                        identifier_agent = get_identifier_agent()
                        runner = Runner(app_name="DQIdentifierAgent", agent=identifier_agent, artifact_service=artifact_service, session_service=session_service)
                        
                        table_name = nl_table.split('.')[-1]
                        
                        prompt = f"""
                        **NATURAL LANGUAGE RULE GENERATION (Standalone)**
                        
                        Table: '{nl_table}'
                        User Request: {nl_rule_desc}
                        Severity: {nl_severity}
                        DQ Dimension: {nl_dimension}
                        
                        **STEPS:**
                        1. Use get_table_schema_with_samples('{table_name}', sample_rows=10)
                        2. Analyze sample data to understand column formats
                        3. Generate ONE SQL-based DQ rule that implements the user's request
                        
                        **Output Format:**
                        Return a JSON array with ONE rule:
                        [{{
                          "rule_id": "DQ_NL_CUSTOM_XXX",
                          "name": "descriptive_name",
                          "description": "Technical description",
                          "natural_language": "{nl_rule_desc}",
                          "sql": "Complete SQL query with full table path",
                          "severity": "{nl_severity}",
                          "dq_dimension": "{nl_dimension}",
                          "scope": "single_table",
                          "source": "natural_language"
                        }}]
                        """
                        
                        content = types.Content(role="user", parts=[types.Part(text=prompt)])
                        events = list(runner.run(user_id="streamlit_user", session_id=session.id, new_message=content))
                        last_event = events[-1]
                        response = "".join([part.text for part in last_event.content.parts if part.text])
                        
                        import json
                        import re
                        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
                        json_str = json_match.group(1) if json_match else re.search(r'\[\s*\{[\s\S]*\}\s*\]', response).group(0)
                        
                        new_rule = json.loads(json_str)[0]
                        new_rule['table'] = table_name
                        
                        if 'generated_rules' not in st.session_state:
                            st.session_state.generated_rules = []
                        st.session_state.generated_rules.append(new_rule)
                        
                        st.success("✅ Rule added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
    
    if 'generated_rules' in st.session_state and st.session_state.generated_rules:
        rules = st.session_state.generated_rules
        
        # Add download button
        import json
        rules_json = json.dumps(rules, indent=2)
        st.download_button(
            label="💾 Download All Rules (JSON)",
            data=rules_json,
            file_name="dq_rules_generated.json",
            mime="application/json",
            key="download_rules"
        )
        
        # Legend for color coding
        st.markdown("""
        **Color Legend:**
        - 🟢 **Green**: Pre-existing DQ Rules (from Collibra/Ataccama)
        - 🔵 **Blue**: Dataplex-generated Rules
        - 🟡 **Yellow**: Gemini AI-generated Rules
        - 🟠 **Orange**: Natural Language Custom Rules
        """)
        
        st.write(f"**Total Rules Generated: {len(rules)}**")
        
        # Display rules with delete functionality and color coding
        rules_to_delete = []
        
        for idx, rule in enumerate(rules):
            # Handle raw responses (failed JSON parsing)
            if 'raw_response' in rule:
                with st.expander(f"⚠️ Raw Response for {rule.get('table', 'Unknown')}", expanded=False):
                    st.markdown(rule['raw_response'])
                    col1, col2 = st.columns([6, 1])
                    with col2:
                        if st.button("🗑️", key=f"delete_raw_{idx}", help="Delete this entry"):
                            rules_to_delete.append(idx)
                continue
            
            # Get natural language description (fallback to description if not present)
            nl_desc = rule.get('natural_language', rule.get('description', 'No description'))
            rule_id = rule.get('rule_id', f'RULE_{idx}')
            table = rule.get('table', 'Unknown')
            source = rule.get('source', 'agent').lower()
            
            # Determine color based on source
            if source == 'preexisting' or source == 'collibra' or source == 'ataccama':
                color = "#90EE90"  # Light green
                emoji = "🟢"
            elif source == 'dataplex':
                color = "#ADD8E6"  # Light blue
                emoji = "🔵"
            elif source == 'natural_language':
                color = "#FFB347"  # Light orange
                emoji = "🟠"
            else:  # agent or gemini
                color = "#FFFFE0"  # Light yellow
                emoji = "🟡"
            
            # Create expander with colored background
            with st.expander(f"{emoji} **{rule_id}** - {nl_desc}", expanded=False):
                # Add colored container
                st.markdown(f"""
                <div style="background-color: {color}; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>Source: {rule.get('source', 'N/A')}</strong>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([6, 1])
                
                with col1:
                    st.markdown(f"**Table:** `{table}`")
                    st.markdown(f"**Rule Name:** `{rule.get('name', 'N/A')}`")
                    st.markdown(f"**Severity:** `{rule.get('severity', 'N/A')}`")
                    st.markdown(f"**DQ Dimension:** `{rule.get('dq_dimension', 'N/A')}`")
                    st.markdown(f"**Scope:** `{rule.get('scope', 'N/A')}`")
                    
                    # Show full description if different from natural_language
                    if rule.get('description') and rule.get('description') != nl_desc:
                        st.markdown(f"**Technical Description:** {rule['description']}")
                    
                    # SQL code block
                    if rule.get('sql'):
                        st.markdown("**SQL Query:**")
                        st.code(rule['sql'], language='sql')
                    
                with col2:
                    if st.button("🗑️", key=f"delete_{idx}", help="Delete this rule"):
                        rules_to_delete.append(idx)
        
        # Process deletions
        if rules_to_delete:
            # Remove rules (reverse order to maintain indices)
            for idx in sorted(rules_to_delete, reverse=True):
                st.session_state.generated_rules.pop(idx)
            st.rerun()
        
        # Add "Go to Treatment" button at the bottom
        st.divider()
        st.markdown("### 🎯 Next Step: Run These Rules")
        st.markdown("Ready to execute these DQ rules and analyze violations? Go to the **Treatment Agent** tab.")
        
        col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])
        with col_btn1:
            if st.button("▶️ Go to Treatment Agent", type="primary", key="goto_treatment", use_container_width=True):
                st.session_state.active_tab = "💊 Treatment"
                st.rerun()
        with col_btn2:
            st.metric("Total Rules", len(rules))
        with col_btn3:
            tables_count = len(set(r.get('table', 'unknown') for r in rules if 'raw_response' not in r))
            st.metric("Tables Covered", tables_count)
        
    else:
        st.info("No rules generated yet. Click '🚀 Generate DQ Rules' to start or use the '➕ Add Natural Language Rule' section above.")
    
    # Info box
    st.info("""
    **How it works:**
    1. Agent analyzes table schemas and metadata
    2. Identifies potential DQ issues based on BaNCS patterns
    3. Generates parameterized SQL rules for detection
    4. Categorizes by DQ dimension and severity
    """)

    
elif active_tab == "💊 Treatment":
    st.markdown("**Workflow:** Run DQ rules → Filter offending rows → Group issues → Suggest remediation strategies")
    
    # STEP 1: Run DQ Rules and Filter Offending Rows
    # Check if we have generated rules from Identifier Agent
    if 'generated_rules' not in st.session_state or not st.session_state.generated_rules:
        st.warning("⚠️ No DQ rules available. Please run the Identifier Agent first (Tab 1).")
    else:
        with st.container():
            st.subheader("Step 1: Run DQ Rules & Filter Issues")
            
            # Allow multi-select of rules to run
            available_rules = [
                rule for rule in st.session_state.generated_rules
                if isinstance(rule, dict) and 'rule_id' in rule
            ]
            
            if not available_rules:
                st.error("No valid rules found. Please regenerate rules in Identifier Agent.")
            else:
                # Select All / Deselect All buttons
                col_select_all, col_deselect_all, col_spacer = st.columns([1, 1, 4])
                with col_select_all:
                    if st.button("☑️ Select All", key="select_all_rules", use_container_width=True):
                        for idx in range(min(10, len(available_rules))):
                            st.session_state[f"select_rule_{idx}"] = True
                        st.rerun()
                with col_deselect_all:
                    if st.button("⬜ Deselect All", key="deselect_all_rules", use_container_width=True):
                        for idx in range(min(10, len(available_rules))):
                            st.session_state[f"select_rule_{idx}"] = False
                        st.rerun()
                
                # Display rules to select
                st.caption("Select DQ rules to run:")
                
                # Initialize session state for checkboxes if not exists
                for idx in range(min(10, len(available_rules))):
                    if f"select_rule_{idx}" not in st.session_state:
                        st.session_state[f"select_rule_{idx}"] = (idx == 0)  # Default first one selected
                
                selected_rule_ids = []
                for idx, rule in enumerate(available_rules[:10]):  # Show first 10
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                    with col1:
                        # Checkbox uses session state key directly, no value parameter
                        selected = st.checkbox(
                            "Select",
                            key=f"select_rule_{idx}",
                            label_visibility="collapsed"
                        )
                        if selected:
                            selected_rule_ids.append(idx)
                    with col2:
                        st.write(f"**{rule.get('name', 'Unknown')}**")
                    with col3:
                        st.caption(f"{rule.get('severity', 'N/A')} | {rule.get('table', 'N/A')}")
                    with col4:
                        st.caption(rule.get('dq_dimension', 'N/A'))
                
                st.divider()
                
                # Show SQL preview for selected rules
                if selected_rule_ids:
                    with st.expander(f"👁️ Preview SQL Queries ({len(selected_rule_ids)} selected)", expanded=False):
                        project_id_preview = st.session_state.get('project_id', 'PROJECT')
                        dataset_id_preview = st.session_state.get('dataset_id', 'DATASET')
                        
                        for idx in selected_rule_ids:
                            rule = available_rules[idx]
                            table_name = rule.get('table', 'table')
                            rule_sql = rule.get('sql', 'No SQL')
                            
                            # Use the same logic as execution
                            sql_preview = rule_sql.strip().replace('`', '')
                            
                            # Use regex to replace ALL table references in PROJECT.DATASET pattern
                            import re
                            
                            # Pattern to match PROJECT.DATASET.any_table_name (case insensitive)
                            def replace_table_ref(match):
                                matched_table = match.group(1)
                                return f"`{project_id_preview}.{dataset_id_preview}.{matched_table}`"
                            
                            # Replace PROJECT.DATASET.table_name patterns
                            sql_preview = re.sub(r'PROJECT\.DATASET\.([a-zA-Z_][a-zA-Z0-9_]*)', replace_table_ref, sql_preview, flags=re.IGNORECASE)
                            
                            # Also handle TABLE_NAME placeholder if it wasn't caught
                            full_table_ref = f"{project_id_preview}.{dataset_id_preview}.{table_name}"
                            sql_preview = sql_preview.replace('TABLE_NAME', table_name)
                            
                            # Ensure the main table is also backticked if not already
                            if full_table_ref in sql_preview and f"`{full_table_ref}`" not in sql_preview:
                                sql_preview = sql_preview.replace(full_table_ref, f"`{full_table_ref}`")
                            
                            st.markdown(f"**{rule.get('name', 'Unknown')}**")
                            st.code(sql_preview, language='sql')
                
                # Run selected rules button
                col_run, col_clear = st.columns([3, 1])
                with col_run:
                    run_rules_btn = st.button(
                        "🔍 Run Selected Rules & Filter Issues",
                        type="primary",
                        disabled=len(selected_rule_ids) == 0,
                        key="run_rules_btn",
                        use_container_width=True
                    )
                with col_clear:
                    if st.button("🗑️ Clear Results", key="clear_results_btn", use_container_width=True):
                        if 'filtered_issues' in st.session_state:
                            del st.session_state['filtered_issues']
                        if 'grouped_issues' in st.session_state:
                            del st.session_state['grouped_issues']
                        if 'failed_rules' in st.session_state:
                            del st.session_state['failed_rules']
                        st.rerun()
                
                # Execute selected rules
                if run_rules_btn:
                    with st.status("🔍 Executing DQ rules and filtering offending rows...", expanded=True) as status:
                        try:
                            from google.cloud import bigquery
                            from google.cloud.exceptions import GoogleCloudError
                            
                            # Get project_id and dataset_id from session state
                            project_id = st.session_state.get('project_id', '')
                            dataset_id = st.session_state.get('dataset_id', '')
                            
                            if not project_id or not dataset_id:
                                status.update(label="❌ Configuration Error", state="error")
                                st.error("❌ Please configure Project ID and Dataset ID in the sidebar settings.")
                                st.stop()
                            
                            # Initialize BigQuery client with timeout
                            client = bigquery.Client(project=project_id)
                            
                            filtered_issues = []
                            failed_rules = []
                            
                            progress_bar = st.progress(0)
                            
                            for rule_idx, idx in enumerate(selected_rule_ids):
                                rule = available_rules[idx]
                                rule_name = rule.get('name', 'Unknown')
                                # Get table name from rule or use first available table
                                default_table = st.session_state.get('available_tables', ['policies_week1'])[0]
                                table_name = rule.get('table', default_table)
                                rule_sql = rule.get('sql', '')
                                
                                # Update progress
                                progress = (rule_idx + 1) / len(selected_rule_ids)
                                progress_bar.progress(progress)
                                st.write(f"Running rule {rule_idx + 1}/{len(selected_rule_ids)}: {rule_name}")
                                
                                if not rule_sql or rule_sql.strip() == '':
                                    failed_rules.append({
                                        "rule_name": rule_name,
                                        "error": "Empty SQL query",
                                        "sql": "No SQL provided"
                                    })
                                    continue
                                
                                # Clean and prepare SQL
                                sql = rule_sql.strip()
                                
                                # Build the full table reference
                                full_table_ref = f"{project_id}.{dataset_id}.{table_name}"
                                
                                # Remove any existing backticks from the SQL first to avoid double-backticking
                                sql = sql.replace('`', '')
                                
                                # Use regex to replace ALL table references in PROJECT.DATASET pattern
                                import re
                                
                                # Pattern to match PROJECT.DATASET.any_table_name (case insensitive)
                                def replace_table_ref_exec(match):
                                    matched_table = match.group(1)
                                    return f"`{project_id}.{dataset_id}.{matched_table}`"
                                
                                # Replace PROJECT.DATASET.table_name patterns (handles cross-table queries)
                                sql = re.sub(r'PROJECT\.DATASET\.([a-zA-Z_][a-zA-Z0-9_]*)', replace_table_ref_exec, sql, flags=re.IGNORECASE)
                                
                                # Handle {TABLE_NAME} placeholder (common template format)
                                if '{TABLE_NAME}' in sql:
                                    sql = sql.replace('{TABLE_NAME}', f"`{full_table_ref}`")
                                
                                # Also handle simple TABLE_NAME placeholder if it wasn't caught
                                if 'TABLE_NAME' in sql:
                                    sql = sql.replace('TABLE_NAME', f"`{full_table_ref}`")
                                
                                # Ensure the main table is also backticked if not already
                                if full_table_ref in sql and f"`{full_table_ref}`" not in sql:
                                    sql = sql.replace(full_table_ref, f"`{full_table_ref}`")
                                
                                # Validate SQL has basic structure
                                if 'SELECT' not in sql.upper():
                                    failed_rules.append({
                                        "rule_name": rule_name,
                                        "error": "Invalid SQL (no SELECT statement)",
                                        "sql": sql[:500]
                                    })
                                    continue
                                
                                # Execute with timeout and error handling
                                try:
                                    # Add LIMIT if not present to prevent huge result sets
                                    sql_upper = sql.upper()
                                    if 'LIMIT' not in sql_upper:
                                        # Wrap in subquery to safely add LIMIT
                                        sql = f"SELECT * FROM ({sql}) AS limited_results LIMIT 1000"
                                    
                                    job_config = bigquery.QueryJobConfig(
                                        maximum_bytes_billed=10**9  # 1GB limit
                                    )
                                    
                                    query_job = client.query(sql, job_config=job_config)
                                    results = query_job.result(timeout=30)  # 30 second timeout
                                    
                                    violations = [dict(row) for row in results]
                                    
                                    if violations:
                                        filtered_issues.append({
                                            "rule": rule,
                                            "violations": violations[:100],  # Limit to 100 for display
                                            "total_count": len(violations),
                                            "table": table_name
                                        })
                                        
                                except GoogleCloudError as e:
                                    error_msg = str(e)
                                    # Extract the actual error message
                                    if 'Error' in error_msg:
                                        error_msg = error_msg.split('Error')[-1].strip()[:200]
                                    failed_rules.append({
                                        "rule_name": rule_name,
                                        "error": error_msg,
                                        "sql": sql[:500]  # First 500 chars of SQL
                                    })
                                except Exception as e:
                                    failed_rules.append({
                                        "rule_name": rule_name,
                                        "error": str(e)[:200],
                                        "sql": sql[:500]
                                    })
                            
                            # Clear progress indicators
                            progress_bar.empty()
                            
                            # Store results in session state (including failed rules)
                            st.session_state.filtered_issues = filtered_issues
                            st.session_state.failed_rules = failed_rules
                            
                            # Show results
                            if filtered_issues:
                                total_violations = sum(f['total_count'] for f in filtered_issues)
                                status.update(label=f"✅ Found {total_violations} violations across {len(filtered_issues)} rules", state="complete", expanded=False)
                                st.success(f"✅ Found {total_violations} violations across {len(filtered_issues)} rules")
                            elif failed_rules:
                                status.update(label=f"⚠️ All {len(failed_rules)} rules failed - see details below", state="error", expanded=False)
                            else:
                                status.update(label="ℹ️ No violations found in selected rules", state="complete", expanded=False)
                                st.info("ℹ️ No violations found. All selected rules passed!")
                            
                            # Show failed rules if any (persistent, not inside status)
                            if failed_rules:
                                st.warning(f"⚠️ {len(failed_rules)} rules failed to execute")
                                with st.expander(f"⚠️ {len(failed_rules)} rules failed - Click to see details", expanded=True):
                                    for failure in failed_rules:
                                        if isinstance(failure, dict):
                                            st.error(f"**Rule:** {failure['rule_name']}")
                                            st.error(f"**Error:** {failure['error']}")
                                            st.code(failure['sql'], language='sql')
                                            st.divider()
                                        else:
                                            st.warning(failure)
                            
                            # Only rerun if we have results to show
                            if filtered_issues:
                                st.rerun()
                            
                        except Exception as e:
                            status.update(label="❌ Critical error", state="error")
                            st.error(f"❌ Critical error: {str(e)}")
                            import traceback
                            with st.expander("Show detailed error"):
                                st.code(traceback.format_exc())
    
    # Display failed rules from session state (persistent after rerun)
    if 'failed_rules' in st.session_state and st.session_state.failed_rules:
        st.divider()
        st.warning(f"⚠️ {len(st.session_state.failed_rules)} rules failed during last execution")
        with st.expander("View Failed Rules Details", expanded=False):
            for failure in st.session_state.failed_rules:
                if isinstance(failure, dict):
                    st.error(f"**Rule:** {failure['rule_name']}")
                    st.error(f"**Error:** {failure['error']}")
                    st.code(failure['sql'], language='sql')
                    st.divider()
    
    # STEP 2: Display Filtered Issues (un-indented to tab level)
    if 'filtered_issues' in st.session_state and st.session_state.filtered_issues:
        st.divider()
        with st.container():
            st.subheader("Step 2: Filtered Issues")
            
            for issue_idx, issue_data in enumerate(st.session_state.filtered_issues):
                rule = issue_data['rule']
                violations = issue_data['violations']
                total_count = issue_data['total_count']
                
                with st.expander(
                    f"📌 {rule.get('name', 'Unknown')} - {total_count} violations found",
                    expanded=(issue_idx == 0)
                ):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Severity", rule.get('severity', 'N/A'))
                    with col2:
                        st.metric("Violations", total_count)
                    with col3:
                        st.metric("Table", issue_data['table'])
                    
                    st.markdown("**Issue Description:**")
                    st.write(rule.get('description', 'No description'))
                    
                    # Show sample violations
                    if violations:
                        st.markdown(f"**Sample Violations (showing {min(5, len(violations))} of {total_count}):**")
                        sample_df = pd.DataFrame(violations[:5])
                        st.dataframe(sample_df, width='stretch')
                        
                        # Link to BigQuery - use session state values
                        project_id = st.session_state.get('project_id', '')
                        dataset_id = st.session_state.get('dataset_id', '')
                        if project_id and dataset_id:
                            bq_url = f"https://console.cloud.google.com/bigquery?project={project_id}&ws=!1m5!1m4!4m3!1s{project_id}!2s{dataset_id}!3s{issue_data['table']}"
                            st.markdown(f"[🔗 View Full Table in BigQuery]({bq_url})")
        
        st.divider()
        
        # STEP 3: Group Issues Button
        st.subheader("Step 3: Group Issues & Analyze Root Cause")
        
        if st.button("🔬 Group Issues & Generate Remediation Strategies", type="primary", key="group_issues_btn"):
            with st.spinner("🤖 Treatment Agent is analyzing and grouping issues..."):
                try:
                    # Import required components
                    from dq_agents.treatment.agent import treatment_agent
                    from google.genai import types
                    from google.adk.sessions import InMemorySessionService
                    from google.adk.artifacts import InMemoryArtifactService
                    from google.adk.runners import Runner
                    
                    # Debug: Check agent
                    st.info(f"✓ Treatment Agent loaded: {treatment_agent.name}")
                    
                    # Set up ADK components
                    session_service = InMemorySessionService()
                    artifact_service = InMemoryArtifactService()
                    
                    # Create session
                    session = asyncio.run(session_service.create_session(
                        app_name="DQTreatmentAgent",
                        user_id="streamlit_user"
                    ))
                    
                    st.info(f"✓ Session created: {session.id}")
                    
                    # Create runner
                    runner = Runner(
                        app_name="DQTreatmentAgent",
                        agent=treatment_agent,
                        artifact_service=artifact_service,
                        session_service=session_service,
                    )
                    
                    st.info("✓ Runner initialized")
                    
                    # Prepare issue summary for agent
                    issues_summary = []
                    for issue_data in st.session_state.filtered_issues:
                        rule = issue_data['rule']
                        violations = issue_data['violations'][:10]  # Sample 10 rows
                        
                        issues_summary.append({
                            "rule_id": rule.get('rule_id'),
                            "rule_name": rule.get('name'),
                            "description": rule.get('description'),
                            "severity": rule.get('severity'),
                            "dq_dimension": rule.get('dq_dimension'),
                            "table": issue_data['table'],
                            "total_violations": issue_data['total_count'],
                            "sample_violations": violations
                        })
                    
                    # Build prompt for Treatment Agent
                    prompt = f"""
**TREATMENT AGENT WORKFLOW: Group Issues & Suggest Remediation**

You have {len(issues_summary)} DQ issues to analyze. Your tasks:

1. **Group Similar Issues**: Cluster issues by:
   - Common root cause (e.g., same source system, time pattern)
   - DQ dimension (Completeness, Accuracy, etc.)
   - Severity level
   
2. **Root Cause Analysis**: For each group, analyze sample violations to identify:
   - Common metadata attributes (creation date, user, system)
   - Patterns in bad data (all from legacy system? specific time range?)
   - Likely source of the problem
   
3. **Generate Top 3 Remediation Strategies** for EACH group:
   - Rank by success probability
   - Include: fix_type, action, description, SQL, success_probability, risk_level
   - Search Knowledge Bank for similar historical fixes
   - Consider: data repair, statistical imputation, deletion, escalation
   
4. **Sampled Row Analysis**: Use the sample_violations provided to understand data patterns

**ISSUES TO ANALYZE:**
{json.dumps(issues_summary, indent=2, default=str)}

**OUTPUT FORMAT:**
Return JSON with:
{{
  "issue_groups": [
    {{
      "group_id": "GROUP_001",
      "group_name": "Future Date of Birth Issues",
      "issues_in_group": [
        {{
          "rule_id": "DQ_001",
          "rule_name": "future_dob_check",
          "table": "{{TABLE_NAME}}",
          "violations": 50
        }}
      ],
      "total_violations": 120,
      "root_cause_analysis": {{
        "pattern": "All from System_Legacy_A",
        "likely_cause": "Date format conversion error",
        "metadata_common": "Created 12:00-1:00 AM"
      }},
      "fix_suggestions": [
        {{
          "rank": 1,
          "fix_type": "Data Repair",
          "action": "Set to NULL and flag",
          "description": "...",
          "success_probability": 0.95,
          "risk_level": "low",
          "auto_approve_eligible": false,
          "sql": "UPDATE {{{{table}}}} SET date_of_birth = NULL WHERE ..."
        }}
      ]
    }}
  ]
}}

**IMPORTANT:** In issues_in_group, include the full issue object with rule_id, rule_name, table, and violations count for each issue."""
                    
                    st.info("✓ Sending prompt to agent...")
                    
                    # Run agent with proper ADK API
                    content = types.Content(role="user", parts=[types.Part(text=prompt)])
                    
                    try:
                        events = list(runner.run(
                            user_id="streamlit_user",
                            session_id=session.id,
                            new_message=content
                        ))
                    except Exception as run_error:
                        st.error(f"❌ Error during runner.run(): {str(run_error)}")
                        import traceback
                        st.code(traceback.format_exc())
                        st.stop()
                    
                    st.info(f"✓ Got {len(events)} events")
                    
                    # Check if we got events
                    if not events:
                        st.error("❌ No response from Treatment Agent. Please check agent configuration.")
                        st.stop()
                    
                    # Extract response from last event
                    last_event = events[-1]
                    if not hasattr(last_event, 'content') or not last_event.content:
                        st.error(f"❌ Last event has no content. Event type: {type(last_event)}")
                        st.stop()
                    
                    if not last_event.content.parts:
                        st.error("❌ Last event content has no parts.")
                        st.stop()
                    
                    response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                    
                    if not response_text:
                        st.error("❌ Treatment Agent returned no text content.")
                        st.stop()
                    
                    st.info(f"✓ Response length: {len(response_text)} characters")
                    
                    # Store grouped issues
                    st.session_state.grouped_issues = response_text
                    st.success("✅ Issues grouped and remediation strategies generated!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # STEP 4: Display Grouped Issues and Remediation Strategies
        if 'grouped_issues' in st.session_state:
            st.divider()
            st.subheader("Step 4: Grouped Issues & Remediation Strategies")
            
            # Parse response
            response_text = st.session_state.grouped_issues
            
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                json_str = json_match.group(0) if json_match else response_text
            
            try:
                grouped_result = json.loads(json_str)
                
                issue_groups = grouped_result.get('issue_groups', [])
                
                if issue_groups:
                    for group_idx, group in enumerate(issue_groups):
                        with st.expander(
                            f"📦 {group.get('group_name', 'Unknown Group')} - {group.get('total_violations', 0)} violations",
                            expanded=(group_idx == 0)
                        ):
                            # Group info
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Issues in Group", len(group.get('issues_in_group', [])))
                            with col2:
                                st.metric("Total Violations", group.get('total_violations', 0))
                            
                            # Root cause analysis
                            st.markdown("### 🔍 Root Cause Analysis")
                            rca = group.get('root_cause_analysis', {})
                            if isinstance(rca, dict):
                                for key, value in rca.items():
                                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                            
                            # Fix suggestions
                            st.markdown("### 💡 Remediation Strategies")
                            fix_suggestions = group.get('fix_suggestions', [])
                            
                            for fix in fix_suggestions:
                                rank = fix.get('rank', 0)
                                
                                with st.container():
                                    st.markdown(f"**Fix {rank}: {fix.get('fix_type')} - {fix.get('action')}**")
                                    
                                    col_metric1, col_metric2, col_metric3 = st.columns(3)
                                    with col_metric1:
                                        st.metric("Success Rate", f"{fix.get('success_probability', 0)*100:.0f}%")
                                    with col_metric2:
                                        st.metric("Risk", fix.get('risk_level', 'unknown').upper())
                                    with col_metric3:
                                        auto = "✅ Yes" if fix.get('auto_approve_eligible', False) else "❌ No"
                                        st.metric("Auto-Approve", auto)
                                    
                                    st.write(fix.get('description', 'No description'))
                                    
                                    if 'sql' in fix:
                                        st.code(fix.get('sql'), language="sql")
                                    
                                    # Action buttons (INSIDE the loop for each fix)
                                    col_btn1, col_btn2 = st.columns(2)
                                    with col_btn1:
                                        if st.button(f"✅ Approve Fix {rank} for Group {group_idx+1}", key=f"approve_g{group_idx}_f{rank}"):
                                            # Extract table name from group's issues
                                            issues_in_group = group.get('issues_in_group', [])
                                            table_name = 'unknown'
                                            if issues_in_group:
                                                first_issue = issues_in_group[0]
                                                if isinstance(first_issue, dict):
                                                    table_name = first_issue.get('table', 'unknown')
                                            
                                            # Store for Remediator with complete context
                                            st.session_state.approved_fix = {
                                                "fix": fix,
                                                "issue": {
                                                    "group_name": group.get('group_name', 'Unknown Group'),
                                                    "total_violations": group.get('total_violations', 0),
                                                    "issues_in_group": issues_in_group,
                                                    "root_cause": group.get('root_cause_analysis', {}),
                                                    "rule": issues_in_group[0] if issues_in_group else {}
                                                },
                                                "table_name": table_name,
                                                "timestamp": __import__('datetime').datetime.now().isoformat()
                                            }
                                            st.success(f"✅ Fix {rank} approved for {table_name}!")
                                            st.info("👉 Go to **Remediator** tab to execute the fix")
                                            st.session_state.active_tab = "🔧 Remediator"
                                            st.rerun()
                                    with col_btn2:
                                        if st.button(f"❌ Reject Fix {rank}", key=f"reject_g{group_idx}_f{rank}"):
                                            st.warning("Fix rejected. Feedback logged to Knowledge Bank.")
                                    
                                    st.divider()
                else:
                    st.warning("No issue groups generated")
                
                # Add navigation button to Remediator
                st.divider()
                st.markdown("### 🎯 Next Step: Execute Approved Fixes")
                st.markdown("Once you've approved a fix above, go to the **Remediator** tab to execute it safely.")
                
                col_btn_nav, col_spacer = st.columns([2, 4])
                with col_btn_nav:
                    if st.button("▶️ Go to Remediator Agent", type="primary", key="goto_remediator", use_container_width=True):
                        st.session_state.active_tab = "🔧 Remediator"
                        st.rerun()
            
            except json.JSONDecodeError:
                st.markdown("### 📄 Analysis Response")
                st.markdown(response_text)

elif active_tab == "🔧 Remediator":
    st.markdown("Execute approved DQ fixes with validation and safety checks")
    
    # Check if there's an approved fix
    if 'approved_fix' not in st.session_state:
        with st.container():
            st.info("ℹ️ No approved fix pending. Please approve a fix in the Treatment tab first.")
            
            # Show recent JIRA tickets
            st.divider()
            st.subheader("📋 Recent JIRA Tickets")
            
            try:
                import sys
                sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
                from jira_mock.ticket_manager import list_tickets
                
                tickets = list_tickets()
                
                if tickets:
                    for ticket in tickets[-5:]:  # Show last 5 tickets
                        with st.expander(f"{ticket['ticket_id']}: {ticket['summary']}", expanded=False):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Priority", ticket['priority'])
                            with col2:
                                st.metric("Status", ticket['status'])
                            with col3:
                                st.metric("Affected Rows", ticket.get('affected_rows', 'N/A'))
                            
                            st.write(f"**Created:** {ticket['created_at']}")
                            st.write(f"**Assignee:** {ticket['assignee']}")
                            st.write(f"**Description:** {ticket['description']}")
                            
                            if ticket.get('attachment') and ticket['attachment'].get('content'):
                                st.code(ticket['attachment']['content'], language="sql")
                else:
                    st.info("No JIRA tickets created yet")
            except Exception as e:
                st.error(f"Error loading JIRA tickets: {str(e)}")
    
    else:
        with st.container():
            # Display approved fix details
            approved = st.session_state.approved_fix
            
            st.success("✅ Fix approved and ready for execution")
            
            # Extract fix details
            fix = approved.get('fix', {})
            issue = approved.get('issue', {})
            table_name = approved.get('table_name', 'unknown')
            
            # Fallback: Try to extract table from issue data if table_name is unknown
            if table_name == 'unknown':
                # Try from issues_in_group
                issues_in_group = issue.get('issues_in_group', [])
                if issues_in_group and isinstance(issues_in_group, list):
                    first_issue = issues_in_group[0]
                    if isinstance(first_issue, dict):
                        table_name = first_issue.get('table', 'unknown')
                
                # Try from rule in issue
                if table_name == 'unknown':
                    rule = issue.get('rule', {})
                    if isinstance(rule, dict):
                        table_name = rule.get('table', 'unknown')
                
                # Try to extract from SQL
                if table_name == 'unknown' and 'sql' in fix:
                    sql = fix.get('sql', '')
                    # Try to extract table name from SQL pattern like: project.dataset.table
                    import re
                    # Look for patterns like `project.dataset.table` or project.dataset.table
                    match = re.search(r'`?([a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.([a-zA-Z0-9_-]+))`?', sql)
                    if match:
                        table_name = match.group(2)  # Extract just the table name
            
            # If still unknown, try to get from session state
            if table_name == 'unknown' and 'filtered_issues' in st.session_state and st.session_state.filtered_issues:
                # Use the first issue's table as fallback
                first_filtered = st.session_state.filtered_issues[0]
                table_name = first_filtered.get('table', 'unknown')
            
            # Display fix summary
            st.subheader("📋 Fix Summary")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fix Type", fix.get('fix_type', 'N/A'))
            with col2:
                st.metric("Risk Level", fix.get('risk_level', 'N/A').upper())
            with col3:
                st.metric("Success Probability", f"{fix.get('success_probability', 0)*100:.0f}%")
            
            st.markdown(f"**Action:** {fix.get('action', 'N/A')}")
            st.markdown(f"**Description:** {fix.get('description', 'N/A')}")
            st.markdown(f"**Table:** `{table_name}`")
            
            if issue:
                st.markdown(f"**Issue Summary:** {issue.get('issue_summary', 'N/A')}")
                st.markdown(f"**Affected Rows:** {issue.get('affected_rows', 'N/A')}")
            
            # Show SQL
            if 'sql' in fix:
                st.markdown("**SQL to Execute:**")
                st.code(fix['sql'], language="sql")
            
            st.divider()
            
            # Execution workflow
            st.subheader("🎯 Execution Workflow")
            
            # Option to skip dry run
            skip_dry_run = st.checkbox(
                "⏭️ Skip dry run and execute directly (not recommended)",
                value=False,
                help="Only skip dry run if you're confident about the fix. Always preview changes when possible."
            )
            
            # Step 1: Dry Run
            st.markdown("### Step 1: Dry Run (Preview Changes)")
            if skip_dry_run:
                st.warning("⚠️ Dry run skipped. Proceeding directly to execution.")
            else:
                st.write("Preview the rows that will be affected without making actual changes.")
            
            col_dry1, col_dry2 = st.columns([2, 1])
            with col_dry1:
                if not skip_dry_run and st.button("🔍 Run Dry Run", type="secondary", key="dry_run_btn"):
                    with st.status("Running dry run...", expanded=True) as status:
                        try:
                            # Import remediator agent
                            from dq_agents.remediator.agent import remediator_agent
                            from google.adk.sessions import InMemorySessionService
                            from google.adk.artifacts import InMemoryArtifactService
                            from google.adk.runners import Runner
                            from google.genai import types
                            
                            # Set up ADK components
                            session_service = InMemorySessionService()
                            artifact_service = InMemoryArtifactService()
                            session = asyncio.run(session_service.create_session(
                                app_name="DQRemediatorAgent",
                                user_id="streamlit_user"
                            ))
                            
                            # Create runner
                            runner = Runner(
                                app_name="DQRemediatorAgent",
                                agent=remediator_agent,
                                artifact_service=artifact_service,
                                session_service=session_service,
                            )
                            
                            # Preprocess SQL to fix dataset/project references
                            original_sql = fix.get('sql', '')
                            
                            # Get correct project and dataset from environment
                            correct_project = project_id or os.getenv('BQ_DATA_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT')
                            correct_dataset = dataset_id or os.getenv('BQ_DATASET_ID')
                            
                            # Replace common hardcoded dataset patterns
                            preprocessed_sql = original_sql
                            # Remove any existing dataset qualifiers and replace with correct ones
                            import re
                            # Pattern: dataset.table or project.dataset.table
                            preprocessed_sql = re.sub(r'\b[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.([a-zA-Z0-9_-]+)\b', 
                                                      f'{correct_project}.{correct_dataset}.\\1', preprocessed_sql)
                            preprocessed_sql = re.sub(r'\b[a-zA-Z0-9_-]+\.([a-zA-Z0-9_-]+)\b(?!\s*\()', 
                                                      f'{correct_dataset}.\\1', preprocessed_sql)
                            
                            # Build prompt for dry run
                            prompt = f"""
**DRY RUN REQUEST**

You must call the dry_run_fix() tool to preview the changes before executing this fix.

**Parameters for dry_run_fix():**
- fix_sql: {preprocessed_sql}
- table_name: {table_name}

**Context:**
- Fix Type: {fix.get('fix_type')}
- Action: {fix.get('action')}
- Project: {correct_project}
- Dataset: {correct_dataset}

Call dry_run_fix() now and return the result.
"""
                            
                            # Run agent
                            content = types.Content(role="user", parts=[types.Part(text=prompt)])
                            events = list(runner.run(
                                user_id="streamlit_user",
                                session_id=session.id,
                                new_message=content
                            ))
                            
                            if not events:
                                status.update(label="❌ No response from Remediator Agent", state="error")
                                st.error("❌ No response from Remediator Agent")
                            else:
                                last_event = events[-1]
                                response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                                
                                # Debug: Show what we received
                                st.info(f"✓ Received response ({len(response_text)} chars)")
                                
                                # Store dry run results
                                st.session_state.dry_run_results = response_text
                                status.update(label="✅ Dry run complete!", state="complete", expanded=False)
                                st.rerun()
                        
                        except Exception as e:
                            status.update(label="❌ Error during dry run", state="error")
                            st.error(f"❌ Error during dry run: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
            
            with col_dry2:
                if st.button("❌ Cancel Fix", key="cancel_fix_btn"):
                    del st.session_state.approved_fix
                    if 'dry_run_results' in st.session_state:
                        del st.session_state.dry_run_results
                    if 'execution_results' in st.session_state:
                        del st.session_state.execution_results
                    st.warning("Fix cancelled")
                    st.rerun()
            
            # Display dry run results or skip to execution
            if skip_dry_run:
                st.info("ℹ️ Dry run skipped. You can proceed directly to execution below.")
                # Set a flag to indicate dry run was skipped
                st.session_state.dry_run_skipped = True
            elif 'dry_run_results' in st.session_state:
                st.markdown("#### 📊 Dry Run Results")
                
                dry_run_text = st.session_state.dry_run_results
                
                # Parse JSON from response
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', dry_run_text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_match = re.search(r'\{[\s\S]*\}', dry_run_text)
                    json_str = json_match.group(0) if json_match else dry_run_text
                
                try:
                    dry_run_result = json.loads(json_str)
                    
                    if dry_run_result.get('status') == 'success':
                        st.info(f"✅ Dry run successful: {dry_run_result.get('affected_row_count', 0)} rows will be affected")
                        
                        # Show sample rows
                        if 'sample_rows' in dry_run_result and dry_run_result['sample_rows']:
                            st.markdown("**Sample Affected Rows:**")
                            import pandas as pd
                            sample_df = pd.DataFrame(dry_run_result['sample_rows'])
                            st.dataframe(sample_df, width='stretch')
                        
                        # Show SQL that was used
                        if 'dry_run_sql' in dry_run_result:
                            with st.expander("View Dry Run SQL"):
                                st.code(dry_run_result['dry_run_sql'], language="sql")
                    else:
                        # Show error with full context
                        error_msg = dry_run_result.get('error', 'Unknown error')
                        st.error(f"❌ Dry run failed: {error_msg}")
                        
                        # Show the full result for debugging
                        with st.expander("🔍 View Full Response"):
                            st.json(dry_run_result)
                        
                        # Show the raw agent response
                        with st.expander("📝 Raw Agent Response"):
                            st.markdown(dry_run_text)
                
                except json.JSONDecodeError as e:
                    st.error(f"❌ Failed to parse dry run response as JSON: {str(e)}")
                    st.markdown("**Raw Response:**")
                    st.markdown(dry_run_text)
                    
                    # Try to show what we got
                    with st.expander("🔍 Debug Info"):
                        st.write(f"JSON string attempted: {json_str[:500]}...")
                        st.write(f"Parse error: {str(e)}")
                
                st.divider()
                
                # Step 2: Execute Fix
                st.markdown("### Step 2: Execute Fix")
                st.write("Apply the fix to the BigQuery table.")
                
                col_exec1, col_exec2 = st.columns(2)
                
                with col_exec1:
                    batch_size = st.number_input(
                        "Batch Size (0 = all rows)",
                        min_value=0,
                        max_value=10000,
                        value=0,
                        help="Limit number of rows to update in one operation"
                    )
                
                with col_exec2:
                    # Auto-enable confirmation if dry run was skipped and user acknowledged
                    can_execute = skip_dry_run or 'dry_run_results' in st.session_state
                    confirm_execute = st.checkbox(
                        "I confirm this fix is safe to execute",
                        value=False,
                        key="confirm_execute",
                        help="Review the fix details and dry run results (if available) before confirming"
                    )
                
                # Allow execution if: user confirmed AND (dry run was skipped OR dry run results exist)
                can_proceed = skip_dry_run or 'dry_run_results' in st.session_state
                execute_disabled = not (confirm_execute and can_proceed)
                
                if st.button("⚡ Execute Fix", type="primary", key="execute_btn", disabled=execute_disabled):
                    with st.status("Executing fix...", expanded=True) as status:
                        try:
                            # Import remediator agent
                            from dq_agents.remediator.agent import remediator_agent
                            from google.adk.sessions import InMemorySessionService
                            from google.adk.artifacts import InMemoryArtifactService
                            from google.adk.runners import Runner
                            from google.genai import types
                            
                            # Set up ADK components
                            session_service = InMemorySessionService()
                            artifact_service = InMemoryArtifactService()
                            session = asyncio.run(session_service.create_session(
                                app_name="DQRemediatorAgent",
                                user_id="streamlit_user"
                            ))
                            
                            # Create runner
                            runner = Runner(
                                app_name="DQRemediatorAgent",
                                agent=remediator_agent,
                                artifact_service=artifact_service,
                                session_service=session_service,
                            )
                            
                            # Preprocess SQL to fix dataset/project references
                            original_sql = fix.get('sql', '')
                            
                            # Get correct project and dataset from environment
                            correct_project = project_id or os.getenv('BQ_DATA_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT')
                            correct_dataset = dataset_id or os.getenv('BQ_DATASET_ID')
                            
                            # Replace hardcoded dataset patterns
                            preprocessed_sql = original_sql
                            import re
                            # Pattern: dataset.table or project.dataset.table
                            preprocessed_sql = re.sub(r'\b[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.([a-zA-Z0-9_-]+)\b', 
                                                      f'{correct_project}.{correct_dataset}.\\1', preprocessed_sql)
                            preprocessed_sql = re.sub(r'\b[a-zA-Z0-9_-]+\.([a-zA-Z0-9_-]+)\b(?!\s*\()', 
                                                      f'{correct_dataset}.\\1', preprocessed_sql)
                            
                            # Build prompt for execution
                            prompt = f"""
                            EXECUTE this DQ fix on the BigQuery table.
                            
                            **Fix Details:**
                            - Fix Type: {fix.get('fix_type')}
                            - Action: {fix.get('action')}
                            - Table: {table_name}
                            - Project: {correct_project}
                            - Dataset: {correct_dataset}
                            - Batch Size: {batch_size}
                            
                            **SQL (preprocessed with correct dataset):**
                            {preprocessed_sql}
                            
                            **Original DQ Rule (for validation):**
                            {issue.get('rule', {}).get('sql', '')}
                            
                            **Instructions:**
                            1. Use execute_fix() tool to apply the fix
                            2. After execution, use validate_fix() to re-run the original DQ rule
                            3. Return execution results and validation status in JSON format
                            
                            If execution fails, consider creating a JIRA ticket using create_jira_ticket().
                            """
                            
                            # Run agent
                            content = types.Content(role="user", parts=[types.Part(text=prompt)])
                            events = list(runner.run(
                                user_id="streamlit_user",
                                session_id=session.id,
                                new_message=content
                            ))
                            
                            if not events:
                                status.update(label="❌ No response from Remediator Agent", state="error")
                                st.error("❌ No response from Remediator Agent")
                            else:
                                last_event = events[-1]
                                response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                                
                                # Store execution results
                                st.session_state.execution_results = response_text
                                status.update(label="✅ Execution complete!", state="complete", expanded=False)
                                st.rerun()
                        
                        except Exception as e:
                            status.update(label="❌ Error during execution", state="error")
                            st.error(f"❌ Error during execution: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
            
            # Display execution results
            if 'execution_results' in st.session_state:
                st.divider()
                st.markdown("### 🎉 Execution Results")
                
                exec_text = st.session_state.execution_results
                
                # Parse JSON from response
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', exec_text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_match = re.search(r'\{[\s\S]*\}', exec_text)
                    json_str = json_match.group(0) if json_match else exec_text
                
                try:
                    exec_result = json.loads(json_str)
                    
                    # Show execution status
                    if exec_result.get('execution_status') == 'success':
                        st.success("✅ Fix executed successfully!")
                        
                        execution = exec_result.get('execution_results', {})
                        st.metric("Rows Affected", execution.get('affected_rows', 'N/A'))
                        
                        # Show validation results
                        if 'validation_results' in exec_result:
                            validation = exec_result['validation_results']
                            
                            if validation.get('status') == 'success':
                                st.success(f"✅ Validation passed: {validation.get('message', 'All issues resolved')}")
                            else:
                                st.warning(f"⚠️ Validation: {validation.get('message', 'Some issues remain')}")
                                
                                if validation.get('remaining_violations', 0) > 0:
                                    st.metric("Remaining Violations", validation['remaining_violations'])
                        
                        # Before/After comparison
                        if 'before_after_comparison' in exec_result:
                            with st.expander("📊 Before/After Comparison"):
                                comparison = exec_result['before_after_comparison']
                                st.json(comparison)
                        
                        # JIRA ticket if created
                        if 'jira_ticket' in exec_result:
                            st.divider()
                            st.markdown("### 📋 JIRA Ticket Created")
                            ticket = exec_result['jira_ticket'].get('ticket', {})
                            
                            st.info(f"Ticket {ticket.get('ticket_id', 'N/A')} created for manual follow-up")
                            st.write(f"**Summary:** {ticket.get('summary', 'N/A')}")
                            st.write(f"**Status:** {ticket.get('status', 'N/A')}")
                            st.write(f"**Priority:** {ticket.get('priority', 'N/A')}")
                    
                    elif exec_result.get('execution_status') == 'failed':
                        st.error("❌ Fix execution failed")
                        
                        if 'execution_results' in exec_result:
                            st.error(exec_result['execution_results'].get('error', 'Unknown error'))
                        
                        # Check if JIRA ticket was created
                        if 'jira_ticket' in exec_result:
                            st.info("📋 JIRA ticket created for manual intervention")
                            ticket = exec_result['jira_ticket'].get('ticket', {})
                            st.write(f"**Ticket ID:** {ticket.get('ticket_id', 'N/A')}")
                    
                except json.JSONDecodeError:
                    st.markdown(exec_text)
                
                # Option to clear and start new fix
                if st.button("🔄 Execute Another Fix", key="new_fix_btn"):
                    del st.session_state.approved_fix
                    del st.session_state.dry_run_results
                    del st.session_state.execution_results
                    if 'treatment_analysis' in st.session_state:
                        del st.session_state.treatment_analysis
                    st.rerun()

    
elif active_tab == "📊 Metrics":
    # =====================================================
    # REVAMPED METRICS DASHBOARD - User-Friendly & Visual
    # =====================================================
    
    # Add custom CSS for animations and styling
    st.markdown("""
    <style>
    /* Animated gradient background for metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #4da6ff33;
        box-shadow: 0 4px 20px rgba(77, 166, 255, 0.15);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(77, 166, 255, 0.25);
        border-color: #4da6ff;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #4da6ff, #00d4aa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: pulse 2s infinite;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #a0a0a0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Insight cards with icons */
    .insight-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #162447 100%);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #4da6ff;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .insight-icon {
        font-size: 2rem;
    }
    .insight-text {
        color: #e0e0e0;
        font-size: 1rem;
    }
    
    /* Chat interface styling */
    .chat-container {
        background: #1a1a2e;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #4da6ff33;
    }
    .chat-message-user {
        background: linear-gradient(135deg, #4da6ff 0%, #0066cc 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-message-ai {
        background: #2d2d44;
        color: #e0e0e0;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
    }
    
    /* Summary card styling */
    .summary-card {
        background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
        border-radius: 20px;
        padding: 25px;
        margin: 15px 0;
        border: 1px solid rgba(77, 166, 255, 0.2);
    }
    .summary-title {
        font-size: 1.2rem;
        color: #4da6ff;
        margin-bottom: 15px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize chat history
    if 'metrics_chat_history' not in st.session_state:
        st.session_state.metrics_chat_history = []
    
    # ===== TOP NAVIGATION - Simple Mode Selection =====
    st.markdown("### Choose What You'd Like to See")
    
    mode_cols = st.columns(4)
    with mode_cols[0]:
        dashboard_btn = st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state.get('metrics_view', 'dashboard') == 'dashboard' else "secondary")
        if dashboard_btn:
            st.session_state.metrics_view = 'dashboard'
            st.rerun()
    with mode_cols[1]:
        chat_btn = st.button("💬 Ask Questions", use_container_width=True, type="primary" if st.session_state.get('metrics_view') == 'chat' else "secondary")
        if chat_btn:
            st.session_state.metrics_view = 'chat'
            st.rerun()
    with mode_cols[2]:
        insights_btn = st.button("💡 Smart Insights", use_container_width=True, type="primary" if st.session_state.get('metrics_view') == 'insights' else "secondary")
        if insights_btn:
            st.session_state.metrics_view = 'insights'
            st.rerun()
    with mode_cols[3]:
        report_btn = st.button("📄 Generate Report", use_container_width=True, type="primary" if st.session_state.get('metrics_view') == 'report' else "secondary")
        if report_btn:
            st.session_state.metrics_view = 'report'
            st.rerun()
    
    st.divider()
    
    # Default to dashboard
    current_view = st.session_state.get('metrics_view', 'dashboard')
    
    # Helper function to get data summary
    def get_data_summary():
        """Get summary of available data for analysis"""
        summary = {
            'has_issues': 'filtered_issues' in st.session_state and st.session_state.filtered_issues,
            'total_violations': 0,
            'total_issues': 0,
            'tables': [],
            'severity_breakdown': {},
            'dimension_breakdown': {}
        }
        
        if summary['has_issues']:
            issues = st.session_state.filtered_issues
            summary['total_issues'] = len(issues)
            summary['total_violations'] = sum(issue.get('total_count', 0) for issue in issues)
            
            for issue in issues:
                table = issue.get('table', 'unknown')
                if table not in summary['tables']:
                    summary['tables'].append(table)
                
                sev = issue.get('severity', 'unknown')
                summary['severity_breakdown'][sev] = summary['severity_breakdown'].get(sev, 0) + 1
                
                dim = issue.get('dq_dimension', 'unknown')
                summary['dimension_breakdown'][dim] = summary['dimension_breakdown'].get(dim, 0) + issue.get('total_count', 0)
        
        return summary
    
    # ===== DASHBOARD VIEW =====
    if current_view == 'dashboard':
        data_summary = get_data_summary()
        
        # Hero Section - Data Quality Health Score
        st.markdown("## 🏥 Your Data Quality Health")
        
        if data_summary['has_issues']:
            # Calculate health score
            total_violations = data_summary['total_violations']
            critical_count = data_summary['severity_breakdown'].get('critical', 0)
            high_count = data_summary['severity_breakdown'].get('high', 0)
            
            # Health score formula: 100 - penalties
            health_score = max(0, 100 - (critical_count * 15) - (high_count * 5) - (data_summary['total_issues'] * 2))
            health_score = min(100, health_score)
            
            # Determine status
            if health_score >= 80:
                status_emoji = "✅"
                status_text = "Excellent"
                status_color = "#00d4aa"
            elif health_score >= 60:
                status_emoji = "⚠️"
                status_text = "Needs Attention"
                status_color = "#ffc107"
            else:
                status_emoji = "🚨"
                status_text = "Critical Issues"
                status_color = "#ff4757"
            
            # Health Score Display with Gauge
            col_health, col_summary = st.columns([1, 2])
            
            with col_health:
                import plotly.graph_objects as go
                
                # Create animated gauge chart
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=health_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Health Score", 'font': {'size': 20, 'color': '#e0e0e0'}},
                    number={'font': {'size': 50, 'color': status_color}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#666"},
                        'bar': {'color': status_color, 'thickness': 0.3},
                        'bgcolor': "#2d2d44",
                        'borderwidth': 2,
                        'bordercolor': "rgba(77, 166, 255, 0.2)",
                        'steps': [
                            {'range': [0, 40], 'color': 'rgba(255,71,87,0.3)'},
                            {'range': [40, 70], 'color': 'rgba(255,193,7,0.3)'},
                            {'range': [70, 100], 'color': 'rgba(0,212,170,0.3)'}
                        ],
                        'threshold': {
                            'line': {'color': "#ffffff", 'width': 4},
                            'thickness': 0.75,
                            'value': health_score
                        }
                    }
                ))
                
                fig_gauge.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=250,
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                
                st.plotly_chart(fig_gauge, use_container_width=True, key="health_gauge")
                st.markdown(f"<p style='text-align:center; font-size: 1.2rem;'>{status_emoji} {status_text}</p>", unsafe_allow_html=True)
            
            with col_summary:
                st.markdown("### 📌 Quick Summary")
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 20px; border-radius: 12px; border: 1px solid #4da6ff33;'>
                    <p style='font-size: 1.1rem; color: #e0e0e0; margin-bottom: 15px;'>
                        We found <strong style='color: #4da6ff;'>{data_summary['total_violations']:,}</strong> data quality issues 
                        across <strong style='color: #4da6ff;'>{len(data_summary['tables'])}</strong> table(s).
                    </p>
                    <p style='font-size: 1rem; color: #a0a0a0;'>
                        {"🔴 " + str(critical_count) + " critical issues need immediate attention!" if critical_count > 0 else "✅ No critical issues found."}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Quick stats in a row
                stat_cols = st.columns(3)
                with stat_cols[0]:
                    st.metric("📋 Total Issues", f"{data_summary['total_issues']}")
                with stat_cols[1]:
                    st.metric("⚠️ High Priority", f"{critical_count + high_count}")
                with stat_cols[2]:
                    st.metric("📊 Tables Affected", len(data_summary['tables']))
            
            st.divider()
            
            # Interactive Charts Section
            st.markdown("## 📈 Visual Analytics")
            
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Animated Pie Chart - Issues by Severity
                st.markdown("### Issues by Severity")
                
                severity_data = data_summary['severity_breakdown']
                if severity_data:
                    colors = {
                        'critical': '#ff4757',
                        'high': '#ffa502',
                        'medium': '#ffc107',
                        'low': '#2ed573'
                    }
                    
                    fig_severity = go.Figure(data=[go.Pie(
                        labels=list(severity_data.keys()),
                        values=list(severity_data.values()),
                        hole=0.5,
                        marker_colors=[colors.get(s, '#666') for s in severity_data.keys()],
                        textinfo='label+percent',
                        textfont_size=14,
                        pull=[0.1 if s == 'critical' else 0 for s in severity_data.keys()]
                    )])
                    
                    fig_severity.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        showlegend=True,
                        legend=dict(font=dict(color='#e0e0e0')),
                        height=350,
                        margin=dict(l=20, r=20, t=20, b=20)
                    )
                    
                    st.plotly_chart(fig_severity, use_container_width=True, key="severity_pie")
            
            with chart_col2:
                # Animated Bar Chart - Issues by Dimension
                st.markdown("### Issues by Category")
                
                dimension_data = data_summary['dimension_breakdown']
                if dimension_data:
                    # Sort by count
                    sorted_dims = sorted(dimension_data.items(), key=lambda x: x[1], reverse=True)
                    dims = [d[0] for d in sorted_dims]
                    counts = [d[1] for d in sorted_dims]
                    
                    fig_dims = go.Figure(data=[go.Bar(
                        x=counts,
                        y=dims,
                        orientation='h',
                        marker=dict(
                            color=counts,
                            colorscale=[[0, '#4da6ff'], [0.5, '#00d4aa'], [1, '#ff6b6b']],
                            line=dict(width=0)
                        ),
                        text=counts,
                        textposition='outside',
                        textfont=dict(color='#e0e0e0')
                    )])
                    
                    fig_dims.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(title='Number of Violations', color='#a0a0a0', gridcolor='#333'),
                        yaxis=dict(title='', color='#e0e0e0'),
                        height=350,
                        margin=dict(l=20, r=80, t=20, b=40)
                    )
                    
                    st.plotly_chart(fig_dims, use_container_width=True, key="dimension_bar")
            
            # Trend Analysis (if multiple tables)
            if len(data_summary['tables']) > 1:
                st.markdown("### 📊 Issues Across Tables")
                
                # Group issues by table
                table_issues = {}
                for issue in st.session_state.filtered_issues:
                    table = issue.get('table', 'unknown')
                    table_issues[table] = table_issues.get(table, 0) + issue.get('total_count', 0)
                
                fig_tables = go.Figure(data=[go.Bar(
                    x=list(table_issues.keys()),
                    y=list(table_issues.values()),
                    marker=dict(
                        color=list(table_issues.values()),
                        colorscale='Blues',
                        line=dict(width=2, color='#4da6ff')
                    ),
                    text=list(table_issues.values()),
                    textposition='outside',
                    textfont=dict(color='#e0e0e0', size=14)
                )])
                
                fig_tables.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(title='Table', color='#a0a0a0', gridcolor='#333'),
                    yaxis=dict(title='Total Violations', color='#a0a0a0', gridcolor='#333'),
                    height=300,
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                
                st.plotly_chart(fig_tables, use_container_width=True, key="table_comparison")
        
        else:
            # No data - show welcome state with options to get started
            st.markdown("""
            <div style='text-align: center; padding: 40px 20px;'>
                <div style='font-size: 4rem; margin-bottom: 20px;'>📊</div>
                <h2 style='color: #4da6ff; margin-bottom: 15px;'>Welcome to Metrics Dashboard</h2>
                <p style='color: #a0a0a0; font-size: 1.1rem; max-width: 600px; margin: 0 auto;'>
                    Choose an option below to get started - you can run analysis directly or use demo data.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # Two column layout for options
            opt_col1, opt_col2 = st.columns(2)
            
            with opt_col1:
                st.markdown("### 🔍 Run Quick Analysis")
                st.markdown("*Analyze your tables directly without previous steps*")
                
                # Get available tables
                available_tables = st.session_state.get('available_tables', [])
                if not available_tables:
                    # Try to fetch from BigQuery
                    try:
                        from google.cloud import bigquery
                        project_id = st.session_state.get('project_id', '')
                        dataset_id = st.session_state.get('dataset_id', '')
                        if project_id and dataset_id:
                            client = bigquery.Client(project=project_id)
                            tables = list(client.list_tables(f"{project_id}.{dataset_id}"))
                            available_tables = [t.table_id for t in tables]
                            st.session_state.available_tables = available_tables
                    except:
                        available_tables = ['policies_week1', 'policies_week2', 'policies_week3', 'policies_week4']
                
                if available_tables:
                    selected_tables = st.multiselect(
                        "Select tables to analyze",
                        available_tables,
                        default=[available_tables[0]] if available_tables else [],
                        key="quick_analysis_tables"
                    )
                    
                    if st.button("🚀 Run Quick Analysis", use_container_width=True, type="primary", disabled=not selected_tables):
                        with st.spinner("🔍 Analyzing tables for data quality issues..."):
                            try:
                                from google.cloud import bigquery
                                project_id = st.session_state.get('project_id', '')
                                dataset_id = st.session_state.get('dataset_id', '')
                                client = bigquery.Client(project=project_id)
                                
                                # Run basic DQ analysis on selected tables
                                quick_issues = []
                                for table in selected_tables:
                                    # Check for NULL values in key columns
                                    schema_query = f"SELECT column_name, data_type FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = '{table}'"
                                    schema_df = client.query(schema_query).to_dataframe()
                                    
                                    for _, row in schema_df.iterrows():
                                        col_name = row['column_name']
                                        # Check NULL count
                                        null_query = f"SELECT COUNT(*) as null_count FROM `{project_id}.{dataset_id}.{table}` WHERE {col_name} IS NULL"
                                        try:
                                            null_result = client.query(null_query).to_dataframe()
                                            null_count = null_result['null_count'].iloc[0]
                                            if null_count > 0:
                                                severity = 'critical' if null_count > 100 else 'high' if null_count > 50 else 'medium' if null_count > 10 else 'low'
                                                quick_issues.append({
                                                    'table': table,
                                                    'severity': severity,
                                                    'total_count': int(null_count),
                                                    'dq_dimension': 'Completeness',
                                                    'rule_name': f'{col_name}_null_check',
                                                    'column': col_name
                                                })
                                        except:
                                            pass
                                
                                if quick_issues:
                                    # Take top issues to avoid overwhelming
                                    quick_issues = sorted(quick_issues, key=lambda x: x['total_count'], reverse=True)[:20]
                                    st.session_state.filtered_issues = quick_issues
                                    st.success(f"✅ Found {len(quick_issues)} data quality issues!")
                                    st.rerun()
                                else:
                                    st.info("✨ No obvious data quality issues found! Your data looks clean.")
                                    
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                                st.info("💡 Make sure you've configured GCP Project and Dataset in the sidebar.")
                else:
                    st.warning("⚠️ Configure your GCP Project and Dataset in the sidebar first.")
            
            with opt_col2:
                st.markdown("### 🎯 Use Demo Data")
                st.markdown("*Try the dashboard with sample data*")
                
                st.markdown("""
                <div style='background: rgba(77, 166, 255, 0.1); padding: 15px; border-radius: 10px; margin: 10px 0;'>
                    <p style='color: #a0a0a0; margin: 0;'>Demo includes:</p>
                    <ul style='color: #e0e0e0; margin: 10px 0;'>
                        <li>5 sample DQ issues</li>
                        <li>Multiple severity levels</li>
                        <li>Various DQ dimensions</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🎯 Load Demo Dashboard", use_container_width=True):
                    # Create demo data
                    st.session_state.filtered_issues = [
                        {'table': 'policies_week1', 'severity': 'critical', 'total_count': 45, 'dq_dimension': 'Completeness', 'rule_name': 'null_check'},
                        {'table': 'policies_week1', 'severity': 'high', 'total_count': 123, 'dq_dimension': 'Validity', 'rule_name': 'date_format'},
                        {'table': 'policies_week2', 'severity': 'medium', 'total_count': 67, 'dq_dimension': 'Accuracy', 'rule_name': 'range_check'},
                        {'table': 'policies_week1', 'severity': 'low', 'total_count': 234, 'dq_dimension': 'Consistency', 'rule_name': 'cross_ref'},
                        {'table': 'policies_week2', 'severity': 'high', 'total_count': 89, 'dq_dimension': 'Timeliness', 'rule_name': 'stale_data'},
                    ]
                    st.rerun()
    
    # ===== CHAT VIEW - Natural Language Analysis =====
    elif current_view == 'chat':
        st.markdown("## 💬 Ask Me Anything About Your Data")
        st.markdown("*I can help you understand your data quality issues in plain English*")
        
        # Chat container
        chat_container = st.container()
        
        # Suggested questions
        st.markdown("### 💡 Try asking:")
        suggestion_cols = st.columns(2)
        
        suggestions = [
            "What are my biggest data quality problems?",
            "How much money could bad data cost us?",
            "Which table needs the most attention?",
            "What should I fix first?",
            "Give me a summary for my manager",
            "Are there any patterns in the issues?"
        ]
        
        for i, suggestion in enumerate(suggestions):
            col_idx = i % 2
            with suggestion_cols[col_idx]:
                if st.button(f"💭 {suggestion}", key=f"suggest_{i}", use_container_width=True):
                    st.session_state.metrics_chat_input = suggestion
                    st.rerun()
        
        st.divider()
        
        # Display chat history
        with chat_container:
            for msg in st.session_state.metrics_chat_history:
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #4da6ff 0%, #0066cc 100%); color: white; 
                                padding: 12px 18px; border-radius: 18px 18px 4px 18px; margin: 8px 0; 
                                max-width: 80%; margin-left: auto;'>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background: #2d2d44; color: #e0e0e0; padding: 12px 18px; 
                                border-radius: 18px 18px 18px 4px; margin: 8px 0;'>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Chat input
        col_input, col_send = st.columns([5, 1])
        with col_input:
            default_input = st.session_state.get('metrics_chat_input', '')
            user_question = st.text_input("Ask a question about your data quality...", 
                                          value=default_input,
                                          key="chat_input_field",
                                          placeholder="e.g., What should I prioritize fixing?")
        with col_send:
            send_clicked = st.button("📤 Send", use_container_width=True, type="primary")
        
        # Clear the stored input after using it
        if 'metrics_chat_input' in st.session_state:
            del st.session_state.metrics_chat_input
        
        if send_clicked and user_question:
            # Add user message
            st.session_state.metrics_chat_history.append({
                'role': 'user',
                'content': user_question
            })
            
            with st.spinner("🤔 Thinking..."):
                try:
                    from dq_agents.metrics.agent import metrics_agent
                    from google.adk.runners import Runner
                    from google.adk.sessions import InMemorySessionService
                    from google.adk.artifacts import InMemoryArtifactService
                    from google.genai import types
                    
                    session_service = InMemorySessionService()
                    artifact_service = InMemoryArtifactService()
                    runner = Runner(
                        app_name="DQMetricsChat",
                        agent=metrics_agent,
                        session_service=session_service,
                        artifact_service=artifact_service
                    )
                    
                    import asyncio
                    session = asyncio.run(session_service.create_session(
                        app_name="DQMetricsChat",
                        user_id="streamlit_user"
                    ))
                    
                    # Build context
                    data_summary = get_data_summary()
                    context = f"""
                    Current Data Quality Status:
                    - Has issues data: {data_summary['has_issues']}
                    - Total violations: {data_summary['total_violations']}
                    - Total issue types: {data_summary['total_issues']}
                    - Tables affected: {', '.join(data_summary['tables']) if data_summary['tables'] else 'None'}
                    - Severity breakdown: {json.dumps(data_summary['severity_breakdown'])}
                    - Category breakdown: {json.dumps(data_summary['dimension_breakdown'])}
                    """
                    
                    prompt = f"""
                    You are a friendly data quality assistant helping a non-technical user understand their data issues.
                    
                    {context}
                    
                    User Question: {user_question}
                    
                    Instructions:
                    1. Answer in plain, simple English - avoid technical jargon
                    2. Use numbers and percentages to make your point
                    3. Be concise but helpful (2-3 paragraphs max)
                    4. If relevant, suggest a specific action they can take
                    5. Use emoji sparingly to make it friendly
                    6. If there's no data, explain they need to run the Identifier/Treatment agents first
                    
                    Respond directly to their question:
                    """
                    
                    content = types.Content(role="user", parts=[types.Part(text=prompt)])
                    events = list(runner.run(
                        user_id="streamlit_user",
                        session_id=session.id,
                        new_message=content
                    ))
                    
                    if events:
                        last_event = events[-1]
                        response = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                        
                        st.session_state.metrics_chat_history.append({
                            'role': 'assistant',
                            'content': response
                        })
                    else:
                        st.session_state.metrics_chat_history.append({
                            'role': 'assistant',
                            'content': "I'm sorry, I couldn't process that question. Please try again."
                        })
                    
                except Exception as e:
                    st.session_state.metrics_chat_history.append({
                        'role': 'assistant',
                        'content': f"Oops! Something went wrong: {str(e)}"
                    })
            
            st.rerun()
        
        # Clear chat button
        if st.session_state.metrics_chat_history:
            if st.button("🗑️ Clear Chat History", key="clear_chat"):
                st.session_state.metrics_chat_history = []
                st.rerun()
    
    # ===== INSIGHTS VIEW =====
    elif current_view == 'insights':
        st.markdown("## 💡 Smart Insights")
        st.markdown("*AI-powered analysis of your data quality issues*")
        
        data_summary = get_data_summary()
        
        if data_summary['has_issues']:
            # Generate insights automatically
            insights = []
            
            # Critical issues insight
            critical = data_summary['severity_breakdown'].get('critical', 0)
            if critical > 0:
                insights.append({
                    'icon': '🚨',
                    'title': 'Urgent Action Required',
                    'text': f'You have {critical} critical issue(s) that need immediate attention. These could impact business operations.',
                    'priority': 1
                })
            
            # Most common dimension
            if data_summary['dimension_breakdown']:
                top_dim = max(data_summary['dimension_breakdown'].items(), key=lambda x: x[1])
                insights.append({
                    'icon': '📊',
                    'title': f'{top_dim[0]} Issues Lead',
                    'text': f'{top_dim[0]} has {top_dim[1]:,} violations - this is your biggest category of issues.',
                    'priority': 2
                })
            
            # Table health
            if len(data_summary['tables']) > 1:
                insights.append({
                    'icon': '📋',
                    'title': 'Multiple Tables Affected',
                    'text': f'{len(data_summary["tables"])} tables have data quality issues. Consider a systematic cleanup approach.',
                    'priority': 3
                })
            
            # Cost estimate
            avg_cost_per_issue = 500  # Estimated GBP per violation
            estimated_cost = data_summary['total_violations'] * avg_cost_per_issue
            insights.append({
                'icon': '💰',
                'title': 'Estimated Financial Impact',
                'text': f'These issues could cost approximately £{estimated_cost:,.0f} if left unaddressed. Fixing them is worth it!',
                'priority': 4
            })
            
            # Quick wins
            low_priority = data_summary['severity_breakdown'].get('low', 0)
            if low_priority > 0:
                insights.append({
                    'icon': '✨',
                    'title': 'Quick Wins Available',
                    'text': f'There are {low_priority} low-severity issues that can be fixed easily to improve your overall score.',
                    'priority': 5
                })
            
            # Display insights as cards
            for insight in sorted(insights, key=lambda x: x['priority']):
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #1e3a5f 0%, #162447 100%); 
                            border-radius: 12px; padding: 20px; margin: 15px 0; 
                            border-left: 4px solid #4da6ff; display: flex; align-items: flex-start; gap: 15px;'>
                    <div style='font-size: 2rem;'>{insight['icon']}</div>
                    <div>
                        <div style='font-size: 1.1rem; font-weight: 600; color: #4da6ff; margin-bottom: 8px;'>{insight['title']}</div>
                        <div style='color: #e0e0e0; font-size: 1rem;'>{insight['text']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Recommendations section
            st.markdown("### 🎯 Recommended Actions")
            
            rec_cols = st.columns(3)
            
            with rec_cols[0]:
                st.markdown("""
                <div style='background: #1a1a2e; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #ff4757;'>
                    <div style='font-size: 2rem; margin-bottom: 10px;'>1️⃣</div>
                    <div style='color: #ff4757; font-weight: 600; margin-bottom: 8px;'>Fix Critical Issues</div>
                    <div style='color: #a0a0a0; font-size: 0.9rem;'>Address high-impact problems first</div>
                </div>
                """, unsafe_allow_html=True)
            
            with rec_cols[1]:
                st.markdown("""
                <div style='background: #1a1a2e; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #ffc107;'>
                    <div style='font-size: 2rem; margin-bottom: 10px;'>2️⃣</div>
                    <div style='color: #ffc107; font-weight: 600; margin-bottom: 8px;'>Validate Fixes</div>
                    <div style='color: #a0a0a0; font-size: 0.9rem;'>Use dry-run mode to test safely</div>
                </div>
                """, unsafe_allow_html=True)
            
            with rec_cols[2]:
                st.markdown("""
                <div style='background: #1a1a2e; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #2ed573;'>
                    <div style='font-size: 2rem; margin-bottom: 10px;'>3️⃣</div>
                    <div style='color: #2ed573; font-weight: 600; margin-bottom: 8px;'>Monitor Regularly</div>
                    <div style='color: #a0a0a0; font-size: 0.9rem;'>Set up recurring DQ checks</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Advanced AI Analysis button
            st.divider()
            if st.button("🤖 Generate Deep AI Analysis", use_container_width=True, type="primary"):
                with st.spinner("🔍 AI is analyzing patterns in your data..."):
                    try:
                        from dq_agents.metrics.agent import metrics_agent
                        from google.adk.runners import Runner
                        from google.adk.sessions import InMemorySessionService
                        from google.adk.artifacts import InMemoryArtifactService
                        from google.genai import types
                        
                        session_service = InMemorySessionService()
                        artifact_service = InMemoryArtifactService()
                        runner = Runner(
                            app_name="DQMetricsInsights",
                            agent=metrics_agent,
                            session_service=session_service,
                            artifact_service=artifact_service
                        )
                        
                        import asyncio
                        session = asyncio.run(session_service.create_session(
                            app_name="DQMetricsInsights",
                            user_id="streamlit_user"
                        ))
                        
                        issues_json = json.dumps(st.session_state.filtered_issues, default=str)
                        
                        prompt = f"""
                        Analyze these data quality issues and provide deep insights:
                        
                        {issues_json}
                        
                        Provide:
                        1. Pattern Analysis: Are there patterns or correlations between issue types?
                        2. Root Cause Hypothesis: What might be causing these issues?
                        3. Priority Matrix: Which issues to fix in what order?
                        4. Time to Fix Estimates: How long might each category take to remediate?
                        5. Prevention Recommendations: How to prevent these issues in the future?
                        
                        Write in a friendly, easy-to-understand style for non-technical stakeholders.
                        Use bullet points and clear headings.
                        """
                        
                        content = types.Content(role="user", parts=[types.Part(text=prompt)])
                        events = list(runner.run(
                            user_id="streamlit_user",
                            session_id=session.id,
                            new_message=content
                        ))
                        
                        if events:
                            last_event = events[-1]
                            response = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                            st.session_state.deep_analysis = response
                            st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            # Display deep analysis if available
            if 'deep_analysis' in st.session_state:
                st.markdown("### 🧠 AI Deep Analysis")
                st.markdown(st.session_state.deep_analysis)
                
                if st.button("🔄 Clear Analysis", key="clear_analysis"):
                    del st.session_state.deep_analysis
                    st.rerun()
        
        else:
            # ===== STANDALONE ANOMALY DETECTION =====
            st.markdown("### 🔬 Standalone Data Analysis")
            st.info("No data from previous steps? Run comprehensive analysis directly on your BigQuery tables!")
            
            analysis_tabs = st.tabs(["🎯 Anomaly Detection", "📊 Data Profiling", "💰 Quality Cost Calculator"])
            
            # ----- ANOMALY DETECTION TAB -----
            with analysis_tabs[0]:
                st.markdown("#### Detect Data Anomalies with ML")
                st.markdown("*Uses IsolationForest algorithm to identify unusual patterns in your data*")
                
                # Get available tables
                try:
                    from google.cloud import bigquery
                    bq_client = bigquery.Client(project=project_id)
                    
                    # Get tables list
                    tables_query = f"""
                        SELECT table_name 
                        FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
                        WHERE table_type = 'BASE TABLE'
                    """
                    tables_result = bq_client.query(tables_query).result()
                    available_tables = [row.table_name for row in tables_result]
                    
                    if available_tables:
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            anomaly_table = st.selectbox(
                                "Select Table for Anomaly Detection",
                                available_tables,
                                key="anomaly_table_select"
                            )
                        
                        with col2:
                            contamination = st.slider(
                                "Anomaly Sensitivity",
                                min_value=0.01,
                                max_value=0.3,
                                value=0.1,
                                step=0.01,
                                help="Higher = more anomalies detected"
                            )
                        
                        if st.button("🔍 Run Anomaly Detection", key="run_anomaly", type="primary"):
                            with st.spinner("Analyzing data for anomalies..."):
                                try:
                                    # Get numeric columns
                                    schema_query = f"""
                                        SELECT column_name, data_type
                                        FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
                                        WHERE table_name = '{anomaly_table}'
                                        AND data_type IN ('INT64', 'FLOAT64', 'NUMERIC', 'BIGNUMERIC')
                                    """
                                    schema_result = bq_client.query(schema_query).result()
                                    numeric_cols = [row.column_name for row in schema_result]
                                    
                                    if len(numeric_cols) >= 2:
                                        # Get sample data
                                        data_query = f"""
                                            SELECT {', '.join(numeric_cols[:5])}
                                            FROM `{project_id}.{dataset_id}.{anomaly_table}`
                                            WHERE {' AND '.join([f'{col} IS NOT NULL' for col in numeric_cols[:5]])}
                                            LIMIT 1000
                                        """
                                        df = bq_client.query(data_query).to_dataframe()
                                        
                                        if len(df) > 10:
                                            # Run IsolationForest
                                            from sklearn.ensemble import IsolationForest
                                            from sklearn.preprocessing import StandardScaler
                                            
                                            scaler = StandardScaler()
                                            X = scaler.fit_transform(df[numeric_cols[:5]])
                                            
                                            iso_forest = IsolationForest(
                                                contamination=contamination,
                                                random_state=42,
                                                n_estimators=100
                                            )
                                            predictions = iso_forest.fit_predict(X)
                                            scores = iso_forest.decision_function(X)
                                            
                                            df['anomaly'] = predictions
                                            df['anomaly_score'] = scores
                                            
                                            anomalies = df[df['anomaly'] == -1]
                                            normal = df[df['anomaly'] == 1]
                                            
                                            # Display results
                                            st.success(f"✅ Analysis complete! Found **{len(anomalies)}** anomalies out of **{len(df)}** records ({len(anomalies)/len(df)*100:.1f}%)")
                                            
                                            # Metrics
                                            m1, m2, m3, m4 = st.columns(4)
                                            with m1:
                                                st.metric("Total Records", f"{len(df):,}")
                                            with m2:
                                                st.metric("Anomalies", f"{len(anomalies):,}")
                                            with m3:
                                                st.metric("Normal Records", f"{len(normal):,}")
                                            with m4:
                                                anomaly_pct = len(anomalies)/len(df)*100
                                                st.metric("Anomaly Rate", f"{anomaly_pct:.1f}%", 
                                                         delta=f"{anomaly_pct - contamination*100:.1f}%" if anomaly_pct > contamination*100 else None,
                                                         delta_color="inverse")
                                            
                                            # Visualization
                                            import plotly.express as px
                                            
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                # Scatter plot of first two dimensions
                                                fig = px.scatter(
                                                    df, 
                                                    x=numeric_cols[0], 
                                                    y=numeric_cols[1],
                                                    color=df['anomaly'].map({1: 'Normal', -1: 'Anomaly'}),
                                                    color_discrete_map={'Normal': '#00d26a', 'Anomaly': '#ff4757'},
                                                    title=f"Anomaly Detection: {numeric_cols[0]} vs {numeric_cols[1]}",
                                                    template="plotly_dark"
                                                )
                                                fig.update_layout(
                                                    plot_bgcolor='rgba(0,0,0,0)',
                                                    paper_bgcolor='rgba(0,0,0,0)'
                                                )
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with col2:
                                                # Score distribution
                                                fig2 = px.histogram(
                                                    df,
                                                    x='anomaly_score',
                                                    color=df['anomaly'].map({1: 'Normal', -1: 'Anomaly'}),
                                                    color_discrete_map={'Normal': '#00d26a', 'Anomaly': '#ff4757'},
                                                    title="Anomaly Score Distribution",
                                                    template="plotly_dark",
                                                    nbins=50
                                                )
                                                fig2.update_layout(
                                                    plot_bgcolor='rgba(0,0,0,0)',
                                                    paper_bgcolor='rgba(0,0,0,0)'
                                                )
                                                st.plotly_chart(fig2, use_container_width=True)
                                            
                                            # Show anomaly samples
                                            if len(anomalies) > 0:
                                                with st.expander("👁️ View Detected Anomalies", expanded=True):
                                                    st.dataframe(
                                                        anomalies.sort_values('anomaly_score').head(20),
                                                        use_container_width=True
                                                    )
                                        else:
                                            st.warning("Not enough data points for anomaly detection (need at least 10 rows)")
                                    else:
                                        st.warning("Need at least 2 numeric columns for anomaly detection")
                                except Exception as e:
                                    st.error(f"Error running anomaly detection: {str(e)}")
                    else:
                        st.warning("No tables found in the dataset")
                except Exception as e:
                    st.error(f"Error connecting to BigQuery: {str(e)}")
            
            # ----- DATA PROFILING TAB -----
            with analysis_tabs[1]:
                st.markdown("#### Quick Data Profiling")
                st.markdown("*Get instant statistics and quality metrics for any table*")
                
                try:
                    from google.cloud import bigquery
                    bq_client = bigquery.Client(project=project_id)
                    
                    tables_query = f"""
                        SELECT table_name 
                        FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
                        WHERE table_type = 'BASE TABLE'
                    """
                    tables_result = bq_client.query(tables_query).result()
                    available_tables = [row.table_name for row in tables_result]
                    
                    if available_tables:
                        profile_table = st.selectbox(
                            "Select Table to Profile",
                            available_tables,
                            key="profile_table_select"
                        )
                        
                        if st.button("📊 Generate Profile", key="run_profile", type="primary"):
                            with st.spinner("Profiling table..."):
                                try:
                                    # Get column info
                                    cols_query = f"""
                                        SELECT column_name, data_type, is_nullable
                                        FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
                                        WHERE table_name = '{profile_table}'
                                    """
                                    cols_result = bq_client.query(cols_query).result()
                                    columns_info = [(row.column_name, row.data_type, row.is_nullable) for row in cols_result]
                                    
                                    # Get row count
                                    count_query = f"SELECT COUNT(*) as cnt FROM `{project_id}.{dataset_id}.{profile_table}`"
                                    count_result = bq_client.query(count_query).result()
                                    row_count = list(count_result)[0].cnt
                                    
                                    # Get null counts for each column
                                    null_queries = []
                                    for col, dtype, nullable in columns_info:
                                        null_queries.append(f"SUM(CASE WHEN `{col}` IS NULL THEN 1 ELSE 0 END) as `{col}_nulls`")
                                    
                                    null_query = f"""
                                        SELECT {', '.join(null_queries)}
                                        FROM `{project_id}.{dataset_id}.{profile_table}`
                                    """
                                    null_result = bq_client.query(null_query).result()
                                    null_row = list(null_result)[0]
                                    
                                    # Build profile data
                                    profile_data = []
                                    for col, dtype, nullable in columns_info:
                                        null_count = getattr(null_row, f"{col}_nulls")
                                        null_pct = (null_count / row_count * 100) if row_count > 0 else 0
                                        completeness = 100 - null_pct
                                        
                                        profile_data.append({
                                            "Column": col,
                                            "Type": dtype,
                                            "Nullable": nullable,
                                            "Total Rows": row_count,
                                            "Null Count": null_count,
                                            "Null %": f"{null_pct:.1f}%",
                                            "Completeness": f"{completeness:.1f}%",
                                            "Quality": "🟢" if completeness >= 95 else ("🟡" if completeness >= 80 else "🟠" if completeness >= 50 else "🔴")
                                        })
                                    
                                    import pandas as pd
                                    profile_df = pd.DataFrame(profile_data)
                                    
                                    # Summary metrics
                                    avg_completeness = sum([float(p["Completeness"].replace("%","")) for p in profile_data]) / len(profile_data)
                                    cols_with_nulls = sum([1 for p in profile_data if float(p["Null %"].replace("%","")) > 0])
                                    
                                    st.success(f"✅ Profile complete for **{profile_table}**")
                                    
                                    m1, m2, m3, m4 = st.columns(4)
                                    with m1:
                                        st.metric("Total Rows", f"{row_count:,}")
                                    with m2:
                                        st.metric("Total Columns", len(columns_info))
                                    with m3:
                                        st.metric("Avg Completeness", f"{avg_completeness:.1f}%")
                                    with m4:
                                        st.metric("Cols with Nulls", cols_with_nulls)
                                    
                                    st.dataframe(profile_df, use_container_width=True)
                                    
                                    # Completeness chart
                                    import plotly.express as px
                                    
                                    completeness_vals = [float(p["Completeness"].replace("%","")) for p in profile_data]
                                    fig = px.bar(
                                        x=[p["Column"] for p in profile_data],
                                        y=completeness_vals,
                                        color=completeness_vals,
                                        color_continuous_scale="RdYlGn",
                                        range_color=[0, 100],
                                        title="Column Completeness Overview",
                                        labels={"x": "Column", "y": "Completeness %"},
                                        template="plotly_dark"
                                    )
                                    fig.update_layout(
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        showlegend=False
                                    )
                                    fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text="Target: 95%")
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                except Exception as e:
                                    st.error(f"Error profiling table: {str(e)}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            # ----- COST CALCULATOR TAB -----
            with analysis_tabs[2]:
                st.markdown("#### 💰 Data Quality Cost Calculator")
                st.markdown("*Estimate the financial impact of data quality issues*")
                
                with st.form("cost_calculator"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        total_records = st.number_input("Total Records in Dataset", min_value=1000, value=100000, step=1000)
                        error_rate = st.slider("Estimated Error Rate (%)", min_value=0.1, max_value=30.0, value=5.0, step=0.1)
                        cost_per_error = st.number_input("Cost per Error (£)", min_value=0.1, value=10.0, step=0.5)
                    
                    with col2:
                        manual_review_time = st.slider("Manual Review Time (min/error)", min_value=1, max_value=60, value=15)
                        hourly_rate = st.number_input("Staff Hourly Rate (£)", min_value=10.0, value=35.0, step=5.0)
                        regulatory_fine_risk = st.slider("Regulatory Fine Risk (%)", min_value=0, max_value=100, value=20)
                    
                    calculate = st.form_submit_button("Calculate Cost of Inaction", type="primary")
                    
                    if calculate:
                        # Calculate costs
                        num_errors = int(total_records * error_rate / 100)
                        direct_cost = num_errors * cost_per_error
                        review_hours = num_errors * manual_review_time / 60
                        review_cost = review_hours * hourly_rate
                        potential_fine = direct_cost * (regulatory_fine_risk / 100) * 10  # Fines often 10x
                        
                        total_cost = direct_cost + review_cost + potential_fine
                        
                        # Savings with automation (assume 80% reduction)
                        automation_savings = total_cost * 0.8
                        
                        st.markdown("---")
                        st.markdown("### 📊 Cost Analysis Results")
                        
                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric("Estimated Errors", f"{num_errors:,}")
                        with m2:
                            st.metric("Direct Error Cost", f"£{direct_cost:,.0f}")
                        with m3:
                            st.metric("Review Labor Cost", f"£{review_cost:,.0f}")
                        
                        m4, m5, m6 = st.columns(3)
                        with m4:
                            st.metric("Regulatory Risk", f"£{potential_fine:,.0f}")
                        with m5:
                            st.metric("Total Cost of Inaction", f"£{total_cost:,.0f}", delta=None)
                        with m6:
                            st.metric("Savings with Automation", f"£{automation_savings:,.0f}", delta="80% reduction", delta_color="normal")
                        
                        # Visualization
                        import plotly.graph_objects as go
                        
                        fig = go.Figure(data=[
                            go.Bar(
                                x=['Direct Costs', 'Review Labor', 'Regulatory Risk', 'TOTAL'],
                                y=[direct_cost, review_cost, potential_fine, total_cost],
                                marker_color=['#ff6b6b', '#ffa502', '#ff4757', '#2f3542'],
                                text=[f'£{v:,.0f}' for v in [direct_cost, review_cost, potential_fine, total_cost]],
                                textposition='outside'
                            )
                        ])
                        fig.update_layout(
                            title="Cost Breakdown Analysis",
                            yaxis_title="Cost (£)",
                            template="plotly_dark",
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # ROI calculation
                        implementation_cost = 50000  # Assumed automation implementation cost
                        payback_months = implementation_cost / (automation_savings / 12) if automation_savings > 0 else float('inf')
                        
                        st.markdown("### 💡 ROI Summary")
                        st.markdown(f"""
                        | Metric | Value |
                        |--------|-------|
                        | Annual Cost of Poor Data | **£{total_cost:,.0f}** |
                        | Potential Annual Savings | **£{automation_savings:,.0f}** |
                        | Estimated Implementation | **£{implementation_cost:,.0f}** |
                        | Payback Period | **{payback_months:.1f} months** |
                        | 3-Year ROI | **{((automation_savings * 3 - implementation_cost) / implementation_cost * 100):.0f}%** |
                        """)
    
    # ===== REPORT VIEW =====
    elif current_view == 'report':
        st.markdown("## 📄 Generate Executive Report")
        st.markdown("*Create a professional report to share with stakeholders*")
        
        data_summary = get_data_summary()
        
        # Report options
        with st.expander("⚙️ Report Options", expanded=True):
            report_title = st.text_input("Report Title", "Data Quality Executive Summary")
            
            include_options = st.multiselect(
                "Include Sections",
                ["Executive Summary", "Key Metrics", "Issue Breakdown", "Financial Impact", "Recommendations", "Next Steps"],
                default=["Executive Summary", "Key Metrics", "Issue Breakdown", "Recommendations"]
            )
            
            report_style = st.radio(
                "Report Style",
                ["Simple (1 page)", "Detailed (full analysis)"],
                horizontal=True
            )
        
        if st.button("📝 Generate Report", type="primary", use_container_width=True):
            with st.spinner("✍️ Writing your report..."):
                try:
                    from dq_agents.metrics.agent import metrics_agent
                    from google.adk.runners import Runner
                    from google.adk.sessions import InMemorySessionService
                    from google.adk.artifacts import InMemoryArtifactService
                    from google.genai import types
                    
                    session_service = InMemorySessionService()
                    artifact_service = InMemoryArtifactService()
                    runner = Runner(
                        app_name="DQMetricsReport",
                        agent=metrics_agent,
                        session_service=session_service,
                        artifact_service=artifact_service
                    )
                    
                    import asyncio
                    session = asyncio.run(session_service.create_session(
                        app_name="DQMetricsReport",
                        user_id="streamlit_user"
                    ))
                    
                    context = json.dumps({
                        'data_summary': data_summary,
                        'report_title': report_title,
                        'sections': include_options,
                        'style': report_style,
                        'date': datetime.now().strftime('%Y-%m-%d')
                    }, default=str)
                    
                    length_instruction = "Keep it to 1 page equivalent (300-400 words max)" if "Simple" in report_style else "Provide comprehensive analysis (600-800 words)"
                    
                    prompt = f"""
                    Generate a professional executive report for data quality stakeholders.
                    
                    Context: {context}
                    
                    Title: {report_title}
                    Sections to include: {', '.join(include_options)}
                    
                    Requirements:
                    1. {length_instruction}
                    2. Use clear, non-technical language
                    3. Include specific numbers and percentages
                    4. Format beautifully with headers and bullet points
                    5. End with clear action items
                    6. Make it suitable for C-level executives
                    
                    Generate the report in markdown format:
                    """
                    
                    content = types.Content(role="user", parts=[types.Part(text=prompt)])
                    events = list(runner.run(
                        user_id="streamlit_user",
                        session_id=session.id,
                        new_message=content
                    ))
                    
                    if events:
                        last_event = events[-1]
                        response = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                        st.session_state.generated_report = response
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Display and download report
        if 'generated_report' in st.session_state:
            st.divider()
            st.markdown("### 📋 Your Report")
            
            with st.container():
                st.markdown(st.session_state.generated_report)
            
            st.divider()
            
            # Download options
            dl_cols = st.columns(3)
            
            with dl_cols[0]:
                st.download_button(
                    "📄 Download Markdown",
                    st.session_state.generated_report,
                    file_name=f"dq_report_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            with dl_cols[1]:
                # Simple HTML conversion
                html_report = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{report_title}</title>
                    <style>
                        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
                        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                        h2 {{ color: #34495e; margin-top: 30px; }}
                        ul {{ padding-left: 20px; }}
                        .footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 0.9em; }}
                    </style>
                </head>
                <body>
                    {st.session_state.generated_report.replace('# ', '<h1>').replace('## ', '<h2>').replace('### ', '<h3>')}
                    <div class="footer">Generated by Data Quality Management System | {datetime.now().strftime('%Y-%m-%d')}</div>
                </body>
                </html>
                """
                
                st.download_button(
                    "🌐 Download HTML",
                    html_report,
                    file_name=f"dq_report_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True
                )
            
            with dl_cols[2]:
                st.download_button(
                    "📝 Download Text",
                    st.session_state.generated_report,
                    file_name=f"dq_report_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            if st.button("🔄 Generate New Report", use_container_width=True):
                del st.session_state.generated_report
                st.rerun()
    
elif active_tab == "⚙️ Advanced Settings":
    with st.container():
        st.markdown("Configure system-level parameters and agent behaviors")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("🧠 Knowledge Bank", expanded=True):
                st.info("Manage the knowledge base used by agents for context.")
                st.text_input("Vector Store Path", "data/vector_store", disabled=True)
                st.slider("Retrieval Threshold", 0.0, 1.0, 0.7, disabled=True)
                st.button("Rebuild Index", disabled=True)
        
        with col2:
            with st.expander("🤖 Model Configuration", expanded=True):
                st.info("Fine-tune model parameters for specific agents.")
                st.selectbox("Default Model", ["gemini-1.5-pro", "gemini-1.5-flash"], index=0, disabled=True)
                st.slider("Temperature", 0.0, 1.0, 0.2, disabled=True)
                st.number_input("Max Output Tokens", value=8192, disabled=True)

        with st.expander("⚡ System Limits", expanded=False):
            st.number_input("Rate Limit (RPM)", value=60, disabled=True)
            st.number_input("Max Concurrent Sessions", value=5, disabled=True)

# Footer
st.divider()
with st.container():
    col_foot1, col_foot2, col_foot3 = st.columns([1, 2, 1])
    with col_foot2:
        st.markdown(
            f"""
            <div style='text-align: center; color: #666;'>
                <small>Built with Google ADK Multi-Agent Framework | {get_organization_name()} &copy; {get_copyright_year()}</small><br>
                <small>Version 2.0.0 (Professional Edition)</small>
            </div>
            """,
            unsafe_allow_html=True
        )
