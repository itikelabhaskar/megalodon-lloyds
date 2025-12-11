# Specification.md

* Automating the clean-up of legacy BaNCS data. from Lloyd’s banking group \- Used for life insurance predictions   
* The given data is not the actual data, it is an example dataset with synthetic issues.  
* So hardcoding is not a good idea.

Build an agentic solution that detects, categorises, and remediates data quality issues autonomously; focus on large-scale anomaly detection and remediation.  
\-\> find all different issues

# Identifier agent

* Good UI for streamlit   
* Should be authenticated into gcp and be able to select the project and table   
* Then do the dataplex query \-\> profilers and quality  
* Run analysis and then the recommended queries by default   
* Add this along with an preexisting rules from colibra / Ataccama (convert to a sensible format) {Retrofit the old cases \-\> if needed spawn sub agent )  
* Now create the temporal (Example date of death shouldn’t be after the current week, alive or deceased status shouldn’t change down the line etc.), and sensible queries (underage in a location shouldn’t be able to work) etc)  
* Check for duplicates or similar rules (priority order)  
* Now display all the possible rules with good ui (and separate them between preexisting, dataplex and the agentic system  
* Allow user to select with dq rules to run   
* Create the needed tools for the same  
* 2 modes \- full new data or have already dq assured data

Clone ADK data science repo if need

Tools

* Web search  
* Dataplex

# Treatment agent 

* Runs the dq rules   
* Loops to check and find issue   
* Tries to find specific issues   
* Suggest solutions to the issues  
  * Queries the different profiles of the person across data and future data (Self heal)  
  * Replace with empty   
  * Replace with null  
  * Delete row  
  * Replace with the statistical mean   
  * Mark with warnings   
  * Raise lira ticket / mail   
* Rank and give top 3 issues for the the issue   
* Get human input   
* Use the knowledge bank and store the treatment strat (using **JSON or local FAISS vector store** for the Knowledge Bank.*Action:* Pre-populate the Knowledge Bank with 3 "Historical Fixes" (e.g., "If DOB \> 2025, set to NULL and Flag"). When the agent sees a similar issue, it should say: *"I found a precedent in the Knowledge Bank (85% similarity). Recommended Action: Set to Null."* This proves the "Memory" aspect without complex DB setup)  
  * The user can use set auto approval for issues.  
  * And the next time issue pops up it auto fixes   
* Button to look at the row or go to the data n GCP

# Remedifier agent  

* Try to apply the find and fix issue   
* Loop (self healing issues \-\> limit to 1 iteration for testing)  
* If fails the jira ticket or mail (group similar issues in a fix) \-\> don’t need to show the actual thing just JSON format example)

# Metrics agent

* Good UI  
* The flow needs to be understandable  
* Anomaly detection and prediction   
  * **Anomaly Detection:** Use a simple `IsolationForest` (sklearn) on the numerical columns to detect "Outliers" and tag them. It takes 5 lines of code but looks very advanced.  
* Power BI like interactive graphs 
* markdown reports   
* Need to be from the perspective of the user   
* Can be run independently to some extent  
* Key metric examples:  
  * Remediation Velocity: Average time to resolve an issue.  
  * Materiality Index: Financial/Regulatory impact score (High/Med/Low).  
  * Auto-Fix Rate: % of issues resolved without human touch (Target: \>80%).  
  * Cost of Inaction: Projected £ risk.  
  * Accuracy: False Positive Rate of the Identifier Agent.  
  * **"Cost of Inaction"** (Currency value). The judges specifically asked for this.  
* **Dynamic Storytelling**, not just charts.  
  *Action:* Instead of just a bar chart, generate a textual summary: *"This DQ issue affects £14M of policy value. The projected Cost of Inaction is £50k/month."* Use a simple math formula in the prompt to calculate "Materiality" (e.g., `Rows Affected * Avg Policy Value`).

# Key metrics

## Cost 

* Need model switcher  
* Need rate limits on the model

## Usability

* Need proper read me and tool tips 

## Explainability 

- Good system prompts  
- No bias prompting  
- Parametrized prompts   
- If possible,  RAG for better context. User can add relevant documentation to the data source to get better results (More priority than the web search)  
- Guard rails  
- 

## Interpretability

- ADK web  
  - The agents and their tools 

## Scalability

* Need to be able to scale to hundreds of rows    
* Possible because all the queries and the fixes are run in GCP itself  
* Cloud run agents

## Verifiability 

* Shadow Validation Sandbox: No fix is ever applied to Production blindly. The Remediator agent spins up a temporary "Shadow Table," applies the fix, runs regression tests, and only then commits.

## Capability

* Above conventional ML solutions \- above and beyond

—  
Bonus implementations

1. ### **"Agent Debate" Mode (Transparency)**

   The brief highlights a **"Multi-Agent System"**. You need to visualize that these are separate "brains" working together, not just one script.  
* **The Wow:** A "Live Logs" or "Thought Process" window. Show the agents "arguing" or collaborating.  
  * *Identifier Agent:* "I found a policy value of £200,000. This looks like an anomaly (\> £100k rule)."  
  * *Treatment Agent:* "Checking Knowledge Bank... Wait. This is a 'Jumbo Policy' type. Value is valid. Marking as False Positive."  
  * *Identifier Agent:* "Understood. Learning this exception."  
* **The "Cheat":** Use the `st.expander` in Streamlit to show the raw "Chain of Thought" text from the LLM response. It proves the AI is reasoning, not just matching regex.

2. ###  **Root Cause "Cluster Analysis" (Treatment Agent)**

   The brief asks for **"Root cause clustering"** and identifying anomalies.  
* **The Wow:** Instead of listing 100 separate errors, show a grouping.  
  * *Agent Output:* "I detected 50 'Invalid Date of Birth' errors. **Analysis:** 100% of these records were created by 'User\_System\_Legacy\_A' between 12:00 AM and 1:00 AM."  
* **The "Cheat":**  
  * Feed the metadata of the bad rows (Creation Date, Source System, Branch ID) into the LLM context.  
  * Prompt: *"Look at these error rows. What is the one common metadata attribute they all share? Tell the user this is the likely root cause."*  
  * **Why it wins:** It moves from "fixing data" to "fixing the process," which is high-value insight.

3. ###  **The "Time Travel" Diff View (Remediator Agent)**

   The brief requires you to **"identify... and if possible, attempts made to clean the data"**.  
* **The Wow:** Don't just show the fixed table. Show a **Side-by-Side Diff** before the user commits the fix.  
  * Left Column: "Original: 19-09-22023" (Red highlight)  
  * Right Column: "Proposed Fix: 19-09-2023" (Green highlight)  
  * Center: "Confidence Score: 98% (Based on historic pattern)."  
* **The "Cheat":** Use `pandas` to compare the two dataframes and `st.dataframe` with column highlighting. It makes the "Black Box" of AI safe and verifiable for the user.

