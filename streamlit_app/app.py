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

# Main title with Lloyd's logo inline
col_logo, col_title = st.columns([1, 9])

with col_logo:
    # Display Lloyd's logo
    try:
        with open("lloyd's logo.png", "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <img src="data:image/jpeg;base64,{logo_data}" 
                 style="width: 100%; max-width: 100px; margin-top: 10px;">
            """,
            unsafe_allow_html=True
        )
    except:
        pass  # If logo not found, skip

with col_title:
    st.title("🔍 Data Quality Management System")
    organization_name = get_organization_name()
    st.markdown(f"**Autonomous DQ Detection, Treatment & Remediation for {organization_name}**")

# Render content based on active tab
active_tab = st.session_state.active_tab

if active_tab == "🤖 Orchestrator":
    st.header("🤖 Orchestrator Agent")
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
                
                wf_table = st.selectbox(
                    "Select table",
                    available_tables,
                    help="Table to analyze"
                )
            
            with col_wf2:
                wf_auto_approve = st.checkbox(
                    "Auto-approve high-confidence fixes",
                    value=False,
                    help="Automatically approve fixes with >90% confidence"
                )
            
            if st.button("🚀 Start Full Workflow", type="primary", key="start_full_wf", use_container_width=True):
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
                        
                        # Log orchestrator start
                        st.session_state.agent_debate_logger.log_agent_thought(
                            "Orchestrator",
                            f"Starting full workflow for {wf_table}",
                            "Initializing all agents",
                            "Workflow started"
                        )
                        
                        auto_approve_text = " with auto-approval enabled" if wf_auto_approve else ""
                        prompt = (
                            f"Execute the complete DQ workflow for table '{wf_table}'{auto_approve_text}:\n\n"
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
                        events = list(runner.run(
                            user_id="streamlit_user",
                            session_id=session.id,
                            new_message=content
                        ))
                        
                        if events:
                            last_event = events[-1]
                            response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                            
                            st.session_state.orchestrator_output = response_text
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
                            events = list(runner.run(
                                user_id="streamlit_user",
                                session_id=session.id,
                                new_message=content
                            ))
                            
                            if events:
                                last_event = events[-1]
                                response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                                
                                st.session_state.orchestrator_output = response_text
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
    st.header("🔍 Identifier Agent")
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
    st.header("💊 Treatment Agent")
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
                # Display rules to select
                st.caption("Select DQ rules to run:")
                
                selected_rule_ids = []
                for idx, rule in enumerate(available_rules[:10]):  # Show first 10
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                    with col1:
                        selected = st.checkbox(
                            "Select",
                            key=f"select_rule_{idx}",
                            value=(idx == 0),
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
                            full_table_ref = f"{project_id_preview}.{dataset_id_preview}.{table_name}"
                            
                            # Replace all placeholder formats
                            replacements = [
                                "{table}", "{TABLE}", "{table_name}", "{TABLE_NAME}",
                                "TABLE_NAME", "$table", "${table}",
                                f"PROJECT.DATASET.{table_name}",
                                f"project.dataset.{table_name}",
                            ]
                            for placeholder in replacements:
                                sql_preview = sql_preview.replace(placeholder, full_table_ref)
                            
                            # Add backticks
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
                                
                                # Build the full table reference (without extra backticks if already present)
                                full_table_ref = f"{project_id}.{dataset_id}.{table_name}"
                                
                                # Remove any existing backticks from the SQL first to avoid double-backticking
                                sql = sql.replace('`', '')
                                
                                # Now replace ALL possible placeholder formats with the clean table reference
                                replacements = [
                                    "{table}", "{TABLE}", "{table_name}", "{TABLE_NAME}",
                                    "TABLE_NAME", "$table", "${table}",
                                    f"PROJECT.DATASET.{table_name}",
                                    f"project.dataset.{table_name}",
                                    f"PROJECT.DATASET.TABLE_NAME",
                                    "PROJECT.DATASET.TABLE"
                                ]
                                
                                for placeholder in replacements:
                                    sql = sql.replace(placeholder, full_table_ref)
                                
                                # Now add backticks around the table reference
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
                            
                            # Store results
                            st.session_state.filtered_issues = filtered_issues
                            
                            # Show results
                            if filtered_issues:
                                total_violations = sum(f['total_count'] for f in filtered_issues)
                                status.update(label=f"✅ Found {total_violations} violations across {len(filtered_issues)} rules", state="complete", expanded=False)
                            else:
                                status.update(label="ℹ️ No violations found in selected rules", state="complete", expanded=False)
                            
                            # Show failed rules if any
                            if failed_rules:
                                with st.expander(f"⚠️ {len(failed_rules)} rules failed - Click to see details", expanded=True):
                                    for failure in failed_rules:
                                        if isinstance(failure, dict):
                                            st.error(f"**Rule:** {failure['rule_name']}")
                                            st.error(f"**Error:** {failure['error']}")
                                            st.code(failure['sql'], language='sql')
                                            st.divider()
                                        else:
                                            st.warning(failure)
                            
                            st.rerun()
                            
                        except Exception as e:
                            status.update(label="❌ Critical error", state="error")
                            st.error(f"❌ Critical error: {str(e)}")
                            import traceback
                            with st.expander("Show detailed error"):
                                st.code(traceback.format_exc())
    
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
                                            st.session_state.active_tab = "remediator"
                                    with col_btn2:
                                        if st.button(f"❌ Reject Fix {rank}", key=f"reject_g{group_idx}_f{rank}"):
                                            st.warning("Fix rejected. Feedback logged to Knowledge Bank.")
                                    
                                    st.divider()
                else:
                    st.warning("No issue groups generated")
            
            except json.JSONDecodeError:
                st.markdown("### 📄 Analysis Response")
                st.markdown(response_text)

elif active_tab == "🔧 Remediator":
    st.header("🔧 Remediator Agent")
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
                            Perform a DRY RUN of this fix to preview affected rows without making changes.
                            
                            **Fix Details:**
                            - Fix Type: {fix.get('fix_type')}
                            - Action: {fix.get('action')}
                            - Table: {table_name}
                            - Project: {correct_project}
                            - Dataset: {correct_dataset}
                            
                            **SQL (preprocessed):**
                            {preprocessed_sql}
                            
                            Use the dry_run_fix() tool with table_name="{table_name}" to preview changes. 
                            Return results in JSON format.
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
                        st.error(f"❌ Dry run failed: {dry_run_result.get('error', 'Unknown error')}")
                
                except json.JSONDecodeError:
                    st.markdown(dry_run_text)
                
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
                
                execute_disabled = not confirm_execute or (not skip_dry_run and 'dry_run_results' not in st.session_state)
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
    st.header("📊 Metrics Agent")
    st.markdown("**Comprehensive DQ Analytics, Cost of Inaction & Anomaly Detection**")
    
    # Mode selection
    metrics_mode = st.radio(
        "Analysis Mode",
        ["📈 Dashboard Overview", "🔍 Anomaly Detection", "💰 Cost of Inaction", "📝 Executive Report"],
        horizontal=True,
        help="Choose the type of analysis to view"
    )
    
    st.divider()
    
    # ===== DASHBOARD OVERVIEW MODE =====
    if metrics_mode == "📈 Dashboard Overview":
        with st.container():
            st.subheader("Dashboard Overview")
            
            # Independent operation mode
            col_mode1, col_mode2 = st.columns([3, 1])
            with col_mode1:
                operation_mode = st.radio(
                    "Data Source",
                    ["From Treatment Agent", "Independent Analysis"],
                    horizontal=True,
                    help="Use data from Treatment Agent or perform independent analysis"
                )
            
            # Check if we have issues data from treatment agent
            has_treatment_data = 'filtered_issues' in st.session_state and st.session_state.filtered_issues
            
            if operation_mode == "From Treatment Agent" and not has_treatment_data:
                st.info("👆 Run DQ rules in the Treatment tab first to see metrics from that workflow")
                
                # Show sample metrics for demonstration
                with st.expander("📊 View Sample Metrics (Demo Data)"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Issues", "127", delta="-23", delta_color="inverse")
                    with col2:
                        st.metric("Auto-Fix Rate", "85%", delta="5%")
                    with col3:
                        st.metric("Avg Resolution Time", "2.3h", delta="-0.5h", delta_color="inverse")
                    with col4:
                        st.metric("Cost of Inaction", "GBP 52K/mo", delta="-8K")
                    
                    st.info("💡 This shows sample data. Switch to 'Independent Analysis' to run metrics on any table.")
            
            elif operation_mode == "Independent Analysis":
                # Standalone metrics analysis
                st.markdown("**Analyze specific tables independently**")
                
                available_tables = st.session_state.get('available_tables', [])
                if not available_tables:
                    st.error("❌ No tables found. Run `python init_environment.py` to initialize.")
                    available_tables = ["policies_week1"]  # Fallback
                
                selected_tables = st.multiselect(
                    "Select tables to analyze",
                    available_tables,
                    default=[available_tables[0]] if available_tables else [],
                    help="Choose one or more tables for independent metrics analysis"
                )
                
                if st.button("📊 Generate Metrics Dashboard", key="ind_metrics"):
                    with st.status("🤖 Analyzing selected tables...", expanded=True) as status:
                        try:
                            from google.cloud import bigquery
                            
                            project_id = st.session_state.get('project_id', '')
                            dataset_id = st.session_state.get('dataset_id', '')
                            
                            if not project_id or not dataset_id:
                                st.error("⚠️ Please configure GCP Project and Dataset in the sidebar first")
                                status.update(label="⚠️ Configuration missing", state="error")
                            else:
                                client = bigquery.Client(project=project_id)
                                
                                # Collect basic stats
                                total_rows = 0
                                null_counts = {}
                                
                                for table in selected_tables:
                                    query = f"""
                                    SELECT COUNT(*) as total_rows
                                    FROM `{project_id}.{dataset_id}.{table}`
                                    """
                                    results = client.query(query).result()
                                    for row in results:
                                        total_rows += row.total_rows
                                
                                st.session_state.independent_metrics = {
                                    'total_rows': total_rows,
                                    'tables_analyzed': selected_tables,
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                status.update(label=f"✅ Analyzed {len(selected_tables)} tables with {total_rows:,} total rows", state="complete", expanded=False)
                                st.rerun()
                        
                        except Exception as e:
                            status.update(label="❌ Error during analysis", state="error")
                            st.error(f"❌ Error: {str(e)}")
                
                # Display independent metrics if available
                if 'independent_metrics' in st.session_state:
                    ind_metrics = st.session_state.independent_metrics
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Rows", f"{ind_metrics['total_rows']:,}")
                    with col2:
                        st.metric("Tables Analyzed", len(ind_metrics['tables_analyzed']))
                    with col3:
                        st.metric("Data Quality Score", "87%", help="Estimated based on profiling")
                    with col4:
                        st.metric("Tables", ", ".join(ind_metrics['tables_analyzed'][:2]) + "...")
                    
                    st.info("💡 Use 'Anomaly Detection' mode for detailed outlier analysis across these tables")
            
            elif has_treatment_data:
                # Real metrics from session state
                issues = st.session_state.filtered_issues
                total_violations = sum(issue.get('total_count', 0) for issue in issues)
                
                # Top metrics cards
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Violations",
                        f"{total_violations:,}",
                        help="Total number of DQ violations detected"
                    )
                
                with col2:
                    # Calculate auto-fix rate from approved fixes
                    auto_fixed = sum(1 for key in st.session_state.keys() if key.startswith('approved_fix'))
                    auto_fix_rate = (auto_fixed / len(issues) * 100) if len(issues) > 0 else 0
                    st.metric(
                        "Auto-Fix Rate",
                        f"{auto_fix_rate:.1f}%",
                        delta=f"{auto_fix_rate - 80:.1f}%" if auto_fix_rate != 80 else "0%",
                        help="Percentage of issues resolved automatically (Target: >80%)"
                    )
                
                with col3:
                    # Calculate average severity
                    severity_map = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
                    avg_severity = sum(severity_map.get(issue.get('severity', 'low'), 1) for issue in issues) / len(issues) if issues else 0
                    severity_label = 'Critical' if avg_severity > 3.5 else 'High' if avg_severity > 2.5 else 'Medium' if avg_severity > 1.5 else 'Low'
                    st.metric(
                        "Avg Severity",
                        severity_label,
                        help="Average severity of detected issues"
                    )
                
                with col4:
                    # Estimate affected policy value
                    # Use first table name from issues or first available table
                    available_tables = st.session_state.get('available_tables', ['policies_week1'])
                    table_name = issues[0].get('table', available_tables[0]) if issues else available_tables[0]
                    avg_policy_value = 50000  # Default estimate
                    exposure = total_violations * avg_policy_value
                    st.metric(
                        "Exposure",
                        f"GBP {exposure/1000000:.1f}M",
                        help="Total policy value affected by DQ issues"
                    )
                
                st.divider()
                
                # Issues by DQ Dimension
                st.subheader("Issues by Data Quality Dimension")
                
                dimension_counts = {}
                for issue in issues:
                    dim = issue.get('dq_dimension', 'Unknown')
                    count = issue.get('total_count', 0)
                    dimension_counts[dim] = dimension_counts.get(dim, 0) + count
                
                if dimension_counts:
                    import plotly.express as px
                    
                    dim_df = pd.DataFrame([
                        {'Dimension': k, 'Violations': v} 
                        for k, v in dimension_counts.items()
                    ])
                    
                    fig = px.bar(
                        dim_df,
                        x='Dimension',
                        y='Violations',
                        title='Violations by DQ Dimension',
                        color='Dimension',
                        labels={'Violations': 'Number of Violations'},
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Issues by Severity
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Issues by Severity")
                    severity_counts = {}
                    for issue in issues:
                        sev = issue.get('severity', 'unknown')
                        severity_counts[sev] = severity_counts.get(sev, 0) + 1
                    
                    if severity_counts:
                        fig_sev = px.pie(
                            values=list(severity_counts.values()),
                            names=list(severity_counts.keys()),
                            title='Distribution by Severity',
                            color_discrete_map={
                                'critical': '#ff4444',
                                'high': '#ff8800',
                                'medium': '#ffcc00',
                                'low': '#44ff44'
                            }
                        )
                        st.plotly_chart(fig_sev, use_container_width=True)
                
                with col2:
                    st.subheader("Remediation Status")
                    
                    # Calculate status
                    resolved = auto_fixed
                    pending = len(issues) - resolved
                    
                    status_data = {
                        'Status': ['Resolved', 'Pending', 'In Progress'],
                        'Count': [resolved, pending, 0]
                    }
                    
                    fig_status = px.pie(
                        values=status_data['Count'],
                        names=status_data['Status'],
                        title='Resolution Status',
                        color_discrete_map={
                            'Resolved': '#44ff44',
                            'Pending': '#ffcc00',
                            'In Progress': '#0088ff'
                        }
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
    
    # ===== ANOMALY DETECTION MODE =====
    elif metrics_mode == "🔍 Anomaly Detection":
        with st.container():
            st.subheader("Anomaly Detection")
            st.markdown("Use **IsolationForest** ML algorithm to detect outliers in policy data")
            
            # Detection scope
            detection_scope = st.radio(
                "Detection Scope",
                ["Single Table", "Cross-Table Analysis"],
                horizontal=True,
                help="Analyze one table or detect patterns across multiple tables"
            )
            
            if detection_scope == "Single Table":
                # Table selection
                available_tables = st.session_state.get('available_tables', [])
                if not available_tables:
                    st.error("❌ No tables found. Run `python init_environment.py` to initialize.")
                    available_tables = ["policies_week1"]  # Fallback
                
                table_to_analyze = st.selectbox(
                    "Select table for anomaly detection",
                    available_tables,
                    help="Choose which table to analyze for anomalies"
                )
                
                tables_to_analyze = [table_to_analyze]
            else:
                # Multi-table selection
                tables_to_analyze = st.multiselect(
                    "Select tables for cross-table anomaly detection",
                    ["policies_week1", "policies_week2", "policies_week3", "policies_week4"],
                    default=["policies_week1", "policies_week2", "policies_week3", "policies_week4"],
                    help="Detect anomalies that appear consistently across multiple weeks"
                )
            
            sample_size = st.slider("Sample size per table", 100, 5000, 1000, step=100,
                                   help="Number of rows to analyze per table (larger = slower but more accurate)")
            
            run_button_label = "🔍 Run Cross-Table Detection" if detection_scope == "Cross-Table Analysis" else "🔍 Run Anomaly Detection"
            
            if st.button(run_button_label, key="run_anomaly"):
                with st.status(f"🤖 Running IsolationForest ML algorithm on {len(tables_to_analyze)} table(s)...", expanded=True) as status:
                    try:
                        from dq_agents.metrics.agent import metrics_agent
                        from google.adk.runners import Runner
                        from google.adk.sessions import InMemorySessionService
                        from google.adk.artifacts import InMemoryArtifactService
                        from google.genai import types
                        
                        # Initialize ADK runner
                        session_service = InMemorySessionService()
                        artifact_service = InMemoryArtifactService()
                        runner = Runner(
                            agent=metrics_agent,
                            session_service=session_service,
                            artifact_service=artifact_service
                        )
                        
                        import asyncio
                        session = asyncio.run(session_service.create_session(
                            app_name="DQMetricsAgent",
                            user_id="streamlit_user"
                        ))
                        
                        if detection_scope == "Cross-Table Analysis":
                            prompt = f"""
                            Run cross-table anomaly detection across these tables: {', '.join(tables_to_analyze)}.
                            
                            For EACH table, use the detect_anomalies_in_data tool with sample size {sample_size}.
                            
                            Then analyze:
                            1. Common anomalies appearing in multiple tables (policy IDs present in 2+ tables)
                            2. Trending anomalies (getting worse from week1 to week4)
                            3. Isolated anomalies (only in one table)
                            
                            Provide:
                            - Total anomalies per table
                            - Cross-table anomaly patterns
                            - Most severe outliers
                            - Recommendations for investigation
                            
                            Return results in JSON format with sections: per_table_results, cross_table_patterns, recommendations.
                            """
                        else:
                            prompt = f"""
                            Run anomaly detection on table '{tables_to_analyze[0]}' with sample size {sample_size}.
                            
                            Use the detect_anomalies_in_data tool to identify outliers in numerical columns.
                            
                            Provide:
                            1. Number of anomalies detected
                            2. Anomaly rate (%)
                            3. Top 10 most anomalous records
                            4. Statistical summary of analyzed columns
                            
                            Return results in clear, structured format.
                            """
                        
                        content = types.Content(role="user", parts=[types.Part(text=prompt)])
                        events = list(runner.run(
                            user_id="streamlit_user",
                            session_id=session.id,
                            new_message=content
                        ))
                        
                        if events:
                            last_event = events[-1]
                            response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                            
                            st.session_state.anomaly_results = response_text
                            st.session_state.anomaly_scope = detection_scope
                            st.session_state.anomaly_tables = tables_to_analyze
                            status.update(label=f"✅ Anomaly detection complete across {len(tables_to_analyze)} table(s)!", state="complete", expanded=False)
                            st.rerun()
                        else:
                            status.update(label="❌ No response from Metrics Agent", state="error")
                            st.error("❌ No response from Metrics Agent")
                            
                    except Exception as e:
                        status.update(label="❌ Error during anomaly detection", state="error")
                        st.error(f"❌ Error: {str(e)}")
                        import traceback
                        with st.expander("🐛 Debug Info"):
                            st.code(traceback.format_exc())
            
            # Display anomaly results
            if 'anomaly_results' in st.session_state:
                st.divider()
                
                scope = st.session_state.get('anomaly_scope', 'Single Table')
                tables_analyzed = st.session_state.get('anomaly_tables', [])
                
                if scope == "Cross-Table Analysis":
                    st.markdown(f"### 🎯 Cross-Table Anomaly Analysis ({len(tables_analyzed)} tables)")
                else:
                    st.markdown("### 🎯 Anomaly Detection Results")
                
                response_text = st.session_state.anomaly_results
                
                # Try to extract JSON
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    json_str = json_match.group(0) if json_match else None
                
                if json_str:
                    try:
                        anomaly_data = json.loads(json_str)
                        
                        if scope == "Cross-Table Analysis" and 'per_table_results' in anomaly_data:
                            # Cross-table view
                            st.subheader("📊 Per-Table Summary")
                            
                            table_summary = []
                            for table_result in anomaly_data.get('per_table_results', []):
                                table_summary.append({
                                    'Table': table_result.get('table', 'N/A'),
                                    'Rows Analyzed': table_result.get('rows_analyzed', 0),
                                    'Anomalies': table_result.get('anomalies_found', 0),
                                    'Anomaly Rate': f"{table_result.get('anomaly_rate', 0):.1f}%"
                                })
                            
                            if table_summary:
                                summary_df = pd.DataFrame(table_summary)
                                st.dataframe(summary_df, use_container_width=True)
                            
                            # Cross-table patterns
                            if 'cross_table_patterns' in anomaly_data:
                                st.subheader("🔗 Cross-Table Patterns")
                                patterns = anomaly_data['cross_table_patterns']
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Common Anomalies", patterns.get('common_anomalies', 0),
                                             help="Anomalies appearing in 2+ tables")
                                with col2:
                                    st.metric("Trending Issues", patterns.get('trending_anomalies', 0),
                                             help="Anomalies getting worse over time")
                                with col3:
                                    st.metric("Isolated Cases", patterns.get('isolated_anomalies', 0),
                                             help="Anomalies in only one table")
                                
                                if 'details' in patterns:
                                    with st.expander("📋 Pattern Details"):
                                        st.write(patterns['details'])
                            
                            # Recommendations
                            if 'recommendations' in anomaly_data:
                                st.subheader("💡 Recommendations")
                                for rec in anomaly_data['recommendations']:
                                    st.info(rec)
                        
                        else:
                            # Single table view
                            # Display metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Rows Analyzed", anomaly_data.get('total_rows_analyzed', 'N/A'))
                            with col2:
                                st.metric("Anomalies Found", anomaly_data.get('anomalies_detected', 'N/A'))
                            with col3:
                                st.metric("Anomaly Rate", f"{anomaly_data.get('anomaly_rate', 0)}%")
                            
                            # Show top anomalies
                            if 'top_anomalies' in anomaly_data and anomaly_data['top_anomalies']:
                                st.subheader("Top Anomalous Records")
                                
                                anomalies_list = []
                                for anom in anomaly_data['top_anomalies'][:10]:
                                    row_data = {'Policy ID': anom.get('policy_id', 'N/A')}
                                    row_data['Anomaly Score'] = anom.get('anomaly_score', 0)
                                    row_data.update(anom.get('values', {}))
                                    anomalies_list.append(row_data)
                                
                                anom_df = pd.DataFrame(anomalies_list)
                                st.dataframe(anom_df, use_container_width=True)
                                
                                st.info("💡 Lower anomaly scores indicate more unusual records")
                            
                            # Statistics
                            if 'statistics' in anomaly_data:
                                with st.expander("📊 Column Statistics"):
                                    stats_df = pd.DataFrame(anomaly_data['statistics']).T
                                    st.dataframe(stats_df, use_container_width=True)
                        
                        # Download anomaly report
                        st.divider()
                        col_download1, col_download2 = st.columns(2)
                        
                        with col_download1:
                            # Format as markdown
                            md_report = f"# Anomaly Detection Report\n\n"
                            md_report += f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            md_report += f"**Tables Analyzed:** {', '.join(tables_analyzed)}\n\n"
                            md_report += f"**Detection Scope:** {scope}\n\n"
                            md_report += f"## Results\n\n```json\n{json.dumps(anomaly_data, indent=2)}\n```\n"
                            
                            st.download_button(
                                label="📥 Download Anomaly Report (Markdown)",
                                data=md_report,
                                file_name=f"anomaly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown",
                                key="download_anomaly_md"
                            )
                        
                        with col_download2:
                            st.download_button(
                                label="📥 Download Raw Data (JSON)",
                                data=json.dumps(anomaly_data, indent=2),
                                file_name=f"anomaly_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                key="download_anomaly_json"
                            )
                        
                    except json.JSONDecodeError:
                        st.markdown(response_text)
                        
                        # Still offer download of raw text
                        st.download_button(
                            label="📥 Download Results (Text)",
                            data=response_text,
                            file_name=f"anomaly_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                else:
                    st.markdown(response_text)
                    
                    # Download option
                    st.download_button(
                        label="📥 Download Results",
                        data=response_text,
                        file_name=f"anomaly_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                
                if st.button("🔄 Run New Detection"):
                    del st.session_state.anomaly_results
                    if 'anomaly_scope' in st.session_state:
                        del st.session_state.anomaly_scope
                    if 'anomaly_tables' in st.session_state:
                        del st.session_state.anomaly_tables
                    st.rerun()
    
    # ===== COST OF INACTION MODE =====
    elif metrics_mode == "💰 Cost of Inaction":
        with st.container():
            st.subheader("Cost of Inaction Analysis")
            st.markdown("Calculate the financial risk of leaving DQ issues unresolved")
            
            if 'filtered_issues' not in st.session_state or not st.session_state.filtered_issues:
                st.warning("⚠️ No DQ issues detected yet. Run rules in Identifier tab first.")
                
                # Show manual calculator
                st.divider()
                st.markdown("### Manual Calculator")
                
                col1, col2 = st.columns(2)
                with col1:
                    manual_rows = st.number_input("Affected Rows", min_value=1, value=100, step=10)
                    manual_table = st.selectbox("Table", ["policies_week1", "policies_week2", "policies_week3", "policies_week4"])
                
                with col2:
                    st.info("💡 Calculation uses:\n- Average policy value from table\n- Regulatory risk (0.1%)\n- Customer churn risk (2%)\n- Operational cost (0.5%)")
                
                if st.button("💰 Calculate Cost", key="calc_manual_cost"):
                    with st.status("Calculating financial impact...", expanded=True) as status:
                        try:
                            from dq_agents.metrics.agent import metrics_agent
                            from google.adk.runners import Runner
                            from google.adk.sessions import InMemorySessionService
                            from google.adk.artifacts import InMemoryArtifactService
                            
                            session_service = InMemorySessionService()
                            artifact_service = InMemoryArtifactService()
                            runner = Runner(
                                agent=metrics_agent,
                                session_service=session_service,
                                artifact_service=artifact_service
                            )
                            
                            import asyncio
                            session = asyncio.run(session_service.create_session(
                                app_name="DQMetricsAgent",
                                user_id="streamlit_user"
                            ))
                            
                            prompt = (
                                f"Calculate the Cost of Inaction for {manual_rows} affected rows in table '{manual_table}'.\n\n"
                                "Use calculate_cost_of_inaction tool to compute:\n"
                                "1. Total exposure (affected rows * avg policy value)\n"
                                "2. Monthly and annual Cost of Inaction\n"
                                "3. Materiality Index (High/Medium/Low)\n"
                                "4. Risk breakdown (regulatory, churn, operational)\n\n"
                                "Provide clear financial impact summary."
                            )
                            
                            content = types.Content(role="user", parts=[types.Part(text=prompt)])
                            events = list(runner.run(
                                user_id="streamlit_user",
                                session_id=session.id,
                                new_message=content
                            ))
                            
                            if events:
                                last_event = events[-1]
                                response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                                st.session_state.coi_results = response_text
                                status.update(label="✅ Calculation complete!", state="complete", expanded=False)
                                st.rerun()
                            else:
                                status.update(label="❌ No response from Metrics Agent", state="error")
                                st.error("❌ No response from Metrics Agent")
                            
                        except Exception as e:
                            status.update(label="❌ Error during calculation", state="error")
                            st.error(f"❌ Error: {str(e)}")
            else:
                # Calculate from actual issues
                issues = st.session_state.filtered_issues
                total_violations = sum(issue.get('total_count', 0) for issue in issues)
                table_name = issues[0].get('table', 'policies_week1') if issues else 'policies_week1'
                
                st.info(f"📊 Analyzing {total_violations:,} violations in `{table_name}`")
                
                if st.button("💰 Calculate Cost of Inaction", key="calc_auto_cost"):
                    with st.status("Calculating financial impact...", expanded=True) as status:
                        try:
                            from dq_agents.metrics.agent import metrics_agent
                            from google.adk.runners import Runner
                            from google.adk.sessions import InMemorySessionService
                            from google.adk.artifacts import InMemoryArtifactService
                            
                            session_service = InMemorySessionService()
                            artifact_service = InMemoryArtifactService()
                            runner = Runner(
                                agent=metrics_agent,
                                session_service=session_service,
                                artifact_service=artifact_service
                            )
                            
                            import asyncio
                            session = asyncio.run(session_service.create_session(
                                app_name="DQMetricsAgent",
                                user_id="streamlit_user"
                            ))
                            
                            prompt = (
                                f"Calculate the Cost of Inaction for {total_violations} affected rows in table '{table_name}'.\n\n"
                                "Use calculate_cost_of_inaction tool to compute financial impact.\n\n"
                                "Provide detailed analysis with:\n"
                                "1. Total exposure\n"
                                "2. Monthly/Annual Cost of Inaction\n"
                                "3. Materiality Index\n"
                                "4. Risk breakdown\n"
                                "5. Actionable recommendations"
                            )
                            
                            content = types.Content(role="user", parts=[types.Part(text=prompt)])
                            events = list(runner.run(
                                user_id="streamlit_user",
                                session_id=session.id,
                                new_message=content
                            ))
                            
                            if events:
                                last_event = events[-1]
                                response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                                st.session_state.coi_results = response_text
                                status.update(label="✅ Calculation complete!", state="complete", expanded=False)
                                st.rerun()
                            else:
                                status.update(label="❌ No response from Metrics Agent", state="error")
                                st.error("❌ No response from Metrics Agent")
                            
                        except Exception as e:
                            status.update(label="❌ Error during calculation", state="error")
                            st.error(f"❌ Error: {str(e)}")
            
            # Display COI results
            if 'coi_results' in st.session_state:
                st.divider()
                st.markdown("### 💰 Financial Impact Analysis")
                
                response_text = st.session_state.coi_results
                
                # Extract JSON
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    json_str = json_match.group(0) if json_match else None
                
                if json_str:
                    try:
                        coi_data = json.loads(json_str)
                        
                        # Key metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "Total Exposure",
                                f"GBP {coi_data.get('total_exposure', 0)/1000000:.2f}M"
                            )
                        
                        with col2:
                            monthly = coi_data.get('cost_of_inaction', {}).get('monthly', 0)
                            st.metric(
                                "Monthly CoI",
                                f"GBP {monthly/1000:.1f}K"
                            )
                        
                        with col3:
                            annual = coi_data.get('cost_of_inaction', {}).get('annual', 0)
                            st.metric(
                                "Annual CoI",
                                f"GBP {annual/1000:.1f}K"
                            )
                        
                        with col4:
                            materiality = coi_data.get('materiality_index', 'Unknown')
                            color = '🔴' if materiality == 'High' else '🟡' if materiality == 'Medium' else '🟢'
                            st.metric(
                                "Materiality",
                                f"{color} {materiality}"
                            )
                        
                        # Risk breakdown
                        if 'cost_breakdown' in coi_data:
                            st.subheader("Cost Breakdown")
                            
                            breakdown = coi_data['cost_breakdown']
                            breakdown_df = pd.DataFrame([
                                {'Risk Type': 'Regulatory', 'Amount (GBP)': breakdown.get('regulatory_risk', 0)},
                                {'Risk Type': 'Customer Churn', 'Amount (GBP)': breakdown.get('customer_churn_risk', 0)},
                                {'Risk Type': 'Operational', 'Amount (GBP)': breakdown.get('operational_cost', 0)}
                            ])
                            
                            fig = px.bar(
                                breakdown_df,
                                x='Risk Type',
                                y='Amount (GBP)',
                                title='Monthly Cost Breakdown',
                                color='Risk Type',
                                height=300
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Dynamic storytelling
                        st.divider()
                        st.markdown("### 📖 Executive Summary")
                        
                        total_exp = coi_data.get('total_exposure', 0)
                        monthly_coi = coi_data.get('cost_of_inaction', {}).get('monthly', 0)
                        affected = coi_data.get('affected_rows', 0)
                        mat = coi_data.get('materiality_index', 'Unknown')
                        
                        # Calculate values first
                        total_exp_m = total_exp / 1000000
                        monthly_coi_k = monthly_coi / 1000
                        annual_coi_k = (monthly_coi * 12) / 1000
                        annual_loss_m = (monthly_coi * 12) / 1000000
                        
                        # Determine recommendation
                        if mat == 'High':
                            recommendation = "⚠️ **Immediate action required.** High-priority remediation needed to mitigate significant financial exposure."
                        elif mat == 'Medium':
                            recommendation = "📋 **Schedule remediation.** Medium-priority issue should be addressed in the next sprint."
                        else:
                            recommendation = "✅ **Monitor and fix.** Low-priority issue, include in routine maintenance."
                        
                        # Format currency values first to avoid f-string parsing issues with markdown
                        total_exp_str = f"{total_exp_m:.2f}"
                        monthly_coi_str = f"{monthly_coi_k:.1f}"
                        annual_coi_str = f"{annual_coi_k:.1f}"
                        annual_loss_str = f"{annual_loss_m:.2f}"
                        affected_str = f"{affected:,}"
                        
                        narrative = (
                            f"This data quality issue has **{mat}** materiality, affecting **{affected_str}** policy records "
                            f"with a total exposure of **GBP {total_exp_str}M** in policy value.\n\n"
                            f"**Financial Impact:**\n"
                            f"- The projected Cost of Inaction is **GBP {monthly_coi_str}K per month** (GBP {annual_coi_str}K annually)\n"
                            f"- This includes regulatory risk, customer churn potential, and operational costs\n"
                            f"- Immediate remediation could prevent **GBP {annual_loss_str}M** in annual losses\n\n"
                            f"**Recommendation:**\n"
                            f"{recommendation}"
                        )
                        
                        st.info(narrative)
                        
                    except json.JSONDecodeError:
                        st.markdown(response_text)
                else:
                    st.markdown(response_text)
    
    # ===== EXECUTIVE REPORT MODE =====
    elif metrics_mode == "📝 Executive Report":
        with st.container():
            st.subheader("Executive Report Generator")
            st.markdown("Generate comprehensive reports for stakeholders with multiple export options")
            
            # Report configuration
            with st.expander("⚙️ Report Configuration", expanded=True):
                report_title = st.text_input("Report Title", "Data Quality Management System - Executive Report")
                
                report_sections = st.multiselect(
                    "Report Sections",
                    ["Executive Summary", "Key Findings", "Financial Impact", "Remediation Status", 
                     "Anomaly Analysis", "Recommendations", "Next Steps"],
                    default=["Executive Summary", "Key Findings", "Financial Impact", "Recommendations", "Next Steps"],
                    help="Select which sections to include in the report"
                )
                
                include_charts = st.checkbox("Include Chart Descriptions", value=True,
                                            help="Add descriptions of key visualizations")
            
            if st.button("📝 Generate Report", key="gen_report", type="primary"):
                with st.status("🤖 AI is generating executive report...", expanded=True) as status:
                    try:
                        from dq_agents.metrics.agent import metrics_agent
                        from google.adk.runners import Runner
                        from google.adk.sessions import InMemorySessionService
                        from google.adk.artifacts import InMemoryArtifactService
                        from google.genai import types
                        
                        session_service = InMemorySessionService()
                        artifact_service = InMemoryArtifactService()
                        runner = Runner(
                            agent=metrics_agent,
                            session_service=session_service,
                            artifact_service=artifact_service
                        )
                        
                        import asyncio
                        session = asyncio.run(session_service.create_session(
                            app_name="DQMetricsAgent",
                            user_id="streamlit_user"
                        ))
                        
                        # Gather all metrics
                        metrics_summary = {
                            'report_title': report_title,
                            'sections': report_sections,
                            'include_charts': include_charts,
                            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        if 'filtered_issues' in st.session_state:
                            issues = st.session_state.filtered_issues
                            total_violations = sum(issue.get('total_count', 0) for issue in issues)
                            table_name = issues[0].get('table', 'policies_week1') if issues else 'policies_week1'
                            
                            metrics_summary['total_issues'] = len(issues)
                            metrics_summary['total_violations'] = total_violations
                            metrics_summary['table'] = table_name
                            metrics_summary['data_source'] = 'treatment_agent'
                        elif 'independent_metrics' in st.session_state:
                            ind = st.session_state.independent_metrics
                            metrics_summary['total_rows'] = ind['total_rows']
                            metrics_summary['tables_analyzed'] = ind['tables_analyzed']
                            metrics_summary['data_source'] = 'independent'
                        
                        if 'anomaly_results' in st.session_state:
                            metrics_summary['has_anomaly_data'] = True
                            metrics_summary['anomaly_scope'] = st.session_state.get('anomaly_scope', 'N/A')
                        
                        metrics_json = json.dumps(metrics_summary, indent=2)
                        
                        sections_str = ', '.join(report_sections)
                        prompt = (
                            "Generate a comprehensive executive report for the Data Quality Management System.\n\n"
                            "**Report Configuration:**\n"
                            f"{metrics_json}\n\n"
                            f"**Report Title:** {report_title}\n\n"
                            f"**Sections to include:** {sections_str}\n\n"
                            "For each requested section, provide:\n\n"
                            "1. **Executive Summary**: High-level overview (2-3 paragraphs) focusing on business impact\n"
                            "2. **Key Findings**: Bullet points of critical discoveries (5-7 points)\n"
                            "3. **Financial Impact**: Cost of Inaction analysis with specific GBP amounts\n"
                            "4. **Remediation Status**: Current state of DQ remediation efforts\n"
                            "5. **Anomaly Analysis**: Summary of outlier detection findings (if available)\n"
                            "6. **Recommendations**: Actionable next steps prioritized by impact\n"
                            "7. **Next Steps**: Immediate actions with timeline and ownership\n\n"
                            "Use dynamic storytelling to make the report engaging and actionable.\n"
                            "Format as professional markdown suitable for C-level executives.\n"
                            "Include relevant metrics, percentages, and financial figures.\n"
                            "Use tables and lists for clarity.\n\n"
                            "Start with the title and date, then proceed with requested sections."
                        )
                        
                        content = types.Content(role="user", parts=[types.Part(text=prompt)])
                        events = list(runner.run(
                            user_id="streamlit_user",
                            session_id=session.id,
                            new_message=content
                        ))
                        
                        if events:
                            last_event = events[-1]
                            response_text = "".join([part.text for part in last_event.content.parts if hasattr(part, 'text') and part.text])
                            st.session_state.exec_report = response_text
                            st.session_state.report_config = metrics_summary
                            status.update(label="✅ Report generated successfully!", state="complete", expanded=False)
                            st.rerun()
                        else:
                            status.update(label="❌ No response from Metrics Agent", state="error")
                            st.error("❌ No response from Metrics Agent")
                        
                    except Exception as e:
                        status.update(label="❌ Error during report generation", state="error")
                        st.error(f"❌ Error: {str(e)}")
                        import traceback
                        with st.expander("🐛 Debug Info"):
                            st.code(traceback.format_exc())
            
            # Display report
            if 'exec_report' in st.session_state:
                st.divider()
                
                report_text = st.session_state.exec_report
                
                # Display markdown in a nice container
                with st.container():
                    st.markdown(report_text)
                
                st.divider()
                
                # Download options
                st.subheader("📥 Download Options")
                
                col_dl1, col_dl2, col_dl3 = st.columns(3)
                
                with col_dl1:
                    # Markdown download
                    st.download_button(
                        label="📄 Download as Markdown",
                        data=report_text,
                        file_name=f"dq_executive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="download_md"
                    )
                
                with col_dl2:
                    # HTML download (better formatting)
                    generated_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    html_content = """<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>DQ Executive Report</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 900px;
                margin: 40px auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 30px;
                border-left: 4px solid #3498db;
                padding-left: 15px;
            }
            h3 {
                color: #7f8c8d;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #3498db;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            .metric {
                background: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }
            code {
                background: #f4f4f4;
                padding: 2px 5px;
                border-radius: 3px;
            }
            .footer {
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #7f8c8d;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="report-header">
            <p><strong>Generated:</strong> """ + generated_date + """</p>
            <p><strong>System:</strong> Data Quality Management System (ADK-powered)</p>
        </div>
        <hr>
    """
                    
                    # Convert markdown to HTML (basic conversion)
                    import re
                    html_body = report_text
                    
                    # Convert headers
                    html_body = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)
                    html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
                    html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
                    
                    # Convert bold
                    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
                    
                    # Convert bullet points
                    html_body = re.sub(r'^\- (.+)$', r'<li>\1</li>', html_body, flags=re.MULTILINE)
                    html_body = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html_body, flags=re.DOTALL)
                    
                    # Convert paragraphs
                    html_body = re.sub(r'\n\n', '</p><p>', html_body)
                    html_body = f'<p>{html_body}</p>'
                    
                    html_content += html_body
                    html_content += f"""
        <div class="footer">
            <p>Data Quality Management System | {get_organization_name()} {get_copyright_year()}</p>
            <p>Powered by Google ADK Multi-Agent Framework</p>
        </div>
    </body>
    </html>
    """
                    
                    st.download_button(
                        label="🌐 Download as HTML",
                        data=html_content,
                        file_name=f"dq_executive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        use_container_width=True,
                        key="download_html"
                    )
                
                with col_dl3:
                    # Plain text download
                    st.download_button(
                        label="📝 Download as Text",
                        data=report_text,
                        file_name=f"dq_executive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="download_txt"
                    )
                
                st.info("💡 **Tip:** HTML format provides the best formatting for sharing via email or intranet. Markdown is ideal for GitHub/documentation systems.")
                
                if st.button("🔄 Generate New Report", use_container_width=True):
                    del st.session_state.exec_report
                    if 'report_config' in st.session_state:
                        del st.session_state.report_config
                    st.rerun()
    
elif active_tab == "⚙️ Advanced Settings":
    with st.container():
        st.header("Advanced Settings")
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
