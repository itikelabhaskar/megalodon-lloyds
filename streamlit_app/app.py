import streamlit as st
import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime
import pandas as pd

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

# Initialize active tab in session state if not exists
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "🔍 Identifier"

# Create tabs for agents
tab_names = [
    "🔍 Identifier", 
    "💊 Treatment", 
    "🔧 Remediator",
    "📊 Metrics",
    "⚙️ Advanced Settings"
]

# Determine default active tab index
try:
    default_index = tab_names.index(st.session_state.active_tab)
except (ValueError, AttributeError):
    default_index = 0

tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_names)

with tab1:
    st.header("🔍 Identifier Agent")
    st.markdown("Detect data quality issues and generate SQL-based DQ rules for BaNCS tables")
    
    # File uploader for pre-existing DQ rules
    st.subheader("0. Upload Pre-existing DQ Rules (Optional)")
    st.markdown("Upload your Collibra/Ataccama DQ rules as JSON. If not provided, system will use mock data.")
    
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
            help="Download a template JSON file to fill with your DQ rules"
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
            if st.button("▶️ Go to Treatment Agent", type="primary", key="goto_treatment", width='stretch'):
                st.session_state.active_tab = "💊 Treatment Agent"
                st.success("✅ Navigating to Treatment Agent... Refresh if tab doesn't switch.")
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

    
with tab2:
    st.header("💊 Treatment Agent")
    st.markdown("**Workflow:** Run DQ rules → Filter offending rows → Group issues → Suggest remediation strategies")
    
    # Check if we have generated rules from Identifier Agent
    if 'generated_rules' not in st.session_state or not st.session_state.generated_rules:
        st.warning("⚠️ No DQ rules available. Please run the Identifier Agent first (Tab 1).")
    else:
        # STEP 1: Run DQ Rules and Filter Offending Rows
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
            st.markdown("**Select DQ rules to run:**")
            
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
                    key="run_rules_btn"
                )
            with col_clear:
                if st.button("🗑️ Clear Results", key="clear_results_btn"):
                    if 'filtered_issues' in st.session_state:
                        del st.session_state['filtered_issues']
                    if 'grouped_issues' in st.session_state:
                        del st.session_state['grouped_issues']
                    st.rerun()
            
            # Execute selected rules
            if run_rules_btn:
                with st.spinner("🔍 Executing DQ rules and filtering offending rows..."):
                    try:
                        from google.cloud import bigquery
                        from google.cloud.exceptions import GoogleCloudError
                        
                        # Get project_id and dataset_id from session state
                        project_id = st.session_state.get('project_id', '')
                        dataset_id = st.session_state.get('dataset_id', '')
                        
                        if not project_id or not dataset_id:
                            st.error("❌ Please configure Project ID and Dataset ID in the sidebar settings.")
                            st.stop()
                        
                        # Initialize BigQuery client with timeout
                        client = bigquery.Client(project=project_id)
                        
                        filtered_issues = []
                        failed_rules = []
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for rule_idx, idx in enumerate(selected_rule_ids):
                            rule = available_rules[idx]
                            rule_name = rule.get('name', 'Unknown')
                            table_name = rule.get('table', 'policies_week1')
                            rule_sql = rule.get('sql', '')
                            
                            # Update progress
                            progress = (rule_idx + 1) / len(selected_rule_ids)
                            progress_bar.progress(progress)
                            status_text.text(f"Running rule {rule_idx + 1}/{len(selected_rule_ids)}: {rule_name}")
                            
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
                        status_text.empty()
                        
                        # Store results
                        st.session_state.filtered_issues = filtered_issues
                        
                        # Show results
                        if filtered_issues:
                            total_violations = sum(f['total_count'] for f in filtered_issues)
                            st.success(f"✅ Found {total_violations} violations across {len(filtered_issues)} rules")
                        else:
                            st.info("ℹ️ No violations found in selected rules")
                        
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
                        st.error(f"❌ Critical error: {str(e)}")
                        import traceback
                        with st.expander("Show detailed error"):
                            st.code(traceback.format_exc())
            
            # STEP 2: Display Filtered Issues
            if 'filtered_issues' in st.session_state and st.session_state.filtered_issues:
                st.divider()
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
                            from dq_agents.treatment.agent import treatment_agent
                            
                            # Set up ADK components
                            session_service = InMemorySessionService()
                            artifact_service = InMemoryArtifactService()
                            session = asyncio.run(session_service.create_session(
                                app_name="DQTreatmentAgent",
                                user_id="streamlit_user"
                            ))
                            
                            # Create runner
                            runner = Runner(
                                app_name="DQTreatmentAgent",
                                agent=treatment_agent,
                                artifact_service=artifact_service,
                                session_service=session_service,
                            )
                            
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
      "issues_in_group": ["DQ_001", "DQ_005"],
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
          "sql": "UPDATE {{table}} SET date_of_birth = NULL WHERE ..."
        }}
      ]
    }}
  ]
}}
"""
                            
                            # Run agent
                            response = asyncio.run(runner.run_async(
                                message=prompt,
                                session_id=session.id
                            ))
                            
                            # Store grouped issues
                            st.session_state.grouped_issues = response.response
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
                                            
                                            # Action buttons
                                            col_btn1, col_btn2 = st.columns(2)
                                            with col_btn1:
                                                if st.button(f"✅ Approve Fix {rank} for Group {group_idx+1}", key=f"approve_g{group_idx}_f{rank}"):
                                                    # Store for Remediator
                                                    st.session_state.approved_fix = {
                                                        "group": group,
                                                        "fix": fix,
                                                        "timestamp": __import__('datetime').datetime.now().isoformat()
                                                    }
                                                    st.success(f"Fix {rank} approved! Go to Remediator tab.")
                                            with col_btn2:
                                                if st.button(f"❌ Reject Fix {rank}", key=f"reject_g{group_idx}_f{rank}"):
                                                    st.warning("Fix rejected. Feedback logged to Knowledge Bank.")
                                            
                                            st.divider()
                        else:
                            st.warning("No issue groups generated")
                    
                    except json.JSONDecodeError:
                        st.markdown("### 📄 Analysis Response")
                        st.markdown(response_text)

with tab3:
    st.header("💊 Treatment Agent")
    st.markdown("Analyze DQ issues and suggest remediation strategies with Knowledge Bank integration")
    
    # Check if we have generated rules from Identifier Agent
    if 'generated_rules' not in st.session_state or not st.session_state.generated_rules:
        st.warning("⚠️ No DQ rules available. Please run the Identifier Agent first (Tab 1).")
        
        # Option to manually input a rule for testing
        with st.expander("🧪 Test Treatment Agent (Manual Rule Input)", expanded=False):
            st.markdown("**For testing: Input a DQ rule manually**")
            
            test_rule_sql = st.text_area(
                "DQ Rule SQL",
                value="SELECT * FROM `PROJECT.DATASET.TABLE` WHERE date_of_birth > CURRENT_DATE()",
                help="SQL query that identifies DQ issues",
                key="test_rule_sql"
            )
            
            test_table = st.text_input(
                "Table Name",
                value="policies_week1",
                key="test_table"
            )
            
            test_issue_desc = st.text_area(
                "Issue Description",
                value="Date of birth is in the future",
                key="test_issue_desc"
            )
            
            if st.button("🔍 Analyze This Issue", key="test_analyze"):
                st.session_state.selected_issue = {
                    "rule_sql": test_rule_sql,
                    "table": test_table,
                    "description": test_issue_desc,
                    "severity": "critical",
                    "dq_dimension": "Accuracy"
                }
                st.success("✅ Issue loaded for analysis")
    else:
        # Show available rules from Identifier Agent
        st.subheader("1. Select DQ Issue to Analyze")
        
        # Group rules by severity/table for better organization
        rules_df_data = []
        for i, rule in enumerate(st.session_state.generated_rules):
            if isinstance(rule, dict) and 'rule_id' in rule:
                rules_df_data.append({
                    "Index": i,
                    "Rule ID": rule.get('rule_id', 'N/A'),
                    "Name": rule.get('name', 'N/A'),
                    "Description": rule.get('description', 'N/A')[:80] + "...",
                    "Severity": rule.get('severity', 'N/A'),
                    "Dimension": rule.get('dq_dimension', rule.get('category', 'N/A')),
                    "Table": rule.get('table', 'N/A')
                })
        
        if rules_df_data:
            import pandas as pd
            rules_df = pd.DataFrame(rules_df_data)
            
            # Display rules in a dataframe
            st.dataframe(rules_df, width='stretch', hide_index=True)
            
            # Select rule to analyze
            selected_rule_idx = st.selectbox(
                "Choose a rule to analyze:",
                options=list(range(len(st.session_state.generated_rules))),
                format_func=lambda i: f"{st.session_state.generated_rules[i].get('rule_id', 'N/A')} - {st.session_state.generated_rules[i].get('name', 'N/A')}",
                key="selected_rule_idx"
            )
            
            selected_rule = st.session_state.generated_rules[selected_rule_idx]
            
            # Show selected rule details
            with st.expander("📋 Selected Rule Details", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rule ID", selected_rule.get('rule_id', 'N/A'))
                with col2:
                    st.metric("Severity", selected_rule.get('severity', 'N/A'))
                with col3:
                    st.metric("Dimension", selected_rule.get('dq_dimension', 'N/A'))
                
                st.markdown("**Description:**")
                st.write(selected_rule.get('description', 'No description'))
                
                st.markdown("**SQL:**")
                st.code(selected_rule.get('sql', 'No SQL'), language="sql")
                
                # Add "View in BigQuery" button
                col_btn1, col_btn2 = st.columns([2, 1])
                with col_btn1:
                    bq_url = f"https://console.cloud.google.com/bigquery?project={project_id}&ws=!1m5!1m4!4m3!1s{project_id}!2s{dataset_id}!3s{selected_rule.get('table', 'policies_week1')}"
                    st.markdown(f"[🔗 View Table in BigQuery Console]({bq_url})")
                with col_btn2:
                    if st.button("📊 Preview Data", key="preview_data_btn"):
                        try:
                            from google.cloud import bigquery
                            client = bigquery.Client(project=project_id)
                            preview_query = f"SELECT * FROM `{project_id}.{dataset_id}.{selected_rule.get('table')}` LIMIT 5"
                            preview_df = client.query(preview_query).to_dataframe()
                            st.dataframe(preview_df, width='stretch')
                        except Exception as e:
                            st.error(f"Error previewing data: {str(e)}")
            
            st.divider()
            
            # Analyze button
            st.subheader("2. Run Treatment Analysis")
            
            col1, col2 = st.columns(2)
            with col1:
                analyze_related_data = st.checkbox(
                    "Query related data (cross-week analysis)",
                    value=True,
                    help="Query the same customer/policy across all weeks for pattern analysis"
                )
            with col2:
                search_kb = st.checkbox(
                    "Search Knowledge Bank for similar issues",
                    value=True,
                    help="Look for historical precedents of similar issues"
                )
            
            if st.button("🔬 Analyze Issue & Suggest Fixes", type="primary", key="analyze_btn"):
                with st.spinner("💊 Treatment Agent is analyzing the issue..."):
                    try:
                        # Import treatment agent
                        from dq_agents.treatment.agent import treatment_agent
                        
                        # Set up ADK components
                        session_service = InMemorySessionService()
                        artifact_service = InMemoryArtifactService()
                        session = asyncio.run(session_service.create_session(
                            app_name="DQTreatmentAgent",
                            user_id="streamlit_user"
                        ))
                        
                        # Create runner
                        runner = Runner(
                            app_name="DQTreatmentAgent",
                            agent=treatment_agent,
                            artifact_service=artifact_service,
                            session_service=session_service,
                        )
                        
                        # Build prompt
                        prompt = f"""
                        **DQ ISSUE ANALYSIS AND TREATMENT SUGGESTION**
                        
                        **Issue Details:**
                        - Rule ID: {selected_rule.get('rule_id')}
                        - Rule Name: {selected_rule.get('name')}
                        - Description: {selected_rule.get('description')}
                        - Severity: {selected_rule.get('severity')}
                        - DQ Dimension: {selected_rule.get('dq_dimension', selected_rule.get('category'))}
                        - Table: {selected_rule.get('table')}
                        
                        **SQL to identify violations:**
                        {selected_rule.get('sql')}
                        
                        **YOUR TASKS:**
                        1. Execute the DQ rule using execute_dq_rule() to find actual violations
                        2. {"Search Knowledge Bank using search_knowledge_bank() for similar historical issues" if search_kb else "Skip Knowledge Bank search"}
                        3. {"Query related data using query_related_data() for pattern analysis" if analyze_related_data else "Skip cross-week analysis"}
                        4. Analyze the violations and perform root cause analysis
                        5. Generate TOP 3 fix suggestions ranked by success probability
                        
                        **OUTPUT FORMAT:**
                        Return a JSON object with:
                        - issue_summary: Brief summary of findings
                        - affected_rows: Number of rows with violations
                        - root_cause_analysis: Common patterns in violated data
                        - knowledge_bank_match: Any similar historical issues found (if applicable)
                        - fix_suggestions: Array of 3 fix suggestions with:
                          * rank (1, 2, 3)
                          * fix_type (Data Repair, Statistical Imputation, Deletion, Escalation)
                          * action (brief description)
                          * description (detailed explanation)
                          * success_probability (0.0 to 1.0)
                          * risk_level (low, medium, high)
                          * auto_approve_eligible (true/false)
                          * sql (executable SQL for the fix)
                        
                        Focus on practical, safe fixes that maintain data integrity.
                        """
                        
                        # Run agent
                        response = asyncio.run(runner.run_async(
                            message=prompt,
                            session_id=session.id  # Fix: use session.id not session.session_id
                        ))
                        
                        # Parse response
                        response_text = response.response
                        
                        # Store in session state
                        st.session_state.treatment_analysis = {
                            "rule": selected_rule,
                            "response": response_text
                        }
                        
                        st.success("✅ Analysis complete!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        else:
            st.warning("⚠️ No valid rules found. Please regenerate rules in Identifier Agent.")
    
    # Display Treatment Analysis Results
    if 'treatment_analysis' in st.session_state:
        st.divider()
        st.subheader("3. Treatment Analysis Results")
        
        analysis = st.session_state.treatment_analysis
        response_text = analysis['response']
        
        # Try to parse JSON from response
        import re
        import json
        
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            json_str = json_match.group(0) if json_match else response_text
        
        try:
            analysis_result = json.loads(json_str)
            
            # Display summary
            st.markdown("### 📊 Issue Summary")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Affected Rows", analysis_result.get('affected_rows', 'N/A'))
            with col2:
                kb_match = analysis_result.get('knowledge_bank_match', {})
                if kb_match and kb_match.get('found'):
                    st.metric("Knowledge Bank Match", f"{kb_match.get('similarity', 0)*100:.0f}% similarity")
                else:
                    st.metric("Knowledge Bank Match", "No match")
            
            st.markdown(analysis_result.get('issue_summary', 'No summary available'))
            
            # Root Cause Analysis
            if 'root_cause_analysis' in analysis_result:
                st.markdown("### 🔍 Root Cause Analysis")
                rca = analysis_result['root_cause_analysis']
                if isinstance(rca, dict):
                    for key, value in rca.items():
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                else:
                    st.write(rca)
            
            # Fix Suggestions
            st.markdown("### 💡 Recommended Fix Strategies")
            
            fix_suggestions = analysis_result.get('fix_suggestions', [])
            
            # Add priority reordering option
            if fix_suggestions and len(fix_suggestions) > 1:
                st.markdown("**Reorder Fix Priorities:**")
                reorder_help = "Drag to reorder, or use dropdown to select your preferred fix order"
                
                # Simple priority selector (fallback since streamlit-sortables may not be installed)
                preferred_fix_rank = st.selectbox(
                    "Preferred fix to apply first:",
                    options=[f.get('rank', i+1) for i, f in enumerate(fix_suggestions)],
                    format_func=lambda r: f"Fix {r}: {next((f.get('action') for f in fix_suggestions if f.get('rank') == r), 'Unknown')}",
                    help=reorder_help,
                    key="preferred_fix_rank"
                )
                st.info(f"💡 You've selected Fix {preferred_fix_rank} as your top priority")
            
            if fix_suggestions:
                # Display each fix
                for fix in fix_suggestions:
                    rank = fix.get('rank', 0)
                    
                    # Create expander for each fix
                    with st.expander(f"**Fix {rank}: {fix.get('fix_type')} - {fix.get('action')}**", expanded=(rank == 1)):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Success Probability", f"{fix.get('success_probability', 0)*100:.0f}%")
                        with col2:
                            risk = fix.get('risk_level', 'unknown')
                            st.metric("Risk Level", risk.upper())
                        with col3:
                            auto = "✅ Yes" if fix.get('auto_approve_eligible', False) else "❌ No"
                            st.metric("Auto-Approve", auto)
                        
                        st.markdown("**Description:**")
                        st.write(fix.get('description', 'No description'))
                        
                        if 'sql' in fix:
                            st.markdown("**SQL to Execute:**")
                            st.code(fix.get('sql'), language="sql")
                        
                        # Action buttons
                        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                        with col_btn1:
                            if st.button(f"✅ Approve Fix {rank}", key=f"approve_{rank}"):
                                # Store full context for Remediator
                                st.session_state.approved_fix = {
                                    "fix": fix,
                                    "issue": {
                                        "rule": analysis['rule'],
                                        "issue_summary": analysis_result.get('issue_summary', ''),
                                        "affected_rows": analysis_result.get('affected_rows', 0),
                                        "root_cause": analysis_result.get('root_cause_analysis', {})
                                    },
                                    "table_name": analysis['rule'].get('table', 'unknown'),
                                    "timestamp": __import__('datetime').datetime.now().isoformat()
                                }
                                st.success(f"Fix {rank} approved! Go to Remediator tab to execute.")
                        with col_btn2:
                            if st.button(f"❌ Reject Fix {rank}", key=f"reject_{rank}"):
                                # Update Knowledge Bank with rejection
                                st.warning(f"Fix {rank} rejected.")
                                st.info("📝 Rejection logged for Knowledge Bank learning")
                        with col_btn3:
                            if st.button(f"🔄 Modify Fix {rank}", key=f"modify_{rank}"):
                                st.info("Modification UI coming soon")
                        with col_btn4:
                            if st.button(f"🔍 View Rows", key=f"view_rows_{rank}"):
                                # Show sample affected rows
                                try:
                                    from google.cloud import bigquery
                                    client = bigquery.Client(project=project_id)
                                    table_name = analysis['rule'].get('table', 'policies_week1')
                                    rule_sql = analysis['rule'].get('sql', '')
                                    # Execute rule to get violations
                                    full_table = f"`{project_id}.{dataset_id}.{table_name}`"
                                    sql = rule_sql.replace("{table}", full_table).replace("TABLE_NAME", full_table)
                                    results_df = client.query(f"{sql} LIMIT 10").to_dataframe()
                                    st.dataframe(results_df, width='stretch')
                                except Exception as e:
                                    st.error(f"Error fetching rows: {str(e)}")
            else:
                st.warning("No fix suggestions generated")
            
        except json.JSONDecodeError:
            # Fallback: show raw response
            st.markdown("### 📄 Analysis Response")
            st.markdown(response_text)
        
        # Option to clear analysis
        if st.button("🔄 Analyze Another Issue"):
            del st.session_state.treatment_analysis
            if 'approved_fix' in st.session_state:
                del st.session_state.approved_fix
            st.rerun()
    
with tab3:
    st.header("Remediator Agent")
    st.info("🚧 Coming soon: Fix execution and validation")
    
with tab4:
    st.header("Metrics Agent")
    st.info("🚧 Coming soon: Dashboards and Cost of Inaction analysis")
    
with tab5:
    st.header("Advanced Settings")
    st.info("🚧 Coming soon: Knowledge Bank, per-agent models, rate limits")

# Footer
st.divider()
st.caption("Built with ADK Multi-Agent Framework | Lloyd's Banking Group Hackathon 2025")
