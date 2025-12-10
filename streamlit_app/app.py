import streamlit as st
import os
import sys
from dotenv import load_dotenv

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

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

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    st.session_state.dataset_id = os.getenv("BQ_DATASET_ID", "")

# Sidebar for settings
with st.sidebar:
    st.title("⚙️ Settings")
    
    # GCP Configuration
    st.subheader("GCP Configuration")
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
    
    # Model Selection
    st.subheader("Model Configuration")
    global_model = st.selectbox(
        "Global Model",
        options=["gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro"],
        index=0,
        help="Default model for all agents"
    )
    
    st.divider()
    st.info("💡 Configure per-agent models in Settings tab")
    
    # Connection Test
    st.divider()
    st.subheader("Connection Test")
    
    if st.button("🔌 Test GCP Connection"):
        with st.spinner("Testing connections..."):
            try:
                from google.cloud import bigquery
                
                # Test BigQuery connection
                client = bigquery.Client(project=project_id)
                
                # List tables in dataset
                dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
                tables = list(client.list_tables(dataset_ref))
                
                st.success(f"✅ Connected to BigQuery!")
                st.success(f"✅ Project: {project_id}")
                st.success(f"✅ Dataset: {dataset_id}")
                st.success(f"✅ Tables found: {len(tables)}")
                
                if tables:
                    st.write("Tables:")
                    for table in tables:
                        st.write(f"  - {table.table_id}")
                        
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")

# Main app header
st.title("🔍 Data Quality Management System")
st.markdown("**Autonomous DQ Detection, Treatment & Remediation for BaNCS Data**")

# Create tabs for agents
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Identifier", 
    "💊 Treatment", 
    "🔧 Remediator",
    "📊 Metrics",
    "⚙️ Advanced Settings"
])

with tab1:
    st.header("🔍 Identifier Agent")
    st.markdown("Detect data quality issues and generate SQL-based DQ rules for BaNCS tables")
    
    # Table selection
    st.subheader("1. Select Tables")
    
    # Get available tables
    selected_tables = []
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project_id)
        dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
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
    
    col1, col2 = st.columns(2)
    with col1:
        include_schema = st.checkbox("Include Schema Analysis", value=True)
        include_dataplex = st.checkbox("Trigger Dataplex Scans", value=True, help="Auto-enabled: Dataplex scans provide profiling data")
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
        max_value=30,
        value=10,
        help="How many DQ rules should the agent generate? (Includes cross-week rules)"
    )
    
    st.divider()
    
    # Generate button
    st.subheader("3. Generate DQ Rules")
    
    if st.button("🚀 Generate DQ Rules", type="primary", disabled=not selected_tables):
        if not selected_tables:
            st.warning("⚠️ Please select at least one table")
        else:
            with st.spinner("🔍 Identifier Agent is analyzing tables..."):
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
                    
                    for table_name in selected_tables:
                        st.write(f"**Analyzing: {table_name}**")
                        
                        # Build prompt
                        prompt = f"""
                        **COMPREHENSIVE DQ ANALYSIS REQUEST**
                        
                        Dataset: '{dataset_id}'
                        Selected Tables: {', '.join(selected_tables)}
                        Current Table: '{table_name}'
                        
                        **MANDATORY STEPS:**
                        1. Load pre-existing rules from Collibra/Ataccama using load_preexisting_rules()
                        2. Get all week tables using get_all_week_tables()
                        3. Trigger Dataplex scan for '{table_name}' to get profiling data
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
                            user_id="strea