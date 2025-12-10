Here is the complete Markdown conversion of your second PDF ("DA Session @LBG_ BQ, Dataplex & AI Features.pdf").

---

# Introduction to GCP Data Analytics Services

**Presented to:** Lloyds Bank  **Date:** 25th Nov 2025  **Status:** Proprietary & Confidential

---

## Contents

> [Image Note: Title Graphic]
>
> A stylized illustration of a city skyline with a bank building in the center, representing the corporate environment.

**Agenda:**

1. **Overview of Data & Analytics Services** (10 min)
2. **Deep Dive: BigQuery & Dataplex** (25 min)
3. **Demo** (~15 min)
4. **QnA** (10 min)

---

## A Comprehensive Data Analytics Platform

> [Image Note: Platform Architecture]
>
> A flowchart showing the data lifecycle from ingestion to usage.

### Capture

- **Data ingestion at any scale:**

    - Pub/Sub
    - Cloud Data Fusion
    - Data Transfer Service
    - Storage Transfer Service
    - Datastream

### Process

- **Reliable data pipelines:**

    - Dataflow
    - Dataproc
    - Cloud Composer

### Store

- **Data lake and data warehousing:**

    - Cloud Storage
    - BigQuery storage
    - Dataplex Universal catalog

### Analyze

- **Data warehousing & Advanced analytics:**

    - BigQuery analysis engine
    - Vertex AI
    - TensorFlow
    - Serverless Spark

### Use

- **Share / Secure sharing:**

    - Looker
    - Sheets
    - Analytics Hub
    - BigQuery Data Sharing

---

## BigQuery Overview

> [Image Note: BigQuery Core]
>
> A circular diagram placing BigQuery at the center of Google's Data & AI Cloud.

**BigQuery is the heart of smart analytics platform**

- **Real-time insights:** From streaming data.
- **Built-in ML:** For out-of-the-box predictive insights.
- **BigQuery Omni:** Connected to data where it is.
- **Scale:** Gigabyte- to petabyte-scale storage and SQL queries.
- **Reliability:** Encrypted, durable, and highly available.
- **Performance:** High-speed, in-memory BI Engine, fully managed and serverless for maximum agility and scale.

---

## BigQuery Architecture Differentiation

> [Image Note: Architecture Diagram]
>
> Illustrates the separation of Storage (Colossus) and Compute (Borg), connected by a Petabit Network (Jupiter).

### Key Advantages

- **Decoupled storage and compute:** Provide maximum flexibility.
- **Storage:** Replicated, Distributed Storage (high durability).
- **Compute:** Scalable, Fast Compute (high availability).
- **Networking:** Petabit Network / Distributed Memory Shuffle.
- **Interfaces:** SQL:2011 Compliant, REST API, Web UI, CLI, Client Libraries in multiple languages.

### Business Impact

- **Time to value:** Data is instantly available for query; no warm-up or pre-loading needed.
- **Reliability:** Infrastructure failures don't impact running workloads.
- **Efficiency:** Idle capacity sharing built-in.
- **Unlimited scale:** Independent scaling of compute / storage without 'scale units' (VMs, accounts etc).

---

## BigQuery Interoperability

> [Image Note: Hub and Spoke Integration]
>
> BigQuery is shown in the center, connected to various services via different methods (API, Federation, External Functions).

- **BigQuery Storage API:** High-performance API for Dataflow, Dataproc (including Serverless Spark), breaks down the Data Warehouse storage wall.
- **Storage Federation:** Easily integrate with data lakes and open formats on Google Cloud and on other clouds with BigQuery Omni (AWS, Azure).
- **Database Federation:** Query your Cloud SQL and Cloud Spanner instances directly from BigQuery, without moving data around.
- **External Functions:** Scalar user-defined external functions that provide BigQuery extensibility (e.g., via Cloud Functions).

---

## Ingestion Formats

> [Image Note: Performance Funnel]
>
> A visualization comparing file formats based on ingestion speed into BigQuery.

**Faster Ingestion:**

1. Avro (Compressed)
2. Avro (Uncompressed)
3. Parquet / ORC

**Slower Ingestion:**

4. CSV
5. JSON
6. CSV (Compressed)
7. JSON (Compressed)

---

## BigQuery AI: Democratizing AI and ML

> [Image Note: User Illustration]
>
> An illustration of a user sitting at a desk with a computer, looking at a cloud interface.

### Overall Product Areas in BQ AI

1. Machine Learning

- Feature engineering
- Model training
- Evals and explain
- Inference

2. Gen AI Functions

- General purpose AI functions: `ai.generate()` family, `ai.generate_text`.
- Managed AI functions: `ai.if`, `ai.score`, `ai.classify`.

3. Search and Vector Search

- Vector Search
- Keyword search / Hybrid Search
- Embeddings

4. Agents and Assistive AI

- Agents in BigQuery: Data Engineering Agent, Data Science Agent.
- Conversational Analytics API.
- Assistive AI in BigQuery: Data Canvas, Data Preparation.

5. Agent Tools

- MCP tools / ADK tools
- A2A
- Gemini CLI extensions
- MLops

---

## BigQuery ML (Structured Data)

**BigQuery ML makes AI super easy:**

- Train and deploy ML models in SQL.
- Execute ML workflows without moving data from BigQuery.
- Automate common ML tasks.
- Built-in infrastructure management, security & compliance.

### Use Case Mapping

|**Use Case**|**BQML Model type**|**Example use cases**|
|---|---|---|
|**Forecasting**|ARIMA PLUS X-REG (multivariate), TimesFM|• Forecasting demand for thousands of SKUs simultaneously<br><br>• Forecasting website traffic and infrastructure load|
|**Anomaly Detection**|Time series data: Arima plus Xreg<br><br>IID data: PCA, Autoencoder, Kmeans|• Anomaly detection on a time series of sensor data<br><br>• Anomaly detection on error events|
|**Regression and Classification**|Linear / Logistic Regression, Boosted Tree, AutoML, TabularFM (coming soon)|• Predicting churn, predicting purchase intent|
|**Clustering**|K-Means|• Creating customer segments for marketing|
|**Dimensionality Reduction**|PCA, Autoencoder|• Dimensionality reduction for downstream processing|
|**Recommendations**|Matrix Factorization, Wide and Deep|• Product recommendations, clustering with user and item embeddings|

---

## General Purpose AI Functions

> [Image Note: GenAI Workflow]
>
> Shows the flow from BigQuery (Cloud Data Warehouse) -> BigQuery ML (SQL interface to Vertex AI Gemini, 3P and OSS models) -> Vertex AI (GCP's AI Platform).

### Use Gemini Models in BigQuery

**1. Create remote model**

SQL

```
CREATE OR REPLACE MODEL bqml_tutorial.gemini_pro
REMOTE WITH CONNECTION `projects/vs-proj-1/locations/us/connections/connection_name`
OPTIONS (endpoint = 'gemini-flash')
```

**2. Predict (Use LLMs via SQL)**

SQL

```
SELECT
    ML.GENERATE_TEXT(
        MODEL bqml_tutorial.gemini_pro,
        (SELECT CONCAT("Which country is this city in:", city) AS prompt FROM example_table),
        STRUCT (0.2 AS temperature, 1024 AS max_output_tokens, TRUE AS flatten_json_output)
    )
```

- **Capabilities:** Execute Generative AI workflows inside BigQuery using BigQuery data.
- **Multimodal:** BigQuery supports structured, text, image, and video data.

---

## Key GenAI Features in BigQuery

- **Structured Data output (new):** Use `AI.GENERATE_TABLE` with a defined output schema (e.g., `STRUCT("age INT64, medications ARRAY<STRING>)`).
- **Table and row wise functions (new):** Use `AI.GENERATE("translate to french", movie_title)` directly in `SELECT` statements.
- **Multimodal:** Work with a table abstraction in BQ, with structured and unstructured data columns (Data stays in GCS). Process data with Gemini, embedding models, DocAI etc.
- **Choice of LLMs:** Gemini (Pro, Flash), Claude, Llama, any Hugging Face model (new).
- **Scalable & Pricing:**

    - Run OSS models on dedicated endpoints you can scale.
    - PT (Provisioned Throughput) support.
    - Gemini Batch inference calls are 50% cheaper (vs online inference).

### Use Cases

- **Entity extraction:** "Extract product name and size from the following text."
- **Data enrichment:** "Which country is this city in?"
- **Sentiment analysis:** "Give me the sentiment of the online reviews in column x."
- **Content generation:** "Create a customized marketing email based on the customer information in BQ table."
- **Video analysis:** "Summarize the content of the video."

---

## Agents and Assistive Capabilities: Data Preparation

> [Image Note: BigQuery Data Preparation UI]
>
> A screenshot of the "BigQuery Data Preparation" interface.
>
> * Main View: A spreadsheet-like view of data with columns like channel, impressions, clicks, campaign_date, etc.
>
> * **Sidebar (Right):** "Recommendations from Gemini." It suggests actions like "Standardize date format" and "Standardize phone numbers" with code previews and "Apply" buttons.
>
**Features:** AI powered insights to prepare your data.

**Engineer and Transform:**

- AI assisted visual data preparation in BigQuery.
- Visual wrangling.
- Intent Driven Pipeline Design.
- AI assisted data cleansing and data mapping.
- Version control & CI/CD.
- Orchestration & Monitoring.

---

## BigQuery Data Canvas

**GenAI-centric experience for accelerating your data to insights journey:**

- GenAI-centric experience for data exploration and visualization.
- Iterative and guided user experience.
- Embedded inside BigQuery Studio.
- Semantic data discovery supported by Dataplex catalog.
- Built-in collaboration for data analysts.
    

---

## Dataplex Universal Catalog

> [Image Note: Governance Wheel]
> 
> A circular diagram with "Dataplex Universal Catalog" in the center. Surrounding it are the core functions: Discover, Organize, Curate, Trust, Secure, Share. 120120120120

**Unified Data and AI Governance:**

1. **Universal Catalog for discovery and access:** One place to discover multi-format and multi-modal data to break down data silos. Powered by an AI-powered metadata knowledge graph. 121
    
2. **Build trust in well-governed data:** Ensure data accuracy and integrity with built-in profiling, data quality checks, and lineage. 122122122122
    
3. **Unified Security:** Simplify governance with centralized policy management and fine-grained access controls. 123
    
4. **Enable Openness and Interoperability:** Future-proof data architecture leveraging a single copy of data and unified runtime metastore across SQL, OSS engines, and AI/ML. 124
    

### Capabilities Overview & Roadmap

- **Discover:** GCP-wide cataloging, GCS metadata discovery, Managed connectivity for 3P data sources. 125
    
- **Understand:** Table-level lineage, Column-level lineage, Data profiling. 126
    
- **Trust:** Automated data quality, Governance center experience, Unified security experience. 127
    
- **Use:** BigQuery sharing, Marketplace integration, Universal semantic search, Business glossary, Automated metadata generation, Anomaly detection. 128
    

### Discovery Sources

**Automatic Cataloging across GCP Sources:** 129

- _Sources:_ Cloud SQL, Bigtable, Spanner, Looker, SDP, BigQuery (incl BigLake), GCS, DPMS, Pub/Sub, Vertex AI. 130
    
- Cataloging of features from Vertex AI (GA). 131
    
- Cataloging of metadata from Cloud SQL (GA). 132
    
- Catalog of notebooks from Dataform (Preview). 133
    

---

## Trust & Data Quality

> [Image Note: Data Quality Dashboard]
> 
> Screenshot of a "Data quality scan configuration" and results page.
> 
> * Header: chiago-taxi-trips-data-quality. 134* Timeline: Shows "Last 7 job results" with "Passed" status checks. 135* Rule List: A table showing rules applied to columns (e.g., dropoff_latitude -> Statistic Range Check). 136* Scorecard: Sidebar showing "Latest data quality status results" (Validity: Passed, Completeness: Passed, Uniqueness: Passed). 137

**Automatic Data Quality:**

- **Enable data quality at-scale:** Auto-generate data quality rules to measure for completeness, accuracy, and validity. 138
    
- **Serverless:** Run on a fully managed, serverless platform with zero copy execution. 139
    
- **Democratized quality insights:** Make quality information readily available alongside your table in BigQuery and Dataplex catalog. 140
    
- **Enable end-to-end observability:** Setup scheduled monitoring, alerts for anomalies, and view detailed table-level metrics. 141
    

---

## Demo & Closing

**Demo** 142

**Thank you** 143

> [Image Note: Closing Graphics]
> 
> Illustration of two people shaking hands/connecting pieces of a puzzle. 144